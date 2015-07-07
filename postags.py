#!/usr/bin/python
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

import re

featMap = {}

PART_OF_SPEECH = "pos"
NOUN = "noun"
VERB = "verb"
ADJECTIVE = "adj"
ADVERB = "adv"
ADVERBIAL = "adverbial"
CONJUNCTION = "conj"
PREPOSITION = "prep"
PRONOUN = "pron"
NUMERAL = "numeral"
INTERJECTION = "interj"
EXCLAMATION = "exclam"
PUNCTUATION = "punc"
featMap[PART_OF_SPEECH] = [NOUN, VERB, ADJECTIVE, ADVERB, ADVERBIAL, CONJUNCTION,
            PREPOSITION, PRONOUN, NUMERAL, INTERJECTION, EXCLAMATION, PUNCTUATION]

PERSON = "person"
FIRST_PERSON = "1st"
SECOND_PERSON = "2nd"
THIRD_PERSON = "3rd"
featMap[PERSON] = [FIRST_PERSON, SECOND_PERSON, THIRD_PERSON]

NUMBER = "number"
SINGULAR = "sg"
PLURAL = "pl"
featMap[NUMBER] = [SINGULAR, PLURAL]

TENSE = "tense"
PRESENT = "pres"
IMPERFECT = "imperf"
PERFECT = "perf"
PLUPERFECT = "plup"
FUTURE_PERFECT = "futperf"
FUTURE = "fut"
featMap[TENSE] = [PRESENT, IMPERFECT, PERFECT, PLUPERFECT, FUTURE_PERFECT, FUTURE]

MOOD = "mood"
INDICATIVE = "ind"
SUBJUNCTIVE = "subj"
INFINITIVE = "inf"
IMPERATIVE = "imperat"
GERUNDIVE = "gerundive"
SUPINE = "supine"
GERUND = "gerund"
PARTICIPLE = "part"
featMap[MOOD] = [INDICATIVE, SUBJUNCTIVE, INFINITIVE, IMPERATIVE, GERUNDIVE,
                 SUPINE, GERUND, PARTICIPLE]

VOICE = "voice"
ACTIVE = "act"
PASSIVE = "pass"
featMap[VOICE] = [ACTIVE, PASSIVE]

GENDER = "gender"
MASCULINE = "masc"
FEMININE = "fem"
NEUTER = "neut"
featMap[GENDER] = [MASCULINE, FEMININE, NEUTER]

CASE = "case"
NOMINATIVE = "nom"
GENITIVE = "gen"
DATIVE = "dat"
ACCUSATIVE = "acc"
ABLATIVE = "abl"
VOCATIVE = "voc"
LOCATIVE = "loc"
featMap[CASE] = [NOMINATIVE, GENITIVE, DATIVE, ACCUSATIVE, ABLATIVE, VOCATIVE, LOCATIVE]

DEGREE = "degree"
POSITIVE = "pos"
COMPARATIVE = "comp"
SUPERLATIVE = "superl"
featMap[DEGREE] = [POSITIVE, COMPARATIVE, SUPERLATIVE]

REGULARITY = "regularity"
REGULAR = "reg"
IRREGULAR = "irreg"
featMap[REGULARITY] = [REGULAR, IRREGULAR]

LEMMA = "lemma"
ACCENTEDFORM = "accentedform"

def LDT2Parse(LDTtag):
    parse = {}

    if LDTtag[0] == '-':
        pass
    elif LDTtag[0] == 'n':
        parse[PART_OF_SPEECH] = NOUN
    elif LDTtag[0] == 'v':
        parse[PART_OF_SPEECH] = VERB
    elif LDTtag[0] == 't':
        #parse[PART_OF_SPEECH] = PARTICIPLE
        parse[PART_OF_SPEECH] = VERB
        parse[MOOD] = PARTICIPLE
        print "Note: 'participle' used as POS"
    elif LDTtag[0] == 'a':
        parse[PART_OF_SPEECH] = ADJECTIVE
    elif LDTtag[0] == 'd':
        parse[PART_OF_SPEECH] = ADVERB
    elif LDTtag[0] == 'c':
        parse[PART_OF_SPEECH] = CONJUNCTION
    elif LDTtag[0] == 'r':
        parse[PART_OF_SPEECH] = PREPOSITION
    elif LDTtag[0] == 'p':
        parse[PART_OF_SPEECH] = PRONOUN
    elif LDTtag[0] == 'm':
        parse[PART_OF_SPEECH] = NUMERAL
    elif LDTtag[0] == 'i':
        parse[PART_OF_SPEECH] = INTERJECTION
    elif LDTtag[0] == 'e':
        parse[PART_OF_SPEECH] = EXCLAMATION
    elif LDTtag[0] == 'u':
        parse[PART_OF_SPEECH] = PUNCTUATION
    else:
        print "Warning: unknown part of speech:", LDTtag[0]

    if LDTtag[1] == '-':
        pass
    elif LDTtag[1] == '1':
        parse[PERSON] = FIRST_PERSON
    elif LDTtag[1] == '2':
        parse[PERSON] = SECOND_PERSON
    elif LDTtag[1] == '3':
        parse[PERSON] = THIRD_PERSON
    else:
        print "Warning: unknown person:", LDTtag[1]

    if LDTtag[2] == '-':
        pass
    elif LDTtag[2] == 's':
        parse[NUMBER] = SINGULAR
    elif LDTtag[2] == 'p':
        parse[NUMBER] = PLURAL
    else:
        print "Warning: unknown number:", LDTtag[2]

    if LDTtag[3] == '-':
        pass
    elif LDTtag[3] == 'p':
        parse[TENSE] = PRESENT
    elif LDTtag[3] == 'i':
        parse[TENSE] = IMPERFECT
    elif LDTtag[3] == 'r':
        parse[TENSE] = PERFECT
    elif LDTtag[3] == 'l':
        parse[TENSE] = PLUPERFECT
    elif LDTtag[3] == 't':
        parse[TENSE] = FUTURE_PERFECT
    elif LDTtag[3] == 'f':
        parse[TENSE] = FUTURE
    else:
        print "Warning: unknown tense:", LDTtag[3]

    if LDTtag[4] == '-':
        pass
    elif LDTtag[4] == 'i':
        parse[MOOD] = INDICATIVE
    elif LDTtag[4] == 's':
        parse[MOOD] = SUBJUNCTIVE
    elif LDTtag[4] == 'n':
        parse[MOOD] = INFINITIVE
    elif LDTtag[4] == 'm':
        parse[MOOD] = IMPERATIVE
    elif LDTtag[4] == 'p':
        parse[MOOD] = PARTICIPLE
    elif LDTtag[4] == 'd':
        parse[MOOD] = GERUND
    elif LDTtag[4] == 'g':
        parse[MOOD] = GERUNDIVE
    elif LDTtag[4] == 'u':
        parse[MOOD] = SUPINE
    else:
        print "Warning: unknown mood:", LDTtag[4]

    if LDTtag[5] == '-':
        pass
    elif LDTtag[5] == 'a':
        parse[VOICE] = ACTIVE
    elif LDTtag[5] == 'p':
        parse[VOICE] = PASSIVE
    else:
        print "Warning: unknown voice:", LDTtag[5]

    if LDTtag[6] == '-':
        pass
    elif LDTtag[6] == 'm':
        parse[GENDER] = MASCULINE
    elif LDTtag[6] == 'f':
        parse[GENDER] = FEMININE
    elif LDTtag[6] == 'n':
        parse[GENDER] = NEUTER
    else:
        print "Warning: unknown gender:", LDTtag[6]

    if LDTtag[7] == '-':
        pass
    elif LDTtag[7] == 'n':
        parse[CASE] = NOMINATIVE
    elif LDTtag[7] == 'g':
        parse[CASE] = GENITIVE
    elif LDTtag[7] == 'd':
        parse[CASE] = DATIVE
    elif LDTtag[7] == 'a':
        parse[CASE] = ACCUSATIVE
    elif LDTtag[7] == 'b':
        parse[CASE] = ABLATIVE
    elif LDTtag[7] == 'v':
        parse[CASE] = VOCATIVE
    elif LDTtag[7] == 'l':
        parse[CASE] = LOCATIVE
    else:
        print "Warning: unknown case:", LDTtag[7]

    if LDTtag[8] == '-':
        pass
    elif LDTtag[8] == 'c':
        parse[DEGREE] = COMPARATIVE
    elif LDTtag[8] == 's':
        parse[DEGREE] = SUPERLATIVE
    # POSITIVE not in use? (default)
    else:
        print "Warning: unknown degree:", LDTtag[8]

    return parse
#enddef

def Parse2LDT(parse):
    LDTtag = ""

    if parse.get(PART_OF_SPEECH,'') == NOUN:
        LDTtag += 'n'
    elif parse.get(PART_OF_SPEECH,'') == VERB:
        LDTtag += 'v'
#    elif parse.get(PART_OF_SPEECH,'') == PARTICIPLE:
#        LDTtag += 't'
    elif parse.get(PART_OF_SPEECH,'') == ADJECTIVE:
        LDTtag += 'a'
    elif parse.get(PART_OF_SPEECH,'') == ADVERB or parse.get(PART_OF_SPEECH,'') == ADVERBIAL:
        LDTtag += 'd'
    elif parse.get(PART_OF_SPEECH,'') == CONJUNCTION:
        LDTtag += 'c'
    elif parse.get(PART_OF_SPEECH,'') == PREPOSITION:
        LDTtag += 'r'
    elif parse.get(PART_OF_SPEECH,'') == PRONOUN:
        LDTtag += 'p'
    elif parse.get(PART_OF_SPEECH,'') == NUMERAL:
        LDTtag += 'm'
    elif parse.get(PART_OF_SPEECH,'') == INTERJECTION:
        LDTtag += 'i'
    elif parse.get(PART_OF_SPEECH,'') == EXCLAMATION:
        LDTtag += 'e'
    elif parse.get(PART_OF_SPEECH,'') == PUNCTUATION:
        LDTtag += 'u'
    else:
        LDTtag += '-'

    if parse.get(PERSON,'') == FIRST_PERSON:
        LDTtag += '1'
    elif parse.get(PERSON,'') == SECOND_PERSON:
        LDTtag += '2'
    elif parse.get(PERSON,'') == THIRD_PERSON:
        LDTtag += '3'
    else:
        LDTtag += '-'

    if parse.get(NUMBER,'') == SINGULAR:
        LDTtag += 's'
    elif parse.get(NUMBER,'') == PLURAL:
        LDTtag += 'p'
    else:
        LDTtag += '-'

    if parse.get(TENSE,'') == PRESENT:
        LDTtag += 'p'
    elif parse.get(TENSE,'') == IMPERFECT:
        LDTtag += 'i'
    elif parse.get(TENSE,'') == PERFECT:
        LDTtag += 'r'
    elif parse.get(TENSE,'') == PLUPERFECT:
        LDTtag += 'l'
    elif parse.get(TENSE,'') == FUTURE_PERFECT:
        LDTtag += 't'
    elif parse.get(TENSE,'') == FUTURE:
        LDTtag += 'f'
    else:
        if parse.get(MOOD,'') == GERUNDIVE or parse.get(MOOD,'') == GERUND:
            LDTtag += 'p'
        else:
            LDTtag += '-'

    if parse.get(MOOD,'') == INDICATIVE:
        LDTtag += 'i'
    elif parse.get(MOOD,'') == SUBJUNCTIVE:
        LDTtag += 's'
    elif parse.get(MOOD,'') == INFINITIVE:
        LDTtag += 'n'
    elif parse.get(MOOD,'') == IMPERATIVE:
        LDTtag += 'm'
    elif parse.get(MOOD,'') == GERUNDIVE:
        LDTtag += 'g'
    elif parse.get(MOOD,'') == SUPINE:
        LDTtag += 'u'
    elif parse.get(MOOD,'') == GERUND:
        LDTtag += 'd'
    elif parse.get(MOOD,'') == PARTICIPLE:
        LDTtag += 'p'
    else:
        LDTtag += '-'

    if parse.get(VOICE,'') == ACTIVE:
        LDTtag += 'a'
    elif parse.get(VOICE,'') == PASSIVE:
        LDTtag += 'p'
    else:
        if parse.get(TENSE,'') == PRESENT and parse.get(MOOD,'') == PARTICIPLE or parse.get(MOOD,'') == GERUND:
            LDTtag += 'a'
        elif parse.get(TENSE,'') == PERFECT and parse.get(MOOD,'') == PARTICIPLE or parse.get(MOOD,'') == GERUNDIVE:
            LDTtag += 'p'
        else:
            LDTtag += '-'

    if parse.get(GENDER,'') == MASCULINE:
        LDTtag += 'm'
    elif parse.get(GENDER,'') == FEMININE:
        LDTtag += 'f'
    elif parse.get(GENDER,'') == NEUTER:
        LDTtag += 'n'
    else:
        LDTtag += '-'

    if parse.get(CASE,'') == NOMINATIVE:
        LDTtag += 'n'
    elif parse.get(CASE,'') == GENITIVE:
        LDTtag += 'g'
    elif parse.get(CASE,'') == DATIVE:
        LDTtag += 'd'
    elif parse.get(CASE,'') == ACCUSATIVE:
        LDTtag += 'a'
    elif parse.get(CASE,'') == ABLATIVE:
        LDTtag += 'b'
    elif parse.get(CASE,'') == VOCATIVE:
        LDTtag += 'v'
    elif parse.get(CASE,'') == LOCATIVE:
        LDTtag += 'l'
    else:
        LDTtag += '-'

    if parse.get(DEGREE,'') == POSITIVE:
        LDTtag += '-'
    elif parse.get(DEGREE,'') == COMPARATIVE and parse.get(REGULARITY,'') != IRREGULAR and LDTtag[0] != 'd':
        ## Irregular forms are not marked for degree in LDT, nor adverbs (with few exceptions)!
        LDTtag += 'c'
    elif parse.get(DEGREE,'') == SUPERLATIVE and parse.get(REGULARITY,'') != IRREGULAR and LDTtag[0] != 'd':
        LDTtag += 's'
    else:
        LDTtag += '-'

    return LDTtag
#enddef

def unicodeaccents(txt):
    for source, replacement in [("a_",u"ā"),("e_",u"ē"),("i_",u"ī"),("o_",u"ō"),("u_",u"ū"),("y_",u"ȳ"),
                                ("A_",u"Ā"),("E_",u"Ē"),("I_",u"Ī"),("O_",u"Ō"),("U_",u"Ū"),("Y_",u"Ȳ"),
                                (u"ä_",u"ā"),(u"ë_",u"ē"),(u"ï_",u"ī"),(u"ö_",u"ō"),(u"ü_",u"ū"),(u"ÿ_",u"ȳ"),
                                (u"æ_",u"æ"),(u"œ_",u"œ"),(u"Æ_",u"Æ"),(u"Œ_",u"Œ")]:
        txt = txt.replace(source,replacement)
    return txt
#enddef
def removemacrons(txt):
    for source, replacement in [(u"ā",u"a"),(u"ē",u"e"),(u"ī",u"i"),(u"ō",u"o"),(u"ū",u"u"),(u"ȳ",u"y"),
                                (u"Ā",u"A"),(u"Ē",u"E"),(u"Ī",u"I"),(u"Ō",u"O"),(u"Ū",u"U"),(u"Ȳ",u"Y")]:
        txt = txt.replace(source,replacement)
    return txt
#enddef
def filteraccents(accented):
    accented = accented.replace("^_","")
    accented = accented.replace("_^","")
    accented = accented.replace("^","")
    accented = re.sub(u"u_m$", "um", accented)
    accented = re.sub(u"([AEIOUYaeiouy])n([sfx]|ct)", "\\1_n\\2", accented)
    return accented
#enddef

## Based on CruncherToXML.java in Perseus Hopper
def Morpheus2Parses(wordform, NL):
    parse = {}
    NL = NL.replace("irreg_comp","irreg comp")
    NL = NL.replace("irreg_superl","irreg superl")
    morphCodes = NL.split()

    accented = morphCodes[1]
    if accented.count(",") == 0:
        lemma = accented
        accented = wordform
    elif accented.count(",") == 1:
        lemma = accented.split(",")[1]
        accented = accented.split(",")[0]
    else:
        print "Warning, should not happen!"
        exit(1)
    parse[LEMMA] = lemma
    parse[ACCENTEDFORM] = filteraccents(accented)

    lastMorphCode = morphCodes[-1]
    partOfSpeechAbbrev = morphCodes[0]

    if lastMorphCode == "adverb":
        parse[PART_OF_SPEECH] = ADVERB
    elif lastMorphCode == "article":
        parse[PART_OF_SPEECH] = ARTICLE
    elif lastMorphCode == "particle":
        parse[PART_OF_SPEECH] = PARTICLE
    elif lastMorphCode == "conj":
        parse[PART_OF_SPEECH] = CONJUNCTION
    elif lastMorphCode == "prep":
        parse[PART_OF_SPEECH] = PREPOSITION
    elif lastMorphCode in ["pron1","pron2","pron3","relative","demonstr","indef","interrog"]:
        parse[PART_OF_SPEECH] = PRONOUN
    elif lastMorphCode == "numeral":
        parse[PART_OF_SPEECH] = NUMERAL
    elif lastMorphCode == "exclam":
        parse[PART_OF_SPEECH] = EXCLAMATION
    elif lastMorphCode == "alphabetic":
        parse[PART_OF_SPEECH] = IRREGULAR
    elif morphCodes[2] == "adverbial":
        parse[PART_OF_SPEECH] = ADVERBIAL
    elif partOfSpeechAbbrev == "V":
        parse[PART_OF_SPEECH] = VERB
    elif partOfSpeechAbbrev == "P":
        #parse[PART_OF_SPEECH] = PARTICIPLE
        parse[PART_OF_SPEECH] = VERB
        parse[MOOD] = PARTICIPLE
    elif partOfSpeechAbbrev == "N":
        if lastMorphCode in ["us_a_um", "0_a_um", "er_ra_rum", "er_era_erum", "ius_ia_ium", "is_e", "er_ris_re", "ans_adj", "ens_adj", 
                             "us_ius_adj", "0_ius_adj", "ior_ius_comp", "or_us_comp", "ax_adj", "0_adj3", "peLs_pedis_adj", "ox_adj", "ix_adj",
                             "s_tis_adj", "ex_icis_adj", "s_dis_adj", "irreg_adj3", "irreg_adj1", "irreg_adj2", "pron_adj1", "pron_adj3"]:
            parse[PART_OF_SPEECH] = ADJECTIVE
        elif "pp4" in lastMorphCode: # This is not in CruncherToXML...
            if 'supine' in  morphCodes:
                parse[PART_OF_SPEECH] = VERB # ? Supine attribute is not used in LDT
            else:
                parse[PART_OF_SPEECH] = ADJECTIVE # Past participles in the comparative or superlative. But what about "amantior"?
        else :
            parse[PART_OF_SPEECH] = NOUN
    else:
        print "Warning: Unknown Morpheus Part-of-Speech tag: " + partOfSpeechAbbrev

    def setfeature(parse, code, overwrite=False):
        featfound = False
        for feature, possiblevalues in featMap.iteritems():
            if code in possiblevalues:
                if parse.get(feature) == None or overwrite:
                    parse[feature] = code
                    featfound = True
                elif parse.get(feature) == code:
                    featfound = True
                else:
                    print "Warning: Feature", feature, "already set! Old:", parse.get(feature), "New:",code
        #if not featfound:
        #    print "Warning: Code", code, "not mapped to feature!"
    #enddef

    groupedParses = [parse]
    for i in range(2,len(morphCodes)-1):
        code = morphCodes[i]
        if code.count('/') > 0:
            codeComponents = code.split('/')
            newParses = []
            for existingParse in groupedParses:
                for codeComponent in codeComponents:
                    dupParse = existingParse.copy()
                    setfeature(dupParse, codeComponent)
                    newParses.append(dupParse)
            groupedParses = newParses
        else:
            for groupParse in groupedParses:
                setfeature(groupParse, code)

    # Morpheus does not report gerunds, only gerundives. So for those gerundives which look like gerunds, add alternative parses.
    # Similarly, many third declension nomina which can be of any gender are not marked for gender at all.
    finalParses = []
    for parse in groupedParses:
        if parse.get(MOOD,'') == GERUNDIVE and parse.get(NUMBER,'') == SINGULAR and parse.get(GENDER,'') == NEUTER and parse.get(CASE,'') != NOMINATIVE:
            newParse = parse.copy()
            setfeature(newParse, GERUND, overwrite=True)
            finalParses.append(newParse)
        elif parse.get(GENDER,'') == '' and parse.get(CASE,'') != '':
            newParse = parse.copy()
            setfeature(newParse, MASCULINE)
            finalParses.append(newParse)
            newParse = parse.copy()
            setfeature(newParse, FEMININE)
            finalParses.append(newParse)
            setfeature(parse, NEUTER)
        #endif
        finalParses.append(parse)
    return finalParses
#enddef

def Parse2ProielTag(parse):
    tag = ""

    if parse.get(PART_OF_SPEECH,'') == NOUN:
        tag += 'Nb'
    elif parse.get(PART_OF_SPEECH,'') == VERB:
        tag += 'V-'
#    elif parse.get(PART_OF_SPEECH,'') == PARTICIPLE:
#        tag += 't'
    elif parse.get(PART_OF_SPEECH,'') == ADJECTIVE:
        tag += 'A-'
    elif parse.get(PART_OF_SPEECH,'') == ADVERB or parse.get(PART_OF_SPEECH,'') == ADVERBIAL:
        tag += 'Df'
    elif parse.get(PART_OF_SPEECH,'') == CONJUNCTION:
        tag += 'C-'
    elif parse.get(PART_OF_SPEECH,'') == PREPOSITION:
        tag += 'R-'
    elif parse.get(PART_OF_SPEECH,'') == PRONOUN:
        tag += 'Pp'
    elif parse.get(PART_OF_SPEECH,'') == NUMERAL:
        tag += 'Ma'
    elif parse.get(PART_OF_SPEECH,'') == INTERJECTION:
        tag += 'I-'
    elif parse.get(PART_OF_SPEECH,'') == EXCLAMATION:
        tag += 'I-'
    elif parse.get(PART_OF_SPEECH,'') == PUNCTUATION:
        tag += 'X-'
    else:
        tag += 'F-'

    if parse.get(PERSON,'') == FIRST_PERSON:
        tag += '1'
    elif parse.get(PERSON,'') == SECOND_PERSON:
        tag += '2'
    elif parse.get(PERSON,'') == THIRD_PERSON:
        tag += '3'
    else:
        tag += '-'

    if parse.get(NUMBER,'') == SINGULAR:
        tag += 's'
    elif parse.get(NUMBER,'') == PLURAL:
        tag += 'p'
    else:
        tag += '-'

    if parse.get(TENSE,'') == PRESENT:
        tag += 'p'
    elif parse.get(TENSE,'') == IMPERFECT:
        tag += 'i'
    elif parse.get(TENSE,'') == PERFECT:
        tag += 'r'
    elif parse.get(TENSE,'') == PLUPERFECT:
        tag += 'l'
    elif parse.get(TENSE,'') == FUTURE_PERFECT:
        tag += 't'
    elif parse.get(TENSE,'') == FUTURE:
        tag += 'f'
    else:
        tag += '-'

    if parse.get(MOOD,'') == INDICATIVE:
        tag += 'i'
    elif parse.get(MOOD,'') == SUBJUNCTIVE:
        tag += 's'
    elif parse.get(MOOD,'') == INFINITIVE:
        tag += 'n'
    elif parse.get(MOOD,'') == IMPERATIVE:
        tag += 'm'
    elif parse.get(MOOD,'') == GERUNDIVE:
        tag += 'g'
    elif parse.get(MOOD,'') == SUPINE:
        tag += 'u'
    elif parse.get(MOOD,'') == GERUND:
        tag += 'd'
    elif parse.get(MOOD,'') == PARTICIPLE:
        tag += 'p'
    else:
        tag += '-'

    if parse.get(VOICE,'') == ACTIVE:
        tag += 'a'
    elif parse.get(VOICE,'') == PASSIVE:
        tag += 'p'
    else:
        if parse.get(TENSE,'') == PRESENT and parse.get(MOOD,'') == PARTICIPLE:
            tag += 'a'
        elif parse.get(TENSE,'') == PERFECT and parse.get(MOOD,'') == PARTICIPLE:
            tag += 'p'
        else:
            tag += '-'

    if parse.get(GENDER,'') == MASCULINE:
        tag += 'm'
    elif parse.get(GENDER,'') == FEMININE:
        tag += 'f'
    elif parse.get(GENDER,'') == NEUTER:
        tag += 'n'
    else:
        tag += '-'

    if parse.get(CASE,'') == NOMINATIVE:
        tag += 'n'
    elif parse.get(CASE,'') == GENITIVE:
        tag += 'g'
    elif parse.get(CASE,'') == DATIVE:
        tag += 'd'
    elif parse.get(CASE,'') == ACCUSATIVE:
        tag += 'a'
    elif parse.get(CASE,'') == ABLATIVE:
        tag += 'b'
    elif parse.get(CASE,'') == VOCATIVE:
        tag += 'v'
    elif parse.get(CASE,'') == LOCATIVE:
        tag += 'l'
    else:
        tag += '-'

    if parse.get(DEGREE,'') == POSITIVE:
        tag += 'p'
    elif parse.get(DEGREE,'') == COMPARATIVE:
        tag += 'c'
    elif parse.get(DEGREE,'') == SUPERLATIVE:
        tag += 's'
    else:
        if parse.get(PART_OF_SPEECH,'') == ADJECTIVE:
            tag += 'p'
        else:
            tag += '-'

    tag += '-'

    if tag[2:] == "---------":
        tag += 'n'
    else:
        tag += 'i'

    return tag
#enddef

def Parses2ProielTags(parses):
    tags = []
    for parse in parses:
        tags.append(Parse2ProielTag(parse))
    tagswithgender = {}
    for tag in tags:
        withoutgender = tag[0:7]+tag[8:12]
        tagswithgender[withoutgender] = tagswithgender.get(withoutgender,set()) | set([tag[7]])
    for withoutgender in tagswithgender:
        genders = tagswithgender[withoutgender]
        if 'm' in genders and 'n' in genders:
            tags.append(withoutgender[0:7]+'o'+withoutgender[7:11])
        if 'm' in genders and 'f' in genders:
            tags.append(withoutgender[0:7]+'p'+withoutgender[7:11])
        if 'm' in genders and 'f' in genders and 'n' in genders:
            tags.append(withoutgender[0:7]+'q'+withoutgender[7:11])
        if 'f' in genders and 'n' in genders:
            tags.append(withoutgender[0:7]+'r'+withoutgender[7:11])
    for tag in tags:
        if tag[0:2] == "Df":
            if tag == "Df---------n":
                tags.append("Df-------p-i")
            tags.append("Dq"+tag[2:])
            tags.append("Du"+tag[2:])
        elif tag[0:2] == "Ma":
            tags.append("Mo"+tag[2:])
        elif tag[0:2] == "Pp":
            tags.append("Pc"+tag[2:])
            tags.append("Pd"+tag[2:])
            tags.append("Pi"+tag[2:])
            tags.append("Pk"+tag[2:])
            tags.append("Pr"+tag[2:])
            tags.append("Ps"+tag[2:])
            tags.append("Pt"+tag[2:])
            tags.append("Px"+tag[2:])
        elif tag[0:2] == "Nb":
            tags.append("Ne"+tag[2:])
        #elif tag[0:8] == "V--s-g-m":
        #    tags.append("V----d--"+tag[8:])
        #elif tag[0:7] == "V--sppa":
        #    tags.append("A--s---"+tag[7:9]+"p-i")
        #elif tag[0:7] == "V--pppa":
        #    tags.append("A--p---"+tag[7:9]+"p-i")
        #elif tag[0:7] == "V--srpp":
        #    tags.append("A--s---"+tag[7:9]+"p-i")
        #elif tag[0:7] == "V--prpp":
        #    tags.append("A--p---"+tag[7:9]+"p-i")
    return tags
#enddef

# To help select the best alternative, define a measure to compare how similar tags are.
def tagDist(tag1, tag2):
    if not ( len(tag1) == len(tag2) == 9 or len(tag1) == len(tag2) == 12 ):
        print "Warning: Strange or mismatching tags!", tag1, tag2
        exit(0)
    def isNomen(tag):
        if tag[0] == 'n' or tag[0] == 'a' or tag[0] == 'v' and (tag[3:6] == 'rpp' or tag[3:6] == 'ppa'):
            return True
        elif tag[0] == 'N' or tag[0] == 'A' or tag[0] == 'V' and (tag[4:7] == 'rpp' or tag[4:7] == 'ppa'):
            return True
        return False
    #enddef
    dist = 0
    bothnomenbutdifferent = False
    if isNomen(tag1) and isNomen(tag2) and tag1[0] != tag2[0]:
        bothnomenbutdifferent = True
    for i in range(0, len(tag1)):
        if bothnomenbutdifferent and ( len(tag1) == 9 and i in [3, 4, 5] or len(tag1) == 12 and i in [4, 5, 6] ):
            continue
        else:
            if tag1[i] != tag2[i]:
                dist += 1
    return dist
#enddef
