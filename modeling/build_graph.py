#!/usr/bin/python

import sys, collections, math
from gensim import corpora, models
import networkx as nx
import matplotlib.pyplot as plt
import pylab
import json

if len(sys.argv) < 2:
    print "Usage: %s <corpus name>" % sys.argv[0]
    exit()

# Load files
dictionary = corpora.Dictionary.load(sys.argv[1]+".dict")
corpus = corpora.MmCorpus(sys.argv[1]+".mm")

# Define number of topics
ntopics = 10

# Train topic model
model = models.LdaModel(corpus, id2word=dictionary, num_topics=ntopics, alpha=1./ntopics, eta=1./ntopics)

### Prob. rescaling, P(t|w)
termcntr = collections.defaultdict(lambda:0)
topiccntr = collections.defaultdict(lambda:0)

for doc in corpus:
    for term, freq in doc:
        termcntr[term] += freq
    for topic, p in model[doc]:
        topiccntr[topic] += p

termtot = float(sum(termcntr.values()))
topictot = len(corpus)

topics = model.show_topics(topics=-1, topn=50, formatted=False)

#P(t|w)
ptw = collections.defaultdict(lambda: {})

for topic, i in zip(topics, range(ntopics)):
    neworder = []
    for pwt, term in topic:
        term_id = dictionary.token2id[term]
        if termcntr[term_id] < 30:
            continue
        #pwt: p(w|t)
        pw = termcntr[dictionary.token2id[term]]/termtot #p(w)
        pt = topiccntr[i]/topictot #p(t)
        ptw[i][term_id] = pwt*pt/pw #p(t|w)
        neworder.append((ptw[i][term_id], term))
    neworder.sort(reverse=True)
    for p, term in neworder[:15]:
        print term, "\t", p
    print


### Probabilistic document-representative word scoring

# P(d)
pd = 1./len(corpus)
pw = collections.defaultdict(lambda: 0)
pwd = collections.defaultdict(lambda: {})
for doc, doc_id in zip(corpus,range(len(corpus))):
    doc_len = sum([x[1] for x in doc])
    for term_id, cnt in doc:
        # Set P(w|d) for current w
        pwd[doc_id][term_id] = cnt/doc_len
        # P(w) update
        pw[term_id] += cnt


pwtot = sum(pw.values())
for w in pw:
    pw[w] = pw[w]/pwtot

# P(d|w)
pdw = collections.defaultdict(lambda: {})
for doc_id in range(len(corpus)):
    for w in pwd[doc_id]:
        pdw[doc_id][w] = pwd[doc_id][w] * pd / pw[w]        

# Distinctiveness
# sum_T(P(T|w)log(P(T|w)/P(T))

visdict = set()

g = nx.Graph()
for topic, topicnr in zip(topics, range(len(topics))):
    target = 'T%d' % topicnr
    g.add_node(target, {'type': 'topic'})
    for w in ptw[topicnr]:
        prob = ptw[topicnr][w]
        if prob < 0.13:
            continue
        source = dictionary[w]
        visdict.add(source)
        g.add_edge(source, target, {'prob': prob})
        

topicsize = collections.defaultdict(lambda: 0)
for doc in corpus:
    for topic, prob in model[doc]:
        topicsize[topic] += prob

totsize = sum(topicsize.values())
for topic in topicsize:
    topicsize[topic] /= totsize

jsondata = {}
jsondata['nodes'] = [{'name': x[0], 
                      'group': 0 if 'type' in x[1] else 1, 
                      'prop': topicsize[int(x[0][1:])] if 'type' in x[1] else 0,
                      'topic': int(x[0][1:]) if 'type' in x[1] else 'NA'} for x in g.nodes(data=True)]
node_id_lookup = dict(zip([x['name'] for x in jsondata['nodes']], range(len(jsondata['nodes']))))
jsondata['links'] = [{'source': node_id_lookup[x[0]], 'target': node_id_lookup[x[1]], 'value': x[2]['prob']} for x in g.edges(data=True)]


open("graph.json","w").write(repr(jsondata)\
    .replace("'",'"')\
    .replace("},","},\n\t")\
    .replace("],","],\n"))


### Document look-up

"""
#Not implemented in front end

topic2docs = collections.defaultdict(lambda: [])
word2docs = collections.defaultdict(lambda: [])
for i in range(len(corpus)):
    for assign, prob in model[corpus[i]]:
        if prob > 0.1:
            topic2docs[assign].append((i,round(prob,5)))
    wordcnt = sum([x[1] for x in corpus[i]])
    for term_id, count in corpus[i]:
        term = dictionary[term_id]
        if term in visdict:
            prob = count/wordcnt
            if prob > 0.01:
                word2docs[term].append((i, round(prob, 5)))


txtdata = open(sys.argv[1] + '.txt')
titles = []
while True:
    line = txtdata.readline()
    if line == "":
        break
    try:
        line = line.split(' . ')[0]
    except:
        pass
    line = line[0].upper() + line[1:].lower()
    titles.append(line)


titles = [title.replace('"', "").replace("'",'') for title in titles]

open("docs.json","w").write(json.dumps({'topic2docs': dict(topic2docs), 'word2docs': dict(word2docs), 'titles':titles}))

"""

