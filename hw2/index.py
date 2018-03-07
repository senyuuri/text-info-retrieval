#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time
import copy

# operator keywords in the order of increasing precedence
OPWORDS = ['OR','AND','NOT']

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"


def punc_normalise(sent):
    """Normalise punctuations"""
    token = token.replace("/",' ')


def get_posting(keyword):
    """Get the posting list by keyword"""
    # TODO implement disk-based postings indexing
    if keyword in postings:
        return postings[keyword]
    else:
        return []


def evaluate_NOT(p):
    """Evaluate NOT operation on a postings list"""
    if len(p) == 0:
        return doclist
    else:
        result = []
        cursor_p = 0
        cursor_doc = 0
        while cursor_doc < len(doclist) and cursor_p < len(p):
            #print("c_doc:"+str(cursor_doc)+" c_p:"+str(cursor_p)+" docid:"+str(doclist[cursor_doc])+" pid:"+str(p[cursor_p]))
            if doclist[cursor_doc] == p[cursor_p]:
                cursor_p += 1
                cursor_doc += 1
            elif doclist[cursor_doc] < p[cursor_p]:
                result.append(doclist[cursor_doc])
                cursor_doc += 1
            else:
                result.append(p[cursor_p])
                cursor_p += 1

        # add remaining items from doclist
        while cursor_doc < len(doclist):
            result.append(doclist[cursor_doc])
            cursor_doc += 1

        # print('evaluated NOT: ' + str(len(result)) + ' results')
        # print('===================')
        return result


def evaluate_AND(p1, p2):
    """Evaluate AND operation on a postings list"""
    #TODO use skip pointer
    if len(p1) == 0 or len(p2) == 0:
        return []
    else:
        result = []
        cursor_p1 = 0
        cursor_p2 = 0
        while cursor_p1 < len(p1) and cursor_p2 < len(p2):
            if p1[cursor_p1] == p2[cursor_p2]:
                result.append(p1[cursor_p1])
                cursor_p1 += 1
                cursor_p2 += 1
            elif p1[cursor_p1] < p2[cursor_p2]:
                cursor_p1 += 1
            else:
                cursor_p2 += 1
        # print('evaluated AND: ' + str(len(result)) + ' results')
        # print(result)
        # print('===================')
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
        cursor_p1 = 0
        cursor_p2 = 0
        while cursor_p1 < len(p1) and cursor_p2 < len(p2):
            if p1[cursor_p1] == p2[cursor_p2]:
                result.append(p1[cursor_p1])
                cursor_p1 += 1
                cursor_p2 += 1
            elif p1[cursor_p1] < p2[cursor_p2]:
                result.append(p1[cursor_p1])
                cursor_p1 += 1
            else:
                result.append(p2[cursor_p2])
                cursor_p2 += 1

        # add all remaining docIDs to result
        while cursor_p1 < len(p1):
            result.append(p1[cursor_p1])
            cursor_p1 += 1
        while cursor_p2 < len(p2):
            result.append(p2[cursor_p2])
            cursor_p2 += 1

        # print('evaluated OR: ' + str(len(result)) + ' results')
        # print(result)
        # print('===================')
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

    for q in qlist:
        if q in OPWORDS:
            if q == 'NOT':
                op1 = stack.pop()
                # print('plist:'+str(op1))
                # print('doclist')
                result = evaluate_NOT(op1)
                stack.append(result)
            else:
                op1 = stack.pop()
                op2 = stack.pop()
                # print('plist1:'+str(op1))
                # print('plist2:'+str(op2))
                if q == 'AND':
                    stack.append(evaluate_AND(op1, op2))
                elif q == 'OR':
                    stack.append(evaluate_OR(op1, op2))
        else:
            # operator, get postings from dictionary 
            q = porter.stem(q.lower())
            print(q)
            plist = [] if q not in postings else postings[q]
            # if q in postings:
            #     print('Retrieving posting for '+q+':' + str(postings[q]))
            # else:
            #     print('No record for '+q)
            # print('==============')
            stack.append(plist)
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
    
    with open(f, 'r') as fopen:
        for sent in nltk.sent_tokenize(fopen.read()):
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
# print('Indexed docID:'+str(doclist))

# query = 'american AND NOT american'

# result = parse_query(query)
# result.sort()
# print(result)
with open('query2.txt', 'r') as fq:
    with open('myout2.txt', 'w') as fout:
        lines = fq.readlines()
        count = 0
        for line in lines:
            count += 1
            # if count > 1:
            #     break
            print('==============================================')
            query = line.replace('\n', ' ').replace('\r', '')
            print("querying: "+ query)
            raw = parse_query(query)
            result = [int(x) for x in raw]
            result.sort()
            print("result:"+str(result))
            fout.write(" ".join([str(x) for x in result]))
            fout.write("\n")