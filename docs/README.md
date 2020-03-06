# Documentation

[View documentation](https://htmlpreview.github.io/?https://raw.githubusercontent.com/SamuelHill/companionsKQML/master/docs/companionsKQML.html) - this is a link to htmlpreview.github.io which will render the documents in this folder as html pages.

Provided in this folder is the output of calling `pydoc` on the package. Specifically;
```
python3 -m pydoc -w companionsKQML
python3 -m pydoc -w companionsKQML.companionsKQMLModule
python3 -m pydoc -w companionsKQML.pythonian
mv *.html docs
```
To explore the documentation on your own machine, simply open any of the files in a browser (they are all linked together). Alternatively, if you want a live browser to look over the objects and functions offered by this package call `python3 -m pydoc -b companionsKQML`.
