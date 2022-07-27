== Python Version ==

I'm using Python Version 2.7.12 for this assignment.


== General Notes about this assignment ==
This assignment uses a character-based 4-gram language model. Each 4-gram is effectively treated as an unigram when calculating probability and context is not considered.

The LM:
The lm is store as a dictionary, where the key is the 4-gram(e.g. 'abcd') and the value is a list of probabilities(e.g. [0.1, 0.2, 0.1]). The probability list represents the possibile origin language of a particular 4-gram with an order of [malaysian, indonesian, tamil].   

The algorithm:
1) Read and pre-process a line in the training set as follows:
	a) to remove punctuation/numbers/special characters
	b) to convert all characters to lowercase
2) Create a temporary LM 'lm' to store the frequency count of 4-grams in each language	
3) Starting from the first characters in a sentence to build 4-grams. Use '^' to pad the begining and '#' to pad the endding.
4) If the 4-gram is already in the LM, add 1 to the entry in 'lm'. Otherwise, create a new entry in 'lm' and add the corresponding language count by 1.
5) When all sentences have been analysed, convert the frequency list to a probabilistic 4-gram LM with add-1 smoothing.

The testing:
1) Break down a sentence into 4-grams and add up each 4-gram's possibility of language(in log form to avoid underflow).
2) If a 4-gram is present in the LM, add match_count by 1. Otherwise, ignore.
3) If a sentence has less than 40% of 4-grams that are not present in the LM, consider it as 'other' language.

== Files included with this submission ==

[build_test_LM.py] The LM building and testing code

== References ==
Use log addition to solve the underflow issue when adding small possibilities together
https://lagunita.stanford.edu/c4x/Engineering/CS-224N/asset/slp4.pdf
