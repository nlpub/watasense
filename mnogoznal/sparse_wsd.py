import csv
import operator
import string
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from collections import defaultdict
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer


class SparseWSD:
    input_text = str()
    synsets = {}  # Словарь {id -> список синсетов}
    synonyms = {}  # Словарь {id -> список синонимов}
    hypernyms = {}  # Словарь {id -> список гиперонимов}
    index = defaultdict(list)  # Словарь {слово -> номера синсетов с упоминаниями}
    lexicon = set()  # Набор всех слов в базе
    v = Pipeline([('dict', DictVectorizer()), ('tfidf', TfidfTransformer())])

    # Конструктор класса
    # Считывание базы данных из файла
    def __init__(self, filename):
        # Считываем файл
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)

            # Перебираем строки и заполняем переменные synsets и relations словами.
            # Ключи - номер строки (с единицы).
            # Значения - словари вида {слово -> частота}.
            for row in reader:
                synonyms_dict = dict()
                hypernyms_dict = dict()

                for word in row[2].split(', '):
                    if word:
                        key, value = SparseWSD.lexeme(self, word)
                        synonyms_dict[key] = value

                self.synonyms[int(row[0])] = synonyms_dict

                for word in row[4].split(', '):
                    if word:
                        key, value = SparseWSD.lexeme(self, word)
                        hypernyms_dict[key] = value

                self.hypernyms[int(row[0])] = hypernyms_dict
                synsets_dict = {**synonyms_dict, **hypernyms_dict}
                self.synsets[int(row[0])] = synsets_dict

                # Закидываем номер строки в index для каждого слова.
                for word in self.synsets[int(row[0])]:
                    self.index[word].append(int(row[0]))

                # Обновляем лексикон базы данных
                self.lexicon.update(self.synsets[int(row[0])])

        self.v.fit(self.synsets.values())

    # Извлечение слова из строки вида 'word#X:Y'
    def lexeme(self, str):
        """Возвращает word, freq для word#X:freq"""
        if '#' in str:
            word, tail = str.split('#', 1)
        else:
            word, tail = str, None

        if tail:
            if ':' in tail:
                labels, tail = tail.split(':', 1)
            else:
                labels, tail = tail, None

        if tail:
            freq = float(tail)
        else:
            freq = 1

        return word, freq

    # Трансформируем слова в начальную форму для дальнейшего поиска по базе данных
    def lemmatize(self, sentences):
        """Возвращает список предложений со списками слов в начальной форме"""
        initial_text_list = list()
        for sentence in sentences:
            initial_sentence_list = list()
            for word_array in sentence:
                initial_sentence_list.append(word_array[1])
            initial_text_list.append(initial_sentence_list)
        return initial_text_list

    # Рассчет векторного расстояния между словарем sentence_dict и синсетов, которые содержат word.
    # relation - переменная bool, означает проверку либо близких слов (значение в синсете = 1),
    # либо вспомогательных слов (значение в синсете < 1)
    def cos_func(self, sentence_dict, word, relation):
        """Возвращает словарь векторных расстояний синсетов и предложений"""
        cos_result = dict()
        for i in self.index[word]:
            synset = self.synsets[i]
            if synset[word] == 1:
                sim = cosine_similarity(self.v.transform(synset), self.v.transform(sentence_dict)).item(0)
                sim = float("{0:.4f}".format(sim))
                if sim != 0:
                    cos_result[i] = sim
            elif relation is True:
                sim = cosine_similarity(self.v.transform(synset), self.v.transform(sentence_dict)).item(0)
                sim = float("{0:.4f}".format(sim))
                if sim != 0:
                    cos_result[i] = sim
        return cos_result

    # Поиск наилучшего синсета для ask_word из предложения words_list
    def cos_similar(self, words_list, ask_word):
        """Возвращает номер синсета для слова в предложении"""

        words_list = [x for x in words_list if x not in set(string.punctuation)]  # Удаляем знаки пунктуации
        words_list.remove(ask_word)  # Удаляем запрашиваемое слово для поиска только по контексту

        # Составляем словарь слов предложения
        words_dict = defaultdict(int)
        for word in words_list:
            if word in words_dict:
                words_dict[word] += 1
            else:
                words_dict[word] = 1

        # Находим расстояние только близких слов и только из контекста
        cos_result = self.cos_func(words_dict, ask_word, False)
        if bool(cos_result):
            result = max(cos_result.items(), key=operator.itemgetter(1))[0]  # Поиск наилучшего значения

        # Если не смогли найти набор близких слов, то ищем через вспомогательные слова
        else:
            cos_result = self.cos_func(words_dict, ask_word, True)
            if bool(cos_result):
                result = max(cos_result.items(), key=operator.itemgetter(1))[0]

            # Если близкие слова из контекста не найдены,
            # то ищем близкие слова с учетом самого слова (понижается точность результата).
            else:
                words_dict[ask_word] = 1
                cos_result = self.cos_func(words_dict, ask_word, False)
                result = max(cos_result.items(), key=operator.itemgetter(1))[0]

        return result

    # Формируем список синсетов
    def text_of_synsets(self, initial_sentences):
        """Возвращает список предложений, каждое состоит из списка синсетов в соответствии со словом"""
        text_result = list()
        for sentence in initial_sentences:
            sentence_result = list()
            for word in sentence:
                if word in self.lexicon:
                    result = self.cos_similar(sentence, word)
                    sentence_result.append(result)
                else:
                    sentence_result.append(None)
            text_result.append(sentence_result)
        return text_result

    # Возвращает список пар "исходное слово - синсет"
    def word_synset_pair(self, text_result, mystem_sentences):
        sentence_index = 0
        synset_text = list()
        for sentence_result in text_result:
            synset_sentence = list()
            word_index = 0
            for synset_number in sentence_result:
                initial_word = mystem_sentences[sentence_index][word_index][0]
                lemma = mystem_sentences[sentence_index][word_index][1]
                speech_part = mystem_sentences[sentence_index][word_index][2]
                if synset_number is not None:
                    synset_word = (initial_word, synset_number, speech_part, lemma)
                else:
                    synset_word = (initial_word, 'None', speech_part, lemma)

                synset_sentence.append(synset_word)
                word_index = word_index + 1

            synset_text.append(synset_sentence)
            sentence_index = sentence_index + 1
        return synset_text

    # Общая функция
    def disambiguate(self, mystem_sentences):
        initial_sentences = self.lemmatize(mystem_sentences)  # Cписок предложений со списками слов в начальной форме
        text_result = self.text_of_synsets(initial_sentences)  # Cписок предложений со списками синсетов слов
        result = self.word_synset_pair(text_result, mystem_sentences)  # Список предложений с парой слово-синсет
        return result