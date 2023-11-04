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

## Getting started

### Create conda environment

```
> conda env create -f environment.yml
> conda activate lThere
```
At the time of writing, langchain still worked with pycharm version 1.
So I kept the software versions same as in my environment.

### Keys
File .env is not part of the repo. I have following keys defined and loaded with dotenv

```
OPENAI_API_KEY=''
SERPAPI_KEY=''
CRAWLBASE_API_KEY='' # JavaScript key
CRAWLBASE_API_KEY_2='' # Regular key to check usage
```

### Configs
File config.yaml stores necessary configuration, including coordinates for
the place I search for venues.


### Code execution

#### SQLite3 database
Script databae/manage_db.py can be used to create and drop local SQLIte database.
Steps in the scrpt defines which action will be executed.
```
_steps= [
    'create',
    # 'drop'
]
```
To create database `schema.sql` is used.

#### Scraping local venue details from Google using SerpAPI
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

#### Scrap facebook pages that were collected by SerpAPI
Unfortunately 10-15% of sites is captured with facebook pages 
so this time the scraping will be much less extensive.

So we attempt to scrap last post of each page that is selected scrapping.
We select places that have facebook page stored in our database and have not been scraped yet.

In table LocalResults.processed I store value 1 if the place was processed once,
and if lunch was not found on the post for ANY reason, I attempt to scan that
page following day one more time.
If the facebook has posts that are older than 14 days I set LocalResults.processed to 9 immediately

Though the script is set to wait for page load, it's frequently that
the data is not captured with first run so I design the script to run
it again on the pages that were previously scanned.

Results of scrap are passed thorugh OpenAI to decide whether 
capture data represents lunch menu, and if yes, at what frequency the data is published


#### Recheck the same facebook pages
As set in the `main.py` file, this is the scame script that's exectued as in previous step.
I set shorte hour window and this time set the LocalResults.processed to 2
to makr the site was scanned twice.

This step should be executed 24h after the step 2

#### Collect daily menu
This script has one-time run over facebook pages of venues
that have LocalResults.has_lunch_menu value set to 1

Results of scan are passed to OpenAI and returned as a list of meals with prices.
Such lists of meals are added to ChromaDB where price and link to facebook is stored
as metadata.
That allows us easily to search for coresponding informaiton.













