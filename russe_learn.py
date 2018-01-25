import csv
import os
import sys
import numpy as np
import unicodedata
import re

import mnogoznal
from collections import namedtuple
from sklearn.metrics.pairwise import cosine_similarity as sim


def vectfunc(row, vectorList, meaninglist):
    wordMeaning = int(row.gold_sense_id)
    meaningVector = np.zeros((100,), dtype=float)
    for element in vectorList:
        meaningVector += element
    meaningVector = meaningVector / len(vectorList)
    vectorList = list()  # Обнулили список векторов предложений внутри смысла
    meaninglist.append(meaningVector)
    return wordMeaning, vectorList, meaninglist

def remove_accents(input_str):
    nfс_form = unicodedata.normalize('NFC', input_str)
    nfс_form = re.sub(r'[^А-Яа-яЁё\s]', u'', nfс_form, flags=re.UNICODE)
    return u"".join([c for c in nfс_form if not unicodedata.combining(c)])

WordBag = namedtuple('WordBag', 'context_id word gold_sense_id positions context')

# To do:
# Сделать переменными из консоли
# filename = 'D:\Documents\Study\Projects\GitHub\\russe-wsi-kit\data\main\wiki-wiki\\train.csv'
# outputName = 'D:\Documents\Study\Projects\GitHub\\russe-wsi-kit\data\main\wiki-wiki\\train.word2vec.csv'
filename = 'D:\Documents\Study\Projects\GitHub\\russe-wsi-kit\data\main\\bts-rnc\\train.csv'
outputName = 'D:\Documents\Study\Projects\GitHub\\russe-wsi-kit\data\main\\bts-rnc\\train.word2vec.csv'

# To do:
# Разобраться с Pyro, пока что запустить его не удалось
if 'W2V_PYRO' in os.environ:
    from mnogoznal.pyro_vectors import PyroVectors as PyroVectors
    w2v = PyroVectors(os.environ['W2V_PYRO'])
elif 'W2V_PATH' in os.environ:
    from gensim.models import KeyedVectors
    w2v = KeyedVectors.load_word2vec_format(os.environ['W2V_PATH'], binary=True, unicode_errors='ignore')
    w2v.init_sims(replace=True)
else:
    print('Please set the W2V_PYRO or W2V_PATH environment variable to enable the dense mode.', file=sys.stderr)

contextAll = ''
trainList = list()
# Считывание данных из файла
with open(filename, 'r', encoding='utf-8', newline='') as f:
    reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)

    next(reader, None)  # skip the headers

    # Считали исходные текст
    # Разбили его по колонкам
    # context_id - номер
    # word - слово
    # gold_sense_id - реальный номер значения
    # predict_sense_id - значение, которое будет сюда записано
    # positions - позиции слова (по символам)
    # context - контекст слова
    for row in reader:
        context = remove_accents(row[5])
        trainList.append(
            WordBag(context_id=int(row[0]),
                    word=row[1],
                    gold_sense_id=int(row[2]),
                    positions=row[4],
                    context=context
                    )
        )
        contextAll = contextAll + context + '\n\n'

contextMystemList = mnogoznal.mystem(contextAll)

wordDict = dict()  # Словарь вида { слово : список векторов значений }
meaninglist = list()  # Список векторов значений слова
vectorList = list()  # Список векторов предложений внутри одного значения
rowVectorList = list()  # Полный список векторов записей для дальнейшего подсчета
wordMeaning = 1
wordInitial = trainList[0].word

# Посчитать вектор предложения
for row in trainList:
    print(row.context_id)
    # Если наткнулись на новое слово
    # Заканчиваем список
    # Записываем в словарь прошлое слово
    if row.word != wordInitial:
        wordMeaning, vectorList, meaninglist = vectfunc(row, vectorList, meaninglist)
        wordDict[wordInitial] = meaninglist
        wordInitial = row.word
        meaninglist = list()  # Обнулили список векторов значений слова

    # Если наткнулись на новый смысл слова
    # То собираем общий вектор прошлого смысла слова
    elif int(row.gold_sense_id) != wordMeaning:
        wordMeaning, vectorList, meaninglist = vectfunc(row, vectorList, meaninglist)

    sentenceVectorList = list()
    vector = np.zeros((100,), dtype=float)
    length = 0
    try:
        sentence = contextMystemList[row.context_id - 1]
    except:
        rowVectorList.append(vector)
        continue

    # Перебираем слова в предложении и записываем их вектора в пределах одной записи таблицы
    for wordTuple in sentence:
        word = wordTuple[1]
        if (word in w2v) and (
                wordTuple[2] not in ['UNKNOWN', 'PR', 'ADV', 'CONJ', 'APRO', 'SPRO', 'ADVPRO', 'PART']) and (
                word != row.word):
            vector += w2v.word_vec(word)
            length += 1

    # Записали вектор одной записи
    if length != 0:
        vector = vector / length
        vectorList.append(vector)
        rowVectorList.append(vector)

#Не забыть записать последнее слово
wordMeaning, vectorList, meaninglist = vectfunc(row, vectorList, meaninglist)
wordDict[wordInitial] = meaninglist

# Выбор лучшего значения по векторам
resultList = list()
simList = list()
for row in trainList:
    originalVector = rowVectorList[int(row.context_id) - 1].reshape(1, -1)
    for wordVector in wordDict[row.word]:
        newVector = wordVector.reshape(1, -1)
        simList.append(sim(originalVector, newVector).item(0))

    resultList.append(simList.index(max(simList)) + 1)
    simList = list()

# To do:
# При записи приходится использовать escapechar для кавычек, попробовать исправить
with open(outputName, 'w', encoding='utf-8', newline='') as myfile:
    wr = csv.writer(myfile, quoting=csv.QUOTE_NONE, escapechar='\\')

    wr.writerow(['context_id\tword\tgold_sense_id\tpredict_sense_id\tpositions\tcontext'])
    for row in trainList:
        stroka = '\t'.join([
            str(row.context_id),
            row.word,
            str(row.gold_sense_id),
            str(resultList[row.context_id - 1]),
            row.positions,
            row.context
        ])
        wr.writerow([stroka])

        # wr.writerow(
        #     [str(row.context_id)] +
        #     [row.word] +
        #     [str(row.gold_sense_id)] +
        #     [str(resultList[row.context_id - 1])] +
        #     [row.positions] +
        #     [row.context]
        # )

# testFile = 'D:\Documents\Study\Projects\GitHub\\russe-wsi-kit\data\main\wiki-wiki\\trainTest.csv'
