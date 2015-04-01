#!/usr/bin/python

import sys, re
from gensim import corpora
import nltk.tokenize.punkt as punkt
# Alt: use TextBlob for tokenization

tokenizer = punkt.PunktWordTokenizer()

# Read corpus file, tokenize, normalize
texts = [[term.lower() for term in [re.sub("\.$", "", token) for token in tokenizer.tokenize(doc)]] 
        for doc in open(sys.argv[1]).read().decode('utf-8').split('\n')]
# Filter non-word tokens
texts = [filter(lambda x: (len(x) > 1 or x.isalpha()) and not x.isdigit(), text) for text in texts]

# Generate gensim dictionary
dictionary = corpora.Dictionary(texts)

# Save dictionary
if len(sys.argv) > 2:
    dictionary.save(sys.argv[2]+".dict")
else:
    print "Usage: %s <corpus file> <output name>" % sys.argv[0]
    exit()

# Save converted corpus
corpus = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize(sys.argv[2]+".mm", corpus)

