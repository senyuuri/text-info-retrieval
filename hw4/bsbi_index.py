#!/usr/bin/python
import re
import os
import nltk
import sys
import glob
import getopt
import time
import pickle
import math
import heapq
from operator import itemgetter
import multiprocessing as mp
import cProfile
from collections import Counter

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

# using porter stemmer
porter = nltk.PorterStemmer()

# document count
fcount = 0

def process_doc(raw_doc):
    # extract zones ('date_posted' is ignored here)
    docID = int(raw_doc[0].replace('"',''))
    title = raw_doc[1]
    content = raw_doc[2]
    court = raw_doc[4].replace('"','').replace('\n', '')

    term_list = []
    # Part 1: tokenizing TITLE
    tokens = nltk.word_tokenize(title)
    for t in tokens:
        t = re.sub(r'\W+', '', t)
        if t != None:
            t = porter.stem(t.lower())
            t = t + '#'
            term_list.append(t)

    # Part 2: tokenizing COURT
    court = court + '&'
    term_list.append(court.lower())

    # Part 3: tokenizing CONTENT
    for sent in nltk.sent_tokenize(content):
        # remove common punctuations
        tokens = nltk.word_tokenize(sent)
        for t in tokens:
            t = re.sub(r'\W+', '', t)
            if t != '':
                t = porter.stem(t.lower()).replace('.','')
                t = t + '$'
                term_list.append(t)

    counter = Counter(term_list)
    tf_log_sum = 0 
    for term, freq in counter.items():
        # normalise tf and add together
        tf_log_sum += math.pow(1 + math.log(freq, 10), 2)

    return (docID, round(math.sqrt(tf_log_sum), 2), term_list)


if __name__ == '__main__':
    start_time = time.time()
    doc_files = []
    sub_block = []
    # indexing the input_data file
    print('Reading corpus file into the memory...')
    with open(input_file, encoding='utf-8', mode='r') as fopen:
        line = fopen.readline()

        # indexing each document
        while True:
            # terms in each document, for later tf-idf calculation
            termlist = []
            raw = []

            # DEBUG
            # if(fcount == 200):
                # break

            line = fopen.readline()
            if line == '':
                break
            while (line[-2:] != '"\n' or line[-3:] == '""\n'):
                raw.append(line)
                line = fopen.readline()
            
            raw += line
            raw_doc = ''.join(raw).split('","')
            sub_block.append(raw_doc)
            fcount += 1

            # create a new block
            if fcount % 1000 == 0:
                doc_files.append(sub_block)
                sub_block = []
    
    # attach the last block
    doc_files.append(sub_block)

    print('Completed loading. Start parsing...')
    print('Total number of blocks:' + str(len(doc_files)))
    print('Total number of documents:' +str(fcount))

    block_count = 0
    for block in doc_files:
        block_count += 1
        print('Processing block ' + str(block_count) + '/' + str(len(doc_files)) + ', size ' + str(len(block)) + '...')
        with mp.Pool() as pool:
            # in-memory temporary posting list 
            postings = {}
            # list of indexed documents and their corresponding 'length' for cosine normalisation
            doclist = []

            results = pool.map(process_doc, block)
            term_count = 0
            for r in results:
                term_count += len(r[2])
            print('Number of terms:' + str(term_count))
            print('block ' + str(block_count) +':' +str(len(results))+' records processed in '+str(time.time() - start_time)+' seconds.')

        r_count = 0
        for r in results:
            doclist.append([r[0], r[1]])
            docID = r[0]
            for term in r[2]:
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
            r_count += 1
            print('Progress: block ' + str(block_count) + ',' + str(r_count) +'/1000')


        print( 'completed. Number of tokens:'+str(len(postings)))
        print("Tokenisation completed in "+str(time.time() - start_time)+" seconds.")

        # sort docIDs in posting list
        for key in postings:
            postings[key].sort(key=itemgetter(0))

        # # sort docID list
        doclist.sort(key=itemgetter(0))

        # dictionary to be saved 
        dictionary = []

        if not os.path.exists('tmp'):
            os.makedirs('tmp')

        # save postings list to temporary file
        postings_filename = 'tmp/postings_' + str(block_count) + '.json'
        doclist_filename = 'tmp/doclist_' + str(block_count) + '.txt'

        with open(doclist_filename, 'w') as fout:
            fout.write(';'.join([str(x[0])+','+str(x[1]) for x in doclist]) + '\n')
        
        with open(postings_filename, 'w') as fout:
            for term, plist in postings.items():
                raw = [str(p[0])+','+str(p[1]) for p in plist]
                line = term + ':' + ';'.join(raw) + '\n'
                fout.write(line)