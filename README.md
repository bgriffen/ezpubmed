
# PubMed Pandas

A basic framework for keeping an up-to-date datastore of PubMed in a format that can be easily turned into a pandas dataframe for analysis.

## Motivation

Most PubMed management systems are rather cumbersome, complex and have awkward dependencies (e.g. setting up a server). Stripping it all back to core Python libraries eases data access and enables data science minded people to immediately obtain an up-to-date, structured dataframe from the get go. General guiding principles are as follows:

- Simplicity.
- Automatically manages and updates with latest PubMed archive.

### XML Dataset

- Baseline: `ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/`
- Daily: `ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/`

## Approach

1. The XML files from the PubMed archive are compared to what you have locally and downloaded where needed.
2. These are then inserted into the `papers.db` SQLite database file using peewee (a light ORM).
3. This can then be queried and converted into a dataframe with ease. Helper functions (e.g. `load_year(2021)`) are being developed over time to avoid any need for SQL knowledge, though the whole point of peewee is to abstract that away anyway.

## Requirements

- pandas
- python
- numpy
- matplotlib
- [peewee](https://github.com/coleifer/peewee)
- [SciSpaCy](https://allenai.github.io/scispacy/)
- [pubmed_parser](https://github.com/titipata/pubmed_parser)

### Storage Requirements

You will need about 300GB to cover the overheads. 

```bash
255G  baseline      # XML files
71G   updatefiles   # XML files (size as of 2021-07-22)
70G   papers.db     # sqlite database
```

## Usage

### Create/Update Dataset

You can get going immediately by simply running `main.py`. Note, the first time you run this it will take a few days to download PubMed and populate the database.

```python
import pubmedpandas as pp
  
p = pp.PubMedPandas()
p.update_db()

```

You should see the following output per file once the download component is done.

```bash
Processing: pubmed21n0001.xml (0.00 complete)
  > Preparing papers...
  > Parsing dates...
  > Creating year-month-day entries...
  > # Papers: 15377
    >> Updating 15377 (100.00) papers into database.
```

### Load Dataset

Note, owing to [issues with writing mixtype data to HDF5](https://stackoverflow.com/questions/57078803/overflowerror-while-saving-large-pandas-df-to-hdf), the papers are stored in parquet format and vectors in HDF5.

```python
import pubmedpandas as pp

p = pp.PubMedPandas()
p.load_year(1970)
p.papers     # pandas dataframe holding title, abstract etc.
```

### Interact with DB via peewee

If the basic queries (`load_year` etc.) are not sufficient, various manipulations can be found [here](https://docs.peewee-orm.com/en/latest/peewee/querying.html#filtering-records). For example you might want all the papers from February:

```python
import pubmedpandas as pp

p = pp.PubMedPandas()
q = db.PaperDB.select().where(db.PaperDB.pubmonth == 2) # all papers in February

# If you would like a pandas dataframe, simply use:
papers = pd.DataFrame(list(q.dicts()))

```

Other variables to query can be found via `db.fields`. For convenience, these are as follows:

```python
fields = ['pmid',
          'title', 
          'abstract', 
          'journal', 
          'authors', 
          'pubdate', 
          'mesh_terms',
          'publication_types', 
          'chemical_list', 
          'keywords', 
          'doi', 
          'delete',
          'affiliations', 
          'pmc', 
          'other_id', 
          'medline_ta', 
          'nlm_unique_id',
          'issn_linking', 
          'country', 
          'pubyear', 
          'pubmonth',
          'pubday']
```

Note: `pubyear`,`pubmonth`,`pubday` are built in extensions of `pubdate` that are created during the `p.update_db()` process to enhance time-based queries.

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
