#!/usr/bin/python
# -*- coding: utf-8 -*-

import postags
import codecs

macronsfile = codecs.open("macrons-full.txt","r","utf8")
lexicon = codecs.open("rftagger-lexicon.txt","w","utf8")

tagtoaccents = {}

for line in macronsfile:
    [wordform, tag, lemma, accented] = line.split()
    tagtoaccents[tag] = tagtoaccents.get(tag,[]) + [postags.unicodeaccents(accented)]
    if accented[0].isupper():
        wordform = wordform.title()
    tag = '.'.join(list(tag))
    lexicon.write(wordform + '\t' + tag + '\t' + lemma + '\n')

def escapedaccents(txt):
    for replacement, source in [("a_",u"ā"),("e_",u"ē"),("i_",u"ī"),("o_",u"ō"),("u_",u"ū"),("y_",u"ȳ"),
                                ("A_",u"Ā"),("E_",u"Ē"),("I_",u"Ī"),("O_",u"Ō"),("U_",u"Ū"),("Y_",u"Ȳ")]:
        txt = txt.replace(source,replacement)
    return txt

endingsfile = codecs.open("macronized-endings.txt","w","utf8")
for tag in tagtoaccents:
    endingfreqs = {}
    for accented in tagtoaccents[tag]:
        for i in range(1,min(len(accented)-3, 12)):
            ending = accented[-i:]
            endingfreqs[ending] = endingfreqs.get(ending,0) + 1
    endingsfile.write(tag)
    relevantendings = []
    for ending in endingfreqs:
        endingwithoutmacrons = postags.removemacrons(ending)
        if ending[0] != endingwithoutmacrons[0] and endingfreqs[ending] > endingfreqs.get(endingwithoutmacrons, 1):
            relevantendings.append(ending)
    relevantendings.sort(lambda x,y: cmp(len(y), len(x)))
    for ending in relevantendings:
        endingsfile.write('\t' + escapedaccents(ending))
    endingsfile.write('\n')

