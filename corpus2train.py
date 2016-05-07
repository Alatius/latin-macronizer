#!/usr/bin/python

import xml.etree.ElementTree as ET
import codecs
import re

corpuspath = "treebank_data/v1.6/latin/data/"
supplement = codecs.open("corpus-supplement.txt","r","utf8")
treebankfile = codecs.open("ldt-corpus.txt","w","utf8")
vocabularyfile = codecs.open("ldt-vocabulary.txt","w","utf8")
vocabulary = set()

xsegment = ""
xsegmentbehind = ""
for f in ["1999.02.0010",
          "2008.01.0002",
          "2007.01.0001",
          "1999.02.0060",
          "phi0448.phi001.perseus-lat1",
          "phi0620.phi001.perseus-lat1",
          "phi0959.phi006.perseus-lat1",
          "phi0690.phi003.perseus-lat1"]:
    bank = ET.parse(corpuspath+f+".tb.xml")
    for sentence in bank.getroot():
        for token in sentence.findall('word'):
            idnum = token.get('id','_')
            head = token.get('head','_')
            relation = token.get('relation','_')
            form = token.get('form','_')
            lemma = token.get('lemma',form)
            postag = token.get('postag','_')
            if form != "|" and postag != "" and postag != "_":
                if lemma == "other" and relation == "XSEG" and int(head) == int(idnum) + 1:
                    xsegment = form
                    continue
                if (lemma == "que1" or lemma == "ne1") and relation == "XSEG" and int(head) == int(idnum) + 1:
                    xsegmentbehind = form
                    continue
                postag = '.'.join(list(postag))
                lemma = lemma.replace("#","").replace("1","").replace(" ","+")
                word = xsegment+form+xsegmentbehind
                treebankfile.write(word+"\t"+postag+"\t"+lemma+"\n")
                vocabulary.add(word)
                xsegment = ""
                xsegmentbehind = ""
        treebankfile.write(".\tu.-.-.-.-.-.-.-.-\tPERIOD1\n")
        treebankfile.write("\n")

for line in supplement:
    treebankfile.write(line)

for word in vocabulary:
    vocabularyfile.write(word+"\n")
