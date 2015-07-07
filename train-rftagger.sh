MORPHLIB=morpheus/stemlib morpheus/bin/cruncher -LS < vocabulary.txt > vocabulary-crunched.txt 
python morpheus2lexicon.py
python corpus2train.py
rft-train -l rftagger-lexicon.txt -c 7 -p 6.5 ldt-corpus.txt wordclass.txt rftagger-ldt.model

