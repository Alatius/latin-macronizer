import os
import re
from tempfile import mkstemp
from html import escape

from . import postags
from .token import Token
from .helpers import toascii, prefixeswithshortj


RFTAGGER_DIR = '/usr/local/bin'


class Tokenization:
    def __init__(self, text):
        self.tokens = []
        possiblesentenceend = False
        sentencehasended = True
        for chunk in re.findall(r"[^\W\d_]+|\s+|[^\w\s]+|[\d_]+", text, re.UNICODE):
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
        from .lemmas import lemma_frequency, word_lemma_freq, wordform_to_corpus_lemmas
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

        from .macronized_endings import tag_to_endings

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
