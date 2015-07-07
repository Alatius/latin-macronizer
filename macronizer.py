#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Johan Winge
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

MACRONIZERLIB = '/path/to/the/latin-macronizer/'
MORPHEUSDIR = MACRONIZERLIB+'morpheus/'
RFTAGGERDIR = '/usr/local/bin/'
DBNAME = 'macronizer'
DBUSER = 'theusername'
DBPASSWORD = 'thepassword'
DBHOST = 'localhost'

import psycopg2
import cgi
from tempfile import mkstemp
import re
import sys
import os
import codecs
from itertools import izip
from xml.sax.saxutils import escape
sys.path.append(MACRONIZERLIB)
import postags

reload(sys)  
sys.setdefaultencoding('utf8')

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)
#enddef
def toascii(txt):
    for source, replacement in [(u"æ","ae"),(u"Æ","Ae"),(u"œ","oe"),(u"Œ","Oe"),
                                (u"ä","a"),(u"ë","e"),(u"ï","i"),(u"ö","o"),(u"ü","u"),(u"ÿ","u")]:
        txt = txt.replace(source,replacement)
    return txt
#enddef
def touiorthography(txt):
    for source, replacement in [(u"v","u"),(u"U","V"),(u"j","i"),(u"J",u"I")]:
        txt = txt.replace(source,replacement)
    return txt
#enddef

class Wordlist():
    def __init__(self):
        try:
            self.dbconn = psycopg2.connect("dbname='%s' host='%s' user='%s' password='%s'" % (DBNAME, DBHOST, DBUSER, DBPASSWORD))
            self.dbcursor = self.dbconn.cursor()
        except:
            raise Exception("Error: Could not connect to the database.")
        self.unknownwords = set() # Unknown to Morpheus
        self.formtolemmas = {}
        self.formtoaccent = {}
        self.formtotaglemmaaccents = {}
    #enddef
    def reinitializedatabase(self):
        self.dbcursor.execute("DROP TABLE IF EXISTS morpheus")
        self.dbcursor.execute("CREATE TABLE morpheus(id SERIAL PRIMARY KEY, wordform TEXT NOT NULL, morphtag TEXT, lemma TEXT, accented TEXT)")
        self.dbconn.commit()
        self.populatemorpheustable()
    #enddef
    def populatemorpheustable(self):
        vocabularyfile = codecs.open(MACRONIZERLIB + "ldt-vocabulary.txt","r","utf8")
        words = set()
        for word in vocabularyfile:
            words.add(word.strip().lower())
        self.crunchwords(words)
    #enddef
    def loadwords(self, words): # Expects a set of lowercase words
        unseenwords = set() # Previously not tested with Morpheus
        for word in words:
            if not self.loadword(word):
                unseenwords.add(word)
        if len(unseenwords) > 0:
            self.crunchwords(unseenwords)
            for word in unseenwords:
                if not self.loadword(word):
                    raise Exception("Error: Could not store "+word+" in the database.")
    #enddef
    def loadword(self, word):
        try:
            self.dbcursor.execute("SELECT wordform, morphtag, lemma, accented FROM morpheus WHERE wordform = %s", (word, ))
        except:
            raise Exception("Error: Database table is missing. Please initialize the database.")
        #endtry
        rows = self.dbcursor.fetchall()
        if len(rows) == 0:
            return False
        elif len(rows) == 1:
            [wordform, morphtag, lemma, accented] = rows[0]
            if accented == None:
                self.unknownwords.add(wordform)
            else:
                self.formtoaccent[wordform] = accented
        else:
            for [wordform, morphtag, lemma, accented] in rows:
                if morphtag == None or lemma == None:
                    raise Exception("Error 4: This should not happen.")
                self.formtolemmas[wordform] = self.formtolemmas.get(wordform,[]) + [lemma]
                self.formtotaglemmaaccents[wordform] = self.formtotaglemmaaccents.get(wordform,[]) + [(morphtag,lemma,accented)]
        return True
    #enddef
    def crunchwords(self, words):
        morphinpfd, morphinpfname = mkstemp()
        os.close(morphinpfd)
        crunchedfd, crunchedfname = mkstemp()
        os.close(crunchedfd)
        morphinpfile = codecs.open(morphinpfname, 'w', 'utf8')
        for word in words:
            morphinpfile.write(word.strip().lower()+'\n')
            morphinpfile.write(word.strip().capitalize()+'\n')
        morphinpfile.close()
        os.system("MORPHLIB="+MORPHEUSDIR+"stemlib "+MORPHEUSDIR+"bin/cruncher -L < "+morphinpfname+" > "+crunchedfname+" 2> /dev/null")
        os.remove(morphinpfname)
        with codecs.open(crunchedfname, 'r', 'utf8') as crunchedfile:
            morpheus = crunchedfile.read()
        os.remove(crunchedfname)
        crunchedwordforms = {}
        knownwords = set()
        for wordform, NLs in pairwise(morpheus.split("\n")):
            wordform = wordform.strip().lower()
            NLs = NLs.strip()
            crunchedwordforms[wordform] = crunchedwordforms.get(wordform,"") + NLs
        for wordform in crunchedwordforms:
            NLs = crunchedwordforms[wordform]
            parses = []
            for NL in NLs.split("<NL>"):
                NL = NL.replace("</NL>","")
                NLparts = NL.split()
                if len(NLparts) > 0:
                    parses += postags.Morpheus2Parses(wordform,NL)
            allaccenteds = set()
            filteredparses = []
            for parse in parses:
                lemma = parse[postags.LEMMA].replace("#","").replace("1","").replace(" ","+")
                parse[postags.LEMMA] = lemma
                accented = parse[postags.ACCENTEDFORM]
                if parse[postags.LEMMA].startswith("trans-") and accented[3] != "_": # Work around shortcoming in Morpheus
                    accented = accented[:3] + "_" + accented[3:]
                if accented == "male_":
                    accented = "male"
                parse[postags.ACCENTEDFORM] = accented
                # Remove highly unlikely alternatives:
                if accented not in ["me_nse_", "fabuli_s", "vi_ri_", "vi_ro_", "vi_rum", "vi_ro_rum", "vi_ri_s", "vi_ro_s"] and not (accented.startswith("vi_ct") and lemma == "vivo") and lemma not in ["pareas","de_-escendo", "de_-eo", "de_-edo", "Nus", "progredio"]:
                    allaccenteds.add(accented.lower())
                    filteredparses.append(parse)
            if len(allaccenteds) > 1:
                knownwords.add(wordform);
                for parse in filteredparses:
                    lemma = parse[postags.LEMMA]
                    accented = parse[postags.ACCENTEDFORM]
                    tag = postags.Parse2LDT(parse)
                    self.dbcursor.execute("INSERT INTO morpheus (wordform, morphtag, lemma, accented) VALUES (%s,%s,%s,%s)", (wordform, tag, lemma, accented))
            elif len(allaccenteds) == 1:
                knownwords.add(wordform);
                accented = allaccenteds.pop()
                self.dbcursor.execute("INSERT INTO morpheus (wordform, accented) VALUES (%s,%s)", (wordform, accented))
        ## The remaining were unknown to Morpheus:
        for wordform in words - knownwords:
            self.dbcursor.execute("INSERT INTO morpheus (wordform) VALUES (%s)", (wordform, ))
        ## Remove duplicates:
        self.dbcursor.execute("DELETE FROM morpheus USING morpheus m2 WHERE morpheus.wordform = m2.wordform AND (morpheus.morphtag = m2.morphtag OR morpheus.morphtag IS NULL AND m2.morphtag IS NULL) AND (morpheus.lemma = m2.lemma OR morpheus.lemma IS NULL AND m2.lemma IS NULL) AND morpheus.accented = m2.accented AND morpheus.id > m2.id")
        self.dbconn.commit()
    #enddef
#endclass

class Token:
    def __init__(self, token):
        self.tag = ""
        self.lemma = ""
        self.accented = ""
        self.macronized = ""
        self.token = postags.removemacrons(token)
        self.isword = re.match("[^\W\d_]", token, flags=re.UNICODE)
        self.isspace = re.match("\s", token, flags=re.UNICODE)
        self.isreordered = False
        self.startssentence = False
        self.endssentence = False
        self.isunknown = False
        self.isambiguous = False
    #enddef
    def split(self, pos, reorder):
        newtokena = Token(self.token[:-pos])
        newtokenb = Token(self.token[-pos:])
        newtokena.startssentence = self.startssentence
        if reorder:
            newtokenb.isreordered = True
            return [newtokenb, newtokena]
        else:
            return [newtokena, newtokenb]
    #enddef
    def show(self):
        print (self.token + "\t"  + self.tag + "\t" + self.lemma + "\t" + self.accented).expandtabs(16)
    #enddef
    def macronize(self, domacronize, alsomaius, performutov, performitoj):
        plain = self.token
        accented = self.accented
        if domacronize and alsomaius and 'j' in accented:
            if not accented.startswith(("bij", "fidej", "Foroj", "ju_rej", "multij", "praej", "quadrij", "rej", "retroj", "se_mij", "sesquij", "u_nij", "introj")):
                accented = re.sub('([aeiouy])(j[aeiouy])', r'\1_\2', accented)
        if not self.isword:
            self.macronized = plain
            return
        if (not domacronize or not "_" in accented) and not performutov and not performitoj:
            self.macronized = plain
            return
        if self.isreordered:
            self.macronized = plain
            if performutov and self.macronized.lower() == "ue":
                if self.macronized[0] == 'u':
                    self.macronized = 'v' + self.macronized[1]
                elif self.macronized[0] == 'U':
                    self.macronized = 'V' + self.macronized[1]
            return
        if plain == accented.replace("_",""):
            if domacronize:
                self.macronized = accented
                return
            else:
                self.macronized = plain
                return
        #endif
        def inscost(a):
            if a == '_':
                return 0
            return 2
        def subcost(p,a):
            if a == '_':
                return 100
            if (a in "IJij" and p in "IJij") or (a in "UVuv" and p in "UVuv"):
                return 1
            return 2
        def delcost(b):
            return 2
        #enddef
        n = len(plain) + 1
        m = len(accented) + 1
        distance = [[0 for i in range(m)] for j in range(n)]
        for i in range(1, n):
            distance[i][0] = distance[i-1][0] + delcost(plain[i-1])
        for j in range(1, m):
            distance[0][j] = distance[0][j-1] + inscost(accented[j-1])
        for i in range(1, n):
            for j in range(1, m):
                if toascii(plain[i-1].lower()) == toascii(accented[j-1].lower()):
                    distance[i][j] = distance[i-1][j-1]
                else:
                    rghtcost = distance[i-1][j] + delcost(plain[i-1])
                    diagcost = distance[i-1][j-1] + subcost(plain[i-1],accented[j-1])
                    downcost = distance[i][j-1] + inscost(accented[j-1])
                    distance[i][j] = min(rghtcost,diagcost,downcost)
        result = ""
        while i != 0 and j != 0:
            upcost = distance[i][j-1] if j > 0 else 1000
            diagcost = distance[i-1][j-1] if j > 0 and i > 0 else 1000
            leftcost = distance[i-1][j] if i > 0 else 1000
            if diagcost <= upcost and diagcost < leftcost: ## To-do: review the comparisons...
                i -= 1
                j -= 1
                if performutov and accented[j].lower() == 'v' and plain[i] == 'u':
                    result = 'v' + result
                elif performutov and accented[j].lower() == 'v' and plain[i] == 'U':
                    result = 'V' + result
                elif performitoj and accented[j].lower() == 'j' and plain[i] == 'i':
                    result = 'j' + result
                elif performitoj and accented[j].lower() == 'j' and plain[i] == 'I':
                    result = 'J' + result
                else:
                    result = plain[i] + result
            elif upcost <= diagcost and upcost <= leftcost:
                j -= 1
                if domacronize and accented[j] == '_':
                    result = "_" + result
            else:
                i -= 1
                result = plain[i] + result
        self.macronized = result
    #enddef
#endclass

class Tokenization:
    def __init__(self, text):
        self.tokens = []
        possiblesentenceend = False
        sentencehasended = True
        # This does not work?: [^\W\d_]+|\s+|([^\w\s]|[\d_])+
        for chunk in re.findall(u"[^\W\d_]+|\s+|[^\w\s]+|[\d_]+", text, re.UNICODE):
            token = Token(chunk)
            if token.isword:
                if sentencehasended:
                    token.startssentence = True
                sentencehasended = False
                possiblesentenceend = (len(token.token) > 1)
            elif possiblesentenceend and any(i in token.token for i in '.;:?!'):
                token.endssentence = True
                possiblesentenceend = False
                sentencehasended = True
            self.tokens.append(token)
    #enddef
    def allwordforms(self):
        words = set()
        for token in self.tokens:
            if token.isword:
                words.add(toascii(token.token).lower())
        return words
    #enddef
    dividenda = {"nequid":4, "attamen":5, "unusquisque":7, "unaquaeque":7, "unumquodque":7, "uniuscuiusque":8, "uniuscujusque":8,
                 "unicuique":6, "unumquemque":7, "unamquamque":7, "unoquoque":6, "unaquaque":6,
                 "cuiusmodi":4, "cujusmodi":4, "quojusmodi":4, "eiusmodi":4, "ejusmodi":4, "huiuscemodi":4, "hujuscemodi":4,
                 "huiusmodi":4, "hujusmodi":4, "istiusmodi":4, "nullomodo":4, "quodammodo":4,
                 "nudiustertius":7, "nonnisi":4, "plusquam":4, "proculdubio":5, "quamplures":6, "quamprimum":6,
                 "quinetiam":5, "uerumetiam":5, "verumetiam":5, "verumtamen":5, "uerumtamen":5,
                 "paterfamilias":8, "patrisfamilias":8, "patremfamilias":8, "patrifamilias":8, "patrefamilias":8, "patresfamilias":8,
                 "patrumfamilias":8, "patribusfamilias":8, "materfamilias":8, "matrisfamilias":8, "matremfamilias":8, "matrifamilias":8,
                 "matrefamilias":8, "matresfamilias":8, "matrumfamilias":8, "matribusfamilias":8,
                 "respublica":7, "reipublicae":8, "rempublicam":8, "senatusconsultum":9, "senatusconsulto":8, "senatusconsulti":8,
                 "usufructu":6, "usumfructum":7, "ususfructus":7, "supradicti":5, "supradictum":6, "supradictus":6, "supradicto":5,
                 "seipse":4, "seipsa":4, "seipsum":5, "seipsam":5, "seipso":4, "seipsos":5, "seipsas":5, "seipsis":5,
                 "semetipse":4, "semetipsa":4, "semetipsum":5, "semetipsam":5, "semetipso":4, "semetipsos":5, "semetipsas":5, "semetipsis":5,
                 "teipsum":5, "temetipsum":5, "vosmetipsos":5, "idipsum":5}
                 #satisdare, satisdetur, etc
    def splittokens(self, wordlist):
        newwords = set()
        newtokens = []
        for oldtoken in self.tokens:
            tobeadded = []
            oldlc = oldtoken.token.lower()
            if oldtoken.isword and (oldlc in wordlist.unknownwords or oldlc in ["nec","neque","necnon","seque","seseque","quique","secumque"]):
                if oldlc == "nec":
                    tobeadded = oldtoken.split(1,True)
                elif oldlc == "necnon":
                    [tempa,tempb] = oldtoken.split(3,False)
                    tobeadded = tempa.split(1,True) + [tempb]
                elif oldlc in Tokenization.dividenda:
                    tobeadded = oldtoken.split(Tokenization.dividenda[oldlc],False)                 
                elif len(oldlc) > 3 and oldlc.endswith("que"):
                    tobeadded = oldtoken.split(3,True)
                elif len(oldlc) > 2 and oldlc.endswith(("ve","ue","ne")):
                    tobeadded = oldtoken.split(2,True)
            #endif
            if len(tobeadded) == 0:
                newtokens.append(oldtoken)
            else:
                for part in tobeadded:
                    newwords.add(toascii(part.token).lower())
                    newtokens.append(part)
        self.tokens = newtokens
        return newwords
    #enddef
    def show(self):
        for token in self.tokens[:500]:
            if token.isword:
                token.show()
            if token.endssentence:
                print
        if len(self.tokens) > 500:
            print "... (truncated) ..."
    #enddef
    def addtags(self):
        totaggerfd, totaggerfname = mkstemp()
        os.close(totaggerfd)
        fromtaggerfd, fromtaggerfname = mkstemp()
        os.close(fromtaggerfd)
        totaggerfile = codecs.open(totaggerfname, 'w', 'utf8')
        for token in self.tokens:
            if not token.isspace:
                totaggerfile.write(toascii(token.token))
                totaggerfile.write("\n")         
            if token.endssentence:
                totaggerfile.write("\n")         
        totaggerfile.close()
        os.system(RFTAGGERDIR+"rft-annotate -s -q "+MACRONIZERLIB+"rftagger-ldt.model "+totaggerfname+" "+fromtaggerfname)
        fromtaggerfile = codecs.open(fromtaggerfname, 'r', 'utf8')
        for token in self.tokens:
            if not token.isspace:
                try:
                    (taggedtoken,tag) = fromtaggerfile.readline().strip().split("\t")
                    assert toascii(token.token) == taggedtoken
                except:
                    raise Exception("Error: Something went wrong with the tagging.")
                #endtry
                token.tag = tag.replace(".","")
            if token.endssentence:
               fromtaggerfile.readline()
        fromtaggerfile.close()
        os.remove(totaggerfname)
        os.remove(fromtaggerfname)
    #enddef
    def addlemmas(self, wordlist):
        lemmafrequency = {}
        wordlemmafreq = {}
        wordformtolemmasintrain = {}
        train = codecs.open(MACRONIZERLIB+'ldt-corpus.txt', 'r', 'utf8')
        for line in train:
            if '\t' in line:
                [wordform, tag, lemma] = line.strip().split('\t')
                lemmafrequency[lemma] = lemmafrequency.get(lemma,0) + 1
                wordlemmafreq[(wordform,lemma)] = wordlemmafreq.get((wordform,lemma),0) + 1
                wordformtolemmasintrain[wordform] =  wordformtolemmasintrain.get(wordform,set()) | set([lemma])
        for token in self.tokens:
            wordform = toascii(token.token)
            bestlemma = "-"
            if wordform in wordformtolemmasintrain:
                bestlemma = ""
                maxfreq = 0
                for trainlemma in wordformtolemmasintrain[wordform]:
                    if wordlemmafreq[(wordform,trainlemma)] > maxfreq:
                        maxfreq = wordlemmafreq[(wordform,trainlemma)]
                        bestlemma = trainlemma
            elif wordform.lower() in wordlist.formtolemmas:
                bestlemma = ""
                maxfreq = -1
                for lexlemma in wordlist.formtolemmas[wordform.lower()]:
                    if lemmafrequency.get(lexlemma,0) > maxfreq:
                        maxfreq = lemmafrequency.get(lexlemma,0)
                        bestlemma = lexlemma
            #endif
            token.lemma = bestlemma
    #enddef
    def getaccents(self, wordlist):
        def levenshtein(s1, s2):
            if len(s1) < len(s2):
                return levenshtein(s2, s1)
            if len(s2) == 0:
                return len(s1)
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            return previous_row[-1]
        #enddef
        tagtoendings = {}
        endingsfile = codecs.open(MACRONIZERLIB+"macronized-endings.txt","r","utf8")
        for line in endingsfile:
            line = line.strip().split("\t")
            endingpairs = []
            for ending in line[1:]:
                endingpairs.append((ending, ending.replace("_","")))
            tagtoendings[line[0]] = endingpairs
        #endfor
        for token in self.tokens:
            if not token.isword:
                continue
            wordform = toascii(token.token)
            iscapital = wordform.istitle()
            wordform = wordform.lower()
            tag = token.tag
            lemma = token.lemma
            if wordform in wordlist.formtoaccent:
                token.accented = wordlist.formtoaccent[wordform]
            elif wordform in wordlist.formtotaglemmaaccents:
                candidates = []
                for (lextag, lexlemma, accented) in wordlist.formtotaglemmaaccents[wordform]:
                    casedist = 1 if (iscapital != lexlemma.replace("-","").istitle()) else 0
                    tagdist = postags.tagDist(tag, lextag)
                    lemdist = levenshtein(lemma, lexlemma)
                    if token.startssentence:
                        candidates.append((0,tagdist,lemdist,accented))
                    else:
                        candidates.append((casedist,tagdist,lemdist,accented))
                candidates.sort()
                token.accented = candidates[0][3]
                token.isambiguous = True
            else:
                ## Unknown word, but attempt to mark vowels in ending:
                ## To-do: Better support for different capitalization and orthography
                token.accented = token.token
                if any(i in token.token for i in u"aeiouyAEIOUY"):
                    for (accentedending, plainending) in tagtoendings.get(tag, []):
                        if wordform.endswith(plainending):
                            token.accented = wordform[:-len(plainending)] + accentedending
                            break
                    token.isunknown = True
    #enddef
    def macronize(self, domacronize, alsomaius, performutov, performitoj):
        for token in self.tokens:
            token.macronize(domacronize, alsomaius, performutov, performitoj)
    #enddef
    def detokenize(self, markambiguous):
        def enspancharacters(text):
            result = ""
            for char in text:
                if char in u"āēīōūȳĀĒĪŌŪȲaeiouyAEIOUY":
                    result = result + '<span>'+char+'</span>'
                else:
                    result = result + char
            return result
        #enddef
        result = ""
        enclitic = ""
        for token in self.tokens:
            if token.isreordered:
                enclitic = token.macronized
            else:
                if token.token.lower() == "ne" and len(enclitic) > 0: ## Not nēque...
                    result += token.token + enclitic
                else:
                    unicodetext = postags.unicodeaccents(token.macronized)
                    if markambiguous:
                        unicodetext = enspancharacters(unicodetext)
                        if token.isambiguous:
                            unicodetext = '<span class="ambig">' + unicodetext + '</span>'
                        elif token.isunknown:
                            unicodetext = '<span class="unknown">' + unicodetext + '</span>'
                        else:
                            unicodetext = '<span class="auto">' + unicodetext + '</span>'
                    result += unicodetext + enclitic
                enclitic = ""
        return result
    #enddef
#endclass

if 'REQUEST_METHOD' in os.environ: # If run as a CGI script
    scriptname = os.environ['REQUEST_URI'].split('/')[-1]
    htmlform = cgi.FieldStorage()
    texttomacronize = htmlform.getvalue('textcontent',"").decode("utf8").replace("\r","")
    #texttomacronize = texttomacronize[:20000]
    domacronize = True if texttomacronize == "" or htmlform.getvalue('macronize') else False
    alsomaius = True if htmlform.getvalue('alsomaius') else False
    performitoj = True if htmlform.getvalue('itoj') else False
    performutov = True if htmlform.getvalue('utov') else False
    
    print "Content-type:text/html\n\n"
    print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
    print '<html>'
    print '<head>'
    print '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
    print '<style>'
    print '  span.wrong {color:red;}'
    print '  span.ambig {background-color:yellow;}'
    print '  span.unknown {background-color:orange;}'
    print '  span.fixed {background-color:lightgreen;}'
    print '</style>'
    print '<title>A Latin Macronizer</title>'
    print '</head>'
    print '<body>'
    print '<h1><a href="'+scriptname+'">A Latin Macronizer</a></h1>'
    print '<p>Please enter a Latin text! (A correctly macronized text can be entered, in which case the performance will be evaluated.)</p>'
    #print '<p>Note: Input longer than 20000 characters will be truncated. (Sorry about that!)</p>'
    print '<form action="'+scriptname+'" method="post">'
    print '<p><textarea name="textcontent" cols="100" rows="20">'
    if texttomacronize == "":
        macronizedtext = ""
    else:
        try:
            wordlist = Wordlist()
            tokenization = Tokenization(texttomacronize)
            wordlist.loadwords(tokenization.allwordforms())
            newwordforms = tokenization.splittokens(wordlist)
            wordlist.loadwords(newwordforms)
            tokenization.addtags()
            tokenization.addlemmas(wordlist)
            tokenization.getaccents(wordlist)
            tokenization.macronize(domacronize, alsomaius, performutov, performitoj)
            macronizedtext = tokenization.detokenize(False)
            sys.stdout.write(macronizedtext)
        except Exception as inst:
            print inst.args[0]
            macronizedtext = ""
    print '</textarea><br>'
    print '<input type="checkbox" name="macronize" value="on" %s> Mark long vowels. &nbsp;&nbsp;&nbsp;' % ("checked" if domacronize else "")
    print u'<input type="checkbox" name="alsomaius" value="on" %s> Also mark <i>māius</i> etc.<br>' % ("checked" if alsomaius else "")
    print '<input type="checkbox" name="utov" value="on" %s> Convert u to v. &nbsp;&nbsp;&nbsp;' % ("checked" if performutov else "")
    print '<input type="checkbox" name="itoj" value="on" %s> Convert i to j.<br>' % ("checked" if performitoj else "")
    print '<input type="submit" value="Submit"> (Please be patient!)<br>'
    print '</p></form>'
    
    if macronizedtext != "":
        print '<h2>Result</h2>'
        print '<p>(Ambiguous forms are marked <span class="ambig">yellow</span>; unknown forms are <span class="unknown">orange</span>. You may click on a vowel to add or remove a macron.)</p>'
        print tokenization.detokenize(True).replace("\n","<br>")
    
    if domacronize and any(i in texttomacronize for i in u"āēīōū"):
        print '<h2>Evaluation</h2>'
        sys.stdout.write('<div style="white-space: pre-wrap;">')
        vowelcount = 0
        lengthcorrect = 0
        for (a,b) in zip(list(texttomacronize),list(macronizedtext)):
            clean = postags.removemacrons(b)
            if touiorthography(toascii(clean)) != touiorthography(toascii(postags.removemacrons(a))):
                raise Exception("Error: Text mismatch.")
            if clean in "AEIOUYaeiouy":
                vowelcount += 1
                if a == b:
                    lengthcorrect += 1
            if toascii(touiorthography(a)) == toascii(touiorthography(b)):
                sys.stdout.write(escape(b))
            else:
                sys.stdout.write('<span class="wrong">'+escape(b)+'</span>')
        print '</div>'
        print '<p>Accuracy:',
        print "{0:.2f}".format(100 * lengthcorrect / float(vowelcount)),
        print '</p>'
    
    if macronizedtext != "":
        if len(tokenization.tokens) > 2:
            if tokenization.tokens[0].token == "DEBUG":
                print '<h2>Debug info</h2>'
                print '<pre>'
                tokenization.show()
                print '</pre>'
    
    print '<h2>Information</h2>'
    print '<p>This automatic macronizer lets you quickly mark all the long vowels in a Latin text. The expected accuracy on an average classical text is estimated to be about 98% to 99%. Please re    view the resulting macrons with a critical eye!</p>'
    print '<p>The macronization is performed using a part-of-speech tagger (<a href="http://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/">RFTagger</a>) trained on the <a href="http://www.dh.uni    -leipzig.de/wo/projects/ancient-greek-and-latin-dependency-treebank-2-0/">Latin Dependency Treebank</a>, and with macrons provided by a customized version of the Morpheus morphological analyze    r. An earlier version of this tool was the subject of my bachelor’s thesis in Language Technology, <i><a href="http://stp.lingfil.uu.se/exarb/arch/winge2015.pdf">Automatic annotation of Latin     vowel length</a></i>.</p>'
    print '<p>Please note that this tool is not designed to perform scansion of poetry. Of course, any text can be macronized, but no metrical analysis is attempted.</p>'
    print '<p>Copyright 2015 Johan Winge. Please send comments to <a href="mailto:johan.winge@gmail.com">johan.winge@gmail.com</a>.</p>'

    print """<script>
    function clickHandler(event) {
      var span = event.target;
      if (span.className == 'ambig' || span.className == 'unknown' || span.className == 'auto') {
         span.className = 'fixed';
         return;
      }
      if (span.parentNode.className == 'ambig' || span.parentNode.className == 'unknown' || span.parentNode.className == 'auto' || span.parentNode.className == 'fixed') {
         span.parentNode.className = 'fixed';
         if      (span.innerHTML == 'ā') { span.innerHTML = 'a'; }
         else if (span.innerHTML == 'a') { span.innerHTML = 'ā'; }
         else if (span.innerHTML == 'ē') { span.innerHTML = 'e'; }
         else if (span.innerHTML == 'e') { span.innerHTML = 'ē'; }
         else if (span.innerHTML == 'ī') { span.innerHTML = 'i'; }
         else if (span.innerHTML == 'i') { span.innerHTML = 'ī'; }
         else if (span.innerHTML == 'ō') { span.innerHTML = 'o'; }
         else if (span.innerHTML == 'o') { span.innerHTML = 'ō'; }
         else if (span.innerHTML == 'ū') { span.innerHTML = 'u'; }
         else if (span.innerHTML == 'u') { span.innerHTML = 'ū'; }
         else if (span.innerHTML == 'ȳ') { span.innerHTML = 'y'; }
         else if (span.innerHTML == 'y') { span.innerHTML = 'ȳ'; }
         else if (span.innerHTML == 'Ā') { span.innerHTML = 'A'; }
         else if (span.innerHTML == 'A') { span.innerHTML = 'Ā'; }
         else if (span.innerHTML == 'Ē') { span.innerHTML = 'E'; }
         else if (span.innerHTML == 'E') { span.innerHTML = 'Ē'; }
         else if (span.innerHTML == 'Ī') { span.innerHTML = 'I'; }
         else if (span.innerHTML == 'I') { span.innerHTML = 'Ī'; }
         else if (span.innerHTML == 'Ō') { span.innerHTML = 'O'; }
         else if (span.innerHTML == 'O') { span.innerHTML = 'Ō'; }
         else if (span.innerHTML == 'Ū') { span.innerHTML = 'U'; }
         else if (span.innerHTML == 'U') { span.innerHTML = 'Ū'; }
         else if (span.innerHTML == 'Ȳ') { span.innerHTML = 'Y'; }
         else if (span.innerHTML == 'Y') { span.innerHTML = 'Ȳ'; }
      }
    }
    function attachHandler(container) {
       if (container.addEventListener) {
          container.addEventListener('click', clickHandler, false);
       } else if (container.attachEvent) {
           container.attachEvent('onclick', function(e) {
               return clickHandler.call(container, e || window.event);
           });
       }
    }
    var ambigs = document.getElementsByClassName("ambig"),
        unknowns = document.getElementsByClassName("unknown");
        autos = document.getElementsByClassName("auto");
    for (var i = 0; i < ambigs.length; i++) {
       attachHandler(ambigs[i]);
    }
    for (var i = 0; i < unknowns.length; i++) {
       attachHandler(unknowns[i]);
    }
    for (var i = 0; i < autos.length; i++) {
       attachHandler(autos[i]);
    }
    </script>"""
    print '</body>'
    print '</html>'

else: # Run as a free-standing Python script

    domacronize = True
    alsomaius = False
    performutov = False
    performitoj = False
    dotest = False
    infilename = ""
    outfilename = ""
    iterator = sys.argv.__iter__()
    scriptname = iterator.next()
    for arg in iterator:
        if arg == "-h" or arg == "--help" or arg == "-?":
            print "python " + scriptname + " <arguments>"
            print "Possible arguments:"
            print "  -i <filename>  File to read from. (Default is stdin.)"
            print "  -o <filename>  File to write to. (Default is stdout.)"
            print "  -v  or --utov  Convert u to v where appropriate."
            print "  -j  or --itoj  Similarly convert i to j."
            print "  --nomacrons    Don't mark long vowels."
            print "  --maius        Do mark vowels also in māius and such."
            print "  --test         Mark vowels in a short example text."
            print "  --initialize   Reset the database (only necessary once)."
            print "  -h  or --help  Show this information."
        elif arg == "--initialize":
            wordlist = Wordlist()
            wordlist.reinitializedatabase()
            exit(0)
        elif arg == "--nomacrons":
            domacronize = False
        elif arg == "--maius":
            alsomaius = True
        elif arg == "-v" or arg == "--utov":
            performutov = True
        elif arg == "-j" or arg == "--itoj":
            performitoj = True
        elif arg == "-i":
            infilename = iterator.next()
        elif arg == "-o":
            outfilename = iterator.next()
        elif arg == "--test":
            dotest = True
    #endfor
    if dotest:
        texttomacronize = "O orbis terrarum te saluto!\n"
    else:
        if infilename == "":
            infile = codecs.getreader('utf-8')(sys.stdin)
        else:
            infile = codecs.open(infilename, 'r', 'utf8')
        texttomacronize = infile.read()
    #endif
    wordlist = Wordlist()
    tokenization = Tokenization(texttomacronize)
    wordlist.loadwords(tokenization.allwordforms())
    newwordforms = tokenization.splittokens(wordlist)
    wordlist.loadwords(newwordforms)
    tokenization.addtags()
    tokenization.addlemmas(wordlist)
    tokenization.getaccents(wordlist)
    tokenization.macronize(domacronize, alsomaius, performutov, performitoj)
    macronizedtext = tokenization.detokenize(False)
    if outfilename == "":
        outfile = codecs.getwriter('utf8')(sys.stdout)
    else:
        outfile = codecs.open(outfilename, 'w', 'utf8')
    outfile.write(macronizedtext)

#EOF

