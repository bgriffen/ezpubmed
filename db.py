import config
import peewee as pw
import datetime
import os
import pubmed_parser
import config
import pandas as pd

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

def get_db():
    #db = pw.SqliteDatabase(':memory:')
    print("Using...",config.papers_db)
    db = pw.SqliteDatabase(config.papers_db)
    return db

def reset_db():
    db = get_db(config.papers_db)
    db.drop_tables([PaperDB])
    db.create_tables([PaperDB])
    return db

def create_db():
    db = get_db(config.papers_db)
    db.create_tables([PaperDB])
    return db

class BaseModel(pw.Model):
    """A base model that will use our MySQL database"""

    class Meta:
       database = get_db(config.papers_db) 
    pass

class PaperDB(BaseModel):
    pmid = pw.IntegerField(unique=True)
    title = pw.CharField()
    abstract = pw.TextField()
    journal = pw.CharField()
    authors = pw.CharField()
    pubdate = pw.DateField()
    mesh_terms = pw.CharField()
    publication_types = pw.CharField()
    chemical_list = pw.CharField()
    keywords = pw.CharField()
    doi = pw.CharField()
    delete = pw.BooleanField()
    affiliations = pw.CharField()
    pmc = pw.IntegerField()
    other_id = pw.CharField()
    medline_ta = pw.CharField()
    nlm_unique_id = pw.IntegerField()
    issn_linking = pw.CharField()
    country = pw.CharField()
    pubyear = pw.IntegerField()
    pubmonth = pw.IntegerField()
    pubday = pw.IntegerField()

if __name__ == '__main__':
    p = PaperDB()
