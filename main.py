import fitz
import numpy as np
import os
import pandas as pd
import re
import sys
import uuid



dirc = '/pdf/files/directoy/as/input'                               # Input directory of pdf files. subfolders are allowed. 
                                                                    # It is better to run the code on classified docs.
    
collection1 = []                                                    # Collecting all the pdf files addresses.
for root, sub, files in os.walk(dirc):
    for file in files:
        if file[-3:].lower() == 'pdf':
            collection1.append([os.path.join(root, file), file])
        if file[-3:] != 'pdf':
            print(file)


docdata = []
K = collection1
fileno = 0

for W in K[:20]:                                                    # A portion of files can be selected.
    if W[1][-3:] == 'pdf':
        try:
            doc = fitz.open(f'{W[0]}')
        except:
            print(W[1][:-4])

    tpth = f'./PDF/{fileno}-{W[1][:-4]}/'                           # Everything will be saved in the PDF folder in the current directory.

    if not os.path.exists(tpth):
        os.makedirs(tpth)
        doc.save(tpth + W[1])                                       # A copy of the pdf file is stored in the file. it can be commented out if not needed.
        # print(pdfid, W[1][:-4])

    pdfid = uuid.uuid5(uuid.NAMESPACE_DNS, W[1][:-4])               # Generates a uniqe id for each file. it can be used in future.
    doi = []
    for p in range(2):
        pg = doc[p].get_text()
        doitmp = re.findall("10\.[\S]+[\d\w]", pg)                  # Looking for DOI pattern.
        if doitmp:
            doi.append(doitmp[0])
    if not doi:
        doi = ["NO DOI"]

    tm = []                                                         # Finding the references list page (refpage).
    for i in range(doc.pageCount):
        for j in ['references', 'acknowledgments', 'declaration']:
            if j in doc[i].get_text().lower():
                tm.append(i)

    refpage = 0
    try:
        refpage = np.max(tm)
    except:
        pass
    

    reflist = []                                                    # Finding different styles of references. Only first 40 characters. It can be changed in specific cases.
    for i in range(refpage, doc.pageCount):
        tx1 = re.findall(r'\n\[*\(*\d{1,3}\]*\)*\.*\s*[A-Z][\s\S]{40}', doc[i].get_text())
        for j in tx1:
            reflist.append(j)
            
            
                                                                    # Storing file no., pdf id, file name, pdf format, DOI, and reference lists.
    
    docdata.append([fileno, pdfid, W[1], doc.metadata['format'], doi[0], [reflist]])
    fileno += 1
    sys.stdout.write(f"Processed PDFs: {fileno}/{len(K)-1} \r")
    sys.stdout.flush()


np.save('./PDF/DOCDATA', docdata, allow_pickle=True)
print("Documents data saved as DOCDATA.npy")

doilist = []                                                        # Collecting DOI list in one place.            
for i in docdata:   
    doilist.append(i[4])
    
np.save('./PDF/DOILIST', doilist, allow_pickle=True)    

totreflist = []                                                     # Collecting the entire reference list of all documents in one place. 
for i in docdata:
    # tm=[]
    for j in i[5][0]:
        # tm.append(j)
        totreflist.append(j)

authors1 = []                                                       # Finding author name pattern along with the raw reference entry to check.
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

        
authorslist = []                                                    # Separating the author names alone.
for i in authors1:
    tm = ', '.join(i[0])
    authorslist.append(tm)

authnames = []                                                      # Cleaning up, picking only authors' surname.
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

        
        
print("Generating authors namelist...")                             # Sorting the author names
authnamesCOPY=authnames.copy()
authnames_count = pd.Series(authnames).value_counts().reset_index()
authnamesTOP500 = authnames_count.loc[:500]['index'].to_list()      # Selecting the top 500 names, including wrong entires.



u = 0                                                               # Cleaning up the most repeated mismatches within the top 500 entries.
index1 = []                                                         # Divided into 20 selections, enter the indices of the mismatches.
blk = []                                                            # The clean up process removes the mistmatches from the final clean version 
for i in range(len(authnamesTOP500) // 20):                         # and re-evaluates the author list.
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
blacklist = []                                                      # The mismatches are stored in blacklist and a new clean list is formed.
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


print(f"""Finished processing {fileno} PDFs, saving DOCDATA, doilist creating top100 author-list, as \
DOCDATA.npy, DOILIST.npy, authnames_CLEANTOP100_LIST.npy and authnames_CLEANTOP100.csv in the ./PDF folder.""")



