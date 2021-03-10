import requests
import pymongo
from bs4 import BeautifulSoup
from flask import Flask

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
app = Flask(__name__)
scrapedList = []

def checkDbExists():
    dblist = myclient.list_database_names()
    if not "projectDB" in dblist:
        return True
def checkCollectionExists():
    collist = mydb.list_collection_names()
    if not "recipies" in collist:
        return True
def createDb():
    if(checkDbExists()):
        mydb = myclient["projectDB"]
        if(checkCollectionExists()):
            global mycol
            mycol = mydb["recipies"]

def insertData(data):
    if not isinstance(data, list):
        x = mycol.insert_one(data)
        print("data was successfully inserted with the id of: " + x.inserted_id)
    else:
        x = mycol.insert_many(data)
        print("data was successfully inserted with the ids of: " + x.inserted_ids)

def getTopics():
    foodnetwork_topics = "https://www.foodnetwork.com/topics"
    topicNav_page = requests.get(foodnetwork_topics)
    topic_soup = BeautifulSoup(topicNav_page.content, 'html.parser')
    topic_elems = topic_soup.find_all('li', class_='m-PromoList__a-ListItem')
    for linkHolder in topic_elems: 
        link = linkHolder.find('a')['href']
        getRecipies(link)
        if "https:" not in foodnetwork_topics: 
            topic_page = requests.get("http:" + foodnetwork_topics)
        elif "http" not in foodnetwork_topics:
            topic_page = requests.get("http:" + foodnetwork_topics)
        else:
            topic_page = requests.get(foodnetwork_topics)

        
def getRecipies(link):
    topic_page = requests.get("http:" + link)
    nav_soup = BeautifulSoup(topic_page.content,'html.parser')
    recipie_links = nav_soup.find_all(class_="m-MediaBlock__m-TextWrap")
    for linkHolder in recipie_links:
        if not None in linkHolder:
            try:
                recipie_link = linkHolder.find('a')['href']
                navToRecipie(recipie_link)
            except:
                continue
            if "https:" not in link: 
                topic_page = requests.get("http:" + link)
            elif "http:" not in link:
                topic_page = requests.get("http:" + link)
            else:
                topic_page = requests.get(link)            
    
def navToRecipie(link):
    if "https:" not in link:
        recipie_page = requests.get("http:" + link)
    else:
        recipie_page = requests.get(link)        
    recipie_soup = BeautifulSoup(recipie_page.content,'html.parser')
    recipie = recipie_soup.find(class_='o-AssetTitle__a-HeadlineText')
    if not "Recipes" in recipie.text: 
        recipieAsDict = {"name":recipie.text}
        scrapedList.append(recipieAsDict)
        print(recipieAsDict)        
        
@app.route('/')
def defaultHome():
    return "Welcome to the default page WIP"

##createDb()
getTopics()    
