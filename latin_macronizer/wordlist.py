from collections import defaultdict
import sqlite3
from tempfile import mkstemp
import os

from . import postags

MACRONS_FILE = os.path.join(os.path.dirname(__file__), 'macrons.txt')
MORPHEUS_DIR = os.path.join(os.path.dirname(__file__), 'morpheus')


def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ..."""
    a = iter(iterable)
    return zip(a, a)


def clean_lemma(lemma):
    return lemma.replace("#", "").replace("1", "").replace(" ", "+").replace("-", "").replace("^", "").replace("_", "")


class Wordlist:
    def __init__(self, db_path):
        self.unknownwords = set()  # Unknown to Morpheus
        self.formtolemmas = defaultdict(list)
        self.formtoaccenteds = defaultdict(list)
        self.formtotaglemmaaccents = defaultdict(list)
        if db_path:
            self.dbconn = sqlite3.connect(db_path)
            self.dbcursor = self.dbconn.cursor()
            self.dbcursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='morpheus';")
            if not self.dbcursor.fetchone():
                print("Initializing database...")
                self.reinitializedatabase()
        else:
            self.dbconn = None
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
                if self.dbconn and storeindb:
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
        if self.dbconn:
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
