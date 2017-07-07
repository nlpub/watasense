import csv
import operator
import platform
import string
import os
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from subprocess import Popen, PIPE, STDOUT
from wsd import synsets, lexicon, index, v, synonyms, hyperonimuses


# Заполнение базы данных синсетов
class BaseWSD:

    # Извлечение слова из строки вида 'word#X:Y'
    @staticmethod
    def lexeme(str):
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

    # Загрузка БД из файла
    # Планируется переделать в одноразовую функцию
    @staticmethod
    def loading_base():
        # Считываем файл
        with open('watset-mcl-mcl-joint-exp-linked.tsv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)

            # Перебираем строки и заполняем переменные synsets и relations словами.
            # Ключи - номер строки (с единицы).
            # Значения - словари вида {слово -> частота}.
            for row in reader:
                synsets_dict = dict()
                synonyms_dict = dict()
                hyperonimuses_dict = dict()

                for word in row[2].split(', '):
                    if word:
                        key, value = BaseWSD.lexeme(word)
                        synonyms_dict[key] = value

                synonyms[int(row[0])] = synonyms_dict

                for word in row[4].split(', '):
                    if word:
                        key, value = BaseWSD.lexeme(word)
                        hyperonimuses_dict[key] = value

                hyperonimuses[int(row[0])] = hyperonimuses_dict
                synsets_dict = {**synonyms_dict, **hyperonimuses_dict}
                synsets[int(row[0])] = synsets_dict

                # Закидываем номер строки в index для каждого слова.
                for word in synsets[int(row[0])]:
                    index[word].append(int(row[0]))

                # Обновляем лексикон базы данных
                lexicon.update(synsets[int(row[0])])

        v.fit(synsets.values())


class RequestWSD:

    @staticmethod
    def mystem_func(text):
        """Возвращает список, состоящий из списков вида [token, lemma, pos]"""

        coding = 'UTF-8'
        if platform.system() == 'Windows':
            coding = 'cp866'

        # Выполнение команды mystem

        command = "mystem -e %s -nidsc" % (coding)
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        output = p.communicate(input=text.encode(coding))[0]

        # Обработка результата в считываемый вид (массив строк)
        string_output = str(output.decode(coding))

        # string_output = string_output[3:]  # В начале вывода стоит кавычка и перевод строки - не значащая информация
        string_output = string_output[:-2]  # В конце вывода стоит кавычка и перевод строки - не значащая информация

        string_output = string_output.replace("_", "")  # Убираем незначащий символ "_" в выводе
        sentences = string_output.split('\s')  # Деление вывода на предложения

        # Обработка каждого предложения по очереди
        # Результат каждого предложения - элемент списка sentences_array
        sentences_array = list()
        for sentence in sentences:
            if platform.system() == 'Windows':
                words = sentence.split(os.linesep)  # Деление предложений на слова
            else:
                words = sentence.split('\n')  # Деление предложений на слова
            words = [x for x in words if x != '']  # В некоторых местах появляются пустые элементы списка - удаляем

            # Обработка каждой строки так, чтобы получить для слова его токен, лемму и часть речи.
            # Результат для каждого слова записывается в список из трех элементов.
            # Все списки хранятся в списке words_array
            words_array = list()
            for word_line in words:
                start_index = word_line.find('{', )
                if start_index == -1:  # Случай, если попалось неизвестное слово
                    token = word_line
                    buf = [word_line, 'UNKNOWN']

                else:  # Случай, если попалось слово
                    end_index = len(word_line) - 1
                    token = word_line[:start_index]

                    # Отбрасываем лишнюю информацию
                    buf = word_line[start_index + 1:end_index].split(',')
                    buf = buf[0].split('=')
                    if len(buf) > 2:
                        del buf[2]

                # Оформляем результат в виде списка
                buf.insert(0, token)
                if len(buf) < 3:
                    buf.insert(2, 'UNKNOWN')
                words_array.append(buf)

            sentences_array.append(words_array)
        return sentences_array

    # Трансформируем слова в начальную форму для дальнейшего поиска по базе данных
    @staticmethod
    def initial_form(sentences):
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
    @staticmethod
    def cos_func(sentence_dict, word, relation):
        """Возвращает словарь векторных расстояний синсетов и предложений"""
        cos_result = dict()
        for i in index[word]:
            synset = synsets[i]
            if synset[word] == 1:
                sim = cosine_similarity(v.transform(synset), v.transform(sentence_dict)).item(0)
                sim = float("{0:.4f}".format(sim))
                if sim != 0:
                    cos_result[i] = sim
            elif relation is True:
                sim = cosine_similarity(v.transform(synset), v.transform(sentence_dict)).item(0)
                sim = float("{0:.4f}".format(sim))
                if sim != 0:
                    cos_result[i] = sim
        return cos_result

    # Поиск наилучшего синсета для ask_word из предложения words_list
    @staticmethod
    def cos_similar(words_list, ask_word):
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
        cos_result = RequestWSD.cos_func(words_dict, ask_word, False)
        if bool(cos_result):
            result = max(cos_result.items(), key=operator.itemgetter(1))[0]  # Поиск наилучшего значения

        # Если близкие слова из контекста не найдены,
        # то ищем близкие слова с учетом самого слова (понижается точность результата).
        else:
            words_dict[ask_word] = 1
            cos_result = RequestWSD.cos_func(words_dict, ask_word, False)
            if bool(cos_result):
                result = max(cos_result.items(), key=operator.itemgetter(1))[0]

            # Если не смогли найти набор близких слов, то ищем через вспомогательные слова
            else:
                cos_result = RequestWSD.cos_func(words_dict, ask_word, True)
                result = max(cos_result.items(), key=operator.itemgetter(1))[0]

        return result

    # Формируем список синсетов
    @staticmethod
    def text_of_synsets(initial_sentences):
        """Возвращает список предложений, каждое состоит из списка синсетов в соответствии со словом"""
        text_result = list()
        for sentence in initial_sentences:
            sentence_result = list()
            for word in sentence:
                if word in lexicon:
                    result = RequestWSD.cos_similar(sentence, word)
                    sentence_result.append(result)
                else:
                    sentence_result.append(None)
            text_result.append(sentence_result)
        return text_result

    # Возвращает список пар "исходное слово - синсет"
    @staticmethod
    def word_synset_pair(text_result, mystem_sentences):
        sentence_index = 0
        synset_text = list()
        for sentence_result in text_result:
            synset_sentence = list()
            word_index = 0
            for synset_number in sentence_result:
                initial_word = mystem_sentences[sentence_index][word_index][0]
                speech_part = mystem_sentences[sentence_index][word_index][2]
                if synset_number is not None:
                    synset_word = (initial_word, synset_number, speech_part)
                else:
                    synset_word = (initial_word, 'None', speech_part)

                synset_sentence.append(synset_word)
                word_index = word_index + 1

            synset_text.append(synset_sentence)
            sentence_index = sentence_index + 1
        return synset_text

    # Общая функция
    @staticmethod
    def wsd_func(input_text):
        mystem_sentences = RequestWSD.mystem_func(input_text)  # Cписок предложений, состоящий из списков [token, lemma, pos] для слов
        initial_sentences = RequestWSD.initial_form(mystem_sentences)  # Cписок предложений со списками слов в начальной форме
        text_result = RequestWSD.text_of_synsets(initial_sentences)  # Cписок предложений со списками синсетов слов
        result = RequestWSD.word_synset_pair(text_result, mystem_sentences)  # Список предложений с парой слово-синсет
        return result