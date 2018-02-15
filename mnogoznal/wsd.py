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

class Inventory(object):
    """Sense inventory representation and loader."""

    synsets = {}
    index = defaultdict(list)

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

Span = namedtuple('Span', 'token pos lemma index')

class BaseWSD(object):
    """
    Base class for word sense disambiguation routines. Should not be used.
    Descendant classes must implement the disambiguate_word() method.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, inventory):
        self.inventory = inventory

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

    def disambiguate(self, sentence):
        """
        Return word sense identifiers corresponding to the words
        in the given sentence.
        """
        result = OrderedDict()

        for index, span in enumerate(sentence):
            # here, span is (token, pos, lemma), but we also need index
            span = Span(*span, index)

            result[span] = self.disambiguate_word(sentence, index)

        return result

class OneBaseline(BaseWSD):
    def __init__(self):
        super().__init__(None)

    def disambiguate_word(self, sentence, index):
        super().disambiguate_word(sentence, index)
        return '1'

class SingletonsBaseline(BaseWSD):
    def __init__(self):
        super().__init__(None)

    def disambiguate_word(self, sentence, index):
        super().disambiguate_word(sentence, index)
        return str(index)

class SparseWSD(BaseWSD):
    """
    A simple sparse word sense disambiguation.
    """

    sparse = Pipeline([('dict', DictVectorizer()), ('tfidf', TfidfTransformer())])

    def __init__(self, inventory):
        super().__init__(inventory)
        self.sparse.fit([synset.bag for synset in self.inventory.synsets.values()])

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
                           for id in self.inventory.index[lemmas[index]]})

        candidates = search(lambda id: self.inventory.synsets[id].synonyms)

        # give the hypernyms a chance if nothing is found
        if not candidates:
            candidates = search(lambda id: self.inventory.synsets[id].bag)

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

    def __init__(self, inventory, wv):
        super().__init__(inventory)
        self.wv = wv
        self.dense = self.densedict(self.inventory.synsets, self.sensegram)

    def sensegram(self, words):
        """
        This is a simple implementation of SenseGram.
        It just averages the embeddings corresponding to the given words.
        """
        vectors = self.words_vec(set(words))

        if not vectors:
            return

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

        if svector is None:
            return

        # map synset identifiers to the cosine similarity value
        candidates = Counter({id: sim(svector, self.dense[id]).item(0)
                              for id in self.inventory.index[lemmas[index]]
                              if self.dense[id] is not None})

        if not candidates:
            return

        for id, _ in candidates.most_common(1):
            return id

class LeskWSD(BaseWSD):
    """
    A word sense disambiguation approach that is based on Lesk method. 
    """
    def __init__(self, inventory):
        super().__init__(inventory)

    def disambiguate_word(self, sentence, word_index):
        super().disambiguate_word(sentence, word_index)

        lemmas = self.lemmatize(sentence)

        if word_index not in lemmas:
            return

        mentions_dict = dict()
        for synset_number in self.inventory.index[lemmas[word_index]]:
            mentions_dict[synset_number] = 0
            for context_word in lemmas.values():
                if context_word != lemmas[word_index]:
                    if context_word in self.inventory.synsets[synset_number].synonyms:
                        mentions_dict[synset_number] = mentions_dict[synset_number] + 1
                    elif context_word in self.inventory.synsets[synset_number].hypernyms:
                        mentions_dict[synset_number] = mentions_dict[synset_number] + self.inventory.synsets[synset_number].hypernyms[context_word]

        if len(mentions_dict) > 0:
            return max(mentions_dict, key=mentions_dict.get)
        else:
            return
