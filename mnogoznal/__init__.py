from .models import SparseWSD, mystem

# Загрузка базы данных из файла
filename = 'watset-mcl-mcl-joint-exp-linked.tsv'
wsd = SparseWSD(filename=filename)