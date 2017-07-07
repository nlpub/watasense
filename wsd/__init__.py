from collections import defaultdict
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import Pipeline

# Переменные базы данных
input_text = str()
synsets = {}  # Словарь {id -> список синсетов}
synonyms = {}  # Словарь {id -> список синонимов}
hyperonimuses = {}  # Словарь {id -> список гиперонимов}

index = defaultdict(list)  # Словарь {слово -> номера синсетов с упоминаниями}
lexicon = set()  # Набор всех слов в базе
v = Pipeline([('dict', DictVectorizer()), ('tfidf', TfidfTransformer())])

from .models import BaseWSD

# Загрузка базы данных из файлы
BaseWSD.loading_base()