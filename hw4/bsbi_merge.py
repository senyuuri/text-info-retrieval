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

# using porter stemmer
porter = nltk.PorterStemmer()

postings = {}
doclist = []

fd = open('spimi_dict.txt', 'w')
fp = open('spimi_postings.txt', 'w')
        
start_time = time.time()
# merge document lists
for i in range(1, 19):
    filename = 'tmp/doclist_' + str(i) + '.txt'

    with open(filename, 'r') as fopen:
        # read docID and length
        raw_doclist = fopen.readline().split(';')
        for raw_doc in raw_doclist:
            parts = raw_doc.split(',')
            doclist.append([int(parts[0]), float(parts[1])])

fd.write(';'.join([str(x[0])+','+str(x[1]) for x in doclist]) + '\n')

print('Merge completed in '+str(time.time() - start_time)+' seconds.')

# heap of temporary postings list
h = []

# load postings list in blocks
for i in range(1, 19):
    filename = 'tmp/postings_' + str(i) + '.json'
    print('Loading postings part '+ str(i) +'/18')
    with open(filename, 'r') as fopen:
        lines = fopen.readlines()
        for line in lines:
            parts = line.split(':')
            term = parts[0]
            raw = parts[1].split(';')
            plist = [[int(x.split(',')[0]), int(x.split(',')[1])] for x in raw]
            heapq.heappush(h, (term, plist))

def write_postings(fd, fp, term, sublist):
    sublist.sort(key=itemgetter(0))
    # write postings to file
    w_cursor = fp.tell()
    fd.write(','.join([term, str(len(sublist)),str(w_cursor)]))
    fd.write('\n')
    fp.write(';'.join([str(p[0])+','+str(p[1]) for p in sublist]))
    fp.write('\n')


print('Heap size:' + str(len(h)))
print('Combining postings list...')
prev_term = None
sublist = []

# merge postings
while(len(h) != 0):
    entry = heapq.heappop(h)
    # print('heap pop',entry)
    if(prev_term == None):
        prev_term = entry[0]
        sublist = entry[1]
    elif entry[0] == prev_term:
        for i in entry[1]:
            sublist.append(i)
    else:
        # merge postings and write to file
        write_postings(fd, fp, prev_term, sublist)

        prev_term = entry[0]
        sublist = entry[1]

write_postings(fd, fp, prev_term, sublist)
print('All tasks completed in '+str(time.time() - start_time)+' seconds.')