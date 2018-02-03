#!/usr/bin/python
import math
import re
import nltk
import sys
import getopt

# convert language tag to index
LANG_TO_INDEX = {
    'malaysian': 0,
    'indonesian': 1,
    'tamil': 2
}

# convert index to language tag
INDEX_TO_LANG = {v: k for k, v in LANG_TO_INDEX.items()}

# threshold for alien language detection
LIMIT = 0.4

def build_LM(in_file):
    """
    build language models for each label
    each line in in_file contains a label and a string separated by a space
    """
    print 'building language models...'
    # create a new language model
    lm = {}
    # count the number of occurance of 4-grams in the training set for each language
    # see LANG_INDEX for the index representation
    count = [0,0,0]

    with open(in_file, 'r') as infile:
        for line in infile:
            # convert language tag to index
            lang = line.split(" ")[0]
            # sentence with punctuation removed and all characters converted to lowercase
            s = re.sub('[^a-zA-Z ]', '', line[len(lang) + 1:]).lower()
            # count frequency of appearance for each 4-grams
            for i in range(-3,len(s)):
                # Use ^ to pad the beginning
                if i < 0:
                    part = '^'*(0 - i) + s[0:4+i]
                # Use # to pad the end
                elif(i+4 > len(s)):
                    part = s[i:len(s)] + '#'*(i+4-len(s))
                else:
                    part = s[i:i+4]
                # create a new 4-grams record if not exist
                if part not in lm: 
                    lm[part] = [0,0,0]

                #print("#"+str(i)+" "+part)
                # add frequency count by 1
                lm[part][LANG_TO_INDEX[lang]] += 1
                count[LANG_TO_INDEX[lang]] += 1
                #print(lm)

    # calculate probability with add-1 smoothing
    # add the size of the LM to 'token' count since we are going to do add-1 for every 4-gram
    count = map(lambda x: x + len(lm),count)

    new_lm = {}
    for key,value in lm.items():
        # probability of a 4-gram
        p = [0, 0, 0]
        for i in range(3):
            p[i] = (value[i] + 1.0) / count[i]
        # save it to the final LM
        new_lm[key] = p

    return new_lm
    
def test_LM(in_file, out_file, LM):
    """
    test the language models on new strings
    each line of in_file contains a string
    you should print the most probable label for each string into out_file
    """
    print "testing language models..."
    fout = open(out_file,'w+')

    with open(in_file, 'r') as testfile:
        for line in testfile:
            # probability of language(in log)
            p = [0.0, 0.0, 0.0]
            # number of matched 4-grams
            match_count = 0
            # sentence with punctuation removed and all characters converted to lowercase
            s = re.sub('[^a-zA-Z ]', '', line).lower()

            # count frequency of appearance for each 4-gram
            for i in range(-3,len(s)):
                # Add padding '0' if the end of a sentenece does not have enough characters to form a 4-gram
                # Use ^ to pad the beginning
                if i < 0:
                    part = '^'*(0 - i) + s[0:4+i]
                # Use # to pad the end
                elif(i+4 > len(s)):
                    part = s[i:len(s)] + '#'*(i+4-len(s))
                else:
                    part = s[i:i+4]

                if part in LM:
                    for j in range(0,3):
                        p[j] += math.log(LM[part][j],10)
                    #     print("p[j]+",p[j])
                    # print(p)
                    match_count += 1
                else:
                    # ignore 4-grams that are not found in the LM
                    pass

            # write result to output file
            # if less than 'LIMIT'% 4-grams are not in the LM, consider other language 
            if((match_count*1.0/(len(s)+3)) < LIMIT):
                fout.write('other '+line)
            else:
                fout.write(INDEX_TO_LANG[p.index((max(p)))]+' '+line)
            
    # append newline at EOF
    fout.write('\n')
    fout.close()

def usage():
    print "usage: " + sys.argv[0] + " -b input-file-for-building-LM -t input-file-for-testing-LM -o output-file"

input_file_b = input_file_t = output_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'b:t:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-b':
        input_file_b = a
    elif o == '-t':
        input_file_t = a
    elif o == '-o':
        output_file = a
    else:
        assert False, "unhandled option"
if input_file_b == None or input_file_t == None or output_file == None:
    usage()
    sys.exit(2)

LM = build_LM(input_file_b)
test_LM(input_file_t, output_file, LM)
