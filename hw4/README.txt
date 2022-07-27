== Python Version ==
I'm using Python 3.4 for this assignment.


== General Notes about this assignment ==
To index the huge dataset in a timely manner was challenging. I was trying to reuse the code form previous assignmet but soon found out that a simple in-memory index constrcution took 40+ hours to run. My final solution is to use blocked sort-based indexing(BSBI) with multi-threaded porter's stemmer. The strategy is:
Part 1: Parallel tokenisation
1) Divide the corpus into 18 blocks with each block contains 2000 documents.
2) For documents in a block, use a multiprocesser.pool of 4 workers to tokenize. A document is divided into three zones: TITLE('#'), COURT('&'), and CONTENT('$'). The special charaters are attached at the end of each term to indicate their belongings. For tokenisation, Porter's stemmer is used and only alphanumeric characters is retained. Stop words are not removed. The processed tokens in each block are collected as a list.
3) Create a folder 'tmp' for temporary files. For each block, the list of document IDs and inverted postings list are saved to the disk. A sample of such intermediate postings looks like:
term + zone: docID, tf, ...
coonambl$:6541786,1;6692923,1

Part 2: Heap merge
All blocks of postings lists in the 'tmp' folder are loaded into a heap. Elemets are popped out and combined to form the final postings list.

seach.py is built on the vector space model with cosine similarity based on tf-idf. If query expansion is enabled(on by default), synonyms of each query term in WordNet are added to the query as well. For terms found in different document zones , different scoring coefficients are used. The score will be the higher if a term appear in the TITLE and COURT zone. The reason to keep the COURT zone is because if there is a conflict between cases, layers can find out which document is more persuasive by look at the issuing court. (Not implemented) We can have a list of court hierarchy in future so that we can assign an authority score to documents.


== Files included with this submission ==
index.py, search.py, dictionary.txt, postings.txt

== References ==
[1]Automatic thesaurus generation, Stanford NLP Group,
https://nlp.stanford.edu/IR-book/html/htmledition/automatic-thesaurus-generation-1.html

[2]Zones and Linear Zone Combinations, Stanford CS276A Lecture 6,
https://web.stanford.edu/class/archive/cs/cs276a/cs276a.1032/handouts/lecture6.ppt

[3]TREC Legal Track
https://trec-legal.umiacs.umd.edu/
