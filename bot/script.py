from future import standard_library
import gensim
import re
import os
import sys
import wget
from ufal.udpipe import Model, Pipeline
import pandas as pd
import numpy as np
import random

class KontaktModel:
    def num_replace(self, word):
        newtoken = 'x' * len(word)
        return newtoken

    def clean_token(self, token, misc):
        """
        :param token:  токен (строка)
        :param misc:  содержимое поля "MISC" в CONLLU (строка)
        :return: очищенный токен (строка)
        """
        out_token = token.strip().replace(' ', '')
        if token == 'Файл' and 'SpaceAfter=No' in misc:
            return None
        return out_token

    def clean_lemma(self, lemma, pos):
        """
        :param lemma: лемма (строка)
        :param pos: часть речи (строка)
        :return: очищенная лемма (строка)
        """
        out_lemma = lemma.strip().replace(' ', '').replace('_', '').lower()
        if '|' in out_lemma or out_lemma.endswith('.jpg') or out_lemma.endswith('.png'):
            return None
        if pos != 'PUNCT':
            if out_lemma.startswith('«') or out_lemma.startswith('»'):
                out_lemma = ''.join(out_lemma[1:])
            if out_lemma.endswith('«') or out_lemma.endswith('»'):
                out_lemma = ''.join(out_lemma[:-1])
            if out_lemma.endswith('!') or out_lemma.endswith('?') or out_lemma.endswith(',') \
                    or out_lemma.endswith('.'):
                out_lemma = ''.join(out_lemma[:-1])
        return out_lemma

    def list_replace(self, search, replacement, text):
        search = [el for el in search if el in text]
        for c in search:
            text = text.replace(c, replacement)
        return text

    def unify_sym(self, text):  # принимает строку в юникоде
        text = self.list_replace('\u00AB\u00BB\u2039\u203A\u201E\u201A\u201C\u201F\u2018\u201B\u201D\u2019', '\u0022',
                                 text)

        text = self.list_replace('\u2012\u2013\u2014\u2015\u203E\u0305\u00AF', '\u2003\u002D\u002D\u2003', text)

        text = self.list_replace('\u2010\u2011', '\u002D', text)

        text = self.list_replace(
            '\u2000\u2001\u2002\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u202F\u205F\u2060\u3000',
            '\u2002', text)

        text = re.sub('\u2003\u2003', '\u2003', text)
        text = re.sub('\t\t', '\t', text)

        text = self.list_replace(
            '\u02CC\u0307\u0323\u2022\u2023\u2043\u204C\u204D\u2219\u25E6\u00B7\u00D7\u22C5\u2219\u2062',
            '.', text)

        text = self.list_replace('\u2217', '\u002A', text)

        text = self.list_replace('…', '...', text)

        text = self.list_replace('\u2241\u224B\u2E2F\u0483', '\u223D', text)

        text = self.list_replace('\u00C4', 'A', text)  # латинская
        text = self.list_replace('\u00E4', 'a', text)
        text = self.list_replace('\u00CB', 'E', text)
        text = self.list_replace('\u00EB', 'e', text)
        text = self.list_replace('\u1E26', 'H', text)
        text = self.list_replace('\u1E27', 'h', text)
        text = self.list_replace('\u00CF', 'I', text)
        text = self.list_replace('\u00EF', 'i', text)
        text = self.list_replace('\u00D6', 'O', text)
        text = self.list_replace('\u00F6', 'o', text)
        text = self.list_replace('\u00DC', 'U', text)
        text = self.list_replace('\u00FC', 'u', text)
        text = self.list_replace('\u0178', 'Y', text)
        text = self.list_replace('\u00FF', 'y', text)
        text = self.list_replace('\u00DF', 's', text)
        text = self.list_replace('\u1E9E', 'S', text)

        currencies = list \
                (
                '\u20BD\u0024\u00A3\u20A4\u20AC\u20AA\u2133\u20BE\u00A2\u058F\u0BF9\u20BC\u20A1\u20A0\u20B4\u20A7\u20B0\u20BF\u20A3\u060B\u0E3F\u20A9\u20B4\u20B2\u0192\u20AB\u00A5\u20AD\u20A1\u20BA\u20A6\u20B1\uFDFC\u17DB\u20B9\u20A8\u20B5\u09F3\u20B8\u20AE\u0192'
            )

        alphabet = list \
                (
                '\t\n\r абвгдеёзжийклмнопрстуфхцчшщьыъэюяАБВГДЕЁЗЖИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ,.[]{}()=+-−*&^%$#@!~;:0123456789§/\|"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')

        alphabet.append("'")

        allowed = set(currencies + alphabet)

        cleaned_text = [sym for sym in text if sym in allowed]
        cleaned_text = ''.join(cleaned_text)

        return cleaned_text

    def process(self, pipeline, text='Строка', keep_pos=True, keep_punct=False):
        # Если частеречные тэги не нужны (например, их нет в модели), выставьте pos=False
        # в этом случае на выход будут поданы только леммы
        # По умолчанию знаки пунктуации вырезаются. Чтобы сохранить их, выставьте punct=True

        entities = {'PROPN'}
        named = False
        memory = []
        mem_case = None
        mem_number = None
        tagged_propn = []

        # обрабатываем текст, получаем результат в формате conllu:
        processed = pipeline.process(text)

        # пропускаем строки со служебной информацией:
        content = [l for l in processed.split('\n') if not l.startswith('#')]

        # извлекаем из обработанного текста леммы, тэги и морфологические характеристики
        tagged = [w.split('\t') for w in content if w]

        for t in tagged:
            if len(t) != 10:
                continue
            (word_id, token, lemma, pos, xpos, feats, head, deprel, deps, misc) = t
            token = self.clean_token(token, misc)
            lemma = self.clean_lemma(lemma, pos)
            if not lemma or not token:
                continue
            if pos in entities:
                if '|' not in feats:
                    tagged_propn.append('%s_%s' % (lemma, pos))
                    continue
                morph = {el.split('=')[0]: el.split('=')[1] for el in feats.split('|')}
                if 'Case' not in morph or 'Number' not in morph:
                    tagged_propn.append('%s_%s' % (lemma, pos))
                    continue
                if not named:
                    named = True
                    mem_case = morph['Case']
                    mem_number = morph['Number']
                if morph['Case'] == mem_case and morph['Number'] == mem_number:
                    memory.append(lemma)
                    if 'SpacesAfter=\\n' in misc or 'SpacesAfter=\s\\n' in misc:
                        named = False
                        past_lemma = '::'.join(memory)
                        memory = []
                        tagged_propn.append(past_lemma + '_PROPN')
                else:
                    named = False
                    past_lemma = '::'.join(memory)
                    memory = []
                    tagged_propn.append(past_lemma + '_PROPN')
                    tagged_propn.append('%s_%s' % (lemma, pos))
            else:
                if not named:
                    if pos == 'NUM' and token.isdigit():  # Заменяем числа на xxxxx той же длины
                        lemma = self.num_replace(token)
                    tagged_propn.append('%s_%s' % (lemma, pos))
                else:
                    named = False
                    past_lemma = '::'.join(memory)
                    memory = []
                    tagged_propn.append(past_lemma + '_PROPN')
                    tagged_propn.append('%s_%s' % (lemma, pos))

        if not keep_punct:
            tagged_propn = [word for word in tagged_propn if word.split('_')[1] != 'PUNCT']
        if not keep_pos:
            tagged_propn = [word.split('_')[0] for word in tagged_propn]
        return tagged_propn

    def process_wiki_data(self):
        def get_only_meanings(list_means_exmpls):
            return [mean[0] for mean in list_means_exmpls if len(mean[0])]

        self.wiki_data['mean_only'] = self.wiki_data.meanings.apply(get_only_meanings)
        self.wiki_data = self.wiki_data[['title', 'mean_only']]
        lst_col = 'mean_only'
        repeats = np.repeat(self.wiki_data['title'].values, self.wiki_data[lst_col].str.len())
        concats = [x for inner in self.wiki_data[lst_col] for x in inner]
        self.wiki_data = pd.DataFrame({'title': repeats, 'meaning': concats})

    def __init__(self):
        standard_library.install_aliases()
        self.wiki_data = pd.read_json('wiktionary_data0.json')
        # self.process_wiki_data()
        self.titles = self.wiki_data[['title', 'POS']]

        self.model = gensim.models.KeyedVectors.load('araneum_none_fasttextcbow_300_5_2018.model')

        # URL of the UDPipe model
        udpipe_model_url = 'https://rusvectores.org/static/models/udpipe_syntagrus.model'
        udpipe_filename = udpipe_model_url.split('/')[-1]

        if not os.path.isfile(udpipe_filename):
            print('UDPipe model not found. Downloading...', file=sys.stderr)
            wget.download(udpipe_model_url)

        self.ud_model = Model.load(udpipe_filename)

    def process_text(self, text):
        res = self.unify_sym(text.strip())
        output = self.process(
            Pipeline(self.ud_model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu'),
            text=res)
        return output

    def predict_word(self, text, prefix='а'):
        # TODO: ADD TEXT LEMMATIZATION
        words = text.split(' ')
        prefix_titles = self.titles[self.titles['title'].str.startswith(prefix)]
        if prefix_titles.empty:
            return ""
        prefix_titles = prefix_titles[prefix_titles.POS == 'noun']
        stats = prefix_titles['title'].map(lambda x: self.model.n_similarity([x], words))
        df = pd.DataFrame({'title': prefix_titles['title'],
                           'POS': prefix_titles['POS'],
                           'stats': stats})
        return df[df['stats'] == df['stats'].max()]['title'].values[0]
        # print(df.idxmax())
        # top_100 = self.model.most_similar(positive=text.split(' '), topn = 100)
        # top_100 = list(filter(lambda x: x[0].startswith(prefix), top_100))
        # top_100 = list(filter(
        #     lambda x: re.findall('_NOUN', self.process_text(x[0])[0]) != [],
        #                       top_100))
        # return top_100

    def get_random_word(self):
        t = self.titles
        return t[t.POS == 'noun'][t.title.str.islower()].sample(1)['title'].values[0]
       # return self.titles[self.titles.POS == 'noun']['titles'].sample(1).value[0]

    def close(self):
        del self.model

    def _get_titles(self):
        return self.titles


# kek = KontaktModel()
# print(kek.wiki_data.head())
# data = kek.wiki_data['title'][kek.wiki_data['title'].startswith('апе') == True]
# print(data.head())
# while 1:
#    msg = input('type msg\n')
#    prefix = input('type prefix\n')
#    print(kek.predict_word(msg, prefix=prefix))
# kek.close()
