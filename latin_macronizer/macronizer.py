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


from html import escape

from . import postags
from .wordlist import Wordlist
from .tokenization import Tokenization
from .helpers import toascii
from .scansion import scanverses


def touiorthography(txt):
    for source, replacement in [("v", "u"), ("U", "V"), ("j", "i"), ("J", "I")]:
        txt = txt.replace(source, replacement)
    return txt


class Macronizer:

    def __init__(self, db_path=None):
        self.wordlist = Wordlist(db_path)
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
        scanverses(self.tokenization.tokens, automatons)
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
