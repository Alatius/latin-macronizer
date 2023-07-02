#!/usr/bin/python
# -*- coding: utf-8 -*-

import postags
from collections import defaultdict
import xml.etree.ElementTree as ET
import pprint

pp = pprint.PrettyPrinter()

tag_to_accents = defaultdict(list)
with open('macrons.txt', 'r', encoding='utf-8') as macrons_file, \
     open('rftagger-lexicon.txt', 'w', encoding='utf-8') as lexicon_file:
    for line in macrons_file:
        [wordform, tag, lemma, accented] = line.split()
        accented = accented.replace('_^', '').replace('^', '')
        tag_to_accents[tag].append(postags.unicodeaccents(accented))
        if accented[0].isupper():
            wordform = wordform.title()
        tag = '.'.join(list(tag))
        lexicon_file.write("%s\t%s\t%s\n" % (wordform, tag, lemma))


with open('macronized_endings.py', 'w', encoding='utf-8') as endings_file:
    endings_file.write('tag_to_endings = {\n')
    for tag in sorted(tag_to_accents):
        ending_freqs = defaultdict(int)
        for accented in tag_to_accents[tag]:
            for i in range(1, min(len(accented)-3, 12)):
                ending = accented[-i:]
                ending_freqs[ending] += 1
        relevant_endings = []
        for ending in ending_freqs:
            ending_without_macrons = postags.removemacrons(ending)
            if ending[0] != ending_without_macrons[0] and ending_freqs[ending] > ending_freqs.get(ending_without_macrons, 1):
                relevant_endings.append(ending)
        cleaned_list = [str(postags.escape_macrons(ending)) for ending in sorted(relevant_endings, key=lambda x: (-len(x), x))]
        endings_file.write("  '%s': %s,\n" % (str(tag), cleaned_list))
    endings_file.write('}\n')


with open('ldt-corpus.txt', 'w', encoding='utf-8') as pos_corpus_file:
    xsegment = ''
    xsegmentbehind = ''
    for f in ['1999.02.0010',
              '2008.01.0002',
              '2007.01.0001',
              '1999.02.0060',
              'phi0448.phi001.perseus-lat1',
              'phi0620.phi001.perseus-lat1',
              'phi0959.phi006.perseus-lat1',
              'phi0690.phi003.perseus-lat1']:
        bank = ET.parse('treebank_data/v1.6/latin/data/%s.tb.xml' % f)
        for sentence in bank.getroot():
            for token in sentence.findall('word'):
                idnum = int(token.get('id', '_'))
                head = int(token.get('head', '_'))
                relation = token.get('relation', '_')
                form = token.get('form', '_')
                lemma = token.get('lemma', form)
                postag = token.get('postag', '_')
                if form != '|' and postag != '' and postag != '_':
                    if lemma == 'other' and relation == 'XSEG' and head == idnum + 1:
                        xsegment = form
                        continue
                    if (lemma == 'que1' or lemma == 'ne1') and relation == 'XSEG' and head == idnum + 1:
                        xsegmentbehind = form
                        continue
                    postag = '.'.join(list(postag))
                    lemma = lemma.replace('#', '').replace('1', '').replace(' ', '+')
                    word = xsegment + form + xsegmentbehind
                    pos_corpus_file.write('%s\t%s\t%s\n' % (word, postag, lemma))
                    xsegment = ''
                    xsegmentbehind = ''
            pos_corpus_file.write('.\tu.-.-.-.-.-.-.-.-\tPERIOD1\n')
            pos_corpus_file.write('\n')
    with open('corpus-supplement.txt', 'r', encoding='utf-8') as supplement:
        for line in supplement:
            pos_corpus_file.write(line)


lemma_frequency = defaultdict(int)
word_lemma_freq = defaultdict(int)
wordform_to_corpus_lemmas = defaultdict(list)
with open('ldt-corpus.txt', 'r', encoding='utf-8') as pos_corpus_file:
    for line in pos_corpus_file:
        if '\t' in line:
            [wordform, _, lemma] = line.strip().split('\t')
            wordform = str(wordform)
            lemma = str(lemma)
            lemma_frequency[lemma] += 1
            word_lemma_freq[(wordform, lemma)] += 1
            if lemma not in wordform_to_corpus_lemmas[wordform]:
                wordform_to_corpus_lemmas[wordform].append(lemma)
with open('lemmas.py', 'w', encoding='utf-8') as lemma_file:
    lemma_file.write('lemma_frequency = %s\n' % pp.pformat(dict(lemma_frequency)))
    lemma_file.write('word_lemma_freq = %s\n' % pp.pformat(dict(word_lemma_freq)))
    lemma_file.write('wordform_to_corpus_lemmas = %s\n' % pp.pformat(dict(wordform_to_corpus_lemmas)))
