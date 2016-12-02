from bs4 import BeautifulSoup
from urllib.request import urlopen
import codecs
import json
import collections
import pprint
import re
import sqlite3 as lite
import sys
import textrazor

def get_entities(culture, story): #perform named entity recognition on the story and culture
    #define the textrazor api client
    textrazor.api_key = "39be7220519a1686a65f38fdc7c4e64286ddeb8dba34a4db944e46fd"
    client = textrazor.TextRazor(extractors=["entities", "topics"])

    keyw=[]
    response1 = client.analyze(story) 
    for topic in response1.topics():
        if topic.score >= 0.5: #keep only tagged topics with high confidence
            keyw.append(topic.label+"="+str(topic.score))
    keywords=json.dumps(keyw)

    #to avoid exception thrown by api (doesn't deal with these two phrases well)
    if culture=="Italian (Venetian)":
        place = "Italy"
        return place,keywords
    if culture=="Austrian":
        place="Austria"
        return place,keywords
    if culture=="Norwegian":
        place="Norway"
        return place,keywords
    
    response2 = client.analyze(culture) #entity to get country from the culture
    for entity in response2.entities():
        place=entity.id
        break
        
    #definition for cases that may not work with the api
    if culture=="Flemish":
        place="Belgium"
    if culture=="English":
        place="England"
    if culture=="British":
        place="Britain"
    if culture=="Netherlandish":
        place="Netherlands"
    return place, keywords


def extract_from_web(): #data extraction using beautifulsoup
    con = lite.connect('getty.db') #create the getty database for paintings
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS Paintings")
        cur.execute("CREATE TABLE Paintings (Title TEXT, Artist TEXT, Culture TEXT, Medium TEXT, Date TEXT, Dimensions TEXT, Story TEXT, Place TEXT, Keywords TEXT);")

    pages=[]
    with open("getty_links.txt",encoding="latin1") as inp: #getting the 18 search webpages corresponding to the paintings 
        for line in inp:
            pages.append(line)

    links=[]
    for u in pages:
        url=u
        page=urlopen(url).read() #opening each of the 18 pages
        soup1=BeautifulSoup(page,'html.parser')
        s=soup1.find('section',id='search-results')
        figs=s.findAll('figcaption')
        for i in figs:
            a=i.find('a') #finding links to paintings on each search page
            links.append(a.get('href'))   

    for l in range(0,len(links)): #links contains links to all 321 paintings
        title="NULL"
        artist="NULL"
        culture="NULL"
        medium="NULL"
        date="NULL"
        dim="NULL"
        story="NULL"
        painting=urlopen(links[l]).read() #opening each painting webpage
        soup2=BeautifulSoup(painting,'html.parser')
        
        #parsing the webpage and extracting entities
        d=soup2.find('section',class_="object-details-primary clearfix details-list")
        cf=d.findAll('div',class_="clearfix")
        for c in cf:
            k=c.find('h6',class_="subheader")
            key=k.contents[0].split(":")[0]
            value=c.find('p').getText(separator=u' ')
            if key=="Title":
                title=value
            if key=="Artist/Maker":
                artist=value
            if key=="Culture":
                culture=value
            if key=="Medium":
                medium=value
            if key=="Date":
                date=value
            if key=="Dimensions":
                dim=value
            print(key,":",value)
        st=soup2.find('div',id="detail-text")
        if st==None:
            story="No Story available"
        else:
            story=st.getText(separator=u' ')
        print(story)
        place, keywords = get_entities(culture, story)
        print(place)
        print(keywords)
        
        #insert records in database
        cur.execute("INSERT INTO Paintings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", (title, artist, culture, medium, date, dim, story, place, keywords ))
        con.commit()
        

if __name__ == "__main__":
    extract_from_web()
    
            
    
            
