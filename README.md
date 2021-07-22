
# PubMed Pandas

A basic framework for keeping an up-to-date datastore of PubMed using pandas.

## Motivation

Most Pubmed management systems are rather cumbersome, complex and have awkward dependencies. Stripping it all back to core Python libraries eases data access and enables data science minded people to hit the ground running with a nice structured dataframe from the get go. General guiding principles are as follows:

- Simplicity without databases (e.g. SQL)
- Automatically manages and updates filesystem with latest PubMed archive.
  - Keep synced with the baseline `ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/`
  - Keep synced with the updates `ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/`
- Basic NLP embeddings, analysis using [SpaCy](https://spacy.io/).
- Simple recommendation engine for generating a 'Paper Digest' periodically.

## Usage

### Update Dataset

```python
  import PubMedDataset

  xml_path = "/path/to/temp/xml/dump/"

  # pubmed_daily_address = r'ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/'
  # pubmed_baseline_address = r'ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/'

  baseline = PubMedDataset(xml_path,"baseline")
  baseline.update()

  updates = PubMedDataset(xml_path,"updatefiles")
  updates.update()
```

### Load Dataset

```python
  import PubMedDataset

  xml_path = "/path/to/temp/xml/dump/"

  pm = PubMedDataset(xml_path)
  pm.load_papers(year=2021)

  pm.papers     # pandas dataframe holding title, abstract, authors, affiliations etc.
```

## Authors

Brendan Griffen, 2021.
- [@brendangriffen](https://www.twitter.com/bgriffen)