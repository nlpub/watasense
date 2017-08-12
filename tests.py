import csv
import mnogoznal

sourse = 'watset-mcl-mcl-joint-exp-linked.tsv'
filename = 'standart/nouns.tsv'
wsd_class = mnogoznal.SparseWSD(inventory_path=sourse)

with open(filename, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)

    result_list = list()
    word_last = None
    for row in reader:
        word = row[3]
        lemma = row[0].split('.')[0]
        speech_part = row[0].split('.')[1]
        sentence_number = row[1].split('.')[3]

        if word[0] == ' ':
            word = word[1:]
        text = (row[2] + ' ' + row[3] + row[4]).replace('  ', ' ')
        spans = mnogoznal.mystem(text)
        result_synset = wsd_class.disambiguate_word(spans, word)
        result_string = str(lemma + '.' + speech_part + ' ' +
                            lemma + '.' + speech_part + '.instance.' + sentence_number + ' ' +
                            lemma + '.' + speech_part + '.' + str(result_synset))
        result_list.append(result_string)