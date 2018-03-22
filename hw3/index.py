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
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
    
for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"
        
if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

start_time = time.time()
# in-memory temporary posting list
postings = {} 
# using porter stemmer
porter = nltk.PorterStemmer()
# get the list of files inside the input directory
files = glob.glob(input_directory + "*")
# list of indexed documents and their corresponding 'length' for cosine normalisation
doclist = []
fcount = 0

for f in files:
    docID = int(f.split('/')[-1])
    fcount += 1

    if fcount % 1000 == 0:
        print(str(fcount)+' files processed......')
    
    # index each file
    with open(f, 'r') as fopen:
        # terms in each document, for later tf-idf calculation
        termlist = []

        for sent in nltk.sent_tokenize(fopen.read()):
            # remove common punctuations
            sent = re.sub('[^A-Za-z0-9.]+', ' ', sent)
            tokens = nltk.word_tokenize(sent)
            for t in tokens:
                t = porter.stem(t.lower()).encode("ascii").replace('.','')
                termlist.append(t)
                # create a new dictionary entry if t is a new keyword
                if t not in postings:
                    postings[t] = [[docID, 1]]
                else:
                    found = False
                    for plist in postings[t]:
                        if plist[0] == docID:
                            # add term frequencuy
                            plist[1] += 1
                            found = True
                            break
                    # add docID to posting list if it is not already inside
                    if not found: 
                        postings[t].append([docID, 1])

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

# sort docIDs in posting list
for key in postings:
    postings[key].sort(key=itemgetter(0))

# sort docID list
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

# save dictionary to file
with open(output_file_dictionary, 'w') as fd:
    # write document list and their lengths in the first line
    fd.write(';'.join([str(x[0])+','+str(x[1]) for x in doclist]) + '\n')
    for d in dictionary:
        fd.write(','.join([str(x) for x in d]) + '\n')