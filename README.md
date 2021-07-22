
# PubMed Pandas

A basic framework for keeping an up-to-date datastore of PubMed using pandas.

## Motivation

Most PubMed management systems are rather cumbersome, complex and have awkward dependencies. Stripping it all back to core Python libraries eases data access and enables data science minded people to immediately obtain an up-to-date, structured dataframe from the get go. General guiding principles are as follows:

- Simplicity without databases (e.g. SQL)
- Automatically manages and updates filesystem with latest PubMed archive.
- Basic NLP embeddings, analysis using [SpaCy](https://spacy.io/).
- Simple recommendation engine for generating a 'Paper Digest' periodically.


## Requirements

- pandas
- python
- numpy
- matplotlib
- [SciSpaCy](https://allenai.github.io/scispacy/)

### XML Dataset

- Baseline: `ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/`
- Daily: `ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/`

### Storage Requirements

You will need about 400GB to cover the overheads. This can be halved by removing XML files once they have been inserted into the dataframe.

```bash
255G  baseline      # XML files
71G   updatefiles   # XML files (size as of 2021-07-22 but will grow over the year)
25G   papers.parq   # also broken down by year, 2021.parq, 2020.parq etc.
```

## Usage

### Update Dataset

```python
  import pubmedpandas as pp

  xml_path = "/path/to/temp/xml/dump/"

  baseline = pp.Dataset(xml_path,"baseline")
  baseline.update()

  updates = pp.Dataset(xml_path,"updatefiles")
  updates.update()
```

### Load Dataset

```python
  import pubmedpandas as pp

  xml_path = "/path/to/temp/xml/dump/"

  pm = pp.Dataset(xml_path)
  pm.load_papers(year=2021)

  pm.papers     # pandas dataframe holding title, abstract, authors, affiliations etc.
```

### NLP

```python
import scispacy
import spacy

# Trained models available here: https://allenai.github.io/scispacy/

# en_core_sci_sm       A full spaCy pipeline for biomedical data.
# en_core_sci_md       ^ with a larger vocabulary and 50k word vectors.
# en_core_sci_scibert  ^ with ~785k vocabulary and allenai/scibert-base as the transformer model.
# en_core_sci_lg       ^ with a larger vocabulary and 600k word vectors.
# en_ner_craft_md      A spaCy NER model trained on the CRAFT corpus(Bada et al., 2011).
# en_ner_jnlpba_md     ^ trained on the JNLPBA corpus(Collierand  Kim,  2004).
# en_ner_bc5cdr_md     ^ trained on the BC5CDR corpus (Li  et  al.,2016).
# en_ner_bionlp13cg_md ^ trained on the BIONLP13CG corpus (Pyysalo et al., 2015).

nlp = spacy.load('en_ner_bionlp13cg_md')

# More coming soon...

```


## License

[MIT](https://choosealicense.com/licenses/mit/)

## Authors

[Brendan Griffen](https://www.brendangriffen.com/), 2021.
-  [@brendangriffen](https://www.twitter.com/bgriffen)
