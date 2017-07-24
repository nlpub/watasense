from .sparse_wsd import SparseWSD
from .mystem import mystem

# Загрузка базы данных из файла
#filename = 'D:\Documents\Study\Projects\Python\mnogoznal\watset-mcl-mcl-joint-exp-linked.tsv'
filename = 'watset-mcl-mcl-joint-exp-linked.tsv'
wsd = SparseWSD(filename=filename)