#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015-2021 Johan Winge
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

import os
import re
from tempfile import mkstemp
from collections import defaultdict
import sqlite3
from html import escape

import postags

USE_DB = True
DB_NAME = 'macronizer.db'
RFTAGGER_DIR = '/usr/local/bin'
MORPHEUS_DIR = os.path.join(os.path.dirname(__file__), 'morpheus')
MACRONS_FILE = os.path.join(os.path.dirname(__file__), 'macrons.txt')


def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ..."""
    a = iter(iterable)
    return zip(a, a)


def toascii(txt):
    for source, replacement in [("æ", "ae"), ("Æ", "Ae"), ("œ", "oe"), ("Œ", "Oe"),
                                ("ä", "a"), ("ë", "e"), ("ï", "i"), ("ö", "o"), ("ü", "u"), ("ÿ", "u")]:
        txt = txt.replace(source, replacement)
    return txt


def touiorthography(txt):
    for source, replacement in [("v", "u"), ("U", "V"), ("j", "i"), ("J", "I")]:
        txt = txt.replace(source, replacement)
    return txt


def clean_lemma(lemma):
    return lemma.replace("#", "").replace("1", "").replace(" ", "+").replace("-", "").replace("^", "").replace("_", "")


class Wordlist:
    def __init__(self):
        self.unknownwords = set()  # Unknown to Morpheus
        self.formtolemmas = defaultdict(list)
        self.formtoaccenteds = defaultdict(list)
        self.formtotaglemmaaccents = defaultdict(list)
        if USE_DB:
            self.dbconn = sqlite3.connect(DB_NAME)
            self.dbcursor = self.dbconn.cursor()
        else:
            self.loadwordsfromfile(MACRONS_FILE)
    # enddef

    def reinitializedatabase(self):
        self.dbcursor.execute("DROP TABLE IF EXISTS morpheus")
        self.dbcursor.execute('''
            CREATE TABLE morpheus(
                id INTEGER PRIMARY KEY, 
                wordform TEXT NOT NULL, 
                morphtag TEXT, 
                lemma TEXT, 
                accented TEXT, 
                UNIQUE(wordform, morphtag, lemma, accented)
            )
        ''')
        self.loadwordsfromfile(MACRONS_FILE, storeindb=True)
        self.dbcursor.execute("CREATE INDEX morpheus_wordform_index ON morpheus (wordform)")
        self.dbconn.commit()
    # enddef

    def loadwordsfromfile(self, filename, storeindb=False):
        with open(filename, 'r', encoding='utf-8') as plaindbfile:
            for line in plaindbfile:
                if line.startswith("#"):
                    continue
                [wordform, morphtag, lemma, accented] = line.split()
                self.addwordparse(wordform, morphtag, lemma, accented)
                if USE_DB and storeindb:
                    self.dbcursor.execute(
                        "INSERT OR IGNORE INTO morpheus (wordform, morphtag, lemma, accented) VALUES (?, ?, ?, ?)",
                        (wordform, morphtag, lemma, accented))
    # enddef

    def loadwords(self, words):  # Expects a set of lowercase words
        unseenwords = set()
        for word in words:
            if word in self.formtotaglemmaaccents:  # Word is already loaded
                continue
            if not self.loadwordfromdb(word):  # Could not find word in database
                unseenwords.add(word)
        if len(unseenwords) > 0:
            self.crunchwords(unseenwords)  # Try to parse unseen words with Morpheus, and add result to the database
            for word in unseenwords:
                if not self.loadwordfromdb(word):
                    raise Exception("Could not store %s in the database." % word)
    # enddef

    def loadwordfromdb(self, word):
        if USE_DB:
            try:
                self.dbcursor.execute(
                    "SELECT wordform, morphtag, lemma, accented FROM morpheus WHERE wordform = ?", (word,))
            except Exception:
                raise Exception("Database table is missing. Please reset the database using --initialize.")
            rows = self.dbcursor.fetchall()
            if len(rows) == 0:
                return False
            for [wordform, morphtag, lemma, accented] in rows:
                self.addwordparse(wordform, morphtag, lemma, accented)
        else:
            self.addwordparse(word, None, None, None)
        return True
    # enddef

    def addwordparse(self, wordform, morphtag, lemma, accented):
        if accented is None:
            self.unknownwords.add(wordform)
        else:
            self.formtolemmas[wordform].append(lemma)
            self.formtoaccenteds[wordform].append(accented.lower())
            self.formtotaglemmaaccents[wordform].append((morphtag, lemma, accented))
    # enddef

    def crunchwords(self, words):
        morphinpfd, morphinpfname = mkstemp()
        os.close(morphinpfd)
        crunchedfd, crunchedfname = mkstemp()
        os.close(crunchedfd)
        with open(morphinpfname, 'w', encoding='utf-8') as morphinpfile:
            for word in words:
                morphinpfile.write(word.strip().lower() + '\n')
                morphinpfile.write(word.strip().capitalize() + '\n')
        morpheus_command = "MORPHLIB=%s/stemlib %s/bin/cruncher -L < %s > %s 2> /dev/null" % \
                               (MORPHEUS_DIR, MORPHEUS_DIR, morphinpfname, crunchedfname)
        exitcode = os.system(morpheus_command)
        if exitcode != 0:
            raise Exception("Failed to execute: %s" % morpheus_command)
        os.remove(morphinpfname)
        with open(crunchedfname, 'r', encoding='utf-8') as crunchedfile:
            morpheus = crunchedfile.read()
        os.remove(crunchedfname)
        crunchedwordforms = {}
        knownwords = set()
        for wordform, nls in pairwise(morpheus.split("\n")):
            wordform = wordform.strip().lower()
            nls = nls.strip()
            crunchedwordforms[wordform] = crunchedwordforms.get(wordform, "") + nls
        for wordform, nls in crunchedwordforms.items():
            parses = []
            for nl in nls.split("<NL>"):
                nl = nl.replace("</NL>", "")
                nlparts = nl.split()
                if len(nlparts) > 0:
                    parses += postags.morpheus_to_parses(wordform, nl)
            lemmatagtoaccenteds = defaultdict(list)
            for parse in parses:
                lemma = clean_lemma(parse[postags.LEMMA])
                parse[postags.LEMMA] = lemma
                accented = parse[postags.ACCENTEDFORM]
                # Work around shortcoming in Morpheus, adding _ in tradu_co_, etc.:
                if parse[postags.LEMMA].startswith("trans") and accented[3] != "_":
                    accented = accented[:3] + "_" + accented[3:]
                parse[postags.ACCENTEDFORM] = accented
                tag = postags.parse_to_ldt(parse)
                lemmatagtoaccenteds[(lemma, tag)].append(accented)
            if len(lemmatagtoaccenteds) == 0:
                continue
            knownwords.add(wordform)
            for (lemma, tag), accenteds in lemmatagtoaccenteds.items():
                # Sometimes there are multiple accented forms; prefer 'volvit' to 'voluit', 'Ju_lius' to 'Iu_lius' etc.:
                bestaccented = sorted(accenteds, key=lambda x: x.count('v') + x.count('j') + x.count('J'))[-1]
                lemmatagtoaccenteds[(lemma, tag)] = bestaccented
            for (lemma, tag), accented in lemmatagtoaccenteds.items():
                self.dbcursor.execute("INSERT OR IGNORE INTO morpheus (wordform, morphtag, lemma, accented) VALUES (?, ?, ?, ?)",
                                      (wordform, tag, lemma, accented))
        # The remaining were unknown to Morpheus:
        for wordform in words - knownwords:
            self.dbcursor.execute("INSERT OR IGNORE INTO morpheus (wordform) VALUES (?)", (wordform,))

        self.dbconn.commit()
    # enddef
# endclass


prefixeswithshortj = ("bij", "fidej", "Foroj", "foroj", "ju_rej", "multij", "praej", "quadrij",
                      "rej", "retroj", "se_mij", "sesquij", "u_nij", "introj")


class Token:
    def __init__(self, text):
        self.tag = ""
        self.lemma = ""
        self.accented = [""]
        self.macronized = ""
        self.text = postags.removemacrons(text)
        self.isword = True if re.match("[^\W\d_]", text, flags=re.UNICODE) else False
        self.isspace = True if re.match("\s", text, flags=re.UNICODE) else False
        self.hasenclitic = False
        self.isenclitic = False
        self.startssentence = False
        self.endssentence = False
        self.isunknown = False
    # enddef

    def split(self, pos, enclitic):
        newtokena = Token(self.text[:-pos])
        newtokenb = Token(self.text[-pos:])
        newtokena.startssentence = self.startssentence
        if enclitic:
            newtokena.hasenclitic = True
            newtokenb.isenclitic = True
        return [newtokena, newtokenb]
    # enddef

    def show(self):
        print("\t".join([self.text, self.tag, self.lemma, self.accented[0]])).expandtabs(16)
    # enddef

    def macronize(self, domacronize, alsomaius, performutov, performitoj):
        plain = self.text
        if not self.isword:
            self.macronized = plain
            return
        accented = self.accented[0]
        accented = accented.replace("_^", "").replace("^", "")
        if domacronize and alsomaius and 'j' in accented:
            if not accented.startswith(prefixeswithshortj):
                accented = re.sub('([aeiouy])(j[aeiouy])', r'\1_\2', accented)
        if (not domacronize or "_" not in accented) and not performutov and not performitoj:
            self.macronized = plain
            return
        if self.isenclitic and not (plain.lower() == "ue" and performutov):
            self.macronized = plain
            return
        if plain == accented.replace("_", ""):
            if domacronize:
                self.macronized = accented
            else:
                self.macronized = plain
            return
        # endif

        def inscost(a):
            if a == '_':
                return 0
            return 2

        def subcost(p, a):
            if a == '_':
                return 100
            if (a in "IJij" and p in "IJij") or (a in "UVuv" and p in "UVuv"):
                return 1
            return 2

        def delcost(_):
            return 2

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
                    diagcost = distance[i-1][j-1] + subcost(plain[i-1], accented[j-1])
                    downcost = distance[i][j-1] + inscost(accented[j-1])
                    distance[i][j] = min(rghtcost, diagcost, downcost)
        result = ""
        while i != 0 and j != 0:
            upcost = distance[i][j-1] if j > 0 else 1000
            diagcost = distance[i-1][j-1] if j > 0 and i > 0 else 1000
            leftcost = distance[i-1][j] if i > 0 else 1000
            if diagcost <= upcost and diagcost < leftcost:  # To-do: review the comparisons...
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
        # Some strange morpheus output (e.g. de_e_recti_) may give an additional _ in the result:
        result = result.replace("__", "_")
        self.macronized = result
    # enddef
# endclass


class Tokenization:
    def __init__(self, text):
        self.tokens = []
        possiblesentenceend = False
        sentencehasended = True
        # This does not work?: [^\W\d_]+|\s+|([^\w\s]|[\d_])+
        for chunk in re.findall("[^\W\d_]+|\s+|[^\w\s]+|[\d_]+", text, re.UNICODE):
            token = Token(chunk)
            if token.isword:
                if sentencehasended:
                    token.startssentence = True
                sentencehasended = False
                possiblesentenceend = (len(token.text) > 1)
            elif possiblesentenceend and any(i in token.text for i in '.;:?!'):
                token.endssentence = True
                possiblesentenceend = False
                sentencehasended = True
            self.tokens.append(token)
        self.scannedfeet = []
    # enddef

    def allwordforms(self):
        words = set()
        for token in self.tokens:
            if token.isword:
                words.add(toascii(token.text).lower())
        return words
    # enddef

    dividenda = {"nequid": 4, "attamen": 5, "unusquisque": 7, "unaquaeque": 7, "unumquodque": 7, "uniuscuiusque": 8,
                 "uniuscujusque": 8, "unicuique": 6, "unumquemque": 7, "unamquamque": 7, "unoquoque": 6,
                 "unaquaque": 6, "cuiusmodi": 4, "cujusmodi": 4, "quojusmodi": 4, "eiusmodi": 4, "ejusmodi": 4,
                 "huiuscemodi": 4, "hujuscemodi": 4, "huiusmodi": 4, "hujusmodi": 4, "istiusmodi": 4, "nullomodo": 4,
                 "quodammodo": 4, "nudiustertius": 7, "nonnisi": 4, "plusquam": 4, "proculdubio": 5, "quamplures": 6,
                 "quamprimum": 6, "quinetiam": 5, "uerumetiam": 5, "verumetiam": 5, "verumtamen": 5, "uerumtamen": 5,
                 "paterfamilias": 8, "patrisfamilias": 8, "patremfamilias": 8, "patrifamilias": 8, "patrefamilias": 8,
                 "patresfamilias": 8, "patrumfamilias": 8, "patribusfamilias": 8, "materfamilias": 8,
                 "matrisfamilias": 8, "matremfamilias": 8, "matrifamilias": 8, "matrefamilias": 8,
                 "matresfamilias": 8, "matrumfamilias": 8, "matribusfamilias": 8,
                 "respublica": 7, "reipublicae": 8, "rempublicam": 8, "senatusconsultum": 9, "senatusconsulto": 8,
                 "senatusconsulti": 8, "usufructu": 6, "usumfructum": 7, "ususfructus": 7,
                 "supradicti": 5, "supradictum": 6, "supradictus": 6, "supradicto": 5,
                 "seipse": 4, "seipsa": 4, "seipsum": 5, "seipsam": 5, "seipso": 4, "seipsos": 5, "seipsas": 5,
                 "seipsis": 5, "semetipse": 4, "semetipsa": 4, "semetipsum": 5, "semetipsam": 5, "semetipso": 4,
                 "semetipsos": 5, "semetipsas": 5, "semetipsis": 5, "teipsum": 5, "temetipsum": 5, "vosmetipsos": 5,
                 "idipsum": 5}
    # satisdare, satisdetur, etc

    def splittokens(self, wordlist):
        newwords = set()
        newtokens = []
        for oldtoken in self.tokens:
            tobeadded = []
            oldlc = oldtoken.text.lower()
            if oldtoken.isword and oldlc != "que" and (
                            oldlc in wordlist.unknownwords or oldlc in ["nec", "neque", "necnon", "seque", "seseque",
                                                                        "quique", "mecumque", "tecumque", "secumque"]):
                if oldlc == "nec":
                    tobeadded = oldtoken.split(1, True)
                elif oldlc == "necnon":
                    [tempa, tempb] = oldtoken.split(3, False)
                    tobeadded = tempa.split(1, True) + [tempb]
                elif oldlc in Tokenization.dividenda:
                    tobeadded = oldtoken.split(Tokenization.dividenda[oldlc], False)
                elif len(oldlc) > 3 and oldlc.endswith("que"):
                    tobeadded = oldtoken.split(3, True)
                elif len(oldlc) > 2 and oldlc.endswith(("ve", "ue", "ne", "st")):
                    tobeadded = oldtoken.split(2, True)
            # endif
            if len(tobeadded) == 0:
                newtokens.append(oldtoken)
            else:
                for part in tobeadded:
                    newwords.add(toascii(part.text).lower())
                    newtokens.append(part)
        self.tokens = newtokens
        return newwords
    # enddef

    def show(self):
        for token in self.tokens[:500]:
            if token.isword:
                token.show()
            if token.endssentence:
                print()
        if len(self.tokens) > 500:
            print("... (truncated) ...")
    # enddef

    def addtags(self):
        totaggerfd, totaggerfname = mkstemp()
        os.close(totaggerfd)
        fromtaggerfd, fromtaggerfname = mkstemp()
        os.close(fromtaggerfd)
        savedencliticbearer = None
        with open(totaggerfname, 'w', encoding='utf-8') as totaggerfile:
            for token in self.tokens:
                if not token.isspace:
                    tokentext = token.text
                    if tokentext == tokentext.upper():
                        tokentext = tokentext.lower()
                    if token.hasenclitic:
                        savedencliticbearer = toascii(tokentext)
                        continue
                    totaggerfile.write(toascii(tokentext) + "\n")
                    if token.isenclitic:
                        assert savedencliticbearer is not None
                        totaggerfile.write(savedencliticbearer + "\n")
                        savedencliticbearer = None
                if token.endssentence:
                    totaggerfile.write("\n")
        rftagger_model = os.path.join(os.path.dirname(__file__), 'rftagger-ldt.model')
        rft_command = "%s/rft-annotate -s -q %s %s %s" % (RFTAGGER_DIR, rftagger_model, totaggerfname, fromtaggerfname)
        exitcode = os.system(rft_command)
        if exitcode != 0:
            raise Exception("Failed to execute: %s" % rft_command)
        with open(fromtaggerfname, 'r', encoding='utf-8') as fromtaggerfile:
            (taggedenclititoken, enclitictag) = (None, None)
            line = None
            for token in self.tokens:
                if not token.isspace:
                    try:
                        if token.hasenclitic:
                            line = fromtaggerfile.readline().strip()
                            assert line
                            assert line.count('\t') == 1
                            (taggedenclititoken, enclitictag) = line.split("\t")
                        if token.isenclitic:
                            assert taggedenclititoken is not None
                            assert enclitictag is not None
                            (taggedtoken, tag) = (taggedenclititoken, enclitictag)
                        else:
                            line = fromtaggerfile.readline().strip()
                            assert line
                            assert line.count('\t') == 1
                            (taggedtoken, tag) = line.split('\t')
                        if token.text == token.text.upper():
                            assert taggedtoken == toascii(token.text.lower())
                        else:
                            assert taggedtoken == toascii(token.text)
                    except AssertionError:
                        raise Exception("Error: Could not handle tagging data in file %s:\n'%s'" %
                                        (fromtaggerfname, "Premature End Of File." if not line else line))
                    # endtry
                    token.tag = tag.replace(".", "")
                if token.endssentence:
                    line = fromtaggerfile.readline()
        os.remove(totaggerfname)
        os.remove(fromtaggerfname)
    # enddef

    def addlemmas(self, wordlist):
        from lemmas import lemma_frequency, word_lemma_freq, wordform_to_corpus_lemmas
        for token in self.tokens:
            wordform = toascii(token.text)
            best_lemma = "-"
            max_freq = -1
            if wordform in wordform_to_corpus_lemmas:
                for corpus_lemma in wordform_to_corpus_lemmas[wordform]:
                    if word_lemma_freq[(wordform, corpus_lemma)] > max_freq:
                        max_freq = word_lemma_freq[(wordform, corpus_lemma)]
                        best_lemma = corpus_lemma
            elif wordform.lower() in wordlist.formtolemmas:
                for lex_lemma in wordlist.formtolemmas[wordform.lower()]:
                    if lemma_frequency.get(lex_lemma, 0) > max_freq:
                        max_freq = lemma_frequency.get(lex_lemma, 0)
                        best_lemma = lex_lemma
            # endif
            token.lemma = best_lemma
    # enddef

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
        # enddef

        from macronized_endings import tag_to_endings

        for token in self.tokens:
            if not token.isword:
                continue
            wordform = toascii(token.text)
            iscapital = wordform.istitle()
            wordform = wordform.lower()
            tag = token.tag
            lemma = token.lemma
            if token.isenclitic:
                token.accented = ["ve"] if token.text.lower() == "ue" else [token.text.lower()]
            elif token.text.lower() == "ne" and token.hasenclitic:  # Not nēque...
                token.accented = ["ne"]
            elif len(set(wordlist.formtoaccenteds[wordform])) == 1:
                token.accented = [wordlist.formtoaccenteds[wordform][0]]
            elif wordform in wordlist.formtotaglemmaaccents:
                candidates = []
                for (lextag, lexlemma, accented) in wordlist.formtotaglemmaaccents[wordform]:
                    # Prefer lemmas with same capitalization as the token, unless the token is at
                    # the start of the sentence and capitalized, in which case any lemma is okay.
                    casedist = 0 if iscapital == lexlemma.istitle() or token.startssentence and iscapital else 1
                    tagdist = postags.tag_distance(tag, lextag)
                    lemdist = levenshtein(lemma, lexlemma)
                    candidates.append((casedist, tagdist, lemdist, accented))
                candidates.sort()
                token.accented = []
                for (casedist, tagdist, lemdist, accented) in candidates:
                    if accented not in token.accented and casedist == candidates[0][0]:
                        token.accented.append(accented)
            else:
                # Unknown word, but attempt to mark vowels in ending:
                # To-do: Better support for different capitalization and orthography
                token.accented = [token.text]
                if any(i in token.text for i in "aeiouyAEIOUY"):
                    for accented_ending in tag_to_endings.get(tag, []):
                        plain_ending = accented_ending.replace("_", "").replace("^", "")
                        if wordform.endswith(plain_ending):
                            token.accented = [wordform[:-len(plain_ending)] + accented_ending]
                            break
                    token.isunknown = True
    # enddef

    def scanverses(self, meterautomatons):
        """Try to scan the text according to meterautomatons. This function will, for each token,
        reconsider the order of the accented forms given by the getaccents function, by finding
        a likely combination of accented forms that make the verses scan."""

        def allvowelsambiguous(accented):
            """Generate accented forms for unknown words"""
            accented = re.sub("([aeiouy])", "\\1_^", accented)
            accented = accented.replace("qu_^", "qu")
            accented = re.sub("_\^(ns|nf|nct)", "_\\1", accented)
            accented = re.sub("_\^([bcdfgjklmnpqrstv]{2,}|[xz])", "\\1", accented)
            accented = re.sub("_\^m$", "m", accented)
            return accented
        # enddef

        def separate_ambiguous_vowels(accenteds):
            """
            If a vowel is ambiguous (_^), generate separate accented forms, one for each possible combination.
            Input: ['ba_^ce_^]
            Output: ['bace', 'ba_ce', 'bace_', 'ba_ce_']
            """
            accented_modifications = {'nescio_': 'nescio_^',
                                      'u_ni_us': 'u_ni_^us',
                                      'illi_us': 'illi_^us',
                                      'ipsi_us': 'ipsi_^us',
                                      'alteri_us': 'alteri_^us'}
            new_accenteds = []
            for accented in accenteds:
                accented = accented_modifications.get(accented, accented)
                parts = accented.split('_^')
                for variant in range(1 << len(parts) - 1):
                    new_accented = []
                    for bit_pos, part in enumerate(parts):
                        new_accented.append(part)
                        if 1 << bit_pos & variant:
                            new_accented.append('_')
                    new_accenteds.append(''.join(new_accented))
            return new_accenteds
        # enddef

        def segmentaccented(accented):
            """Split an accented form into a list of individual vowel phonemes and consonant clusters"""
            if accented == "hoc":  # Ad hoc fix. (Haha!)
                return ['o', 'cc']
            text = accented.lower().replace("qu", "q").replace("x", "cs").replace("z", "ds").replace("+", "^") + "#"
            segments = []
            segmentstart = 0
            pos = 0
            while True:
                if text[pos:pos+2] in ["ae", "au", "ei", "eu", "oe"] and text[pos+2] not in "_^+":
                    pos += 2
                elif text[pos] in "aeiouy":
                    pos += 1
                    while text[pos] in "_^+":
                        pos += 1
                else:
                    while text[pos] not in "aeiouy#":
                        pos += 1
                segment = text[segmentstart:pos].replace("h", "")
                if segment != "":
                    segments.append(segment)
                if text[pos] == "#":
                    break
                segmentstart = pos
            return segments
        # enddef

        def possiblescans(accentedcandidates, followingsegment):
            """A form with marked vowel lengths can be scanned differently, considering
            muta cum liquida, diphthong vs. diaeresis, elision, etc.
            input: followingsegment is one of ["V", "C", "CC", "#"]
            returns: [(penalty, scansion, accented), ...]"""
            REPRIORITIZEPENALTY = 1
            MUTACUMLIQUIDAPENALTY = 1
            DIAERESISPENALTY = 2
            NOSYNEZISPENALTY = 2  # in the context s or ng + u + vowel
            SYNEZISPENALTY = 3
            HIATUSPENALTY = 3
            isfirstaccented = True
            scans = []
            for accented in separate_ambiguous_vowels(accentedcandidates):
                segments = segmentaccented(accented)
                segments.append(followingsegment)
                basepenalty = 0 if isfirstaccented else REPRIORITIZEPENALTY
                temps = [(basepenalty, "")]
                for i, thisseg in enumerate(segments):
                    prevseg = "#" if i == 0 else segments[i-1]
                    nextseg = "#" if i == len(segments) - 1 else segments[i+1]
                    if i == 0 and not thisseg[0] in "aeiouy":
                        continue
                    news = []
                    for (penaltysofar, scansofar) in temps:
                        if "_" in thisseg:
                            news.append((penaltysofar, scansofar + "L"))
                        elif thisseg in ["ae", "au", "ei", "oe", "eu"]:
                            news.append((penaltysofar, scansofar + "L"))
                            news.append((penaltysofar + DIAERESISPENALTY, scansofar + "VV"))
                        elif (prevseg.endswith("s") or prevseg.endswith("ng")) and thisseg == "u" and nextseg[0] in "aeiouy":
                            news.append((penaltysofar, scansofar + "C"))
                            news.append((penaltysofar + NOSYNEZISPENALTY, scansofar + "V"))
                        elif thisseg[0] in "ui" and (nextseg[0] in "aeiouy" or prevseg[0] in "aeiouy"):
                            news.append((penaltysofar, scansofar + "V"))
                            news.append((penaltysofar + SYNEZISPENALTY, scansofar + "C"))
                        elif thisseg[0] in "aeiouy":
                            news.append((penaltysofar, scansofar + "V"))
                        elif thisseg == "m" and nextseg in ["V", "C", "CC", "#"]:
                            news.append((penaltysofar, scansofar + "M"))
                        elif thisseg == "j" and prevseg != "#":
                            if accented.startswith(prefixeswithshortj):
                                news.append((penaltysofar, scansofar + "C"))
                            else:
                                news.append((penaltysofar, scansofar + "CC"))
                        elif thisseg == "V":  # next word begins with vowel
                            if scansofar.endswith("V") or scansofar.endswith("L"):
                                news.append((penaltysofar, scansofar[:-1]))
                                news.append((penaltysofar + HIATUSPENALTY, scansofar))
                            elif scansofar.endswith("M"):
                                news.append((penaltysofar, scansofar[:-2]))
                                news.append((penaltysofar + HIATUSPENALTY, scansofar))
                            else:
                                news.append((penaltysofar, scansofar))
                        elif thisseg == "#":
                            news.append((penaltysofar, scansofar))
                        elif len(thisseg) == 1:
                            news.append((penaltysofar, scansofar + "C"))
                        elif len(thisseg) == 2 and thisseg[0] in "tpcdbgf" and thisseg[1] in "rl":
                            news.append((penaltysofar, scansofar + "C"))
                            news.append((penaltysofar + MUTACUMLIQUIDAPENALTY, scansofar + "CC"))
                        else:
                            news.append((penaltysofar, scansofar + "CC"))
                    temps = news
                for (penalty, scansion) in temps:
                    scansion = re.sub("VMC*|VCCC*|LM?C*", "L", scansion)
                    scansion = re.sub("VC?", "S", scansion)
                    scansion = re.sub("^C*", "", scansion)
                    scans.append((penalty, scansion, accented))
                isfirstaccented = False
            filteredscans = []
            foundscansions = set()
            for (penalty, scansion, accented) in sorted(scans):
                if scansion not in foundscansions:
                    filteredscans.append((penalty, scansion, accented))
                    foundscansions.add(scansion)
            return filteredscans
        # enddef

        def scanverse(verse, automaton):
            """Input: The "verse" is a complicated list of the format
            [(tokenindex, [(penalty, scansion, accented), (penalty, scansion, accented), ...]), ...]
            For example: [(0, [(0, 'L', 'in')]), (2, [(0, 'SL', 'no^va_'), (1, 'SS', 'no^va')]), ...]
            It returns a tuple such as ([(0, 'in'), (2, 'no^va'), (4, 'fe^rt'), ...], 'DDSSDS') """
            def scanverserecurse(verse, wordindex, automaton, oldnodeindex):
                if wordindex == len(verse):
                    return [], [], 0
                (tokenindex, wordscansions) = verse[wordindex]
                besttail = []
                besttailfeet = []
                besttailpenalty = 100
                for (scanpenalty, scansion, accented) in wordscansions:
                    nodeindex = oldnodeindex
                    feet = []
                    finished = False
                    meterpenalty = 0
                    for syllable in scansion:
                        (nodeindex, foot, meterpenaltypart) = automaton.get((nodeindex, syllable), (-1, "", 0))
                        meterpenalty += meterpenaltypart
                        if nodeindex == 0:
                            finished = True
                        feet.append(foot)
                    if nodeindex == -1 or finished and (nodeindex != 0 or wordindex != len(verse)-1):
                        continue
                    tail, tailfeet, tailpenalty = scanverserecurse(verse, wordindex+1, automaton, nodeindex)
                    if scanpenalty + meterpenalty + tailpenalty < besttailpenalty:
                        besttail = [(tokenindex, accented)] + tail
                        besttailfeet = feet + tailfeet
                        besttailpenalty = scanpenalty + meterpenalty + tailpenalty
                return besttail, besttailfeet, besttailpenalty
            # enddef
            indexaccentedpairs, feet, penalty = scanverserecurse(verse, 0, automaton, 0)
            return indexaccentedpairs, "".join(feet)
        # enddef

        self.scannedfeet = []
        verse = []
        automatonindex = 0
        for (index, token) in enumerate(self.tokens):
            if token.isword:
                followingtext = ""
                nextindex = index
                while True:
                    nextindex += 1
                    if nextindex == len(self.tokens) or "\n" in self.tokens[nextindex].text:
                        break
                    if self.tokens[nextindex].isspace:
                        followingtext += " "
                    elif self.tokens[nextindex].isword:
                        followingtext += self.tokens[nextindex].accented[0]
                        if "aeiouy" in followingtext:
                            break
                followingtext = followingtext.lower().replace("h", "")
                if followingtext == "":
                    followingsegment = "#"
                elif re.match(" *[aeiouy]", followingtext):
                    followingsegment = "V"
                elif re.match(" *([bcdfgjklmnpqrstv] *|[tpcdbgf][lr])[aeiouy]", followingtext):
                    followingsegment = "C"
                else:
                    followingsegment = "CC"
                if token.isunknown:
                    token.accented.append(allvowelsambiguous(token.text.lower()))
                verse.append((index, possiblescans(token.accented, followingsegment)))
            if "\n" in token.text or index == len(self.tokens) - 1:
                (accentcorrections, feet) = scanverse(verse, meterautomatons[automatonindex])
                self.scannedfeet.append(feet)
                self.scannedfeet += [""] * (token.text.count("\n") - 1)
                for (tokenindex, newaccented) in accentcorrections:
                    try:
                        self.tokens[tokenindex].accented.remove(newaccented)
                    except ValueError:
                        pass
                    self.tokens[tokenindex].accented.insert(0, newaccented)
                verse = []
                automatonindex += 1
                if automatonindex == len(meterautomatons):
                    automatonindex = 0
    # enddef

    def macronize(self, domacronize, alsomaius, performutov, performitoj):
        for token in self.tokens:
            token.macronize(domacronize, alsomaius, performutov, performitoj)
    # enddef

    def detokenize(self, markambiguous):
        result = []
        for token in self.tokens:
            if token.isword:
                unicodetext = postags.unicodeaccents(token.macronized)
                if markambiguous:
                    unicodetext = re.sub(r"([āēīōūȳĀĒĪŌŪȲaeiouyAEIOUY])", "<span>\\1</span>", unicodetext)
                    if token.isunknown:
                        unicodetext = '<span class="unknown">%s</span>' % unicodetext
                    elif len(set([x.replace("^", "") for x in token.accented])) > 1:
                        unicodetext = '<span class="ambig">%s</span>' % unicodetext
                    else:
                        unicodetext = '<span class="auto">%s</span>' % unicodetext
                result.append(unicodetext)
            else:
                if markambiguous:
                    result.append(escape(token.macronized))
                else:
                    result.append(token.macronized)
        return "".join(result)
    # enddef
# endclass


class Macronizer:

    dactylichexameter = {
        (0, 'L'): (1, '', 0),
        (0, 'S'): (-1, '', 0),
        (1, 'L'): (3, 'S', 0),
        (1, 'S'): (2, '', 0),
        (2, 'L'): (-1, '', 0),
        (2, 'S'): (3, 'D', 0),

        (3, 'L'): (4, '', 0),
        (3, 'S'): (-1, '', 0),
        (4, 'L'): (6, 'S', 0),
        (4, 'S'): (5, '', 0),
        (5, 'L'): (-1, '', 0),
        (5, 'S'): (6, 'D', 0),

        (6, 'L'): (7, '', 0),
        (6, 'S'): (-1, '', 0),
        (7, 'L'): (9, 'S', 0),
        (7, 'S'): (8, '', 0),
        (8, 'L'): (-1, '', 0),
        (8, 'S'): (9, 'D', 0),

        (9, 'L'): (10, '', 0),
        (9, 'S'): (-1, '', 0),
        (10, 'L'): (12, 'S', 0),
        (10, 'S'): (11, '', 0),
        (11, 'L'): (-1, '', 0),
        (11, 'S'): (12, 'D', 0),

        (12, 'L'): (13, '', 0),
        (12, 'S'): (-1, '', 0),
        (13, 'L'): (15, 'S', 0),
        (13, 'S'): (14, '', 0),
        (14, 'L'): (-1, '', 0),
        (14, 'S'): (15, 'D', 0),

        (15, 'L'): (16, '', 0),
        (15, 'S'): (-1, '', 0),
        (16, 'L'): (0, 'S', 0),
        (16, 'S'): (0, 'T', 0),
    }

    dactylicpentameter = {
        (0, 'L'): (1, '', 0),
        (0, 'S'): (-1, '', 0),
        (1, 'L'): (3, 'S', 0),
        (1, 'S'): (2, '', 0),
        (2, 'L'): (-1, '', 0),
        (2, 'S'): (3, 'D', 0),

        (3, 'L'): (4, '', 0),
        (3, 'S'): (-1, '', 0),
        (4, 'L'): (6, 'S', 0),
        (4, 'S'): (5, '', 0),
        (5, 'L'): (-1, '', 0),
        (5, 'S'): (6, 'D', 0),

        (6, 'L'): (7, '-', 0),
        (6, 'S'): (-1, '', 0),

        (7, 'L'): (8, '', 0),
        (7, 'S'): (-1, '', 0),
        (8, 'L'): (-1, '', 0),
        (8, 'S'): (9, '', 0),
        (9, 'L'): (-1, '', 0),
        (9, 'S'): (10, 'D', 0),

        (10, 'L'): (11, '', 0),
        (10, 'S'): (-1, '', 0),
        (11, 'L'): (-1, '', 0),
        (11, 'S'): (12, '', 0),
        (12, 'L'): (-1, '', 0),
        (12, 'S'): (13, 'D', 0),

        (13, 'L'): (0, '-', 0),
        (13, 'S'): (0, '-', 0)
    }

    hendecasyllable = {
        (0, 'L'): (1, '-', 0),
        (0, 'S'): (1, 'u', 0),
        (1, 'L'): (2, '-', 0),
        (1, 'S'): (2, 'u', 0),
        (2, 'L'): (3, '-', 0),
        (2, 'S'): (-1, '', 0),
        (3, 'L'): (-1, '', 0),
        (3, 'S'): (4, 'u', 0),
        (4, 'L'): (-1, '', 0),
        (4, 'S'): (5, 'u', 0),
        (5, 'L'): (6, '-', 0),
        (5, 'S'): (-1, '', 0),
        (6, 'L'): (-1, '', 0),
        (6, 'S'): (7, 'u', 0),
        (7, 'L'): (8, '-', 0),
        (7, 'S'): (-1, '', 0),
        (8, 'L'): (-1, '', 0),
        (8, 'S'): (9, 'u', 0),
        (9, 'L'): (10, '-', 0),
        (9, 'S'): (-1, '', 0),
        (10, 'L'): (0, '-', 0),
        (10, 'S'): (0, 'u', 0)
    }

    iambictrimeter = {
        (0, 'L'): (3, '-', 0),
        (0, 'S'): (1, 'u', 0),
        (1, 'L'): (5, '-|', 0),
        (1, 'S'): (2, 'u', 0),
        (2, 'L'): (5, '-|', 0),
        (2, 'S'): (5, 'u|', 0),
        (3, 'L'): (5, '-|', 0),
        (3, 'S'): (4, 'u', 0),
        (4, 'L'): (-1, '', 0),
        (4, 'S'): (5, 'u|', 0),

        (5, 'L'): (-1, '', 0),
        (5, 'S'): (6, 'u', 0),
        (6, 'L'): (7, '-|', 0),
        (6, 'S'): (21, 'u', 1),
        (21, 'L'): (-1, '', 0),
        (21, 'S'): (7, 'u|', 0),

        (7, 'L'): (10, '-', 0),
        (7, 'S'): (8, 'u', 0),
        (8, 'L'): (12, '-|', 0),
        (8, 'S'): (9, 'u', 0),
        (9, 'L'): (12, '-|', 0),
        (9, 'S'): (12, 'u|', 0),
        (10, 'L'): (12, '-|', 0),
        (10, 'S'): (11, 'u', 0),
        (11, 'L'): (-1, '', 0),
        (11, 'S'): (12, 'u|', 0),

        (12, 'L'): (-1, '', 0),
        (12, 'S'): (13, 'u', 0),
        (13, 'L'): (14, '-|', 0),
        (13, 'S'): (-1, '', 0),

        (14, 'L'): (17, '-', 0),
        (14, 'S'): (15, 'u', 0),
        (15, 'L'): (19, '-|', 0),
        (15, 'S'): (16, 'u', 0),
        (16, 'L'): (19, '-|', 0),
        (16, 'S'): (19, 'u|', 0),
        (17, 'L'): (19, '-|', 0),
        (17, 'S'): (18, 'u', 0),
        (18, 'L'): (-1, '', 0),
        (18, 'S'): (19, 'u|', 0),

        (19, 'L'): (-1, '', 0),
        (19, 'S'): (20, 'u', 0),
        (20, 'L'): (0, '-', 0),
        (20, 'S'): (0, 'u', 0),
    }

    iambicdimeter = {
        (0, 'L'): (3, '-', 0),
        (0, 'S'): (1, 'u', 0),
        (1, 'L'): (5, '-|', 0),
        (1, 'S'): (2, 'u', 0),
        (2, 'L'): (5, '-|', 0),
        (2, 'S'): (5, 'u|', 0),
        (3, 'L'): (5, '-|', 0),
        (3, 'S'): (4, 'u', 0),
        (4, 'L'): (-1, '', 0),
        (4, 'S'): (5, 'u|', 0),

        (5, 'L'): (-1, '', 0),
        (5, 'S'): (6, 'u', 0),
        (6, 'L'): (7, '-|', 0),
        (6, 'S'): (14, 'u', 1),
        (14, 'L'): (-1, '', 0),
        (14, 'S'): (7, 'u|', 0),

        (7, 'L'): (10, '-', 0),
        (7, 'S'): (8, 'u', 0),
        (8, 'L'): (12, '-|', 0),
        (8, 'S'): (9, 'u', 0),
        (9, 'L'): (12, '-|', 0),
        (9, 'S'): (12, 'u|', 0),
        (10, 'L'): (12, '-|', 0),
        (10, 'S'): (11, 'u', 0),
        (11, 'L'): (-1, '', 0),
        (11, 'S'): (12, 'u|', 0),

        (12, 'L'): (-1, '', 0),
        (12, 'S'): (13, 'u', 0),
        (13, 'L'): (0, '-', 0),
        (13, 'S'): (0, 'u', 0)
    }

    def __init__(self):
        self.wordlist = Wordlist()
        self.tokenization = Tokenization("")
    # enddef

    def settext(self, text):
        self.tokenization = Tokenization(text)
        self.wordlist.loadwords(self.tokenization.allwordforms())
        newwordforms = self.tokenization.splittokens(self.wordlist)
        self.wordlist.loadwords(newwordforms)
        self.tokenization.addtags()
        self.tokenization.addlemmas(self.wordlist)
        self.tokenization.getaccents(self.wordlist)
    # enddef

    def scan(self, automatons):
        self.tokenization.scanverses(automatons)
    # enddef

    def gettext(self, domacronize=True, alsomaius=False, performutov=False, performitoj=False, markambigs=False):
        self.tokenization.macronize(domacronize, alsomaius, performutov, performitoj)
        return self.tokenization.detokenize(markambigs)
    # enddef

    def macronize(self, text, domacronize=True, alsomaius=False, performutov=False, performitoj=False, markambigs=False):
        self.settext(text)
        return self.gettext(domacronize, alsomaius, performutov, performitoj, markambigs)
    # enddef
# endclass


def evaluate(goldstandard, macronizedtext):
    vowelcount = 0
    lengthcorrect = 0
    outtext = []
    for (a, b) in zip(list(goldstandard), list(macronizedtext)):
        plaina = postags.removemacrons(a)
        plainb = postags.removemacrons(b)
        if touiorthography(toascii(plaina)) != touiorthography(toascii(plainb)):
            raise Exception("Error: Text mismatch.")
        if plaina in "AEIOUYaeiouy":
            vowelcount += 1
            if a == b:
                lengthcorrect += 1
        if toascii(touiorthography(a)) == toascii(touiorthography(b)):
            outtext.append(escape(b))
        else:
            outtext.append('<span class="wrong">%s</span>' % b)
    return lengthcorrect / float(vowelcount), "".join(outtext)
# enddef


if __name__ == "__main__":
    print("""Library for marking Latin texts with macrons. Copyright 2015-2017 Johan Winge.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Minimal example of usage:
    from macronizer import Macronizer
    macronizer = Macronizer()
    macronizedtext = macronizer.macronize("Iam primum omnium satis constat Troia capta in ceteros saevitum esse Troianos")

Initializing Macronizer() may take a couple of seconds, so if you want
to mark macrons in several strings, you are better off reusing the
same Macronizer object.

The macronizer function takes a couple of optional parameters, which
control in what way the input string is transformed:
    domacronize: mark long vowels; default True
    alsomaius: also mark vowels before consonantic i; default False
    performutov: change consonantic u to v; default False
    performitoj: similarly change i to j; default False
    markambigs: mark up the text in various ways with HTML tags; default False

If you want to transform the same text in different ways, you should use
the separate gettext and settext functions, instead of macronize:
    from macronizer import Macronizer
    macronizer = Macronizer()
    macronizer.settext("Iam primum omnium")
    print(macronizer.gettext())
    print(macronizer.gettext(domacronize=False, performitoj=True))

NOTE: If you are not a developer, you probably want to call the front end
macronize.py instead.
""")
