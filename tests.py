import csv
import mnogoznal
import os
import sys

sourse = 'watset-mcl-mcl-joint-exp-linked.tsv'

filename = 'standart/nouns.tsv'
#filename = 'standart/verbs.tsv'

#wsd_class = mnogoznal.SparseWSD(inventory_path=sourse)

if 'PYRO4_W2V' in os.environ:
    w2v_type = 'pyro4'
    w2v_path = os.environ['PYRO4_W2V']
elif 'W2V_PATH' in os.environ:
    w2v_type = 'gensim'
    w2v_path = os.environ['W2V_PATH']
else:
    print('No word2vec model is loaded. Please set the PYRO4_W2V or W2V_PATH environment variable.',
          file=sys.stderr)
    exit()

wsd_class = mnogoznal.DenseWSD(inventory_path=sourse, w2v_type=w2v_type, w2v_path=w2v_path)

source_list = list()
text_string = str()

# Считывание данных из файла
with open(filename, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
    for row in reader:
        source_list.append(row)
        if len(text_string) > 0:
            text_string = text_string + '\n\n\t\n\n'
        text_string = text_string + (row[2] + ' ' + row[3] + row[4]).replace('  ', ' ')

f.close()

# Собираем все предложения в одну кучу
# И запихиваем в mystem (для экономии времени)
text_string = text_string + '\n\n\t'
text_mystem = mnogoznal.mystem(text_string)
text_mystem_list = list()
element_list = list()
for element in text_mystem:
    for subj in element:
        if subj[0] == '\\t':
            text_mystem_list.append(element_list)
            element_list = list()
        else:
            element_list.append(subj)

del text_mystem
del element
del element_list

index = 0

#new_file_name = 'nouns_test.key'
#new_file_name = 'verbs_test.key'

new_file_name = 'nouns_dense_test.key'
#new_file_name = 'verbs_dense_test.key'

with open(new_file_name, 'w', newline='') as myfile:
    wr = csv.writer(myfile, quoting=csv.QUOTE_NONE)
    for row in source_list:
        print(index)
        if index == 550:
            print('Hi')
        word = row[3]
        lemma = row[0].split('.')[0]
        speech_part = row[0].split('.')[1]
        sentence_number = row[1].split('.')[3]
        if word[0] == ' ':
            word = word[1:]

        spans = list()
        spans.append(text_mystem_list[index])
        result_synset = wsd_class.disambiguate_word(spans, word)
        result_string = str(lemma + '.' + speech_part + ' ' +
                            lemma + '.' + speech_part + '.instance.' + sentence_number + ' ' +
                            lemma + '.' + speech_part + '.' + str(result_synset))
        wr.writerow([result_string])
        index = index + 1