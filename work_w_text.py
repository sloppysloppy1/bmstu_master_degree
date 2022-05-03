import re, string
import nltk
import sqlite3
import os
from os.path import basename, splitext
import pandas as pd
import numpy as np
from pymorphy2 import MorphAnalyzer
from nltk.corpus import stopwords
from math import log
from gensim.models import Word2Vec

path = 'files'
fds = sorted(os.listdir(path))

con = sqlite3.connect('db')
cur = con.cursor()
ex_cur = con.cursor()

morph = MorphAnalyzer()
unneeded_tags = ['INTJ', 'PRCL', 'CONJ', 'PREP', 'PRED', 'NPRO', 'NUMR', None]
needed_tags = ['NOUN', 'ADJF', 'ADJS', 'INFN', 'VERB', 'ADVB']

def preprocess(text):
    text = text.lower().strip()
    text = text.replace('-','')
    text = text.replace('_','')
    text = re.sub(r'\d',' ',text)
    text = re.findall(r'\w+', text)
    return text

def process_texts(fds = fds):
    for file in fds:
        bill_num = splitext(file)[0]
        cur.execute('select upd_flg, dl_flg from bills where bill_num = ?', (bill_num,))
        flags = cur.fetchone()
        upd_flg, dl_flg = flags[0], flags[1]
        if int(dl_flg) == 1 and int(upd_flg) == 0:
            print(bill_num, upd_flg, dl_flg)
            with open(path + '/' + file, 'r', encoding = 'utf-8') as f: #
                text = f.read()
            preprocessed_text = preprocess(text)
            normal_form_text = []
            for word in preprocessed_text:
                n_form_parser = morph.parse(word)
                is_name = any(tag in str(n_form_parser) for tag \
                    in ['Name', 'Surn', 'Patr', 'Geox', 'Abbr', 'Trad' \
                        'Subx', 'Supr', 'Qual',	'Apro',	'Anum',	'Poss',	\
                        'V-ey',	'V-oy',	'Cmp2',	'V-ej', 'Infr', 'Erro']) # проверка на имя и всякое другое
                n_form_parser = n_form_parser[0]
                n_form_word = n_form_parser.normal_form
                if n_form_word not in stopwords.words('russian'):
                    if n_form_parser.tag.POS in needed_tags and len(word) > 2:
                        if is_name == False:
                            normal_form_text.append(n_form_word)
            # записываем обработанный
            with open(path + '/' + file, 'w', encoding = 'utf-8') as f:
                f.write(" ".join(normal_form_text))
            ex_cur.execute('update bills set upd_flg = 1 where bill_num = ?', (bill_num,))
            con.commit()

tfidf = {}
idf = {}
def compile_tfidf(fds = fds):
    # строим idf
    for file in fds:
        bill_num = splitext(file)[0]
        with open(path + '/' + file, 'r', encoding = 'utf-8') as f:
            text = f.read().split()
        tfidf[bill_num] = dict.fromkeys(set(text), 0)
        for word in text:
            tfidf[bill_num][word] += 1
        for word in set(text):
            if word in idf:
                idf[word] += 1
            else:
                idf[word] = 1
    for word in idf.keys():
        idf[word] = log((len(fds) / idf[word]))
    # tfidf
    for file in fds:
        bill_num = splitext(file)[0]
        with open(path + '/' + file, 'r', encoding = 'utf-8') as f:
            text = f.read().split()
        for bill_num in tfidf:
            for word in tfidf[bill_num].keys():
                tfidf[bill_num][word] = tfidf[bill_num][word] / len(tfidf[bill_num]) * idf[word]

process_texts()
compile_tfidf()

df = {}
# частота
for bill_num in tfidf:
    arr = []
    for word in tfidf[bill_num].keys():
        arr.append(tfidf[bill_num][word])
    array_of_words = []
    # берем только больше персентиля
    for word in tfidf[bill_num].keys():
        if tfidf[bill_num][word] >= np.percentile(arr, 44):
            array_of_words.append(word)
    df[bill_num] = array_of_words

df = pd.DataFrame(list(df.items()), columns = ['bill_num', 'text'])

model = Word2Vec(df['text'])
learned_words = list(model.wv.vocab)
#print the learned words
print(learned_words)
print(w2vec)
#for elem in df:
    #print(elem, df[elem])
