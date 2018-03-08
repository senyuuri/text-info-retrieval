#!/usr/bin/python
import re
import nltk
import sys
import glob
import getopt
import time
from abc import ABCMeta, abstractmethod

# operator keywords in the order of increasing precedence
OPWORDS = ['OR','AND','NOT']

class PLlist:
    """Abstract wrapper class for on-disk postings list and in-memory intermediate result"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self):
        """return the docID in which the cursor is pointing to"""
        pass

    @abstractmethod
    def move(self):
        """move the cursor to the next adjacent docID"""
        pass

    @abstractmethod
    def move_or_skip(self, x):
        """given a larger value x from another list, move or skip to the next docID"""
        pass

    @abstractmethod
    def has_next(self):
        """return true if the cursor has not reached to the end of the list"""
        pass


class PListMemory(PList):
    """Wrapper class for operations on in-memory docID list(the intermediate result)"""
    def __init__(self, plist):
        self.plist = plist 
        self.cursor = 0

    def get(self):
        return self.plist[self.cursor]

    def move(self):
        return self.cursor += 1

    def move_or_skip(self, x):
        # in-memory list has no skip pointer
        return self.move()

    def has_next(self):
        return self.cursor < len(self.plist)


class PListDisk(PList):
     """Wrapper class for reading postings list from disk"""
    def __init__(self, fin, offset):
        # file handler of postings_file
        self.fin = fopen
        # read() offset
        self.cursor = offset
        # is current node a skip pointer
        self.is_pointer = False

    def get(self):
        self.fin.seek(self.cursor)
        start_offset = self.cursor
        docID = ''
        # read the first character of the docID
        char = self.fin.read(1)
        if char == '#':
            # the current docID node has a skip pointer
            self.is_pointer = True
        # read the rest of the docID
        while char != ',' and char != '\n':
            docID += char
            char = self.fin.read(1)
        # restore to start offset
        self.cursor = start_offset
        print("read:"+docID)
        return int(docID)

    def move(self):
        return self.cursor += 1

    def move_or_skip(self, x):
        # in-memory list has no skip pointer
        return self.move()

    def has_next(self):
        return self.cursor < len(self.plist)


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
            # operator, get postings from disk
            q = porter.stem(q.lower())
            print(q)
            if q in d:
                # read postings list from disk
                # set read cursor as offset from the beginning of the file
                fp.seek(d[q][1], 0)
                line = fp.readline()
                plist = [int(x) for x in line.split(',')]
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
            result = [int(x) for x in raw]
            result.sort()
            print("result:"+str(result))
            fout.write(" ".join([str(x) for x in result]))
            fout.write("\n")

        print(str(len(lines))+" queries processed in "+str(time.time() - start_time)+" seconds.")