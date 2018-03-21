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

DEBUG = True

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
    # TESTING ONLY
    fcount += 1
    # if DEBUG:
    #     if fcount > 20:
    #         break

    if fcount % 1000 == 0:
        print(str(fcount)+' files processed......')
    
    # index each file
    with open(f, 'r') as fopen:
        # terms in each document, for later tf-idf calculation
        termlist = []

        for sent in nltk.sent_tokenize(fopen.read()):
            # remove common punctuations
            sent = sent.replace(',',' ').replace('\'',' ')
            tokens = nltk.word_tokenize(sent)
            for t in tokens:
                t = porter.stem(t.lower()).encode("ascii")
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
            tf_log_sum += (1 + math.log(freq, 10))

        doclist.append([docID ,round(math.sqrt(tf_log_sum), 2)])

# if DEBUG:
#     print("In-memory postings list:")
#     print("=================================================")
#     for term, plist in postings.items():
#         print(term, len(plist) ,plist) 

#     print("doclist:", doclist[:10])

# sort docIDs in posting list
for key in postings:
    postings[key].sort(key=itemgetter(0))

# sort docID list
doclist.sort(key=itemgetter(0))
print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")

# create dict index for doclist
# so that we can quickly get the index of a docID in doclist
dl_idx = {}
for i in range(len(doclist)): 
    docID = doclist[i][0]
    dl_idx[docID] = i

#TEST in-memory search using VSM
queries = ["marketing analyst", "profit loss statement", "suffer loss"]

for query in queries:
    N = len(doclist)
    # cosine socres, order is the same as doclist
    score = [0] * N
    # process query term
    tf_raw_query = {}
    q_tokens = nltk.word_tokenize(query)
    for t in q_tokens:
        t = porter.stem(t.lower()).encode("ascii")
        if t not in tf_raw_query:
            tf_raw_query[t] = 1
        else:
            tf_raw_query[t] += 1

    if DEBUG:
        print("tf_raw_query", tf_raw_query)

    for term, freq in tf_raw_query.items(): 
        # fetch postings list
        # TODO: fetch from disk
        # ignore the term if it is not found in postings
        if term in postings:
            print("----------------processing query:", term,"-------------------------")
            plist = postings[term]
            for pair in plist: 
                docID = pair[0]
                docfreq = len(plist)
                # find the docID index in score[]
                idx = dl_idx[docID]
                # calculate normalised tf 
                tf_wt = 1 + math.log(freq, 10)
                # calculate term idf
                idf = math.log(len(doclist) / docfreq, 10)
                # calculate term weight 
                w_term = tf_wt * idf
                # calculate document weight, using tf-wt for lnc.ltc
                w_doc = 1 + math.log(docfreq, 10)
                # add to doc score
                score[idx] += w_term * w_doc

                # if DEBUG:
                #     print('docID', docID, 'docfreq', docfreq, 'idx', idx, 'w_doc', w_doc)
                #     print('term', term, 'tf', freq,'tf_wt', tf_wt, 'idf', idf, 'w_term', w_term, 'score+', w_term * w_doc, 'final_score', score[idx])
                
        else:
            if DEBUG:
                print("ignoring term:", term)

    # heap for generating top 10 scores 
    h = []

    # normalise scores by dividing document length
    for i in range(N):
        score[i] = score[i] / doclist[i][1]
        # push (score, docID) tuple into heap
        heapq.heappush(h, (score[i], doclist[i][0]))

    # return top 10 components of scores
    print(heapq.nlargest(10, h))


# dictionary to be saved 
# dictionary = {}

# save postings list to file
# with open(output_file_postings, 'w') as fp:
#     for key, p_list in postings.items():
#         # get initial write cursor position
#         w_cursor = fp.tell()
#         # add skip pointers
#         skip_list = []
#         interval = int(math.floor(math.sqrt(len(p_list))))
#         for i in range(len(p_list)):
#             # this is a node with skip pointer
#             if (i % interval == 0) and (i != len(p_list) - 1):

#                 # add special tag '#' to indicate that the following node is a skip pointer
#                 skip_list.append('#'+str(p_list[i]))
#                 # docID in which the skip pointer is pointing to  
#                 skip_index = (i + interval) if (i + interval < len(p_list)) else (len(p_list) - 1)
#                 doc_id = p_list[skip_index]
#                 # offset to the skip destination
#                 offset = interval
#                 # skip pointer format: !docID!offset 
#                 skip_list.append('!'+str(doc_id)+'!'+str(offset))
#             else:
#                 # normal node
#                 skip_list.append(str(p_list[i]))

#         fp.write(','.join(skip_list))
#         fp.write('\n')
#         dictionary[key] = [len(p_list), w_cursor]

# # save dictionary to file
# with open(output_file_dictionary, 'w') as fd:
#     # write the list of docIDs in the first line
#     fd.write(','.join([str(x) for x in doclist]) + '\n')
#     for key, value in dictionary.items():
#         fd.write(key + ',' + str(value[0]) + ',' + str(value[1]) + '\n')