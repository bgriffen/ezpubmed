import socket
import smtplib
import dateparser
import config
import os,sys
import pubmed_parser
import pandas as pd
import spacy
import glob
import numpy as np
import datetime
import json

today = datetime.date.today()


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))

def difference(li1, li2):
    return list(set(li1) - set(li2)) + list(set(li2) - set(li1))

def nonoverlap(a,b):
    return list(set(a) ^ set(b))

def get_list_of_xml_files(xml_path):
    return sorted(pubmed_parser.list_xml_path(xml_path))

def has_internet(website="www.gmail.com"):

    try:
      # see if we can resolve the host name -- tells us if there is
      # a DNS listening
      host = socket.gethostbyname(website)
      # connect to the host -- tells us if the host is actually
      # reachable
      s = socket.create_connection((host, 80), 2)
      return True
    except:
       pass
    return False

def send_email(to_address,to_subject,to_content):
    
    if has_internet(website="www.gmail.com"):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(config.from_address, config.from_password)
        
        BODY = '\r\n'.join(['To: %s' % to_address,
                            'From: Scaled Pump #1 <%s>' % from_address,
                            'Subject: %s' % to_subject,
                            '', to_content])
        fmt = 'From: {}\r\nTo: {}\r\nSubject: {}\r\n{}'
        server.sendmail(from_address,to_address, fmt.format(config.to_address, 
                                                            config.from_address, 
                                                            to_subject, 
                                                            BODY).encode('utf-8'))

        server.quit()

def parse_dates(datei):
    return dateparser.parse(datei,date_formats=['%Y-%m-%d','%Y-%m','%Y'])

def prepare_papers(papers):
    print('  > Preparing papers...')
    papers['pmid'] = papers['pmid'].astype("int32")
    papers.drop_duplicates(subset='pmid',inplace=True)
    papers['abstract'].replace('', np.nan, inplace=True)
    papers.dropna(subset=['pmid','abstract','pubdate'], inplace=True)
    #papers.papers['title'].str.contains("Errata")
    return papers

def append_dateinfo(papers):
    print('  > Parsing dates...')
    papers['pubdate'] = papers['pubdate'].apply(parse_dates)
    papers = papers.sort_values('pubdate')
    print("  > Creating year-month-day entries...")
    papers['pubyear'] = papers['pubdate'].apply(lambda x: x.year)
    papers['pubmonth'] = papers['pubdate'].apply(lambda x: x.month)
    papers['pubday'] = papers['pubdate'].apply(lambda x: x.day)
    return papers

def fix_dtypes(df):
    str_cols = ['title','abstract','journal','authors','doi']
    int_cols = ['pubyear','pubmonth','pubday']
    df[str_cols] = df[str_cols].astype("str")
    df[int_cols] = df[int_cols].fillna(0)
    df[int_cols] = df[int_cols].astype("int32")
    return df
