# Project lunchThere

The repository stores the code tha scraps facebook pages of local venues
for lunch menu. Before that, serp API is used to create database 
of local restaurants. Data collected during the scan is than used
to scrap facebook pages and search for lunch menu offering.
OpenAI and LangChain are used to process facebook data.

### Built with:
- LangChain
- OpenAI
- Chainlit
- Crawlbase
- SerpAPI
- ChromaDB
- SQLite3
</br></br>


## Getting started

### Create conda environment

```
> conda env create -f environment.yml
> conda activate lThere
```
At the time of writing, langchain still worked with pycharm version 1.
So I kept the software versions same as in my environment.
</br></br>

#### Keys
File .env is not part of the repo. I have following keys defined and loaded with dotenv

```
OPENAI_API_KEY=''
SERPAPI_KEY=''
CRAWLBASE_API_KEY='' # JavaScript key
CRAWLBASE_API_KEY_2='' # Regular key to check usage
```

#### Configs
File config.yaml stores necessary configuration, including coordinates for
the place I search for venues.
</br></br>


### Create SQLite3 database
Script databae/manage_db.py can be used to create and drop local SQLIte database.
Steps in the scrpt defines which action will be executed.
```
_steps= [
    'create',
    # 'drop'
]
```
To create database `schema.sql` is used.

### Scraping local venues details from Google using SerpAPI
From now on `main.py` will be our center of command.

```commandline
_steps = [
    # Uses SerpAPI to query results based on GPS coordinates, upload to DB
    # 'search_for_new_places',

    # Extract FB with Crawlbase, scrap posts, identify new places with lunch, save extracted lunch menu for processing
    # 'check_fb_of_new_places',

    # Recheck pages that were scanned but lunch menu was not found or scrapping returned no results
    # 'recheck_fb_pages'

    # collect daily menu, store records in chromaDB
    # 'collect_menu'
]
```

Before executing 'search_for_new_places' update coordinates in `config.yaml`
Please note there is a function called `clean_db_of_places` that uses polish keywords
to remove all places captured by SerpAPI that does not offer food.
So the search will resultes in around 400-500 records in database.
</br></br>

### Scrap facebook pages that were collected by SerpAPI
Only 10-15% of sites is captured with facebook pages.

We select places that have facebook page stored in our database 
and have not been scraped yet.

In table LocalResults.processed I set value 1 if the place was processed once.
If the facebook has posts that are older than 14 days I set LocalResults.processed to 9 immediately

Though the script is set to wait for page load, it's frequently that
the data is not captured with first run.

Results of scrap are passed through OpenAI to tag those with lunch menu and frequency the data is published
LocalResults.has_lunch_menu is a value that's set to 1 if, the lunch menu is present
</br></br>

### Recheck the same facebook pages
As set in the `main.py` file, this is the scame script that's executed as in previous step.
It's used to second inspects sites that were not successful with first execution.
Sites inspected twice ahve LocalResults.processed set to 2
This step should be executed 24h after the previous step
</br></br>


### Collect daily menu
This script has one-time run over facebook pages of venues
that have LocalResults.has_lunch_menu value set to 1

Results of scan are passed to OpenAI and returned as a list of meals with prices.
Such lists of meals are added to ChromaDB where price and link to facebook is stored
as metadata. There is new vector database created for the day so the old one
can be easily deleted with a crontab script.
That allows us easily to search for corresponding information that's relevant only few hours.


#### Example of a record from ChromaDB
| metadatas | documents |
------------------------ | --------------------------------|
| {'price': '22 zł', 'url': 'https://www.facebook.com/element4wroclaw'} | Pierogi ruskie ( 7 sztuk ) z okrasą |
---------------------------------------------------------------------------------------------------------------


### About Data Classes

 **Class LocalResult**
Store data that are scrapped from Google. Most of the data would be used if the project grows beyond answering simple questions

 **Class FBPost**
At the very begining, Apify was used to scrap the data and this class is JSON representation of what data is scraped.
Apify was replaced by cheaper Crawlbase which can scrap only text.

 **Class LocalWithFB**
I use that class to pass place_id, facebook url and a post scrapped from internet

 **Class Tagging**
The class is used to instruct OpenAI how to tag posts with lunch menu

 **Class Meal & Menu**
Class Meal os used to instruct OpenAI how to extract meal and price of each meal.
Menu is a list of meals found in one post


## Chat with the data
Chainlit is initiated from command line. Change director to lThere/chat and execute
```commandline
chainlit run chat.py -w
```








