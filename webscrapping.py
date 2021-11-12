from requests.models import Response
from selenium import webdriver
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas
import math
import re

def connect(url):
    return BeautifulSoup(requests.get(url).text, "html.parser")

def getPlans(wantPlan, url):
    initSearchResult = connect(url).find_all(["div"], class_="eny-heading")
    numPlans = {}
    for div in initSearchResult:
        child = div.contents
        if(len(numPlans) < wantPlan):
            numPlans[child[0].text] = child[0]['href']
            # numPlans.append(child[0]['href'])

    pagesLeftToVist = int(math.ceil(wantPlan/len(numPlans)))
    # first for-loop for scrapping through the search page for lesson plan url
    for i in range(1, pagesLeftToVist):
        planUrl = url[:-1] + str(i)
        currSearchResult = connect(planUrl).find_all(["div"], class_="eny-heading")
        for div in currSearchResult:
            child = div.contents
            if(len(numPlans) < wantPlan):
                numPlans[child[0].text] = child[0]['href']
                # numPlans.append(child[0]['href'])
    return numPlans

def getLikes(doc):
    like = doc.find(class_="count").string
    return like

def getTag(doc):
    metatag = doc.find("dl",class_="metatag-dl")
    # formatting the metadata.
    metatagData = []
    for child in metatag.children:
        if(len(child.text.strip()) > 0):
            child.string = child.text.removeprefix("\xa0 ").removesuffix("  - ")
            metatagData.append(child)
        elif(len(child.text.strip()) == 0 and child.name == "dd"):
            metatagData.append(child)
    # adding the metadata into a dictionary for ez reference
    tagDic = {}
    # print(list(metatagData))
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
                        # with open(localFile, "wb") as file:
                        #     file.write(response.content)
                    else:
                        dlFail += 1
    return {'totalFile': totalFile, 'dlFile': dlFile, 'totalFileSize': totalFileSize, 'dlFail': dlFail, 'filePath': filePath}

domain = "https://www.engageny.org"
url = "https://www.engageny.org/video-library/?page=0%2C0"

FILETYPE = ['pdf', 'docx', 'ppt', 'pptx']
wantPlan = 3
numPlans = getPlans(1, url)

# loop through the url to get data of the pages:
for title in numPlans.keys():
    url = domain + numPlans[title]
    doc = connect(url)
    like = getLikes(doc)
    tag = getTag(doc)
    downloadFiles = getFiles(doc)
    numPlans[title] = {'url': url, 'title': title, 'tag': tag, 'downloadFiles': downloadFiles}

print(numPlans)



