import spacy
import pandas as pd
import glob,os
import utils
import swifter
import re
import joblib
import numpy as np
import config
import json

import umap

def cosine_similarity(vec,df):
    dotprocuts = df.dot(vec)
    vec2norm = df.apply(np.linalg.norm,axis=1)
    denom = np.linalg.norm(vec1)*vec2norm
    cs = dotprocuts/denom
    return cs
    
def calculate_embedding(dfv):
    umapp = umap.UMAP()
    embedding = umapp.fit_transform(dfv)
    return embedding

def normalize_fn(comment, nlp, lowercase=True, remove_stopwords=True):
    #stops = stopwords.words("english")
    comment = str(comment)
    stops = spacy.lang.en.stop_words.STOP_WORDS

    if lowercase:
        comment = comment.lower()
    comment = nlp(comment)
    lemmatized = list()
    for word in comment:
        lemma = word.lemma_.strip()
        if lemma:
            if not remove_stopwords or (remove_stopwords and lemma not in stops):
                lemmatized.append(lemma)
    return " ".join(lemmatized)

def get_zotero_pmids(zotero_df):
    pmdids =[]
    for idi in zotero_df['note'].dropna():
        for idj in idi.split("\n"):
            if "PMID" in idj:
                pmdids.append(idj.split(":")[-1])
    pmdids = np.array(pmdids,dtype='int64')
    return pmdids

def generate_zotero_embeddings(library_df):
    nlp = spacy.load('en_ner_bionlp13cg_md')
    vecs = np.zeros((library_df.shape[0],200))
    library_vectors = pd.DataFrame(vecs,index=library_df.index)
    print("Combining titles and abstracts...")
    library_df['title+abstract'] = library_df['title'].replace(np.nan, '') + " " + library_df['abstract'].replace(np.nan, '')
    print("Removing stopwords...")
    library_df['title+abstract'] = library_df['title+abstract'].replace(np.nan, '')
    library_df['title+abstract+cleaned'] = library_df['title+abstract'].apply(normalize_fn,nlp=nlp)
    counter = 0
    print("Populating with vectors...")
    for doc in nlp.pipe(library_df['title+abstract+cleaned'],disable=["textcat","tokenizer","ner","tagger", "parser"]):
        library_vectors.iloc[counter] = doc.vector
        print(" >> %5i abstracts vectorized..." % counter)
        counter+=1
    
    #library_vectors.to_hdf(config.library_path+library_basename+".h5",'vectors')
    return library_vectors

def read_zotero_json(zotero_file):
    with open(zotero_file) as json_file:  
        zotero = json.load(json_file)
    zotero_df = pd.DataFrame(zotero)  
    zotero_df['abstract'].dropna(inplace=True)
    return zotero_df

def initialize_zotero_library(fpath,rebuild_library=False):
    library_basename = os.path.basename(fpath).replace(".json","")
    if os.path.exists(config.library_path+library_basename+".h5") and not rebuild_library:
        with pd.HDFStore(config.library_path+library_basename+".h5") as hdf:
            keys = sorted(hdf.keys())
        library_df = pd.read_hdf(config.library_path+library_basename+".h5","library")
        if "/vectors" in keys:
            library_vectors = pd.read_hdf(config.library_path+library_basename+".h5","vectors")
        else:
            generate_zotero_embeddings()
    else:
        library_df = read_zotero_json(config.library_path+fpath)
        library_df.drop_duplicates(subset='title',inplace=True)
        library_df.to_hdf(config.library_path+library_basename+".h5",'library')
        generate_zotero_embeddings()

    library_pmids = get_zotero_pmids(library_df)
    email_content = []
    return library_df

def cleaner(text_str):
    "Extract relevant text from DataFrame using a regex"
    # Regex pattern for only alphanumeric, hyphenated text with 3 or more chars
    pattern = re.compile(r'(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b')
    clean = " ".join(pattern.findall(text_str))
    return clean

def text_to_vector(text,nlp):
    doc = nlp(text)
    vec = pd.Series(doc.vector)
    return vec

def process_text(text,nlp):
    t = cleaner(text)
    vec = text_to_vector(text=t,nlp=nlp)
    return vec

def update_embeddings(years=['*'],model="en_core_sci_lg",disabled=['ner', 'tagger', 'parser', 'textcat', "lemmatizer"]):
    # note this takes a long time when doing all years first
    print("Loading model...",model)
    filelists = []

    nlp = spacy.load('en_core_sci_lg')
    
    for y in years:
        filelists.extend(glob.glob(config.data_path+"by_year/papers/%s.parq"%str(y)))
    
    n_process = 28
    batch_size = 2500
    
    for fname in sorted(filelists):
        print("Creating vectors for:",fname)
        year = os.path.basename(fname).split(".")[0]
        paperi = utils.load_year(year)
        print("> Processing # of papers...",paperi.shape[0])
        corpus = paperi['title'] + " " + paperi['abstract']
        #print("> Cleaning...")
        corpus_clean = corpus.swifter.apply(cleaner)
        #print("> Vectorizing...")
        #vecs = corpus_clean.swifter.apply(text_to_vector,nlp=nlp)

        num_papers = corpus_clean.shape[0]
        vecs = np.zeros((num_papers,200))
        count = 0

        disabled=['ner', 'tagger', 'parser', 'textcat', "lemmatizer"]
        for doc in nlp.pipe(list(corpus_clean), n_process=28,disable=disabled, batch_size=batch_size):
            vecs[count,:] = pd.Series(doc.vector)
            count += 1
            if count % 50000 == 0:
                print("Complete: %s | %3.1f | %8i | %8i" %(os.path.basename(fname),100*count/num_papers,count,num_papers))
        
        vecdf = pd.DataFrame(vecs,index=paperi.index)
        print("Saving...")
        utils.save_year_vectors(vecdf,int(year))

def generate_paper_vectors(papers):

    corpus = papers['title'] + " " + papers['abstract']

    corpus_clean = corpus.swifter.apply(cleaner)
    num_papers = corpus_clean.shape[0]

    vecs = np.zeros((num_papers,200))
    count = 0

    disabled=['ner', 'tagger', 'parser', 'textcat', "lemmatizer"]
    for doc in nlp.pipe(list(corpus_clean), n_process=28,disable=disabled, batch_size=batch_size):
        vecs[count,:] = pd.Series(doc.vector)
        count += 1
        if count % 50000 == 0:
            print("Complete: %s | %3.1f | %8i | %8i" %(os.path.basename(fname),100*count/num_papers,count,num_papers))

    return vecs