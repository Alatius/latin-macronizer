#!/usr/bin/python
# -*- coding: utf-8 -*-

import postags
import codecs
from collections import defaultdict

tag_to_accents = defaultdict(list)
with codecs.open('macrons.txt', 'r', 'utf8') as macrons_file, \
     codecs.open('rftagger-lexicon.txt', 'w', 'utf8') as lexicon_file:
    for line in macrons_file:
        [wordform, tag, lemma, accented] = line.split()
        accented = accented.replace('_^', '').replace('^', '')
        tag_to_accents[tag].append(postags.unicodeaccents(accented))
        if accented[0].isupper():
            wordform = wordform.title()
        tag = '.'.join(list(tag))
        lexicon_file.write("%s\t%s\t%s\n" % (wordform, tag, lemma))

with codecs.open('macronized-endings.txt', 'w', 'utf8') as endings_file:
    for tag in tag_to_accents:
        ending_freqs = defaultdict(int)
        for accented in tag_to_accents[tag]:
            for i in range(1, min(len(accented)-3, 12)):
                ending = accented[-i:]
                ending_freqs[ending] += 1
        endings_file.write(tag)
        relevant_endings = []
        for ending in ending_freqs:
            ending_without_macrons = postags.removemacrons(ending)
            if ending[0] != ending_without_macrons[0] and ending_freqs[ending] > ending_freqs.get(ending_without_macrons, 1):
                relevant_endings.append(ending)
        for ending in sorted(relevant_endings, key=len):
            endings_file.write('\t' + postags.escape_macrons(ending))
        endings_file.write('\n')

