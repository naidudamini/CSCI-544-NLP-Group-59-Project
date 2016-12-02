import nltk
import sqlite3
import itertools
import json
import re
import collections
from bs4 import BeautifulSoup
from urllib.request import urlopen

def getDateandCountry(pos): #to extract the date periods and the country names from the provenance section of each painting
    grammar1 = "DATEr: {<CD><:><CD>}" #grammar for daterange
    grammar2 = "DATE: {<CD>}" #grammar for date 
    cp1 = nltk.RegexpParser(grammar1)
    cp2 = nltk.RegexpParser(grammar2)
    result1 = [cp1.parse(sentence) for sentence in pos]
    result2 = [cp2.parse(sentence) for sentence in pos]
    #print(result)
    dateranges=[extract(r1,"DATEr") for r1 in result1]
    dates=[extract(r2,"DATE") for r2 in result2]
    for d in dates: #keeping only 4 digit numbers as years
        if len(d)!=4:
            dates.remove(d)
    d=collections.OrderedDict.fromkeys(sum(dates,[])) #maintaining order or provenance
    dr=collections.OrderedDict.fromkeys(sum(dateranges,[]))
    d=z=collections.OrderedDict.fromkeys([re.sub('[^0-9]+', '', date) for date in d])
    chunks = nltk.ne_chunk_sents(pos)
    #print(list(chunks))
    gpe=[extract(c,"GPE") for c in chunks] #extracting country/city geo political entity names from chunks
    #print(primechunks)
    countries=collections.OrderedDict.fromkeys(sum(gpe,[])) #maintaining order of country names to combine with date ranges
    #print(countries)
    #return mergedchunks
    return dr.keys(),d.keys(),countries

def getNP(tagged_sentences): #to extract noun phrases from the story paragraph for getting more infor about the painting
    grammar = "NP: {<DT>?<JJ.*>*<NN.*>+<IN>?<NN>?}"
    cp = nltk.RegexpParser(grammar)
    result = [cp.parse(sentence) for sentence in tagged_sentences]
    #print(result)
    nounphrases=[extract(r,"NP") for r in result]
    #print(nounphrases)
    return nounphrases

def getNNP(tagged_sentences): #to extract all primary entities from a painting story
    propernouns = [[word for word,pos in sentence if pos == 'NNP'] for sentence in tagged_sentences]
    mergedpp=set(sum(propernouns,[]))
    #print(mergedpp)
    return mergedpp

def chunk_NER(tagged_sentences): #to extract entities with more relevance to a painting from its story
    chunked_sentences = nltk.ne_chunk_sents(tagged_sentences,binary=True)
    #print(list(chunked_sentences))
    primechunks=[extract(c,"NE") for c in chunked_sentences]
    #print(primechunks)
    mergedchunks=set(sum(primechunks,[]))
    #print(mergedchunks)
    return mergedchunks
        
def extract(tree,l): #to traverse through the nltk tree and extract respective entities based on given label
    n=[]
    if hasattr(tree,'label') and tree.label:
        if tree.label()==l:
            n.append(' '.join([child[0] for child in tree]))
        else:
            for child in tree:
                n.extend(extract(child,l))
    return n

if __name__ == "__main__":
    
    #advanced extraction for date and country of a sample painting (results not used in system hence not extracted for all paintings)
    
    sampleurl="http://www.getty.edu/art/collection/objects/650/alessandro-magnasco-the-triumph-of-venus-italian-about-1720-1730/"
    painting=urlopen(sampleurl).read()
    soup=BeautifulSoup(painting,'html.parser')
    prov=soup.find('section',id="object-section-provenance")
    provenance=prov.getText(separator=u' ')
    sents=nltk.sent_tokenize(provenance)
    tokens = [nltk.word_tokenize(sent) for sent in sents]
    pos = [nltk.pos_tag(sent) for sent in tokens]
    dateranges,dates,countries=getDateandCountry(pos)
    print(list(dateranges))
    print(list(dates))
    print(list(countries))

    #creating a new database containing more context on a painting's background/story
    
    conn = sqlite3.connect('getty.db')
    con=sqlite3.connect('painting_story.db')
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Paintings_Context")
        cur.execute("CREATE TABLE Paintings_Context (Title TEXT, Entities TEXT, ProperNouns TEXT, Phrases TEXT);")
    cursor=conn.execute("Select Title,Story from Paintings") #taking the title and story from current db in use
    for row in cursor:
        title=row[0]
        story=row[1]

        #tokenizing and pos tagging of the story
        sentences = nltk.sent_tokenize(story)
        tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
        #print(tagged_sentences)

        #calling necessary functions to get the nounphrases, proper nouns and chunked entities
        nounphrases=json.dumps(getNP(tagged_sentences))
        pnouns=json.dumps(list(getNNP(tagged_sentences)))
        chunks=json.dumps(list(chunk_NER(tagged_sentences)))
        
        #inserting records in the new database
        cur.execute("INSERT INTO Paintings_Context VALUES (?, ?, ?, ?);", (title, chunks, pnouns, nounphrases))
        con.commit()
        
    
        
