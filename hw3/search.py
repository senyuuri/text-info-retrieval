#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time
import pdb
import string

all=string.maketrans('','')
nodigs=all.translate(all, string.digits)



def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

dictionary_file = postings_file = file_of_queries = output_file_of_results = None
    
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

# in-memory dictionary
d = {}
queries = []

# using porter stemmer
porter = nltk.PorterStemmer()

# read dictionary into memory
with open(dictionary_file, 'r') as fd:
    # read docID list
    doclist = [int(x) for x in fd.readline().split(',')]
    lines = fd.readlines()
    for line in lines:
        parts = line.split(',')
        d[parts[0]] = (int(parts[1]), int(parts[2]))


start_time = time.time()
# process query
with open(file_of_queries, 'r') as fq:
    with open(file_of_output, 'w') as fout:
        lines = fq.readlines()
        for line in lines:
            print('==============================================')
            query = line.replace('\n', ' ').replace('\r', '')
            print("querying: "+ query)
            raw = parse_query(query)
            result = []
            for x in raw:
                if str(x)[0] != '!':
                    result.append(int(str(x).replace('#', '')))
            result.sort()
            fout.write(" ".join([str(x) for x in result]))
            fout.write("\n")

        print(str(len(lines))+" queries processed in "+str(time.time() - start_time)+" seconds.")
