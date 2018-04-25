#!/usr/bin/python
import re
import nltk
from nltk.corpus import wordnet 
import sys
import glob
import getopt
import time
import pdb
import string
import math
import heapq
from operator import itemgetter

# Optional features
DEBUG = False
QUERY_EXPANSION = True
ZONE_SENSITIVE = True

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

dictionary_file = postings_file = file_of_queries = output_file_of_results = None
    
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
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
dic = {}
# using porter stemmer
porter = nltk.PorterStemmer()

# read dictionary into memory
with open(dictionary_file, 'r') as fd:
    # read docID and length
    raw_doclist = fd.readline().split(';')
    doclist = []
    for raw_doc in raw_doclist:
        parts = raw_doc.split(',')
        doclist.append([int(parts[0]), float(parts[1])])
    # read other dictionary entries
    lines = fd.readlines()
    for line in lines:
        parts = line.split(',')
        dic[parts[0]] = [int(parts[1]), int(parts[2])]
        

# create dict index for doclist
# so that we can quickly get the index of a docID in doclist
dl_idx = {}
for i in range(len(doclist)): 
    docID = doclist[i][0]
    dl_idx[docID] = i


N = len(doclist)
start_time = time.time()
# process query
fp = open(postings_file, 'r')
fq = open(file_of_queries, 'r')
fout = open(file_of_output, 'w')

# cosine socres, order is the same as doclist
score = [0] * N

raw_query = re.sub('[^A-Za-z0-9. ]+', ' ', fq.readline())
# parse boolean query 
queries = [x.strip() for x in raw_query.replace('AND',' ').split(' ')]

# expand query
expanded = []
if QUERY_EXPANSION:
    for query in queries:
        #print('expanding: '+query)
        terms = query.split(' ') 
        for t in terms:
            syn = wordnet.synsets(t)[0]
            lemmas = syn.lemmas()
            for i in range(len(lemmas)):
                if query != lemmas[i].name():
                    #print(query + '->' + lemmas[i].name())
                    expanded.append(lemmas[i].name())
    queries = queries + expanded


for query in queries:
    # print('Original query:' + query)
    # process query term
    tf_raw_query = {}
    q_tokens = nltk.word_tokenize(query)
    for t in q_tokens:
        t = porter.stem(t.lower()).replace('.','')
        tag_list = ['#', '&', '$']
        for tag in tag_list:
            tag_t = t + tag
            if tag_t not in tf_raw_query:
                tf_raw_query[tag_t] = 1
            else:
                tf_raw_query[tag_t] += 1

    if DEBUG:
        print("tf_raw_query", tf_raw_query)

    for term, freq in tf_raw_query.items(): 
        # fetch postings list
        # ignore the term if it is not found in postings
        if term in dic:
            # move cursor in postings list
            fp.seek(dic[term][1], 0)
            # read postings list from disk
            line = ''
            char = fp.read(1)
            while char != '\n' and char != '':
                line += char
                char = fp.read(1)

            plist = []
            plist_raw = line.split(';')
            for p in plist_raw:
                parts = p.split(',')
                plist.append([int(parts[0]), int(parts[1])])

            for pair in plist:
                docID = pair[0]
                docfreq = pair[1]
                # find the docID index in score[]
                idx = dl_idx[docID]
                # calculate normalised tf 
                tf_wt = 1 + math.log(freq, 10)
                # calculate term idf
                idf = math.log(len(doclist) / dic[term][0], 10)
                # calculate term weight 
                w_term = tf_wt * idf
                # calculate document weight, using tf-wt for lnc.ltc
                w_doc = 1 + math.log(docfreq, 10)
                # add to doc score
                # give TITLE and COURT zone more weightage
                if(term[-1] == '#' or term[-1] == '&'):
                    score[idx] += w_term * w_doc * 1.5
                else:
                    score[idx] += w_term * w_doc
                

                if DEBUG:
                    print('docID', docID, 'docfreq', docfreq, 'idx', idx, 'w_doc', w_doc, 'doc_len', doclist[idx][1])
                    print('term', term, 'tf', freq,'tf_wt', tf_wt, 'idf', idf, 'w_term', w_term, 'score+', w_term * w_doc/doclist[idx][1], 'final_score', score[idx]/doclist[idx][1])
                
        else:
            if DEBUG:
                print("ignoring term:", term)


result = []

# normalise scores by dividing document length
for i in range(N):
    if doclist[i][1] != 0:
        score[i] = score[i] / doclist[i][1]
    # only keep relevant documents
    if score[i] > 0:
        result.append([score[i], doclist[i][0]])

# sort by relevance
result.sort(key=itemgetter(0), reverse=True)

#print(raw_query, " ".join([str(x[1]) for x in result]))
fout.write(" ".join([str(x[1]) for x in result]))
fout.write("\n")

fp.close()
fq.close()
fout.close()

print(str(len(result))+" documents found in "+str(time.time() - start_time)+" seconds.")
