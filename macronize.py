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

MACRONIZERLIB = '.'

import cgi
import os
import sys
import codecs
from xml.sax.saxutils import escape
os.chdir(MACRONIZERLIB)
from macronizer import Macronizer

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
    print '<style type="text/css">'
    print '  span.wrong {color:red;}'
    print '  span.ambig {background-color:yellow;}'
    print '  span.unknown {background-color:orange;}'
    print '  span.fixed {background-color:lightgreen;}'
    print '  div.prewrap {white-space: pre-wrap;}'
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
            macronizer = Macronizer()
            macronizer.settext(texttomacronize)
            macronizedtext = macronizer.gettext(domacronize, alsomaius, performutov, performitoj, markambigs=False)
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
        print '<div class="prewrap" id="selectme">' + macronizer.tokenization.detokenize(True) + '</div>'
        print '<p><input id="selecttext" type="button" value="Copy text"/></p>'

    if macronizedtext != "" and domacronize and any(i in texttomacronize for i in u"āēīōū"):
        print '<h2>Evaluation</h2>'
        sys.stdout.write('<div class="prewrap">')
        vowelcount = 0
        lengthcorrect = 0
        for (a,b) in zip(list(texttomacronize), list(macronizedtext)):
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
        if len(macronizer.tokenization.tokens) > 2:
            if macronizer.tokenization.tokens[0].token == "DEBUG":
                print '<h2>Debug info</h2>'
                print '<pre>'
                macronizer.tokenization.show()
                print '</pre>'
    
    print '<h2>Information</h2>'
    print '<p>This automatic macronizer lets you quickly mark all the long vowels in a Latin text. The expected accuracy on an average classical text is estimated to be about 98% to 99%. Please review the resulting macrons with a critical eye!</p>'
    print '<p>The macronization is performed using a part-of-speech tagger (<a href="http://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/">RFTagger</a>) trained on the <a href="http://www.dh.uni-leipzig.de/wo/projects/ancient-greek-and-latin-dependency-treebank-2-0/">Latin Dependency Treebank</a>, and with macrons provided by a customized version of the Morpheus morphological analyzer. An earlier version of this tool was the subject of my bachelor’s thesis in Language Technology, <i><a href="http://stp.lingfil.uu.se/exarb/arch/winge2015.pdf">Automatic annotation of Latin vowel length</a></i>.</p>'
    print '<p>If you want to run the macronizer locally, or develop it further, you may find the <a href="https://github.com/Alatius/latin-macronizer">source code on GitHub</a>.</p>'
    print '<p>Copyright 2015 Johan Winge. Please send comments to <a href="mailto:johan.winge@gmail.com">johan.winge@gmail.com</a>.</p>'

    print """<script type="text/javascript">
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
            exit(0)
        elif arg == "--initialize":
            try:
                macronizer = Macronizer()
                macronizer.wordlist.reinitializedatabase()
            except Exception as inst:
                print inst.args[0]
                exit(1)
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
        else:
            print "Unknown argument:", arg
            exit(1)
    #endfor
    try:
        macronizer = Macronizer()
        if dotest:
            texttomacronize = "O orbis terrarum te saluto!\n"
        else:
            if infilename == "":
                infile = codecs.getreader('utf-8')(sys.stdin)
            else:
                infile = codecs.open(infilename, 'r', 'utf8')
            texttomacronize = infile.read()
        #endif
        macronizer.settext(texttomacronize)
        macronizedtext = macronizer.gettext(domacronize, alsomaius, performutov, performitoj, markambigs=False)
        if outfilename == "":
            outfile = codecs.getwriter('utf8')(sys.stdout)
        else:
            outfile = codecs.open(outfilename, 'w', 'utf8')
        outfile.write(macronizedtext)
    except Exception as inst:
        print inst.args[0]
        exit(1)

#endif


