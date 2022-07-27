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
import multiprocessing as mp
import cProfile

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

# in-memory temporary posting list 
postings = {}
# list of indexed documents and their corresponding 'length' for cosine normalisation
manager = mp.Manager()
doclist = manager.list()

def initpool(a):
    global doclist
    doclist = a

def process_doc(raw_doc):
    # extract zones ('date_posted' is ignored here)
    docID = int(raw_doc[0].replace('"',''))
    title = raw_doc[1]
    content = raw_doc[2]
    court = raw_doc[4].replace('"','').replace('\n', '')

    term_list = []
    termset = []
    # Part 1: tokenizing TITLE
    if '[' in title:
        tokens = nltk.word_tokenize(title.split('[')[0])
        caseid = title.split(']')[1].replace(' ','')
        term_list.append([caseid, docID])
        termset.append(caseid)
    else:
        tokens = nltk.word_tokenize(title)
    for t in tokens:
        t = re.sub(r'\W+', '', t)
        if t != None:
            t = porter.stem(t.lower())
            t = t + '#'
            term_list.append([t, docID])
            termset.append(t)

    # Part 2: tokenizing COURT
    court = court + '&'
    term_list.append([court.lower(), docID])
    termset.append(court.lower())

    # Part 3: tokenizing CONTENT
    for sent in nltk.sent_tokenize(content):
        # remove common punctuations
        tokens = nltk.word_tokenize(sent)
        for t in tokens:
            t = re.sub(r'\W+', '', t)
            if t != '':
                t = porter.stem(t.lower()).replace('.','')
                t = t + '$'
                term_list.append([t, docID])
                termset.append(t)

    termset = set(termset)
    tf_log_sum = 0 
    for t in termset:
        # get term frequency from postings
        # assertion: t in postings 
        # must be true since all terms are added to the postings list in the previous loop
        freq = 0 

        for pair in term_list:
            if pair[0] == t:
                freq += 1

        # bulletproof code. This should never happen!
        if freq == 0:
            raise LookupError("Term '" + t + "'not found in the postings list. Not good:(")
            sys.exit(2)

        # normalise tf and add together
        tf_log_sum += math.pow(1 + math.log(freq, 10), 2)
    
    doclist.append([docID ,round(math.sqrt(tf_log_sum), 2)])

    return term_list


def process_tokens(token_list):
    global postings 

    prev_term = token_list[0][0]
    sub_postings = []
    count = 0
    for entry in token_list:
        count += 1
        if count % 10000 == 0:
            print('Progress: ' + str(count) + '/' + str(len(token_list)) + ', ' + str(count/len(token_list)*100) +'%')

        term = entry[0]
        docID = entry[1]

        if term == prev_term:
            found = False
            for pair in sub_postings:
                if pair[0] == docID:
                    # add term frequencuy
                    pair[1] += 1
                    found = True
                    break
            # add docID to posting list if it is not already inside
            if not found: 
                sub_postings.append([docID, 1])
        else:
            # save the previous term's postings list
            postings[prev_term] = sub_postings
            sub_postings = [[docID, 1]]
            prev_term = term

    postings[prev_term] = sub_postings


if __name__ == '__main__':
    start_time = time.time()
    doc_files = []

    # indexing the input_data file
    print('Reading corpus file into the memory...')
    with open(input_file, encoding='utf-8', mode='r') as fopen:
        line = fopen.readline()

        # indexing each document
        while True:
            fcount += 1
            # terms in each document, for later tf-idf calculation
            termlist = []
            raw = []

            # if fcount == 2000:
            #     break

            line = fopen.readline()
            if line == '':
                break
            while (line[-2:] != '"\n' or line[-3:] == '""\n'):
                raw.append(line)
                line = fopen.readline()
            
            raw += line
            raw_doc = ''.join(raw).split('","')
            doc_files.append(raw_doc)

    print('Completed loading. Start parsing...')
    with mp.Pool(initializer=initpool, initargs=(doclist,)) as pool:
        tokens = pool.map(process_doc, doc_files)
        print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")

    flat_tokens = [item for sublist in tokens for item in sublist]
    print(len(flat_tokens))
    flat_tokens.sort(key=itemgetter(0, 1))
    print("Sorting completed in "+str(time.time() - start_time)+" seconds.")

    # Add token to postings list
    cProfile.run('process_tokens(flat_tokens)')

    # DEBUG
    # for k, v in postings.items():
    #     print(k, v[:10])
    # print(doclist)

    # sort docIDs in posting list
    for key in postings:
        postings[key].sort(key=itemgetter(0))

    # sort docID list
    doclist.sort(key=itemgetter(0))

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
    
    print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")
        