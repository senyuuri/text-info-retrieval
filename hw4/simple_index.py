#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time
import pickle
import math
import heapq
from operator import itemgetter

DEBUG = False

def usage():
    print("usage: " + sys.argv[0] + " -i dataset-file -d dictionary-file -p postings-file")


input_file = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)
    
for o, a in opts:
    if o == '-i': # input directory
        input_file = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"
        
if input_file == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

start_time = time.time()
# in-memory temporary posting list 
postings = {} 

# using porter stemmer
porter = nltk.PorterStemmer()
# list of indexed documents and their corresponding 'length' for cosine normalisation
doclist = []

# document count
fcount = 0

# add term to postings list
def addToPostings(docID, term):
    if term not in postings:
        # create a new dictionary entry if t is a new keyword
        postings[term] = [[docID, 1]]
    else:
        found = False
        for plist in postings[term]:
            if plist[0] == docID:
                # add term frequencuy
                plist[1] += 1
                found = True
                break
        # add docID to posting list if it is not already inside
        if not found: 
            postings[term].append([docID, 1])

# main
# indexing the input_data file
with open(input_file, encoding='utf-8', mode='r') as fopen:
    line = fopen.readline()

    # indexing each document
    while True:
        fcount += 1
        # terms in each document, for later tf-idf calculation
        termlist = []
        raw = []

        # DEBUG
        # if fcount == 200:
        #     break

        line = fopen.readline()
        if line == '':
            break
        while (line[-2:] != '"\n' or line[-3:] == '""\n'):
            raw.append(line)
            line = fopen.readline()
        
        raw += line
        raw_doc = ''.join(raw).split('","')
        
        # extract zones ('date_posted' is ignored here)
        docID = int(raw_doc[0].replace('"',''))
        title = raw_doc[1]
        content = raw_doc[2]
        court = raw_doc[4].replace('"','').replace('\n', '')
        
        # DEBUG 
        print('======================================')
        print('fcount: ' + str(fcount))
        print('docID: ' + str(docID))
        print('title: ' + title)
        print('abstract:' + content[:50])
        print('court:' + court)
        time.sleep(0.1)

        # Part 1: tokenizing TITLE
        if '[' in title:
            tokens = nltk.word_tokenize(title.split('[')[0])
            caseid = title.split(']')[1].replace(' ','')
            addToPostings(docID, caseid)
        else:
            tokens = nltk.word_tokenize(title)
        for t in tokens:
            t = re.sub(r'\W+', '', t)
            if t != None:
                t = porter.stem(t.lower())
                t = t + '#'
                termlist.append(t)
                addToPostings(docID, t)

        # Part 2: tokenizing COURT
        court = court + '&'
        termlist.append(court.lower())
        addToPostings(docID, court.lower())

        # Part 3: tokenizing CONTENT
        for sent in nltk.sent_tokenize(content):
            # remove common punctuations
            tokens = nltk.word_tokenize(sent)
            for t in tokens:
                t = re.sub(r'\W+', '', t)
                if t != '':
                    t = porter.stem(t.lower()).replace('.','')
                    t = t + '$'
                    termlist.append(t)
                    addToPostings(docID, t)

        # calculate document length
        # remove duplicate terms
        termset = set(termlist)
        tf_log_sum = 0 
        for t in termset:
            # get term frequency from postings
            # assertion: t in postings 
            # must be true since all terms are added to the postings list in the previous loop
            for plist in postings[t]:
                if plist[0] == docID:
                    freq = plist[1]

            # bulletproof code. This should never happen!
            if freq == None:
                raise LookupError("Term '" + t + "'not found in the postings list. Not good:(")
                sys.exit(2)

            # normalise tf and add together
            tf_log_sum += math.pow(1 + math.log(freq, 10), 2)

        doclist.append([docID ,round(math.sqrt(tf_log_sum), 2)])

# for p in postings:
#     print(p)
# print(doclist)

# # sort docIDs in posting list
for key in postings:
    postings[key].sort(key=itemgetter(0))

# # sort docID list
doclist.sort(key=itemgetter(0))
print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")

# dictionary to be saved 
dictionary = []

# save postings list to file
with open(output_file_postings, 'w') as fp:
    for term, plist in postings.items():
        # get write cursor position
        w_cursor = fp.tell()
        # each dictionary entry contains: term, df, pointer to postings file
        dictionary.append([term, len(plist), w_cursor])
        # write postings list to file
        raw = [str(p[0])+','+str(p[1]) for p in plist]
        line = ';'.join(raw)
        fp.write(line)
        fp.write('\n')

# # save dictionary to file
with open(output_file_dictionary, 'w') as fd:
    # write document list and their lengths in the first line
    fd.write(';'.join([str(x[0])+','+str(x[1]) for x in doclist]) + '\n')
    for d in dictionary:
        fd.write(','.join([str(x) for x in d]) + '\n')