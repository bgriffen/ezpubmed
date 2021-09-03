
import multiprocessing as mp
from joblib import Parallel, delayed

import pandas as pd
import pylab as plt
import numpy as np
import subprocess as sub
import sys,os,glob
import re

import pubmed_parser
import utils
import ftplib
import utils_nlp
import config
import db
import numpy as np
import time

_start_time = time.time()

def tic():
    global _start_time
    _start_time = time.time()

def tac(method):
    t_sec = time.time() - _start_time
    (t_min, t_sec) = divmod(t_sec,60)
    (t_hour,t_min) = divmod(t_min,60)
    rstr  = '[ TIMER ]: %30s - %2ihour:%2imin:%3.2fsec' % (method,t_hour,t_min,t_sec)
    print(rstr)

class Dataset:
    def __init__(self,work_path,datatype,dbase):

        self.cols = db.fields

        self.dbase = dbase
        self.datatype = datatype
        self.xml_path = work_path + "pubmed_data/%s/xml/"%datatype

        self.dbtracking_path = config.data_path+"updates_so_far_%s.csv" % datatype
        self.pubmed_ftp = r'ftp.ncbi.nlm.nih.gov'
        self.pubmed_ext = "/pubmed/%s/"%datatype
        self.pubmed_directory = r"ftp://ftp.ncbi.nlm.nih.gov"+self.pubmed_ext

        print("Working on:",datatype)
        print("FTP:",self.pubmed_directory)

        self.xml_files = sorted(pubmed_parser.list_xml_path(self.xml_path))
        self.has_internet = utils.has_internet()

        if not os.path.isdir(self.xml_path):
            os.makedirs(self.xml_path)
    
    def get_completed_list(self):
        if os.path.exists(self.dbtracking_path):
            self.xml_done = pd.read_csv(self.dbtracking_path,index_col=0)
        else:
            self.xml_done = pd.DataFrame(columns=['Filename'])

    def update_db(self,current_pmids):
        self.get_completed_list()
        self.xml_files = sorted(pubmed_parser.list_xml_path(self.xml_path))
        self.xml_update = [f for f in self.xml_files if f not in list(self.xml_done['Filename'])]

        if len(self.xml_update) == 0:
            return

        print("Files to be inserted...")
        for f in self.xml_update:
            print(f)

        for xml in self.xml_update:
            print()
            print("Processing...",os.path.basename(xml))
            documents = pubmed_parser.parse_medline_xml(xml,year_info_only=False,reference_list=True)
            df = pd.DataFrame(documents)
            df = utils.prepare_papers(df)
            df = utils.append_dateinfo(df)[self.cols]
            df = utils.fix_dtypes(df)
            df.dropna(subset=['pmid'],inplace=True)
            lpmids = list(df['pmid'])

            # split into papers that are new vs. to-be-updated
            self.update_pmid = intersection(lpmids,current_pmids)
            self.new_pmid = np.setdiff1d(lpmids,current_pmids)
            dfi = df.set_index("pmid")
            self.new_l = dfi.loc[self.new_pmid].reset_index().to_dict('records')
            self.update_l = dfi.loc[self.update_pmid].reset_index().to_dict('records')

            num_papers_update = len(self.update_l)
            num_papers_new = len(self.new_l)
            num_papers = df.shape[0]

            print("> # Papers:",num_papers)

            if num_papers_new != 0:
                n_batch = 5000
                print(">> Inserting %5i (%3.2f) papers into database." % (num_papers_new,num_papers_new*100/num_papers))
                with self.dbase.atomic():
                    for idx in range(0, num_papers_new, n_batch):
                        print("Inserted %5i papers" % (idx+n_batch))
                        db.PaperDB.insert_many(self.new_l[idx:idx+n_batch]).execute()

            if num_papers_update != 0:
                print(">> Updating %5i (%3.2f) papers into database." % (num_papers_update,num_papers_update*100/num_papers))
                updates = []
                for u in self.update_l:
                    e = db.PaperDB(**u)
                    updates.append(e)

                with self.dbase.atomic():
                    db.PaperDB.bulk_update(updates,fields=self.cols, batch_size=1000)

            current_pmids.extend(lpmids)

        print("Saving the completed list...")
        self.dbtracking_df = pd.DataFrame(list(self.xml_done['Filename']) + self.xml_update,columns=['Filename'])
        self.dbtracking_df.to_csv(self.dbtracking_path)
        print("UPDATE COMPLETE!")

    def download_latest(self):
        if self.has_internet:
            self.ftp=ftplib.FTP(self.pubmed_ftp)
            self.ftp.login("","")
            self.ftp.cwd(self.pubmed_ext)
            pubmedfilelist = self.ftp.nlst()
            fdownload = []
            for filei in pubmedfilelist:
                bname = os.path.basename(filei)
                checking = bname.strip(".gz")
                if filei.endswith("xml.gz") and not os.path.exists(self.xml_path+checking) and not os.path.exists(self.xml_path+bname):
                    if ".md5" not in filei:
                        fdownload.append(filei)
            for filename in fdownload:
                cmdin = ["wget","-P",self.xml_path,self.pubmed_directory+filename]
                print(cmdin)
                sub.call(cmdin)
    
        # unzip all recently downloaded files
        for filei in glob.glob(self.xml_path+"*.xml.gz"):
            print("Unzipping",filei)
            sub.call(["gunzip " + filei],shell=True)
        self.xml_files = utils.get_list_of_xml_files(self.xml_path)

class PubMedPandas():
    def __init__(self):

        if ~os.path.exists(config.papers_db):
            self.dbase = db.create_db()
        else:
            self.dbase = db.get_db()

        self.baseline = Dataset(config.data_path,"baseline",self.dbase)
        self.updates = Dataset(config.data_path,"updatefiles",self.dbase)

    def update_db(self):
        tic()
        print("Getting current pmids...")        
        q = db.PaperDB.select(db.PaperDB.pmid) 
        dfq = pd.DataFrame(list(q.dicts()))
        self.current_pmids = []
        if dfq.shape[0] != 0:
            self.current_pmids = list(dfq['pmid'])

        print("Downloading latest data...")
        self.baseline.download_latest()
        self.updates.download_latest()

        print("Updating database...")
        self.baseline.update_db(self.current_pmids)
        self.updates.update_db(self.current_pmids)
        tac("UPDATE COMPLETE")

    def update_embeds(self,years):
        utils_nlp.update_embeddings(years=years)

    def load_year(self,year):
        q = db.PaperDB.select().where(db.PaperDB.pubyear == year) 
        self.papers = pd.DataFrame(list(q.dicts()))

    def load_all(self):
        q = db.PaperDB.select()
        self.papers = pd.DataFrame(list(q.dicts()))
