#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015-2017 Johan Winge
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

MACRONIZER_LIB = '.'

import cgi
import os
import sys
import codecs
sys.path.append(MACRONIZER_LIB)
from macronizer import Macronizer, evaluate
import unicodedata
import argparse

PROSE = 'prose'
HEXAMETER = 'hexameter'
ELEGIACS = 'elegiacs'
HENDECA = 'hendeca'
IAMBTRIDI = 'iambtridi'
TRUNCATETHRESHOLD = 20000

if 'REQUEST_METHOD' in os.environ:  # If run as a CGI script
    scriptname = os.environ['REQUEST_URI'].split('/')[-1]
    htmlform = cgi.FieldStorage()
    texttomacronize = htmlform.getvalue('textcontent', "").decode("utf8").replace("\r", "")
    texttomacronize = unicodedata.normalize('NFC', texttomacronize)
    # texttomacronize = texttomacronize[:TRUNCATETHRESHOLD]
    domacronize = True if texttomacronize == "" or htmlform.getvalue('macronize') else False
    alsomaius = True if htmlform.getvalue('alsomaius') else False
    scan = htmlform.getvalue('scan')
    if not scan:
        scan = PROSE
    performitoj = True if htmlform.getvalue('itoj') else False
    performutov = True if htmlform.getvalue('utov') else False
    doevaluate = True if htmlform.getvalue('doevaluate') else False
    debugcommand = "DEBUG\n"
    if texttomacronize.startswith(debugcommand):
        dodebug = True
        texttomacronize = texttomacronize[len(debugcommand):]
    else:
        dodebug = False

    print("Content-type:text/html\n\n")
    print("""
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style type="text/css">
    h1 a {font-style: italic; text-decoration: none; color: black;}
    body {padding: 2em;}
    span.wrong {background-color: #ff6666;}
    span.ambig {background-color: yellow;}
    span.unknown {background-color: orange;}
    span.fixed {background-color: lightgreen;}
    div.feet {float: left; border: 1px hidden; padding: 0.5em;}
    div.prewrap {display:inline-block; white-space: pre-wrap; border: 1px dashed black; padding: 0.5em;}
</style>
<title>A Latin Macronizer</title>
</head>
<body>""")
    print('<h1><a href="' + scriptname + '">A Latin Macronizer</a></h1>')
    print('<p>Please enter a Latin text!</p>')
    # print('<p>Note: In order to avoid time out from the server, input longer than %s characters will be truncated. Sorry about that!</p>' % (TRUNCATETHRESHOLD))
    print('<form action="' + scriptname+'" method="post">')
    print('<p><textarea name="textcontent" onclick="enlarge(this)" cols="100" rows="%s">' % ('20' if texttomacronize == "" else '3'))
    if texttomacronize == "":
        macronizedtext = ""
    else:
        try:
            macronizer = Macronizer()
            macronizer.settext(texttomacronize)
            if scan == HEXAMETER:
                macronizer.scan([Macronizer.dactylichexameter])
            elif scan == ELEGIACS:
                macronizer.scan([Macronizer.dactylichexameter, Macronizer.dactylicpentameter])
            elif scan == HENDECA:
                macronizer.scan([Macronizer.hendecasyllable])
            elif scan == IAMBTRIDI:
                macronizer.scan([Macronizer.iambictrimeter, Macronizer.iambicdimeter])
            macronizedtext = macronizer.gettext(domacronize, alsomaius, performutov, performitoj, markambigs=False)
            # sys.stdout.write(macronizedtext)
        except Exception as inst:
            print(inst.args[0])
            macronizedtext = ""
    print('</textarea><br>')
    print('<input type="checkbox" name="macronize" onchange="toggleDisabled(this.checked)" value="on" %s> Mark long vowels.<br>' % ("checked" if domacronize else ""))
    print(u'&nbsp;&nbsp;&nbsp;<input class="macronizersetting" type="checkbox" name="alsomaius" value="on" %s> Also mark <i>māius</i> etc.<br>' % ("checked" if alsomaius else ""))
    print('&nbsp;&nbsp;&nbsp;To improve the result, try to scan the text as <select name="scan">')
    print('<option value="%s"%s>prose (no scansion)</option>' % (PROSE, " selected" if scan == PROSE else ""))
    print('<option value="%s"%s>dactylic hexameters</option>' % (HEXAMETER, " selected" if scan == HEXAMETER else ""))
    print('<option value="%s"%s>elegiac distichs</option>' % (ELEGIACS, " selected" if scan == ELEGIACS else ""))
    print('<option value="%s"%s>hendecasyllables</option>' % (HENDECA, " selected" if scan == HENDECA else ""))
    print('<option value="%s"%s>iambic trimeter + dimeter</option>' % (IAMBTRIDI, " selected" if scan == IAMBTRIDI else ""))
    print('</select>.<br>')
    print(u'&nbsp;&nbsp;&nbsp;<input class="macronizersetting" type="checkbox" name="doevaluate" value="off" %s> Compare result with correctly macronized input text.<br>' % ("checked" if doevaluate else ""))
    print('<input type="checkbox" name="utov" value="on" %s> Convert u to v.<br>' % ("checked" if performutov else ""))
    print('<input type="checkbox" name="itoj" value="on" %s> Convert i to j.<br>' % ("checked" if performitoj else ""))
    print('<input type="submit" value="Submit"> (Please be patient!)<br>')
    print('</p></form>')

    if macronizedtext != "":
        print('<h2>Result</h2>')
        print('<p>(Ambiguous forms are marked <span class="ambig">yellow</span>; unknown forms are <span class="unknown">orange</span>. You may click on a vowel to add or remove a macron.)</p>')
        if scan != PROSE:
            print('<div class="feet">' + "<br>".join(macronizer.tokenization.scannedfeet) + '</div>')
        print('<div class="prewrap" id="selectme" contenteditable="true">' + macronizer.tokenization.detokenize(True) + '</div>')
        print('<p><input id="selecttext" type="button" value="Copy text"></p>')
    
    if macronizedtext != "":
        if doevaluate:
            print('<h2>Evaluation</h2>')
            (accuracy, evaluatedtext) = evaluate(texttomacronize, macronizedtext)
            print('<div class="prewrap">%s</div>' % evaluatedtext)
            print('<p>Accuracy: %f%%</p>' % (accuracy * 100))
        if dodebug:
            print('<h2>Debug info</h2>')
            print('<pre>')
            macronizer.tokenization.show()
            print('</pre>')
    print("""<h2>News</h2>

    <p>August 2017: More meters added! The macronizer can now handle hendecasyllables as well as distichs of iambic trimeters and dimeters (<i>Beātus ille quī procul negōtiīs...</i>).</p>

    <p>May 2017: I have now made the macronized text editable, which means that it will now be much easier to correct typos or misspellings while proofreading the text.</p>

    <p>October 2016: The performance on texts written in all uppercase letters has been greatly improved.</p>

    <p>July 2016: I am happy to announce that the Macronizer now is
    able to take the meter into account when guessing the vowel
    lengths in poetry. When tested on a couple of books of the
    Aeneid (from the eminent <a href="http://dcc.dickinson.edu/">Dickinson College
    Commentaries</a>), this has been demonstrated to cut the number of
    erroneous vowel lengths in half! Currently, dactylic hexameters
    and elegiac distichs are supported; other meters may be added.</p>

    <p>Also, I have now added a PayPal donation button:
    if you use the macronizer regularly and find it helpful and
    time-saving, please consider making a donation, to support
    maintenance and continuous development! Any amount is very much
    appreciated!
    <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
    <p>
    <input type="hidden" name="cmd" value="_s-xclick">
    <input type="hidden" name="hosted_button_id" value="KKJ2V4ZVB3WGU">
    <input type="image" src="https://www.paypalobjects.com/en_US/SE/i/btn/btn_donateCC_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
    <img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
    </p>
    </form>
    """)
    print("""<h2>Information</h2>

    <p>This automatic macronizer lets you quickly mark all the long vowels
    in a Latin text. The expected accuracy on an average classical text is
    estimated to be about 98% to 99%. Please review the resulting macrons
    with a critical eye!</p>

    <p>The macronization is performed using a part-of-speech tagger
    (<a href="http://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/">RFTagger</a>)
    trained on the <a href="http://www.dh.uni-leipzig.de/wo/projects/ancient-greek-and-latin-dependency-treebank-2-0/">Latin
    Dependency Treebank</a>, and with macrons provided by a customized
    version of the Morpheus morphological analyzer. An earlier version of
    this tool was the subject of my bachelor’s thesis in Language
    Technology, <i><a href="http://stp.lingfil.uu.se/exarb/arch/winge2015.pdf">Automatic
    annotation of Latin vowel length</a></i>.</p>

    <p>If you want to run the macronizer locally, or develop it further,
    you may find the <a href="https://github.com/Alatius/latin-macronizer">source
    code on GitHub</a>.</p>

    <p>Copyright 2015-2017 Johan Winge. Please send comments to
    <a href="mailto:johan.winge@gmail.com">johan.winge@gmail.com</a>.</p>

    <script type="text/javascript">
    function enlarge(textbox) {
       textbox.rows = 20;
    }

    function toggleDisabled(_checked) {
       var elements = document.getElementsByClassName('macronizersetting')
       for (var i = 0; i < elements.length; i++) {
          elements[i].disabled = _checked ? false : true;
       }
    }

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
    document.getElementById("selecttext").onclick = function () {
       var text = document.getElementById("selectme"), range, selection;
       if (document.body.createTextRange) {
          range = document.body.createTextRange();
          range.moveToElementText(text);
          range.select();
       } else if (window.getSelection) {
          selection = window.getSelection();
          range = document.createRange();
          range.selectNodeContents(text);
          selection.removeAllRanges();
          selection.addRange(range);
       }
       var successful = document.execCommand('copy');
    };
    </script>""")
    print('</body>')
    print('</html>')

else:  # Run as a free-standing Python script

    parser = argparse.ArgumentParser()
    infile_group = parser.add_mutually_exclusive_group()
    infile_group.add_argument("-i", "--infile", help="file to read from; otherwise stdin")
    parser.add_argument("-o", "--outfile", help="file to write to; otherwise stdout")
    parser.add_argument("-v", "--utov", action="store_true", help="convert u to v where appropriate")
    parser.add_argument("-j", "--itoj", action="store_true", help="similarly convert i to j")
    macrons_group = parser.add_mutually_exclusive_group()
    macrons_group.add_argument("--nomacrons", action="store_true", help="don't mark long vowels")
    macrons_group.add_argument("--maius", action="store_true", help="do mark vowels also in māius and such")
    infile_group.add_argument("--test", action="store_true", help="mark vowels in a short example text")
    parser.add_argument("--initialize", action="store_true", help="reset the database (only necessary once)")
    parser.add_argument("--evaluate", action="store_true", help="test accuracy against input gold standard")
    args = parser.parse_args()

    if args.initialize:
        try:
            macronizer = Macronizer()
            macronizer.wordlist.reinitializedatabase()
        except Exception as inst:
            print(inst.args[0])
            exit(1)
        exit(0)

    macronizer = Macronizer()
    if args.test:
        texttomacronize = u"O orbis terrarum te saluto!\n"
    else:
        if args.infile is None:
            if sys.version_info[0] < 3:
                infile = codecs.getreader('utf-8')(sys.stdin)
            else:
                infile = sys.stdin
        else:
            infile = codecs.open(args.infile, 'r', 'utf8')
        texttomacronize = infile.read()
    # endif
    texttomacronize = unicodedata.normalize('NFC', texttomacronize)
    macronizer.settext(texttomacronize)
    macronizedtext = macronizer.gettext(not args.nomacrons, args.maius, args.utov, args.itoj, markambigs=False)
    if args.evaluate:
        (accuracy, _) = evaluate(texttomacronize, macronizedtext)
        print("Accuracy: %f" % (accuracy*100))
    else:
        if args.outfile is None:
            if sys.version_info[0] < 3:
                outfile = codecs.getwriter('utf8')(sys.stdout)
            else:
                outfile = sys.stdout
        else:
            outfile = codecs.open(args.outfile, 'w', 'utf8')
        outfile.write(macronizedtext)
    # endif
# endif
