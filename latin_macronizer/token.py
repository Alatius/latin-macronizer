import re

from . import postags
from .helpers import toascii, prefixeswithshortj


class Token:
    def __init__(self, text):
        self.tag = ""
        self.lemma = ""
        self.accented = [""]
        self.macronized = ""
        self.text = postags.removemacrons(text)
        self.isword = True if re.match(r"[^\W\d_]", text, flags=re.UNICODE) else False
        self.isspace = True if re.match(r"\s", text, flags=re.UNICODE) else False
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
        print("\t".join([self.text, self.tag, self.lemma, self.accented[0]]).expandtabs(16))
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
