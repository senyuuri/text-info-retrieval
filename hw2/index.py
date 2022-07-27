#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time
import pickle
import math

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
# list of indexed documents 
doclist = []
fcount = 0

for f in files:
    docID = f.split('/')[-1]
    # TESTING ONLY
    fcount += 1
    # if fcount > 1000:
    #     break
    if fcount % 1000 == 0:
        print(str(fcount)+' files processed......')
    #     break
    doclist.append(docID)
    
    # index each file
    with open(f, 'r') as fopen:
        for sent in nltk.sent_tokenize(fopen.read()):
            # remove common punctuations
            sent = sent.replace(',',' ').replace('.',' ').replace('\'',' ')
            tokens = nltk.word_tokenize(sent)
            for t in tokens:
                t = porter.stem(t.lower()).encode("ascii")
                # create a new dictionary entry if t is a new keyword
                if t not in postings:
                    postings[t] = [docID]
                else:
                    # add docID to posting list if it is not inside
                    if docID not in postings[t]:
                        postings[t].append(docID)

# sort docIDs in posting list
for key in postings:
    postings[key] = [int(x) for x in postings[key]]
    postings[key].sort()

# sort docID list
doclist = [int(x) for x in doclist]
doclist.sort()

print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")


# dictionary to be saved 
dictionary = {}

# save postings list to file
with open(output_file_postings, 'w') as fp:
    for key, p_list in postings.items():
        # get initial write cursor position
        w_cursor = fp.tell()
        # add skip pointers
        skip_list = []
        interval = int(math.floor(math.sqrt(len(p_list))))
        for i in range(len(p_list)):
            # this is a node with skip pointer
            if (i % interval == 0) and (i != len(p_list) - 1):

                # add special tag '#' to indicate that the following node is a skip pointer
                skip_list.append('#'+str(p_list[i]))
                # docID in which the skip pointer is pointing to  
                skip_index = (i + interval) if (i + interval < len(p_list)) else (len(p_list) - 1)
                doc_id = p_list[skip_index]
                # offset to the skip destination
                offset = interval
                # skip pointer format: !docID!offset 
                skip_list.append('!'+str(doc_id)+'!'+str(offset))
            else:
                # normal node
                skip_list.append(str(p_list[i]))

        fp.write(','.join(skip_list))
        fp.write('\n')
        dictionary[key] = [len(p_list), w_cursor]

# save dictionary to file
with open(output_file_dictionary, 'w') as fd:
    # write the list of docIDs in the first line
    fd.write(','.join([str(x) for x in doclist]) + '\n')
    for key, value in dictionary.items():
        fd.write(key + ',' + str(value[0]) + ',' + str(value[1]) + '\n')