#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

def punc_normalise(sent):
    """Normalise punctuations"""
    token = token.replace("/",' ')

def parse_query(raw):
    """Use shunting-yard algorithm to convert query into Reverse Polish notation(RPN)"""
    # operator keywords in the order of increasing precedence
    OPWORDS = ['OR','AND','NOT']
    ORDER = OPWORDS + ['('+')']
    # operator stack
    op = []
    # output queue
    output = []
    raw = raw.replace('(',' ( ').replace(')',' ) ').split(' ')
    for r in raw:
        print(r)
        if r=='(':
            op.append(r)
        elif r==')':
            top = op.pop()
            while top != '(':
                output.append(top)
                top = op.pop()
            op.append(top)
        elif r not in OPWORDS:
            output.append(r)
        else:
            if len(op) != 0:
                top = op.pop()
                while top != '(' and len(op) > 0 and OPWORDS.index(top) >= OPWORDS.index(r):
                    output.append(top)
                    top = op.pop()
                op.append(top)
            op.append(r)

    while(len(op) != 0):
        output.append(op.pop())

    return output



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
p = {} 
# using porter stemmer
porter = nltk.PorterStemmer()
# get the list of files inside the input directory
files = glob.glob(input_directory + "*")
fcount = 0
for f in files:
    docID = f.split('/')[-1]
    # TESTING ONLY
    fcount += 1
    if fcount > 100:
        break

    with open(f, 'r') as fopen:
        for sent in nltk.sent_tokenize(fopen.read()):
            tokens = nltk.word_tokenize(sent)
            for t in tokens:
                t = porter.stem(t.lower()).encode("ascii")
                # create a new dictionary entry if t is a new keyword
                if t not in p:
                    p[t] = [docID]
                else:
                    # add docID to posting list if it is not inside
                    if docID not in p[t]:
                        p[t].append(docID) 
    # print(p)

print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")
query = "bill OR Gates AND (vista OR XP) AND NOT mac"
print(parse_query(query))