import abc
import csv
from collections import namedtuple, defaultdict, OrderedDict, Counter
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity as sim
import numpy as np

STOP_POS = {'CONJ', 'INTJ', 'PART', 'PR', 'UNKNOWN'}

Synset = namedtuple('Synset', 'id synonyms hypernyms bag')

class BaseWSD(object):
    """
    Base class for word sense disambiguation routines. Should not be used.
    Descendant classes must implement the disambiguate_word() method.
    """

    __metaclass__ = abc.ABCMeta

    synsets = {}
    index = defaultdict(list)
    lexicon = set()

    def __init__(self, inventory_path):
        """
        During the construction, BaseWSD parses the given sense inventory file.
        """
        def field_to_bag(field):
            return {word: freq for record in field.split(', ')
                               for word, freq in (self.lexeme(record),)
                               if record}

        with open(inventory_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)

            for row in reader:
                id = row[0]

                synonyms  = field_to_bag(row[2])
                hypernyms = field_to_bag(row[4])

                self.synsets[id] = Synset(
                    id=id,
                    synonyms=synonyms,
                    hypernyms=hypernyms,
                    bag={**synonyms, **hypernyms}
                )

                for word in self.synsets[id].bag:
                    self.index[word].append(id)

                self.lexicon.update(self.synsets[id].bag.keys())

    def lexeme(self, record):
        """
        Parse the sense representations like 'word#sid:freq'.
        Actually, we do not care about the sid field because
        we use synset identifiers instead.
        """
        if '#' in record:
            word, tail = record.split('#', 1)
        else:
            word, tail = record, None

        if tail:
            if ':' in tail:
                sid, tail = tail.split(':', 1)
            else:
                sid, tail = tail, None

        if tail:
            freq = float(tail)
        else:
            freq = 1

        return word, freq

    def lemmatize(self, sentence):
        """
        This method transforms the given sentence into the dict that
        maps the word indices to their lemmas. It also excludes those
        words which part of speech is in the stop list.
        """
        return {i: lemma for i, (_, lemma, pos) in enumerate(sentence)
                if pos not in STOP_POS}

    @abc.abstractmethod
    def disambiguate_word(self, sentence, index):
        """
        Return word sense identifier for the given word in the sentence.
        """
        if not sentence or not isinstance(sentence, list):
            raise ValueError('sentence should be a list')

        if not isinstance(index, int) or index < 0 or index >= len(sentence):
            raise ValueError('index should be in [0...%d]' % len(sentence))

    def disambiguate(self, sentences):
        """
        Return word sense identifiers corresponding to the words
        in the given sentences.
        """
        result = []

        for sentence in sentences:
            sentence_result = OrderedDict()

            for index, span in enumerate(sentence):
                sentence_result[span] = self.disambiguate_word(sentence, index)

            result.append(sentence_result)

        return result

class SparseWSD(BaseWSD):
    """
    A simple sparse word sense disambiguation.
    """

    sparse = Pipeline([('dict', DictVectorizer()), ('tfidf', TfidfTransformer())])

    def __init__(self, inventory_path):
        super().__init__(inventory_path)
        self.sparse.fit([synset.bag for synset in self.synsets.values()])

    def disambiguate_word(self, sentence, index):
        super().disambiguate_word(sentence, index)

        lemmas = self.lemmatize(sentence)

        if index not in lemmas:
            return

        svector = self.sparse.transform(Counter(lemmas.values())) # sentence vector

        def search(query):
            """
            Map synset identifiers to the cosine similarity value.
            This function calls the function query(id) that retrieves
            the corresponding dict of words.
            """
            return Counter({id: sim(svector, self.sparse.transform(query(id))).item(0)
                           for id in self.index[lemmas[index]]})

        candidates = search(lambda id: self.synsets[id].synonyms)

        # give the hypernyms a chance if nothing is found
        if not candidates:
            candidates = search(lambda id: self.synsets[id].bag)

        if not candidates:
            return

        for id, _ in candidates.most_common(1):
            return id

class DenseWSD(BaseWSD):
    """
    A word sense disambiguation approach that is based on SenseGram.
    """

    class densedict(dict):
        """
        A handy dict that transforms a synset into its dense representation.
        """

        def __init__(self, synsets, sensegram):
            self.synsets   = synsets
            self.sensegram = sensegram

        def __missing__(self, id):
            value = self[id] = self.sensegram(self.synsets[id].bag.keys())
            return value

    def __init__(self, inventory_path, wv):
        super().__init__(inventory_path)
        self.wv = wv
        self.dense = self.densedict(self.synsets, self.sensegram)

    def sensegram(self, words):
        """
        This is a simple implementation of SenseGram.
        It just averages the embeddings corresponding to the given words.
        """
        vectors = self.words_vec(set(words))

        if not vectors:
            return None

        return np.mean(np.vstack(vectors.values()), axis=0).reshape(1, -1)

    def words_vec(self, words, use_norm=False):
        """
        Return a dict that maps the given words to their embeddings.
        """
        if callable(getattr(self.wv, 'words_vec', None)):
            return self.wv.words_vec(words, use_norm)

        return {word: self.wv.word_vec(word, use_norm) for word in words if word in self.wv}

    def disambiguate_word(self, sentence, index):
        super().disambiguate_word(sentence, index)

        lemmas = self.lemmatize(sentence)

        if index not in lemmas:
            return

        svector = self.sensegram(lemmas.values()) # sentence vector

        # map synset identifiers to the cosine similarity value
        candidates = Counter({id: sim(svector, self.dense[id]).item(0)
                              for id in self.index[lemmas[index]]})

        if not candidates:
            return None

        for id, _ in candidates.most_common(1):
            return id
