# fixofx #
### Canonicalize various financial data file formats to OFX 2 (a.k.a XML) ###

`fixofx.py` is a Python utility that canonicalizes various financial data file
formats to OFX 2, which is an XML format and hence a lot easier for other code
to deal with. It recognizes OFX 1.x, OFX 2.x, QFX, QIF, and OFC.

Pipe a data file to `fixofx.py`, or specify an input file with the `-f` flag, and
if the file is successfully parsed, an OFX 2 file with equivalent data will
be output.

Various parts of fixofx go through contortions to try to interpret ambiguous
or malformed data, both of which are very common when importing bank data
files. QIF, in particular, is an extremely irregular file format, and fixofx
makes best efforts but will not cover all cases. Also, some international
formats are recognized and interpreted, such as British versus US date
formats, but more work could be done on this.

Sometimes a data file will not contain information that is important for OFX --
for instance, neither OFC nor QIF include the OFX "FID" and "ORG" fields. Other times,
the data format will include this data, but inconsistently, such as QIF's account
type, which can be ambiguous or absent. In these cases you can ask the user to 
provide hints to fixofx, and convey those hints via command-line options (see 
_Command line operation_, below).

The fixofx project also includes `fakeofx.py`, a utility script to generate fake
OFX files for testing purposes.

## Installation ##

There are no external dependencies other than Python 2.6 or above. The project
has not been tested at all with Python 3.

Just clone the repo from GitHub and you're good to go:

    git clone git://github.com/wesabe/fixofx.git

## Tests ##

A partial test suite is included. Run it as follows:
    
    cd test
    ./test_suite.py

## Command line operation ##

The simplest invocation of the script is:

    ./fixofx.py -f <path-to-data-file.fmt>
    
You can also pipe a data file to standard input -- that is, this invocation
is equivalent to the above:

    ./fixofx.py < <path-to-data-file.fmt>

There are several command line options, as follows:

    -h, --help                     show this help message and exit
    -d, --debug                    spit out gobs of debugging output during parse
    -v, --verbose                  be more talkative, social, outgoing
    -t, --type                     print input file type and exit
    -f FILENAME, --file=FILENAME   source file to convert (writes to STDOUT)
    --fid=FID                      (OFC/QIF only) FID to use in output
    --org=ORG                      (OFC/QIF only) ORG to use in output
    --curdef=CURDEF                (OFC/QIF only) Currency identifier to use in output
    --lang=LANG                    (OFC/QIF only) Language identifier to use in output
    --bankid=BANKID                (QIF only) Routing number to use in output
    --accttype=ACCTTYPE            (QIF only) Account type to use in output
    --acctid=ACCTID                (QIF only) Account number to use in output
    --balance=BALANCE              (QIF only) Account balance to use in output
    --dayfirst                     (QIF only) Parse dates day first (UK format)

## Debugging ##

If you find a data file fixofx can't parse, try running with the `-v` flag,
and if that doesn't help (which it probably won't), try the `-d` flag, too.

Most of the time a failed parse is due to a malformed data file. QIF,
especially, is damn near undocumented, and different banks just seem to make
stuff up about how they think it should work. And they don't talk to each
other about their crazy QIF theories, either. So that's bad.

If you think the script is basically working (e.g., tests pass) but a parse is
failing, the best thing to do is to just look at the data file and see how it
is different from other examples you've seen. Post a cleaned-up (sensitive
data removed) snippet as a gist if you want someone else to help. Usually a
difference will jump out at you after a while if you're familiar with the
format.

## fakeofx.py ##

The `fakeofx.py` script generates real-ish-seeming OFX for testing and demo
purposes. You can generate a few fake OFX files using the script, and upload
them to Wesabe to try it out or demonstrate it without showing your real
account data to anyone.

The script uses some real demographic data to make the fake transactions it
lists look real, but otherwise it isn't at all sophisticated. It will randomly
choose to generate a checking or credit card statement and has no options.

## Contributing ##

Contributions to fixofx are welcome. Please add tests for your contribution
and make sure all tests pass before sending a pull request. Here are some
ideas for things to do:

* fakeofx could use some command line options and a little more control over
  the output. **(EASY)**
* The OFX parser class has some ugly regular expression hacks added to deal
  with a variety of malformed OFX inputs. Each new regex makes things slower
  and makes the baby jwz cry. Find a better path. **(EASY)**
* Fill in missing tests, especially in QIF conversion. **(MEDIUM)**
* fixofx currently converts QIF to OFX/1, and then OFX/1 to OFX/2, which is
  totally crazy-pants and makes everything ungodly slow. Go straight from QIF
  to OFX/2 instead. **(MEDIUM)**
* Some people would be happy if fixofx accepted a bunch of input formats (as
  it does) and had options for outputing any of those formats, too (right now
  OFX/2 output is the only option). Basically, convert everything to an
  internal representation and then output whatever kind of document the user
  wants. **(MEDIUM)**
* The date format parsing could be a lot more intelligent, using windows of
  transactions to guess the date format instead of requiring at least one
  unambiguous date. **(MEDIUM)**
* The test suite uses the old unittest module, which is super annoying.
  Convert the tests to use `nose` instead. **(MEDIUM)**
* There is the start of a CSV converter in lib/ofxtools. This has to be one of
  the most-requested Wesabe features evar. Have at it. **(HARD)**
* Convert this whole thing to ruby so it can be run in the Rails process
  instead of as an external script. The original reasons it was done in python
  don't matter any more and running it internally would be a lot more stable.
  Or go straight to Java and make it part of BRCM. **(HARD EITHER WAY)**

## Thanks ##

The following people have contributed patches to fixofx - thanks!

* [James Nylen](http://github.com/nylen)
* [Jeremy Milum](http://github.com/jmilum)
