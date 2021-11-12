from requests.models import Response
from selenium import webdriver
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import math
import re
import pprint

def connect(url):
    """
        return a requests.get that been parsed by html.parser from given url

        Parameters:
            url (string): the url to get
        
        Return:
            BeautifulSoup parsed html
    """
    return BeautifulSoup(requests.get(url).text, "html.parser")

def getPlans(wantPlan, url):
    """
        Get the title and url of the lesson plans

        Parameters:
            wantPlan (int): the number of lesson plans to get
            url (string): the url being scrapped
        
        Returns:
            numPlans (dictionary): a dictionary with the title being keys and url being values
    """
    initSearchResult = connect(url).find_all(["div"], class_="eny-heading")
    numPlans = {}
    # first for-loop for scrapping through the search page for lesson plan url
    for div in initSearchResult:
        child = div.contents
        if(len(numPlans) < wantPlan):
            numPlans[child[0].text] = child[0]['href']
    # second for-loop for scrapping for lesson plans exceeding 24
    pagesLeftToVist = int(math.ceil(wantPlan/len(numPlans)))
    for i in range(1, pagesLeftToVist):
        planUrl = url[:-1] + str(i)
        currSearchResult = connect(planUrl).find_all(["div"], class_="eny-heading")
        for div in currSearchResult:
            child = div.contents
            if(len(numPlans) < wantPlan):
                numPlans[child[0].text] = child[0]['href']
    return numPlans

def getLikes(doc):
    """
        Get the likes for the lesson plans

        Parameters:
            doc - a BeautifulSoup parsed html
        
        Return:
            likes (string) - the number of likes of the lesson plan
    """
    like = doc.find(class_="count").string
    like = re.sub("[^0-9]", "", like)
    return like

def getTag(doc):
    """
        get all the tags within a lesson page

        Parameters:
            doc - a BeautifulSoup parsed html

        Return:
            tagDic (dictionary): a dictionary with dt tags as keys and dd tags as values
    """
    # getting the tag
    metatag = doc.find("dl",class_="metatag-dl")
    # formatting the tag.
    metatagData = []
    for child in metatag.children:
        if(len(child.text.strip()) > 0):
            child.string = child.text.removeprefix("\xa0 ").removesuffix("  - ")
            metatagData.append(child)
        elif(len(child.text.strip()) == 0 and child.name == "dd"):
            metatagData.append(child)
    # adding the tag into a dictionary for ez reference
    tagDic = {}
    for i in range(len(metatagData)):
        if(metatagData[i].name == "dt"):
            values = []
            for x in range(i+1, len(metatagData)):
                if(metatagData[x].name == "dt"):
                    break
                if(metatagData[x].name == "dd"):
                    if(metatagData[x].get('class') == ['meta-cc-image']):
                        values.append(metatagData[x].a['href'])
                    else:
                        values.append(metatagData[x].string)
            tagDic[metatagData[i].text] = values
    return tagDic

def getFiles(doc):
    """
        Get all files with file types given FILETYPE

        Parameters:
            doc - a BeautifulSoup parsed html
        
        Return:
            a dictionary with total files, total files downloaded, size of files, files Path, total fail downloads
    """
    dlRes = doc.find_all("a")
    totalFile= 0
    dlFile = 0
    totalFileSize = 0
    dlFail = 0
    filePath = []
    for link in dlRes:
        dlLink = link.get('href')
        if(dlLink != None):
            for file in FILETYPE:
                if(file in dlLink):
                    totalFile += 1
                    dl= ""
                    if dlLink.startswith('http'):
                        dl = dlLink
                    else:
                        dl = domain + dlLink
                    dlDoc = requests.head(dl)
                    if dlDoc.status_code == 200:
                        totalFileSize += (int(dlDoc.headers['Content-Length'])/1048576)
                        dlFile += 1
                        localFile = dlLink.split("/")[-1]
                        localFile = re.sub("[^A-Za-z0-9]", "", localFile) + "." + file
                        filePath.append(localFile)
                        response = requests.get(dl)
                        # uncomment code below to download files
                        # with open(localFile, "wb") as file:
                        #     file.write(response.content)
                    else:
                        dlFail += 1
    return {'totalFile': totalFile, 'dlFile': dlFile, 'totalFileSize': totalFileSize, 'dlFail': dlFail, 'filePath': filePath}

FILETYPE = ['pdf', 'docx', 'ppt', 'pptx']
wantPlan = 0
domain = ""
url = ""
while True:
    try:
        wantPlan = int(input('How many lesson plan are you are scrapping? '))
        domain = str(input('What is the domain of the webiste you are scrapping? '))
        url = str(input('What is the url of the webpage you are scrapping? '))
        break
    except:
        print("That's not a valid option!")
numPlans = getPlans(wantPlan, url)

# loop through the url to get data of the pages:
for title in numPlans.keys():
    url = domain + numPlans[title]
    doc = connect(url)
    like = getLikes(doc)
    tag = getTag(doc)
    downloadFiles = getFiles(doc)
    numPlans[title] = {'url': url, 'like': like , 'tag': tag, 'downloadFiles': downloadFiles}

df = pd.DataFrame(columns=['url', 'title', 'Date', 'Author(s)', 'Topic(s)', 'Subject(s)', 'CCLS', 'Grade(s)', 'Like','Total Files', 'Files Size (MB)', 'Files'])
i = 0
for title in numPlans.keys():
    url = numPlans.get(title).get('url')
    date = numPlans.get(title).get('tag').get('Created On:')
    authors = numPlans.get(title).get('tag').get('Posted By')
    topics = numPlans.get(title).get('tag').get('Topic(s):')
    subjects = numPlans.get(title).get('tag').get('Subject(s):')
    ccls = numPlans.get(title).get('tag').get('CCLS:')
    grades = numPlans.get(title).get('tag').get('Grade(s):')
    likes = numPlans.get(title).get('like')
    totalFiles = numPlans.get(title).get('downloadFiles').get('totalFile')
    filesSize = numPlans.get(title).get('downloadFiles').get('totalFileSize')
    filesPath= numPlans.get(title).get('downloadFiles').get('filePath')
    df.at[i,:] = [url, title, date, authors, topics, subjects, ccls, grades, likes, totalFiles, filesSize, filesPath]
    i += 1
df.to_csv('lessplans.csv')

