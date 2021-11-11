from selenium import webdriver
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas
import math


url = "https://www.engageny.org/video-library/?page=0%2C0"
result = requests.get(url)
doc = BeautifulSoup(result.text, "html.parser")
searchResult = doc.find_all(["div"], class_="eny-heading")

wantPlan = 10
numPlans = []

for div in searchResult:
    child = div.contents
    numPlans.append(child[0]['href'])

pagesLeftToVist = int(math.ceil(wantPlan/len(numPlans)))
for i in range(1, pagesLeftToVist):
    url = f"https://www.engageny.org/resource-type/lesson-plan?sort=created&order=asc&page=0%2C{i}"
    result = requests.get(url)
    doc = BeautifulSoup(result.text, "html.parser")
    for div in searchResult:
        child = div.contents
        if(len(numPlans) < wantPlan):
            numPlans.append(child[0]['href'])

print(len(numPlans))
print(numPlans)
