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
    

def getData(query):
    myData = mycol.find(query)
    return myData

def ajaxCall(url,page):
    params = {
        'search':'',
        'page':page
        }
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-CA,en-US;q=0.7,en;q=0.3',
        'Connection':'keep-alive',
        'Host':'www.allrecipes.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'
        }
    response = requests.get(url,params=params, headers=headers)
    return response.json()

def getRecipiesAllRecipies():
    allrecipiesSearch = "https://www.allrecipes.com/search/results/?search="
    Nav_Page = requests.get(allrecipiesSearch)
    #page loads in sets of 20
    data = []
    sentinel = True
    i = 1
    while sentinel == True:
        call = ajaxCall('https://www.allrecipes.com/element-api/content-proxy/faceted-searches-load-more/', i)
        i=i+1
        callSoup = BeautifulSoup(call['html'], 'html.parser')
        elems_images = callSoup.find_all('div', class_='card__imageContainer')
        for find in elems_images:
            elems = find.findChildren('a')
            for link in elems:
                mongoEntry = {}
                mongoEntry = getRecipeInfo(mongoEntry,link)
                mongoEntry = reviewInfo = getReviewInfo(mongoEntry,link)
                mongoEntry = getPrep(mongoEntry, link)
                mongoEntry = getNutInfo(mongoEntry,link)
                #mongoEntry = getAuth(mongoEntry,link)
                print(mongoEntry)
                data.append(mongoEntry)
                print(call['hasNext'])
                if not call['hasNext'] == True:
                    sentinel= False
                    
    print(data)
    #insertData(data)
               
#this is the recipe info such as name and ingredients
def getRecipeInfo(entry,recipe):
    recipe_Page = requests.get(recipe['href'])
    recipeSoup = BeautifulSoup(recipe_Page.content, 'html.parser')
    name = recipeSoup.find('h1',class_='headline heading-content')
    entry['name']=name.text
    ingredList = []
    ingreds = recipeSoup.findAll('span',class_='ingredients-item-name')
    for ingred in ingreds:
        ingredList.append(ingred.text.strip())
    entry['ingredients']=ingredList
    return entry

#this is the nutritional info, have to sanitize heavily
def getNutInfo(entry,recipe):
    nutlist = {}

    recipe_Page = requests.get(recipe['href'])
    recipeSoup = BeautifulSoup(recipe_Page.content, 'html.parser')
    
    calstr = recipeSoup.find('div', class_='nutrition-top').text.replace("Servings Per Recipe:","")
    calstr = calstr[25:50]
    for x in "Calories:":
        calstr=calstr.replace(x,'')
    nutlist['Calories']=float(calstr.strip())  
    
    nutbody = recipeSoup.find('div',class_='nutrition-body')
    nutrition = nutbody.findChildren('div', class_='nutrition-row')
    for row in nutrition:
        category = row.findChildren(class_='nutrient-name')[0].find(text=True)
        amount = row.findChildren(class_='nutrient-value')[0].text
        if not 'calories from fat' in category:
            nutlist[category.strip().replace(':','')]=amount.strip()

    entry['nutritionalInfo'] = nutlist
    return entry
#this will be the author info
def getAuth(entry,recipe):
    recipe_Page = requests.get(recipe['href'])
    auth = {}
    recipeSoup = BeautifulSoup(recipe_Page.content, 'html.parser')
    link = recipeSoup.find('a',class_='author-name link')
    auth['Name'] = link.text
    print(link['href'])
    #have to strip link in order to get the id then put it https://apps.allrecipes.com/v1/users/XXXX/recipes
    jsonLink = link['href'] + '?isemailtofriend=false&page=1&pageSize=20&tenantId=12'
    jsonRecipe = requests.get(jsonLink)
    #author_Page = requests.get(link['href'])
    #authSoup = BeautifulSoup(author_Page.content, 'html.parser')
    #followers is a ajax call that returns json????
    #auth['Followers'] = followers.text

    print(recList)
    auth['RecipeAmount'] = len(recList)
    entry['Author'] = auth
    return entry

#this will be the prep time, serving size ect
def getPrep(entry,recipe):
    recipe_Page = requests.get(recipe['href'])
    recipeSoup = BeautifulSoup(recipe_Page.content, 'html.parser')
    metaItem = recipeSoup.findAll('div',class_='recipe-meta-item')
    prep = {}
    for item in metaItem:
        childs = item.findChildren()
        prep[childs[0].text.strip().replace(':','')]=childs[1].text.strip()
    entry['Preparation'] = prep
    return entry

#theres something wrong in the averaging here
def getReviewInfo(entry,recipe):
    recipe_Page = requests.get(recipe['href'])
    recipeSoup = BeautifulSoup(recipe_Page.content, 'html.parser')
    recipeReviews = recipeSoup.find('ul',class_='ratings-list')
    recipeReviewList = recipeReviews.findChildren('li')
    revTotal = 0
    revScore = 0
    i=5
    reviews = {}
    for rev in recipeReviewList:
        count = rev.findChildren('span', class_='rating-count')
        #print(count[0].text + " reviews for " + str(i) + " stars")
        revTotal += int(count[0].text)
        #print(str(revTotal) + " is the amount of reviews currently")
        revScore += (int(count[0].text) * i)
        #print(str(revScore) + " is the amount of score")
        i-=1
    recipieAv = revScore / revTotal
    reviews['Review Average']=recipieAv
    reviews['Total Ratings'] = revTotal
    entry['Reviews']=reviews
    return entry
    
#createDb()
getRecipiesAllRecipies()
#def getTopicsFN():
 #   foodnetwork_topics = "https://www.foodnetwork.com/topics"
  #  topicNav_page = requests.get(foodnetwork_topics)
   # topic_soup = BeautifulSoup(topicNav_page.content, 'html.parser')
   # topic_elems = topic_soup.find_all('li', class_='m-PromoList__a-ListItem')
   # for linkHolder in topic_elems: 
   #     link = linkHolder.find('a')['href']
   #     getRecipiesFN(link)
   #     if "https:" not in foodnetwork_topics: 
   #         topic_page = requests.get("http:" + foodnetwork_topics)
   #     elif "http" not in foodnetwork_topics:
   #         topic_page = requests.get("http:" + foodnetwork_topics)
   #     else:
   #         topic_page = requests.get(foodnetwork_topics)

        
#def getRecipiesFN(link):
 #   topic_page = requests.get("http:" + link)
  #  nav_soup = BeautifulSoup(topic_page.content,'html.parser')
   # recipie_links = nav_soup.find_all(class_="m-MediaBlock__m-TextWrap")
    #for linkHolder in recipie_links:
     #   if not None in linkHolder:
      #      try:
       #         recipie_link = linkHolder.find('a')['href']
        #        navToRecipieFN(recipie_link)
         #   except:
          #      continue
           # if "https:" not in link: 
            #    topic_page = requests.get("http:" + link)
            #elif "http:" not in link:
            #    topic_page = requests.get("http:" + link)
            #else:
             #   topic_page = requests.get(link)            
    
#def navToRecipieFN(link):
 #   if "https:" not in link:
  #      recipie_page = requests.get("http:" + link)
   # else:
    #    recipie_page = requests.get(link)        
    #this is the object containing all tags
    #recipie_soup = BeautifulSoup(recipie_page.content,'html.parser')
    #
    #recipie = recipie_soup.find(class_='o-AssetTitle__a-HeadlineText')
    
    #if not "Recipes" in recipie.text: 
     #   recipieAsDict = {"name":recipie.text, }
      #  scrapedList.append(recipieAsDict)
       # print(recipieAsDict)
        
#createDb()
#getTopicsFN()    
