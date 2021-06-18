import fitz
import numpy as np
import os
import pandas as pd
import re
import sys
import uuid

"""""""""
import spacy
#nlp=spacy.load('en_core_web_lg')
import cv2
import pytesseract
from pytesseract import Output
"""""""""

dirc = '/Users/mo/Documents/articles'

collection1 = []
for root, sub, files in os.walk(dirc):
    for file in files:
        if file[-3:].lower() == 'pdf':
            collection1.append([os.path.join(root, file), file])
        if file[-3:] != 'pdf':
            print(file)


docdata = []
K = collection1
fileno = 0


for W in K[:20]:
    if W[1][-3:] == 'pdf':
        try:
            doc = fitz.open(f'{W[0]}')
        except:
            print(W[1][:-4])

    tpth = f'./PDF/{fileno}-{W[1][:-4]}/'

    if not os.path.exists(tpth):
        os.makedirs(tpth)
        doc.save(tpth + W[1])
        # print(pdfid, W[1][:-4])

    pdfid = uuid.uuid5(uuid.NAMESPACE_DNS, W[1][:-4])
    doi = []
    for p in range(2):
        pg = doc[p].get_text()
        doitmp = re.findall("10\.[\S]+[\d\w]", pg)
        if doitmp:
            doi.append(doitmp[0])
    if not doi:
        doi = ["NO DOI"]

    tm = []
    for i in range(doc.pageCount):
        for j in ['references', 'acknowledgments', 'declaration']:
            if j in doc[i].get_text().lower():
                tm.append(i)

    refpage = 0
    try:
        refpage = np.max(tm)
    except:
        pass

    reflist = []
    for i in range(refpage, doc.pageCount):
        tx1 = re.findall(r'\n\[*\(*\d{1,3}\]*\)*\.*\s*[A-Z][\s\S]{40}', doc[i].get_text())
        for j in tx1:
            reflist.append(j)

    docdata.append([fileno, pdfid, W[1], doc.metadata['format'], doi[0], [reflist]])
    fileno += 1
    sys.stdout.write(f"Processed PDFs: {fileno}/{len(K)-1} \r")
    sys.stdout.flush()


np.save('./PDF/DOCDATA', docdata, allow_pickle=True)
print("Documents data saved as DOCDATA.npy")

doilist = []
for i in docdata:
    doilist.append(i[4])

totreflist = []
for i in docdata:
    # tm=[]
    for j in i[5][0]:
        # tm.append(j)
        totreflist.append(j)

authors1 = []
for rf in totreflist:
    nm = []
    reg = [r"[A-Z][\S]+\,\s*[A-Z]\.",
           r"[A-Z]\.\s[A-Z][\S]+\,*",
           r"[A-Z][\S]+\,*\s*[A-Z]+\.*",
           ]
    i = 0
    while nm == [] and i < 3:
        nm = re.findall(reg[i], rf)
        i += 1

    tm = []
    for j in nm:
        tm.append(j)

    if tm.__len__() > 0:
        authors1.append([tm, rf])

authorslist = []
for i in authors1:
    tm = ', '.join(i[0])
    authorslist.append(tm)

authnames = []
for i in authorslist:
    tm = []
    for j in i.split(" "):
        if "." in j or len(j) == 1:
            continue
        j = j.strip()
        j = j.replace("\n", "")
        j = j.replace(",", "")
        j = j.replace("  ", " ")
        if j.__len__() > 1:
            tm.append(j)
    if len(tm) > 0:
        authnames.append(tm)

print("Authors namelist generated.")
authnamesCOPY=authnames.copy()
authnames_count = pd.Series(authnames).value_counts().reset_index()
authnamesTOP500 = authnames_count.loc[:500]['index'].to_list()

u = 0
index1 = []
blk = []
for i in range(len(authnamesTOP500) // 20):
    for k in range(0, 20):
        print(u + k, authnamesTOP500[u + k])
    print("\tEnter comma-separated indices of the mismatch entries (eg. 1,5,11 'press return'): ")
    c = input()
    if not c:
        u += 20
        continue
    else:
        if c[-1] == ",":
            c = c[:-1]

        ctmp = c.split(",")
        ctmp = [int(e) for e in ctmp]
        index1.append(ctmp)
        blk.append(np.array(authnamesTOP500)[ctmp])
        u += 20
        continue


print("Generating the mismatch blacklist...")
blacklist = []
for i in blk:
    for j in i:
        for k in j:
            if k not in blacklist:
                blacklist.append(k)

authnamesCLEAN = []
for i in authnamesCOPY:
    for j in i:
        if j not in blacklist:
            authnamesCLEAN.append(i)


print("Generating top100 author-list...")
authnamesCLEAN_count = pd.Series(authnamesCLEAN).value_counts().reset_index()
authnames_CLEANTOP100 = authnamesCLEAN_count.loc[:100]['index']
authnames_CLEANTOP100.to_csv('authnames_CLEANTOP100.csv', index=False)

authnames_CLEANTOP100_LIST = authnamesCLEAN_count.loc[:100]['index'].to_list()
np.save('./PDF/authnames_CLEANTOP100', authnames_CLEANTOP100_LIST, allow_pickle=True)


print(f"""Finished processing {fileno} PDFs, saving DOCDATA, creating top100 author-list, as \
DOCDATA.npy, authnames_CLEANTOP100_LIST.npy and authnames_CLEANTOP100.csv in ./PDF folder.""")
