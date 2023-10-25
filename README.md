# Extractor
A german OIE system for relational Tripel with facets.

This OIE system requires the spaCy library and was build upon the model "de_dep_news_trf".


# Setup
This project requieres spaCy and a german nlp pipeline that can be used by spaCy.
```sh
pip install -U pip setuptools wheel
pip install -U spacy
python -m spacy download de_dep_news_trf
```

# Usage
You can run the extractor by using the following command:
```sh
python MainExtractor.py <pathToInputFile>
```
optional arguments are:

--dest DEST: target directory for the results (current working directory by default)

--model MODEL: nlp pipeline spaCy shall use (de_dep_news_trf by default)

(Note that the input file must be utf-8 encoded and the resulting files will also be utf-8 encoded)

# Formatting
The extractor will read the sentences line by line from the input file. Therefore every sentence needs to be in a seperate line of the input file.

As a result the extractor will generate the two text files "extractedTupels.txt" and "extractedTupelsWithFacets.txt". Both files seperate the elements of the tripel via a tab. Also every tripel starts with the line number of the sentence in the input file and a tab. The file "extractedTupelsWithFacets.txt" stores every found triple with their respective facets whereas "extractedTupels.txt" the triple and their facets as one triple combined stores.

## Example
The sentence "Der verzwickte Fall handelt von einem Diamanten mit einem Kratzer in der Mitte." results in:

extractedTupels.txt
```
1 -> Der verzwickte Fall -> handelt -> von einem Diamanten
1 -> Der verzwickte Fall -> handelt von einem Diamanten -> mit einem Kratzer
1 -> Der verzwickte Fall -> handelt von einem Diamanten mit einem Kratzer -> in der Mitte
1 -> Diamanten -> mit -> Kratzer
1 -> Kratzer -> in -> Mitte
```

extractedTupelsWithFacets.txt
```
1 -> Fall -> handelt -> von Diamanten
sb: Der
    verzwickte
vb: []
ob: einem
    mit Kratzer
	einem
	in Mitte
          der
cd: []
1 -> Diamanten -> mit -> Kratzer
sb: []
vb: []
ob: []
cd: []
1 -> Kratzer -> in -> Mitte
sb: []
vb: []
ob: []
cd: []
```
