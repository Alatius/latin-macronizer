#!/usr/bin/python

import xml.etree.ElementTree as ET
import codecs

with codecs.open('ldt-corpus.txt', 'w', 'utf8') as pos_corpus_file:
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
    with codecs.open('corpus-supplement.txt', 'r', 'utf8') as supplement:
        for line in supplement:
            pos_corpus_file.write(line)
