#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time

# operator keywords in the order of increasing precedence
OPWORDS = ['OR','AND','NOT']

# TODO metadata to be read from the 1st line of dictionary.txt
# range of docIDs used for indexing
DOCID_MIN = 1
DOCID_MAX = 10158


def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"


def punc_normalise(sent):
    """Normalise punctuations"""
    token = token.replace("/",' ')


def get_posting(keyword):
    """Get the posting list by keyword"""
    # TODO implement disk-based postings indexing
    if keyword in p:
        return p[keyword]
    else:
        return []


def evaluate_NOT(p):
    """Evaluate NOT operation on a postings list"""
    result = []
    for i in range(DOCID_MIN, DOCID_MAX+1):
        if str(i) not in p:
            result.append(str(i))
    print('evaluated NOT: ' + str(len(result)) + ' results')
    return result

def evaluate_AND(p1, p2):
    """Evaluate AND operation on a postings list"""
    #TODO use skip pointer
    if len(p1) == 0 or len(p2) == 0:
        return []
    else:
        result = []
        while len(p1) != 0 and len(p2) != 0:
            if p1[0] == p2[0]:
                result.append(p1[0])
                p1.pop(0)
                p2.pop(0)
            elif p1[0] < p2[0]:
                p1.pop(0)
            else:
                p2.pop(0)
        print('evaluated AND: ' + str(len(result)) + ' results')
        print(result)
        print('===================')
        return result

def evaluate_OR(p1, p2):
    """Evaluate OR operation on a postings list"""
    # TODO use skip pointer
    if len(p1) == 0:
        return p2
    elif len(p2) == 0:
        return p1
    else:
        result = []
        while len(p1) != 0 and len(p2) != 0:
            if p1[0] == p2[0]:
                p1.pop(0)
                p2.pop(0)
            elif p1[0] < p2[0]:
                result.append(p1.pop(0))
            else:
                result.append(p2.pop(0))
        print('evaluated OR: ' + str(len(result)) + ' results')
        print(result)
        print('===================')
        return result

def parse_query(raw):
    """Use shunting-yard algorithm to convert query into Reverse Polish notation(RPN)
    
    Args:
        raw: the query string

    Returns:
        output: a list of operators and operands in RPN order
    """

    # operator stack
    op = []
    # output queue
    output = []
    raw = raw.replace('(',' ( ').replace(')',' ) ').split(' ')
    for r in raw:
        print(r)
        if r!='':
            if r=='(':
                op.append(r)
            elif r==')':
                top = op.pop()
                while top != '(':
                    output.append(top)
                    top = op.pop()
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
            print('op:'+str(op))
            print('output:'+str(output))
            print('==============')

    while(len(op) != 0):
        output.append(op.pop())

    return evaluate_query(output)


def evaluate_query(qlist):
    """Evaluate a boolean query in the form of Reverse Polish notation

    Query is evaluated from left to right.

    Input:
        qlist: a list of operators and operands in RPN order

    Output:
        result: a string of docIDs, separated by space
    """
    stack = []
    result = []

    for q in qlist:
        if q in OPWORDS:
            if q == 'NOT':
                op1 = stack.pop()
                # if op1 is a list: it is an intermediate result from previosu steps
                # else: op1 is a keyword, retrieve corresponding postings list
                print('plist:'+str(plist))
                plist = op1 if type(op1)==list else get_posting(op1)
                stack.append(evaluate_NOT(plist))
            else:
                op1 = stack.pop()
                op2 = stack.pop()
                plist1 = op1 if type(op1)==list else get_posting(op1)
                plist2 = op2 if type(op2)==list else get_posting(op2)
                print('plist1:'+str(plist1))
                print('plist2:'+str(plist2))
                if q == 'AND':
                    stack.append(evaluate_AND(plist1, plist2))
                elif q == 'OR':
                    stack.append(evaluate_OR(plist1, plist2))
        else:
            stack.append(q)
    return stack.pop()



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

print(str(fcount)+" records processed in "+str(time.time() - start_time)+" seconds.")
#query = "bill OR Gates AND (vista OR XP) AND NOT mac"
query = "bill AND Gates"
print(parse_query(query))