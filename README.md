
![ezpubmed_logo](ezpubmed_logo.png)

# ezpubmed

A basic framework for keeping an up-to-date datastore of PubMed in a format that can be easily turned into a pandas dataframe for analysis.

## Motivation

Most PubMed management systems are rather cumbersome, complex and have awkward dependencies (e.g. setting up a server). The goal here is to prioritize two features.

- Simplicity.
- Automatically manage and update your local store to the latest PubMed archive.

## Data Ingest

PubMed publishes two core datasets:

* `baseline` are all papers up until the current year (e.g. 1900-2020)
* `updatefiles` are all the papers of the current year AND corrections to the baseline

These datasets are found at the following FTPs:

- Baseline: `ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/`
- Daily: `ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/`

A direct `pandas` handling of this can be done and actually if you look at early commits was what was done but owing to how simple it is to maintain a SQLite DB in [`peewee`](https://github.com/coleifer/peewee), that was found to be the best path forward.

## Data Management

1. The XML files from the PubMed archive are compared to what you have locally and downloaded where needed (essentially syncing with the FTP).
2. New papers are inserted into the `papers.db` SQLite database file using `peewee`. Papers with metadata to be updated are also updated in the database during the update phase.
3. Helper functions in `utils_pubs` can then load the relevant dataframe for downstream use. New additions are welcome. =)

## Requirements

### Packages

- `pandas>=1.0.5`
- `python>=3.8`
- `numpy>=1.18.5`
- [`peewee>=3.13.3`](https://github.com/coleifer/peewee)
- [`pubmed_parser>=0.2.2`](https://github.com/titipata/pubmed_parser)
- [`scispacy==0.2.5`](https://allenai.github.io/scispacy/)

### Storage 

You will need about 400GB to cover the overheads. Work is being done to reduce this to just retain the `papers.db` and updating the XML files where needed and deleting once done.

```bash
255G  baseline      # XML files
71G   updatefiles   # XML files (size as of 2021-07-22)
70G   papers.db     # Full SQLite database
```

## Getting Started

### Create/Update Dataset

You can get going immediately by simply setting your paths in `config.py`,

```python
data_path = r'/path/to/data/'
papers_db = data_path + 'papers.db'
```

and then running `main.py`. Note, the first time you run this it will take a few days to download PubMed and populate the database.

```python
import ezpubmed as pp
  
p = pp.EzPubMed()
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
...
```

### Load Dataset

Once the `update_db` has been run at least once, you can then obtain your data in pandas format simply as follows:

```python
import ezpubmed as pp
  
p = pp.EzPubMed()
p.load_year(1970)
p.papers     # pandas dataframe holding title, abstract etc.
```

### Customized queries via peewee

If the basic queries (`load_year` etc.) are not sufficient, various manipulations can be found [here](https://docs.peewee-orm.com/en/latest/peewee/querying.html#filtering-records). These can be done directly on the database (`dbase`). An example you might want all the papers from February:

```python
from ezpubmed import db

# Query all papers published in the month of February
q = db.PaperDB.select().where(db.PaperDB.pubmonth == 2) 

# If you would like a pandas dataframe, simply use:
papers = pd.DataFrame(list(q.dicts()))

```

Other variables to query can be found via `db.fields`, though use some of the peewee docs as a guide if you're going this way. For convenience, the other fields can be found below ([NIH data information](https://www.nlm.nih.gov/bsd/mms/medlineelements.html) if curious).

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

If you use Zotero to manage your papers, you can generate a latent space embedding using the following:

```python
# load zotero papers
dfz = utils_nlp.initialize_zotero_library("papers.json")

# generate vectors from titles + abstracts (see below for details)
dfv = utils_nlp.generate_zotero_embeddings(df,model='en_ner_bionlp13cg_md')

# generate reduced embedding
embedding = utils_nlp.calculate_embedding(dfv)
```

Under the hood, a NLP model is used from scispacy. Some details as follows:

```python
# Trained models available here: https://allenai.github.io/scispacy/

# en_core_sci_sm       A full spaCy pipeline for biomedical data.
# en_core_sci_md       ^ with a larger vocabulary and 50k word vectors.
# en_core_sci_scibert  ^ with ~785k vocabulary and allenai/scibert-base as the transformer model.
# en_core_sci_lg       ^ with a larger vocabulary and 600k word vectors.
# en_ner_craft_md      A spaCy NER model trained on the CRAFT corpus(Bada et al., 2011).
# en_ner_jnlpba_md     ^ trained on the JNLPBA corpus(Collierand  Kim,  2004).
# en_ner_bc5cdr_md     ^ trained on the BC5CDR corpus (Li  et  al.,2016).
# en_ner_bionlp13cg_md ^ trained on the BIONLP13CG corpus (Pyysalo et al., 2015).
```

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Authors

[Brendan Griffen](https://www.brendangriffen.com/) ([@brendangriffen](https://www.twitter.com/bgriffen)), 2021.
