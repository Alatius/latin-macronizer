import re

from .helpers import prefixeswithshortj


def allvowelsambiguous(accented):
    """Generate accented forms for unknown words"""
    accented = re.sub("([aeiouy])", "\\1_^", accented)
    accented = accented.replace("qu_^", "qu")
    accented = re.sub(r"_\^(ns|nf|nct)", "_\\1", accented)
    accented = re.sub(r"_\^([bcdfgjklmnpqrstv]{2,}|[xz])", "\\1", accented)
    accented = re.sub(r"_\^m$", "m", accented)
    return accented


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


def segmentaccented(accented):
    """Split an accented form into a list of individual vowel phonemes and consonant clusters"""
    if accented == "hoc":  # Ad hoc fix. (Haha!)
        return ['o', 'cc']
    text = accented.lower().replace("qu", "q").replace("x", "cs").replace("z", "ds").replace("+", "^") + "#"
    segments = []
    segmentstart = 0
    pos = 0
    while True:
        if text[pos:pos + 2] in ["ae", "au", "ei", "eu", "oe"] and text[pos + 2] not in "_^+":
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
            prevseg = "#" if i == 0 else segments[i - 1]
            nextseg = "#" if i == len(segments) - 1 else segments[i + 1]
            if i == 0 and not thisseg[0] in "aeiouy":
                continue
            news = []
            for (penaltysofar, scansofar) in temps:
                if "_" in thisseg:
                    news.append((penaltysofar, scansofar + "L"))
                elif thisseg in ["ae", "au", "ei", "oe", "eu"]:
                    news.append((penaltysofar, scansofar + "L"))
                    news.append((penaltysofar + DIAERESISPENALTY, scansofar + "VV"))
                elif (prevseg.endswith("s") or prevseg.endswith("ng")) and thisseg == "u" and nextseg[
                    0] in "aeiouy":
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
            if nodeindex == -1 or finished and (nodeindex != 0 or wordindex != len(verse) - 1):
                continue
            tail, tailfeet, tailpenalty = scanverserecurse(verse, wordindex + 1, automaton, nodeindex)
            if scanpenalty + meterpenalty + tailpenalty < besttailpenalty:
                besttail = [(tokenindex, accented)] + tail
                besttailfeet = feet + tailfeet
                besttailpenalty = scanpenalty + meterpenalty + tailpenalty
        return besttail, besttailfeet, besttailpenalty

    # enddef
    indexaccentedpairs, feet, penalty = scanverserecurse(verse, 0, automaton, 0)
    return indexaccentedpairs, "".join(feet)


def scanverses(tokens, meterautomatons):
    """Try to scan the text according to meterautomatons. This function will, for each token,
    reconsider the order of the accented forms given by the getaccents function, by finding
    a likely combination of accented forms that make the verses scan."""

    scannedfeet = []
    verse = []
    automatonindex = 0
    for (index, token) in enumerate(tokens):
        if token.isword:
            followingtext = ""
            nextindex = index
            while True:
                nextindex += 1
                if nextindex == len(tokens) or "\n" in tokens[nextindex].text:
                    break
                if tokens[nextindex].isspace:
                    followingtext += " "
                elif tokens[nextindex].isword:
                    followingtext += tokens[nextindex].accented[0]
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
        if "\n" in token.text or index == len(tokens) - 1:
            (accentcorrections, feet) = scanverse(verse, meterautomatons[automatonindex])
            scannedfeet.append(feet)
            scannedfeet += [""] * (token.text.count("\n") - 1)
            for (tokenindex, newaccented) in accentcorrections:
                try:
                    tokens[tokenindex].accented.remove(newaccented)
                except ValueError:
                    pass
                tokens[tokenindex].accented.insert(0, newaccented)
            verse = []
            automatonindex += 1
            if automatonindex == len(meterautomatons):
                automatonindex = 0
