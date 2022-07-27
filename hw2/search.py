#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time
import pdb
import string
from abc import ABCMeta, abstractmethod

# operator keywords in the order of increasing precedence
OPWORDS = ['OR','AND','NOT']

all=string.maketrans('','')
nodigs=all.translate(all, string.digits)

def evaluate_NOT(p):
    """Evaluate NOT operation on a postings list

    Skip pointers are ignored here since NOT needs to iterate through both the postings list and the docID list."""
    if len(p) == 0:
        return doclist
    else:
        result = []
        cursor_p = 0
        cursor_doc = 0
        docid_p = int(str(p[cursor_p]).replace('#',''))

        while cursor_doc < len(doclist) and cursor_p < len(p):
            if doclist[cursor_doc] == docid_p:
                # since we ignores skip pointers in NOT queries,
                # if the current docID has a skip pointer(start with '#'),
                # advance cursor_p by 2 to ignore the skip pointer
                cursor_p += 2 if str(p[cursor_p])[0] == '#' else 1
                # docID list is in-memory so we can simply add 1
                cursor_doc += 1

            elif doclist[cursor_doc] < p[cursor_p]:
                result.append(doclist[cursor_doc])
                cursor_doc += 1

            else:
                result.append(docid_p)
                cursor_p += 2 if p[cursor_p][0] == '#' else 1
            if cursor_doc < len(doclist) and cursor_p < len(p):
                docid_p = int(str(p[cursor_p]).replace('#',''))

        # add remaining items from doclist
        while cursor_doc < len(doclist):
            result.append(doclist[cursor_doc])
            cursor_doc += 1

        return result


def evaluate_AND(p1, p2, fp):
    """Evaluate AND operation on a postings list"""
    #TODO use skip pointer
    if len(p1) == 0 or len(p2) == 0:
        return []
    else:
        result = []
        cursor_p1 = 0
        cursor_p2 = 0
        # remove '#' from a docID
        docid_p1 = int(str(p1[cursor_p1]).replace('#',''))
        docid_p2 = int(str(p2[cursor_p2]).replace('#',''))

        while cursor_p1 < len(p1) and cursor_p2 < len(p2):
            if docid_p1 == docid_p2:
                result.append(docid_p1)
                cursor_p1 += 2 if str(p1[cursor_p1])[0] == '#' else 1
                cursor_p2 += 2 if str(p2[cursor_p2])[0] == "#" else 1

            elif docid_p1 < docid_p2:
                # if the node has a skip pointer
                if str(p1[cursor_p1])[0] == '#':
                    # get skip pointer from the next adjacent node
                    parts = p1[cursor_p1+1].split('!')
                    next_docid = int(parts[1])
                    offset = int(parts[2])
                    if next_docid <= docid_p2:
                        print('SKIP')
                        cursor_p1 += offset+1
                    else:
                        cursor_p1 += 2
                else:
                    cursor_p1 += 1

            else:
                cursor_p2 += 2 if str(p2[cursor_p2])[0] == "#" else 1

            if cursor_p1 < len(p1) and cursor_p2 < len(p2):
                docid_p1 = int(str(p1[cursor_p1]).replace('#',''))
                docid_p2 = int(str(p2[cursor_p2]).replace('#',''))

        return result


def evaluate_OR(p1, p2):
    """Evaluate OR operation on a postings list

    Skip pointers are ignored here since OR needs to iterate through both lists.
    """
    if len(p1) == 0:
        return p2
    elif len(p2) == 0:
        return p1
    else:
        # pdb.set_trace()
        result = []
        cursor_p1 = 0
        cursor_p2 = 0
        
        # remove '#' from a docID
        docid_p1 = int(str(p1[cursor_p1]).replace('#',''))
        docid_p2 = int(str(p2[cursor_p2]).replace('#',''))
        while cursor_p1 < len(p1) and cursor_p2 < len(p2):
            if docid_p1 == docid_p2:
                result.append(docid_p1)
                # ignore skip pointers
                cursor_p1 += 2 if str(p1[cursor_p1])[0] == '#' else 1
                cursor_p2 += 2 if str(p2[cursor_p2])[0] == "#" else 1
            elif docid_p1 < docid_p2:
                result.append(docid_p1)
                cursor_p1 += 2 if str(p1[cursor_p1])[0] == '#' else 1
            else:
                result.append(docid_p2)
                cursor_p2 += 2 if str(p2[cursor_p2])[0] == "#" else 1

            if cursor_p1 < len(p1) and cursor_p2 < len(p2):
                docid_p1 = int(str(p1[cursor_p1]).replace('#',''))
                docid_p2 = int(str(p2[cursor_p2]).replace('#',''))

        # add all remaining docIDs to result
        while cursor_p1 < len(p1):
            result.append(p1[cursor_p1])
            cursor_p1 += 2 if str(p1[cursor_p1])[0] == '#' else 1
        while cursor_p2 < len(p2):
            result.append(p2[cursor_p2])
            cursor_p2 += 2 if str(p2[cursor_p2])[0] == "#" else 1
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
                # case: `NOT` is immediately followed by an operand
                if len(op) != 0 and op[-1] == 'NOT':
                    output.append(op.pop())
            elif r == 'NOT':
                op.append(r)
            else:
                if len(op) != 0:
                    top = op.pop()
                    while top != '(' and len(op) > 0 and OPWORDS.index(top) >= OPWORDS.index(r):
                        output.append(top)
                        top = op.pop()
                    op.append(top)
                op.append(r)
            # print('op:'+str(op))
            # print('output:'+str(output))
            # print('==============')

    while(len(op) != 0):
        output.append(op.pop())

    print('RPN:'+str(output))
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

    with open(postings_file,'r') as fp:
        for q in qlist:
            if q in OPWORDS:
                if q == 'NOT':
                    op1 = stack.pop()
                    result = evaluate_NOT(op1)
                    stack.append(result)
                else:
                    op1 = stack.pop()
                    op2 = stack.pop()
                    if q == 'AND':
                        stack.append(evaluate_AND(op1, op2, fp))
                    elif q == 'OR':
                        stack.append(evaluate_OR(op1, op2))
            else:
                # operator, get postings from disk
                q = porter.stem(q.lower())
                # print(q)
                if q in d:
                    # read postings list from disk
                    # set read cursor as offset from the beginning of the file
                    fp.seek(d[q][1], 0)
                    plist = fp.readline().replace('\n','').split(',')
                    # print(plist)
                else:
                    plist = []
                
                stack.append(plist)

    return stack.pop()



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
