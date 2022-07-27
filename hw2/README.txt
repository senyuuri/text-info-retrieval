== Python Version ==
I'm using Python Version 2.7.12 for this assignment.


== General Notes about this assignment ==
dictionary format: (dictionary.txt)
[line 1]: a list of indexed docIDs
[line 2 and above]: dictionary entries in the format of 
(keyword, frequency ,offset to the beginning of postings.txt(in bytes))

postings list format: (postings.txt)
Each line in the postings list corresponds to a same line entry in the dictionary file. 
A special tag '#' is to indicate that a node has a skip pointer which is the next 
adjacent node. Skip pointers are in the format of "!next_docID!offset". The offset is
measured in the number of entries to be skipped after this skip pointer. 
For example: "#3092,!3122!2" means the node of docID 3092 has a skip pointer pointing to
docID 3122, which is 2 nodes away from the skip pointer itself. 

The search code uses a customised shunting-yard algorithm to parse the query to Reverse
Polish Notation(RPN). The dictionary file is fully loaded into the memory at startup while 
the postings list is kept on disk and only a specific portion is loaded into memory 
when a keyword is queried.


== Files included with this submission ==
index.py: for indexing
search.py: for searching
dictionary.txt: indexed dictionary file
postings.txt: indexed postings list 

== References ==
[1]NLTK Howto: 3.Processing Raw Text
http://www.nltk.org/book/ch03.html

[2]How sent_tokenizer + word_tokenizer work together
https://stackoverflow.com/questions/33773157/word-tokenize-typeerror-expected-string-or-buffer

[3]Shunting-yard Algorithm
https://en.wikipedia.org/wiki/Shunting-yard_algorithm

[4]Reverse Polish Notation
https://en.wikipedia.org/wiki/Reverse_Polish_notation
