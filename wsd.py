#!/usr/bin/env python

import argparse
import string
import csv
import platform
import subprocess
import os
import operator
import sys
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from collections import defaultdict
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

parser = argparse.ArgumentParser(description='WSD.')
parser.add_argument('--inventory', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--mystem', required=True, type=argparse.FileType('rb'))
parser.add_argument('--mode', choices=('sparse', 'dense'), default='sparse', type=str)
parser.add_argument('--w2v', default=None, type=argparse.FileType('rb'))
args = parser.parse_args()

if args.mode == 'dense':
    if args.w2v is None:
        print('Please set the --w2v option to engage the dense mode.', file=sys.stderr)
        exit()

text = input()

# Извлечение слова из строки вида 'word#X:Y'
def lexeme(str):
    """Возвращает word, если вид word#X
    Возвращает word, freq, если вид word#X:freq
    """
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


synsets = {}  # Словарь {id -> список синсетов}
synonyms = {}  # Словарь {id -> список синонимов}
hypernyms = {}  # Словарь {id -> список гиперонимов}
index = defaultdict(list)  # Словарь {слово -> номера синсетов с упоминаниями}
lexicon = set()  # Набор всех слов в базе
v = Pipeline([('dict', DictVectorizer()), ('tfidf', TfidfTransformer())])

# Считываем файл
reader = csv.reader(args.inventory, delimiter='\t', quoting=csv.QUOTE_NONE)

# Перебираем строки и заполняем переменные synsets и relations словами.
# Ключи - номер строки (с единицы).
# Значения - словари вида {слово -> частота}.
for row in reader:
    synonyms_dict = dict()
    hypernyms_dict = dict()

    for word in row[2].split(', '):
        if word:
            key, value = lexeme(word)
            synonyms_dict[key] = value

    synonyms[int(row[0])] = synonyms_dict

    for word in row[4].split(', '):
        if word:
            key, value = lexeme(word)
            hypernyms_dict[key] = value

    hypernyms[int(row[0])] = hypernyms_dict
    synsets_dict = {**synonyms_dict, **hypernyms_dict}
    synsets[int(row[0])] = synsets_dict

    # Закидываем номер строки в index для каждого слова.
    for word in synsets[int(row[0])]:
        index[word].append(int(row[0]))

    # Обновляем лексикон базы данных
    lexicon.update(synsets[int(row[0])])

if args.mode == 'sparse':
    v.fit(synsets.values())

elif args.mode == 'dense':
    # Расчет плотных векторов для всех синсетов
    import numpy
    import gensim

    w2v = gensim.models.KeyedVectors.load_word2vec_format(args.w2v, binary=True, unicode_errors='ignore')
    w2v.init_sims(replace=True)

    synset_vector_dict = dict()
    for synset_id in synsets.keys():
        vector = numpy.zeros(w2v.vector_size)
        vector = vector.reshape(1, -1)
        word_count = 0
        for word in synsets[synset_id].keys():
            try:
                vector = vector + synsets[synset_id][word] * w2v[word].reshape(1, -1)
                word_count = word_count + 1
            except:
                continue
        if word_count > 0:
            synset_vector_dict[synset_id] = vector / word_count


def mystem_func(text):
    """Возвращает список, состоящий из списков вида [token, lemma, pos]"""

    coding = 'UTF-8'
    if platform.system() == 'Windows':
        coding = 'cp866'

    # Выполнение команды mystem
    command = "echo '%s' | '%s' -e %s -nidsc" % (text, args.mystem.name, coding)
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, )
    output = proc.communicate()[0]

    # Обработка результата в считываемый вид (массив строк)
    string_output = str(output.decode(coding))

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
            if len(word_line) == 1:  # Случай, если попался знак пунктуации
                token = word_line
                buf = [word_line, 'PUNC']

            else:  # Случай, если попалось слово
                start_index = word_line.find('{', )
                end_index = len(word_line) - 1
                token = word_line[:start_index]

                # Отбрасываем лишнюю информацию
                buf = word_line[start_index + 1:end_index].split(',')
                buf = buf[0].split('=')
                if len(buf) > 2:
                    del buf[2]

            # Оформляем результат в виде списка
            buf.insert(0, token)
            words_array.append(buf)

        sentences_array.append(words_array)
    return sentences_array


# Трансформируем слова в начальную форму для дальнейшего поиска по базе данных
def lemmatize(sentences):
    """Возвращает список предложений со списками слов в начальной форме"""
    initial_text_list = list()
    for sentence in sentences:
        initial_sentence_list = list()
        for word_array in sentence:
            initial_sentence_list.append(word_array[1])
        initial_text_list.append(initial_sentence_list)
    return initial_text_list


# Расчет векторного расстояния между словарем sentence_dict и синсетов, которые содержат word.
# relation - переменная bool, означает проверку либо близких слов (значение в синсете = 1),
# либо вспомогательных слов (значение в синсете < 1)
def cos_func(sentence_dict, word, relation):
    """Возвращает словарь векторных расстояний синсетов и предложений"""
    cos_result = dict()
    for i in index[word]:
        synset = synsets[i]
        if synset[word] == 1:
            sim = cosine_similarity(v.transform(synset), v.transform(sentence_dict)).item(0)
            if sim != 0:
                cos_result[i] = sim
        elif relation is True:
            sim = cosine_similarity(v.transform(synset), v.transform(sentence_dict)).item(0)
            if sim != 0:
                cos_result[i] = sim
    return cos_result


# Поиск наилучшего синсета для ask_word из предложения words_list
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
    cos_result = cos_func(words_dict, ask_word, False)
    if bool(cos_result):
        result = max(cos_result.items(), key=operator.itemgetter(1))[0]  # Поиск наилучшего значения

    # Если не смогли найти набор близких слов, то ищем через вспомогательные слова
    else:
        cos_result = cos_func(words_dict, ask_word, True)
        if bool(cos_result):
            result = max(cos_result.items(), key=operator.itemgetter(1))[0]

        # Если близкие слова из контекста не найдены,
        # то ищем близкие слова с учетом самого слова (понижается точность результата).
        else:
            words_dict[ask_word] = 1
            cos_result = cos_func(words_dict, ask_word, False)
            result = max(cos_result.items(), key=operator.itemgetter(1))[0]

    return result


# Поиск наилучшего синсета для каждого слова из предложения words_list с помощью векторов
def cos_similar_dense(words_list):
    """Возвращает номер синсета для слова в предложении"""

    sentence_vector = numpy.zeros(w2v.vector_size)
    sentence_vector = sentence_vector.reshape(1, -1)
    word_count = 0
    sentence_result = list()

    # Расчет плотного вектора для предложения
    for word in words_list:
        try:
            sentence_vector = sentence_vector + w2v[word].reshape(1, -1)
            word_count = word_count + 1
        except:
            continue
    if word_count > 0:
        sentence_vector = sentence_vector / word_count

    # Поиск наилучшего синсета для каждого слова из предложения
    for word in words_list:
        if word not in string.punctuation:
            sim_max_result = 0
            answer = 0
            for synset_number in index[word]:
                sim = cosine_similarity(synset_vector_dict[synset_number], sentence_vector).item(0)
                if sim > sim_max_result:
                    sim_max_result = sim
                    answer = synset_number
            if answer != 0:
                sentence_result.append(answer)
            else:
                sentence_result.append(None)
        else:
            sentence_result.append(None)

    return sentence_result


# Формируем список синсетов
def text_of_synsets(initial_sentences):
    """Возвращает список предложений, каждое состоит из списка синсетов в соответствии со словом"""
    text_result = list()
    for sentence in initial_sentences:
        sentence_result = list()
        for word in sentence:
            if word in lexicon:
                result = cos_similar(sentence, word)
                sentence_result.append(result)
            else:
                sentence_result.append(None)
        text_result.append(sentence_result)
    return text_result

# Формируем список синсетов
def text_of_synsets_dense(initial_sentences):
    """Возвращает список предложений, каждое состоит из списка синсетов в соответствии со словом"""
    text_result = list()
    for sentence in initial_sentences:
        sentence_result = cos_similar_dense(sentence)
        text_result.append(sentence_result)
    return text_result

# Вывод
# Возвращает список пар "исходное слово - синсет"
def word_synset_pair(text_result, mystem_sentences):
    sentence_index = 0
    synset_text = list()
    for sentence_result in text_result:
        synset_sentence = list()
        word_index = 0
        for synset_number in sentence_result:
            initial_word = mystem_sentences[sentence_index][word_index][0]
            lemma = mystem_sentences[sentence_index][word_index][1]
            #speech_part = mystem_sentences[sentence_index][word_index][2]
            if synset_number is not None:
                synset_word = (initial_word, synset_number, lemma)
            else:
                synset_word = (initial_word, 'None', lemma)

            synset_sentence.append(synset_word)
            word_index = word_index + 1

        synset_text.append(synset_sentence)
        sentence_index = sentence_index + 1
    return synset_text

mystem_sentences = mystem_func(text)  # Cписок предложений, состоящий из списков [token, lemma, pos] для слов
initial_sentences = lemmatize(mystem_sentences)  # Cписок предложений со списками слов в начальной форме
if args.mode == 'sparse':
    text_result = text_of_synsets(initial_sentences)  # Cписок предложений со списками синсетов слов
elif args.mode == 'dense':
    text_result = text_of_synsets_dense(initial_sentences)
else:
    print('Error in mode')
    exit()
result = word_synset_pair(text_result, mystem_sentences)  # Список предложений с парой слово-синсет

for sentence in result:
    for word in sentence:
        print(word[0], '\t', word[2], '\t', word[1])
    print()
