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
ARTICLE = "article"
PARTICLE = "particle"
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


def ldt_to_parse(ldt_tag):
    parse = {}

    if ldt_tag[0] == '-':
        pass
    elif ldt_tag[0] == 'n':
        parse[PART_OF_SPEECH] = NOUN
    elif ldt_tag[0] == 'v':
        parse[PART_OF_SPEECH] = VERB
    elif ldt_tag[0] == 't':
        # parse[PART_OF_SPEECH] = PARTICIPLE
        parse[PART_OF_SPEECH] = VERB
        parse[MOOD] = PARTICIPLE
        print("Note: 'participle' used as POS")
    elif ldt_tag[0] == 'a':
        parse[PART_OF_SPEECH] = ADJECTIVE
    elif ldt_tag[0] == 'd':
        parse[PART_OF_SPEECH] = ADVERB
    elif ldt_tag[0] == 'c':
        parse[PART_OF_SPEECH] = CONJUNCTION
    elif ldt_tag[0] == 'r':
        parse[PART_OF_SPEECH] = PREPOSITION
    elif ldt_tag[0] == 'p':
        parse[PART_OF_SPEECH] = PRONOUN
    elif ldt_tag[0] == 'm':
        parse[PART_OF_SPEECH] = NUMERAL
    elif ldt_tag[0] == 'i':
        parse[PART_OF_SPEECH] = INTERJECTION
    elif ldt_tag[0] == 'e':
        parse[PART_OF_SPEECH] = EXCLAMATION
    elif ldt_tag[0] == 'u':
        parse[PART_OF_SPEECH] = PUNCTUATION
    else:
        print("Warning: unknown part of speech:", ldt_tag[0])

    if ldt_tag[1] == '-':
        pass
    elif ldt_tag[1] == '1':
        parse[PERSON] = FIRST_PERSON
    elif ldt_tag[1] == '2':
        parse[PERSON] = SECOND_PERSON
    elif ldt_tag[1] == '3':
        parse[PERSON] = THIRD_PERSON
    else:
        print("Warning: unknown person:", ldt_tag[1])

    if ldt_tag[2] == '-':
        pass
    elif ldt_tag[2] == 's':
        parse[NUMBER] = SINGULAR
    elif ldt_tag[2] == 'p':
        parse[NUMBER] = PLURAL
    else:
        print("Warning: unknown number:", ldt_tag[2])

    if ldt_tag[3] == '-':
        pass
    elif ldt_tag[3] == 'p':
        parse[TENSE] = PRESENT
    elif ldt_tag[3] == 'i':
        parse[TENSE] = IMPERFECT
    elif ldt_tag[3] == 'r':
        parse[TENSE] = PERFECT
    elif ldt_tag[3] == 'l':
        parse[TENSE] = PLUPERFECT
    elif ldt_tag[3] == 't':
        parse[TENSE] = FUTURE_PERFECT
    elif ldt_tag[3] == 'f':
        parse[TENSE] = FUTURE
    else:
        print("Warning: unknown tense:", ldt_tag[3])

    if ldt_tag[4] == '-':
        pass
    elif ldt_tag[4] == 'i':
        parse[MOOD] = INDICATIVE
    elif ldt_tag[4] == 's':
        parse[MOOD] = SUBJUNCTIVE
    elif ldt_tag[4] == 'n':
        parse[MOOD] = INFINITIVE
    elif ldt_tag[4] == 'm':
        parse[MOOD] = IMPERATIVE
    elif ldt_tag[4] == 'p':
        parse[MOOD] = PARTICIPLE
    elif ldt_tag[4] == 'd':
        parse[MOOD] = GERUND
    elif ldt_tag[4] == 'g':
        parse[MOOD] = GERUNDIVE
    elif ldt_tag[4] == 'u':
        parse[MOOD] = SUPINE
    else:
        print("Warning: unknown mood:", ldt_tag[4])

    if ldt_tag[5] == '-':
        pass
    elif ldt_tag[5] == 'a':
        parse[VOICE] = ACTIVE
    elif ldt_tag[5] == 'p':
        parse[VOICE] = PASSIVE
    else:
        print("Warning: unknown voice:", ldt_tag[5])

    if ldt_tag[6] == '-':
        pass
    elif ldt_tag[6] == 'm':
        parse[GENDER] = MASCULINE
    elif ldt_tag[6] == 'f':
        parse[GENDER] = FEMININE
    elif ldt_tag[6] == 'n':
        parse[GENDER] = NEUTER
    else:
        print("Warning: unknown gender:", ldt_tag[6])

    if ldt_tag[7] == '-':
        pass
    elif ldt_tag[7] == 'n':
        parse[CASE] = NOMINATIVE
    elif ldt_tag[7] == 'g':
        parse[CASE] = GENITIVE
    elif ldt_tag[7] == 'd':
        parse[CASE] = DATIVE
    elif ldt_tag[7] == 'a':
        parse[CASE] = ACCUSATIVE
    elif ldt_tag[7] == 'b':
        parse[CASE] = ABLATIVE
    elif ldt_tag[7] == 'v':
        parse[CASE] = VOCATIVE
    elif ldt_tag[7] == 'l':
        parse[CASE] = LOCATIVE
    else:
        print("Warning: unknown case:", ldt_tag[7])

    if ldt_tag[8] == '-':
        pass
    elif ldt_tag[8] == 'c':
        parse[DEGREE] = COMPARATIVE
    elif ldt_tag[8] == 's':
        parse[DEGREE] = SUPERLATIVE
    # POSITIVE not in use? (default)
    else:
        print("Warning: unknown degree:", ldt_tag[8])

    return parse


def parse_to_ldt(parse):
    ldt_tag = ""

    if parse.get(PART_OF_SPEECH, '') == NOUN:
        ldt_tag += 'n'
    elif parse.get(PART_OF_SPEECH, '') == VERB:
        ldt_tag += 'v'
    # elif parse.get(PART_OF_SPEECH, '') == PARTICIPLE:
    #     LDTtag += 't'
    elif parse.get(PART_OF_SPEECH, '') == ADJECTIVE:
        ldt_tag += 'a'
    elif parse.get(PART_OF_SPEECH, '') == ADVERB or parse.get(PART_OF_SPEECH, '') == ADVERBIAL:
        ldt_tag += 'd'
    elif parse.get(PART_OF_SPEECH, '') == CONJUNCTION:
        ldt_tag += 'c'
    elif parse.get(PART_OF_SPEECH, '') == PREPOSITION:
        ldt_tag += 'r'
    elif parse.get(PART_OF_SPEECH, '') == PRONOUN:
        ldt_tag += 'p'
    elif parse.get(PART_OF_SPEECH, '') == NUMERAL:
        ldt_tag += 'm'
    elif parse.get(PART_OF_SPEECH, '') == INTERJECTION:
        ldt_tag += 'i'
    elif parse.get(PART_OF_SPEECH, '') == EXCLAMATION:
        ldt_tag += 'e'
    elif parse.get(PART_OF_SPEECH, '') == PUNCTUATION:
        ldt_tag += 'u'
    else:
        ldt_tag += '-'

    if parse.get(PERSON, '') == FIRST_PERSON:
        ldt_tag += '1'
    elif parse.get(PERSON, '') == SECOND_PERSON:
        ldt_tag += '2'
    elif parse.get(PERSON, '') == THIRD_PERSON:
        ldt_tag += '3'
    else:
        ldt_tag += '-'

    if parse.get(NUMBER, '') == SINGULAR:
        ldt_tag += 's'
    elif parse.get(NUMBER, '') == PLURAL:
        ldt_tag += 'p'
    else:
        ldt_tag += '-'

    if parse.get(TENSE, '') == PRESENT:
        ldt_tag += 'p'
    elif parse.get(TENSE, '') == IMPERFECT:
        ldt_tag += 'i'
    elif parse.get(TENSE, '') == PERFECT:
        ldt_tag += 'r'
    elif parse.get(TENSE, '') == PLUPERFECT:
        ldt_tag += 'l'
    elif parse.get(TENSE, '') == FUTURE_PERFECT:
        ldt_tag += 't'
    elif parse.get(TENSE, '') == FUTURE:
        ldt_tag += 'f'
    else:
        if parse.get(MOOD, '') == GERUNDIVE or parse.get(MOOD, '') == GERUND:
            ldt_tag += 'p'
        else:
            ldt_tag += '-'

    if parse.get(MOOD, '') == INDICATIVE:
        ldt_tag += 'i'
    elif parse.get(MOOD, '') == SUBJUNCTIVE:
        ldt_tag += 's'
    elif parse.get(MOOD, '') == INFINITIVE:
        ldt_tag += 'n'
    elif parse.get(MOOD, '') == IMPERATIVE:
        ldt_tag += 'm'
    elif parse.get(MOOD, '') == GERUNDIVE:
        ldt_tag += 'g'
    elif parse.get(MOOD, '') == SUPINE:
        ldt_tag += 'u'
    elif parse.get(MOOD, '') == GERUND:
        ldt_tag += 'd'
    elif parse.get(MOOD, '') == PARTICIPLE:
        ldt_tag += 'p'
    else:
        ldt_tag += '-'

    if parse.get(VOICE, '') == ACTIVE:
        ldt_tag += 'a'
    elif parse.get(VOICE, '') == PASSIVE:
        ldt_tag += 'p'
    else:
        if parse.get(TENSE, '') == PRESENT and parse.get(MOOD, '') == PARTICIPLE or parse.get(MOOD, '') == GERUND:
            ldt_tag += 'a'
        elif parse.get(TENSE, '') == PERFECT and parse.get(MOOD, '') == PARTICIPLE or parse.get(MOOD, '') == GERUNDIVE:
            ldt_tag += 'p'
        else:
            ldt_tag += '-'

    if parse.get(GENDER, '') == MASCULINE:
        ldt_tag += 'm'
    elif parse.get(GENDER, '') == FEMININE:
        ldt_tag += 'f'
    elif parse.get(GENDER, '') == NEUTER:
        ldt_tag += 'n'
    else:
        ldt_tag += '-'

    if parse.get(CASE, '') == NOMINATIVE:
        ldt_tag += 'n'
    elif parse.get(CASE, '') == GENITIVE:
        ldt_tag += 'g'
    elif parse.get(CASE, '') == DATIVE:
        ldt_tag += 'd'
    elif parse.get(CASE, '') == ACCUSATIVE:
        ldt_tag += 'a'
    elif parse.get(CASE, '') == ABLATIVE:
        ldt_tag += 'b'
    elif parse.get(CASE, '') == VOCATIVE:
        ldt_tag += 'v'
    elif parse.get(CASE, '') == LOCATIVE:
        ldt_tag += 'l'
    else:
        ldt_tag += '-'

    if parse.get(DEGREE, '') == POSITIVE:
        ldt_tag += '-'
    elif parse.get(DEGREE, '') == COMPARATIVE and parse.get(REGULARITY, '') != IRREGULAR and ldt_tag[0] != 'd':
        # Irregular forms are not marked for degree in LDT, nor adverbs (with few exceptions)!
        ldt_tag += 'c'
    elif parse.get(DEGREE, '') == SUPERLATIVE and parse.get(REGULARITY, '') != IRREGULAR and ldt_tag[0] != 'd':
        ldt_tag += 's'
    else:
        ldt_tag += '-'

    return ldt_tag


def unicodeaccents(txt):
    for source, replacement in [("a_", "ā"), ("e_", "ē"), ("i_", "ī"), ("o_", "ō"), ("u_", "ū"), ("y_", "ȳ"),
                                ("A_", "Ā"), ("E_", "Ē"), ("I_", "Ī"), ("O_", "Ō"), ("U_", "Ū"), ("Y_", "Ȳ"),
                                ("ä_", "ā"), ("ë_", "ē"), ("ï_", "ī"), ("ö_", "ō"), ("ü_", "ū"), ("ÿ_", "ȳ"),
                                ("æ_", "æ"), ("œ_", "œ"), ("Æ_", "Æ"), ("Œ_", "Œ")]:
        txt = txt.replace(source, replacement)
    return txt


def escape_macrons(txt):
    for source, replacement in [("ā", "a_"), ("ē", "e_"), ("ī", "i_"), ("ō", "o_"), ("ū", "u_"), ("ȳ", "y_"),
                                ("Ā", "A_"), ("Ē", "E_"), ("Ī", "I_"), ("Ō", "O_"), ("Ū", "U_"), ("Ȳ", "Y_")]:
        txt = txt.replace(source, replacement)
    return txt


def removemacrons(txt):
    for source, replacement in [("ā", "a"), ("ē", "e"), ("ī", "i"), ("ō", "o"), ("ū", "u"), ("ȳ", "y"),
                                ("Ā", "A"), ("Ē", "E"), ("Ī", "I"), ("Ō", "O"), ("Ū", "U"), ("Ȳ", "Y")]:
        txt = txt.replace(source, replacement)
    return txt


def filter_accents(accented):
    accented = accented.replace("^_", "_^")
    accented = re.sub("_\^([bcdfgpt][lr])", "^\\1", accented)
    accented = re.sub("u_m$", "um", accented)
    accented = re.sub("([AEIOUYaeiouy])\^?n([sfx]|ct)", "\\1_n\\2", accented)
    return accented


def morpheus_to_parses(wordform, nl):
    """Based on CruncherToXML.java in Perseus Hopper"""
    parse = {}
    nl = nl.replace("irreg_comp", "irreg comp")
    nl = nl.replace("irreg_superl", "irreg superl")
    morph_codes = nl.split()

    accented = morph_codes[1]
    lemma = None
    if accented.count(",") == 0:
        lemma = accented
        if accented[0] == accented[0].upper():
            accented = wordform.capitalize()
        else:
            accented = wordform
    elif accented.count(",") == 1:
        lemma = accented.split(",")[1]
        accented = accented.split(",")[0]
    assert lemma is not None
    parse[LEMMA] = lemma
    parse[ACCENTEDFORM] = filter_accents(accented)

    last_morph_code = morph_codes[-1]
    pos_abbrev = morph_codes[0]

    if last_morph_code == "adverb":
        parse[PART_OF_SPEECH] = ADVERB
    elif last_morph_code == "article":
        parse[PART_OF_SPEECH] = ARTICLE
    elif last_morph_code == "particle":
        parse[PART_OF_SPEECH] = PARTICLE
    elif last_morph_code == "conj":
        parse[PART_OF_SPEECH] = CONJUNCTION
    elif last_morph_code == "prep":
        parse[PART_OF_SPEECH] = PREPOSITION
    elif last_morph_code in ["pron1", "pron2", "pron3", "relative", "demonstr", "indef", "interrog"]:
        parse[PART_OF_SPEECH] = PRONOUN
    elif last_morph_code == "numeral":
        parse[PART_OF_SPEECH] = NUMERAL
    elif last_morph_code == "exclam":
        parse[PART_OF_SPEECH] = EXCLAMATION
    elif last_morph_code == "alphabetic":
        parse[PART_OF_SPEECH] = IRREGULAR
    elif morph_codes[2] == "adverbial":
        parse[PART_OF_SPEECH] = ADVERBIAL
    elif pos_abbrev == "V":
        parse[PART_OF_SPEECH] = VERB
    elif pos_abbrev == "P":
        # parse[PART_OF_SPEECH] = PARTICIPLE
        parse[PART_OF_SPEECH] = VERB
        parse[MOOD] = PARTICIPLE
    elif pos_abbrev == "N":
        if last_morph_code in ["us_a_um", "0_a_um", "er_ra_rum", "er_era_erum", "ius_ia_ium", "is_e", "er_ris_re",
                               "ans_adj", "ens_adj", "us_ius_adj", "0_ius_adj", "ior_ius_comp", "or_us_comp", "ax_adj",
                               "0_adj3", "peLs_pedis_adj", "ox_adj", "ix_adj", "s_tis_adj", "ex_icis_adj", "s_dis_adj",
                               "irreg_adj3", "irreg_adj1", "irreg_adj2", "pron_adj1", "pron_adj3"]:
            parse[PART_OF_SPEECH] = ADJECTIVE
        elif "pp4" in last_morph_code:  # This is not in CruncherToXML...
            if 'supine' in morph_codes:
                parse[PART_OF_SPEECH] = VERB  # ? Supine attribute is not used in LDT
            else:
                parse[PART_OF_SPEECH] = ADJECTIVE  # Past participles in the comparative or superlative. But what about "amantior"?
        else:
            parse[PART_OF_SPEECH] = NOUN
    else:
        print("Warning: Unknown Morpheus Part-of-Speech tag: " + pos_abbrev)

    def setfeature(parse, code, overwrite=False):
        featfound = False
        for feature, possiblevalues in featMap.items():
            if code in possiblevalues:
                if parse.get(feature) is None or overwrite:
                    parse[feature] = code
                    featfound = True
                elif parse.get(feature) == code:
                    featfound = True
                else:
                    print("Warning: Feature", feature, "already set! Old:", parse.get(feature), "New:", code)
        if not featfound:
            pass
            # print("Warning: Code", code, "not mapped to feature!")
    # enddef

    grouped_parses = [parse]
    for i in range(2, len(morph_codes)-1):
        code = morph_codes[i]
        if code.count('/') > 0:
            code_components = code.split('/')
            new_parses = []
            for existingParse in grouped_parses:
                for code_component in code_components:
                    dup_parse = existingParse.copy()
                    setfeature(dup_parse, code_component)
                    new_parses.append(dup_parse)
            grouped_parses = new_parses
        else:
            for group_parse in grouped_parses:
                setfeature(group_parse, code)

    # Morpheus does not report gerunds, only gerundives. So for those gerundives which look like gerunds, add alternative parses.
    # Similarly, many third declension nomina which can be of any gender are not marked for gender at all.
    final_parses = []
    for parse in grouped_parses:
        if parse.get(MOOD, '') == GERUNDIVE and parse.get(NUMBER, '') == SINGULAR \
                and parse.get(GENDER, '') == NEUTER and parse.get(CASE, '') != NOMINATIVE:
            new_parse = parse.copy()
            setfeature(new_parse, GERUND, overwrite=True)
            final_parses.append(new_parse)
        elif parse.get(GENDER, '') == '' and parse.get(CASE, '') != '':
            new_parse = parse.copy()
            setfeature(new_parse, MASCULINE)
            final_parses.append(new_parse)
            new_parse = parse.copy()
            setfeature(new_parse, FEMININE)
            final_parses.append(new_parse)
            setfeature(parse, NEUTER)
        # endif
        final_parses.append(parse)
    return final_parses


def parse_to_proiel_tag(parse):
    tag = ""

    if parse.get(PART_OF_SPEECH, '') == NOUN:
        tag += 'Nb'
    elif parse.get(PART_OF_SPEECH, '') == VERB:
        tag += 'V-'
    # elif parse.get(PART_OF_SPEECH, '') == PARTICIPLE:
    #     tag += 't'
    elif parse.get(PART_OF_SPEECH, '') == ADJECTIVE:
        tag += 'A-'
    elif parse.get(PART_OF_SPEECH, '') == ADVERB or parse.get(PART_OF_SPEECH, '') == ADVERBIAL:
        tag += 'Df'
    elif parse.get(PART_OF_SPEECH, '') == CONJUNCTION:
        tag += 'C-'
    elif parse.get(PART_OF_SPEECH, '') == PREPOSITION:
        tag += 'R-'
    elif parse.get(PART_OF_SPEECH, '') == PRONOUN:
        tag += 'Pp'
    elif parse.get(PART_OF_SPEECH, '') == NUMERAL:
        tag += 'Ma'
    elif parse.get(PART_OF_SPEECH, '') == INTERJECTION:
        tag += 'I-'
    elif parse.get(PART_OF_SPEECH, '') == EXCLAMATION:
        tag += 'I-'
    elif parse.get(PART_OF_SPEECH, '') == PUNCTUATION:
        tag += 'X-'
    else:
        tag += 'F-'

    if parse.get(PERSON, '') == FIRST_PERSON:
        tag += '1'
    elif parse.get(PERSON, '') == SECOND_PERSON:
        tag += '2'
    elif parse.get(PERSON, '') == THIRD_PERSON:
        tag += '3'
    else:
        tag += '-'

    if parse.get(NUMBER, '') == SINGULAR:
        tag += 's'
    elif parse.get(NUMBER, '') == PLURAL:
        tag += 'p'
    else:
        tag += '-'

    if parse.get(TENSE, '') == PRESENT:
        tag += 'p'
    elif parse.get(TENSE, '') == IMPERFECT:
        tag += 'i'
    elif parse.get(TENSE, '') == PERFECT:
        tag += 'r'
    elif parse.get(TENSE, '') == PLUPERFECT:
        tag += 'l'
    elif parse.get(TENSE, '') == FUTURE_PERFECT:
        tag += 't'
    elif parse.get(TENSE, '') == FUTURE:
        tag += 'f'
    else:
        tag += '-'

    if parse.get(MOOD, '') == INDICATIVE:
        tag += 'i'
    elif parse.get(MOOD, '') == SUBJUNCTIVE:
        tag += 's'
    elif parse.get(MOOD, '') == INFINITIVE:
        tag += 'n'
    elif parse.get(MOOD, '') == IMPERATIVE:
        tag += 'm'
    elif parse.get(MOOD, '') == GERUNDIVE:
        tag += 'g'
    elif parse.get(MOOD, '') == SUPINE:
        tag += 'u'
    elif parse.get(MOOD, '') == GERUND:
        tag += 'd'
    elif parse.get(MOOD, '') == PARTICIPLE:
        tag += 'p'
    else:
        tag += '-'

    if parse.get(VOICE, '') == ACTIVE:
        tag += 'a'
    elif parse.get(VOICE, '') == PASSIVE:
        tag += 'p'
    else:
        if parse.get(TENSE, '') == PRESENT and parse.get(MOOD, '') == PARTICIPLE:
            tag += 'a'
        elif parse.get(TENSE, '') == PERFECT and parse.get(MOOD, '') == PARTICIPLE:
            tag += 'p'
        else:
            tag += '-'

    if parse.get(GENDER, '') == MASCULINE:
        tag += 'm'
    elif parse.get(GENDER, '') == FEMININE:
        tag += 'f'
    elif parse.get(GENDER, '') == NEUTER:
        tag += 'n'
    else:
        tag += '-'

    if parse.get(CASE, '') == NOMINATIVE:
        tag += 'n'
    elif parse.get(CASE, '') == GENITIVE:
        tag += 'g'
    elif parse.get(CASE, '') == DATIVE:
        tag += 'd'
    elif parse.get(CASE, '') == ACCUSATIVE:
        tag += 'a'
    elif parse.get(CASE, '') == ABLATIVE:
        tag += 'b'
    elif parse.get(CASE, '') == VOCATIVE:
        tag += 'v'
    elif parse.get(CASE, '') == LOCATIVE:
        tag += 'l'
    else:
        tag += '-'

    if parse.get(DEGREE, '') == POSITIVE:
        tag += 'p'
    elif parse.get(DEGREE, '') == COMPARATIVE:
        tag += 'c'
    elif parse.get(DEGREE, '') == SUPERLATIVE:
        tag += 's'
    else:
        if parse.get(PART_OF_SPEECH, '') == ADJECTIVE:
            tag += 'p'
        else:
            tag += '-'

    tag += '-'

    if tag[2:] == "---------":
        tag += 'n'
    else:
        tag += 'i'

    return tag


def parses_to_proiel_tags(parses):
    tags = []
    for parse in parses:
        tags.append(parse_to_proiel_tag(parse))
    tagswithgender = {}
    for tag in tags:
        withoutgender = tag[0:7]+tag[8:12]
        tagswithgender[withoutgender] = tagswithgender.get(withoutgender, set()) | {tag[7]}
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
        # elif tag[0:8] == "V--s-g-m":
        #     tags.append("V----d--"+tag[8:])
        # elif tag[0:7] == "V--sppa":
        #     tags.append("A--s---"+tag[7:9]+"p-i")
        # elif tag[0:7] == "V--pppa":
        #     tags.append("A--p---"+tag[7:9]+"p-i")
        # elif tag[0:7] == "V--srpp":
        #     tags.append("A--s---"+tag[7:9]+"p-i")
        # elif tag[0:7] == "V--prpp":
        #     tags.append("A--p---"+tag[7:9]+"p-i")
    return tags


def tag_distance(tag1, tag2):
    """To help select the best alternative, define a measure to compare how similar tags are."""
    if not (len(tag1) == len(tag2) == 9 or len(tag1) == len(tag2) == 12):
        print("Warning: Strange or mismatching tags!", tag1, tag2)
        exit(0)

    def is_nomen(tag):
        if tag[0] == 'n' or tag[0] == 'a' or tag[0] == 'v' and (tag[3:6] == 'rpp' or tag[3:6] == 'ppa'):
            return True
        elif tag[0] == 'N' or tag[0] == 'A' or tag[0] == 'V' and (tag[4:7] == 'rpp' or tag[4:7] == 'ppa'):
            return True
        return False
    # enddef

    dist = 0
    bothnomenbutdifferent = False
    if is_nomen(tag1) and is_nomen(tag2) and tag1[0] != tag2[0]:
        bothnomenbutdifferent = True
    for i in range(0, len(tag1)):
        if bothnomenbutdifferent and (len(tag1) == 9 and i in [3, 4, 5] or len(tag1) == 12 and i in [4, 5, 6]):
            continue
        else:
            if tag1[i] != tag2[i]:
                dist += 1
    return dist
# enddef
