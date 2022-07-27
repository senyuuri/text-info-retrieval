== Python Version ==
I'm using Python Version 2.7.12 for this assignment.


== General Notes about this assignment ==
1) Indexing & Seaching
For both document indexing and query processing, special characters(we include ',' as well) 
are converted to empty space ' '. Terms are converted to lowercases with Porter stemming applied. 
One additional treatment is to replace '.' to '' after Porter stemming. This is to ensure 
acronyms such as 'U.S.A.' are uniformly tokenised. For example, 'U.S.A.' in a document can be 
correcly tokenised by using Porter's. However, for queries like 'american U.S.A.', the ending dot 
will be incorrectly removed and result in a mismatched case. Here we scarifice a little bit of 
indexing accuracy('U.S.A.' and 'USA' are mixed) in exchange for a more stable tokenisation result.

For searching, we first load the dictionary into the memeroy. This includes a list of docIDs, their 
document length and all dictionary terms. We then create a lookup table dl_idx for faster convertion
from docID to their index in the doclist. This helps to speed up the score calculation later.

lnc.ltc is used as the searching algorithm. Postings lists are stored on the disk and only a small 
portion(one line) is loaded into memeory whenever required.


3) File Format
[dictionary.txt] 
The first line of the dictionary contains a list of indexed docIDs and 
their length for later cosine normalisation. Document length is rounded to 2 d.p.
Foramt: docID1, doclen; docID2, doclen...

Format for the rest of lines:
"term, term frequency, byte offset for the postings list in postings.txt"

[postings.txt]
Each line represents a postings list for a term. ';' separates documents. For
each document element, the first number is the docID while the second number is the
term frequency tf for the term inside this document.
 

== Files included with this submission ==
index.py, search.py, dictionary.txt, postings.txt

== References ==
N/A
