# Latin Macronizer

Python package for marking Latin texts with macrons. Copyright 2015-2023 Johan Winge.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Minimal example of usage:
```
from latin_macronizer import Macronizer
macronizer = Macronizer(db_path="macronizer.db")
macronizedtext = macronizer.macronize("Iam primum omnium satis constat Troia capta in ceteros saevitum esse Troianos")
```

Initializing Macronizer() may take a couple of seconds, so if you want
to mark macrons in several strings, you are better off reusing the
same Macronizer object.

The macronizer function takes a couple of optional parameters, which
control in what way the input string is transformed:
* domacronize: mark long vowels; default True
* alsomaius: also mark vowels before consonantic i; default False 
* performutov: change consonantic u to v; default False
* performitoj: similarly change i to j; default False
* markambigs: mark up the text in various ways with HTML tags; default False

If you want to transform the same text in different ways, you should use
the separate gettext and settext functions, instead of macronize:
```
from latin_macronizer import Macronizer
macronizer = Macronizer(db_path="macronizer.db")
macronizer.settext("Iam primum omnium")
print(macronizer.gettext())
print(macronizer.gettext(domacronize=False, performitoj=True))
```

NOTE: If you are not a developer, you probably want to call the front end
macronize.py instead.
