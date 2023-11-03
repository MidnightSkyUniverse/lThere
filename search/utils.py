"""
Author: Ali Binkowska
October 2023
"""
from itertools import islice

import numpy as np
import tiktoken
from dateutil import parser
from dotenv import load_dotenv
from joblib import dump, load
from serpapi import GoogleSearch

load_dotenv()

from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser

from crawlbase import CrawlingAPI
import json
import re
import os
from datetime import timedelta

load_dotenv()

from class_utils import LocalResult, FBPost, LocalWithFB

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

import logging
logging.basicConfig(
    level=logging.INFO, format="(%(levelname)s):  %(message)s"
)
log = logging.getLogger()

from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from langchain.vectorstores import Chroma

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)

from chromadb.errors import InvalidDimensionException

from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function


with open('config.yaml', 'rb') as f:
    cfg = f.read()


#*************************
### SERPAPI scraper
#*************************

def generate_grid_points(boundary: dict, step_size=0.05) -> List[LocalResult]:
    """Generates grid points based on the given boundary and step size."""

    lats = np.arange(boundary['SOUTH'], boundary['NORTH'], step_size)
    longs = np.arange(boundary['WEST'], boundary['EAST'], step_size)

    grid_points = [(lat, lon) for lat in lats for lon in longs]

    return grid_points


def dict_to_local_result(data: Dict) -> LocalResult:
    """Function to convert a dictionary to a LocalResult object"""
    return LocalResult(**data)

def serpapi_query(lat: float, lon: float) -> list:
    """
    Queries up to 100 results from Google Maps using SERPAPI.

    Parameters:
        lat (float): The latitude coordinate.
        lon (float): The longitude coordinate.

    Returns:
        list: List of local results parsed from the SERPAPI response.
    """

    coordinates = f"@{lat},{lon},15z"
    local_results = []

    for i in range(0, 5):
        params = {
            "api_key": os.getenv("SERPAPI_KEY"),
            "engine": "google_maps",
            "q": "restauracja lunch",
            "google_domain": "google.com",
            "ll": coordinates,
            "type": "search",
            "hl": "pl",
            "start": str(i * 20),
        }

        search = GoogleSearch(params)
        search_results = search.get_dict()
        current_local_results = search_results.get('local_results', [])

        # Parse each dictionary to a LocalResult object
        for result in current_local_results:
            try:
                local_result = dict_to_local_result(result)
                local_results.append(local_result)
            except Exception as e:
                # Handle the exception as you see fit
                pass

    return local_results


#*************************
### APIFY scraper (replaced by Crawlbase)
#*************************

### APify - FB scrapping ###

# def fb_posts_scrapper(
#         list_of_place_ids: List[str],
#         list_of_urls: List[str],
#         how_many_posts: int
#     ) -> List[Any]:
#     """
#     Scan FB pages for information about lunch menu.
#
#     Parameters:
#         list_of_urls (List[str]): List of Facebook URLs to scrape.
#         how_many_posts (int): Number of posts to scrape per URL.
#
#     Returns:
#         list: List of validated FBPost objects.
#     """
#     token = os.getenv('APIFY_API_TOKEN', 'default_token')
#     if not token:
#         raise ValueError("APIFY_API_TOKEN is not set!")
#
#     client = ApifyClient(token)
#     all_validated_posts = []  # List to store all validated FBPost objects
#
#     for id_, url in zip(list_of_place_ids,list_of_urls):
#         time.sleep(1)  # Simple rate limiter, you can replace with more advanced logic
#         run_input = {
#             "startUrls": [{"url": url}],
#             "resultsLimit": how_many_posts,
#         }
#         actor_id = "apify/facebook-posts-scraper"
#
#         try:
#             run = client.actor(actor_id).call(run_input=run_input)
#             for item in client.dataset(run["defaultDatasetId"]).iterate_items():
#                 # validated_post = FBPost(**item)  # Assuming FBPost is a valid model class
#                 validated_object = LocalWithFB(
#                     place_id=id_,
#                     fb_post=FBPost(**item),
#                 )
#                 all_validated_posts.append(validated_object)
#         except Exception as e:
#             log.error(f"Error fetching data for {url}. Error: {e}")
#
#     return all_validated_posts



#*************************
### CRAWLBASE scraper
#*************************
def parse_facebook_timestamp(timeStamp: str) -> datetime:
    """
    Parse Facebook timestamp string into a datetime object.

    Parameters:
    - timeStamp (str): The timestamp string from Facebook (e.g., '1d', '4h', 'October 20 at 4:22 PM').

    Returns:
    - datetime: The parsed datetime object.
    """
    try:
        if 'd' in timeStamp:
            return datetime.now() - timedelta(days=int(timeStamp.replace('d', '').strip()))
        elif 'h' in timeStamp:
            return datetime.now() - timedelta(hours=int(timeStamp.replace('h', '').strip()))
        elif 'm' in timeStamp:
            return datetime.now() - timedelta(minutes=int(timeStamp.replace('m', '').strip()))
        else:
            dt = datetime.strptime(timeStamp, '%B %d at %I:%M %p')
            return dt.replace(year=datetime.now().year)
    except ValueError:
        return datetime(2000, 1, 1)

def fb_posts_scrapper(
        objects: List[LocalWithFB],
    ) -> List[Any]:
    """
    Scan FB page for recent post

    Parameters:
    - List[LocalWithFB]

    Returns:
    - the same list updated with last post scrapped for given page
    """
    token = os.getenv('CRAWLBASE_API_KEY')
    if not token:
        raise ValueError("CRAWLBASE_API_KEY is not set!")

    api = CrawlingAPI({'token': token})

    # results = []
    for item in objects:
        try:
            item.fb_post = FBPost() # initialize object here to avoid NoneType later in the processing
            response = api.get(item.facebook_url, {'ajax_wait': 'true', 'page_wait': 10000})
            if response['status_code'] == 200:
                body_str = response['body'].decode('utf-8')
                post_urls = re.findall(r'https?://\S*post\S*', body_str)

                # Assuming you want to process only the first post URL
                if post_urls:
                    response = api.get(post_urls[0], {'autoparse': 'true', 'ajax_wait': 'true', 'page_wait': 10000})
                    response_content = response['body'].decode('utf-8')
                    data = json.loads(response_content)

                    if 'body' in data and 'posts' in data['body'] and data['body']['posts']:
                        post = data['body']['posts'][0]
                        item.fb_post = FBPost(
                            facebook_url=item.facebook_url,
                            text=post.get('text'),
                            time=parse_facebook_timestamp(post.get('timeStamp')),
                        )
            else:
                print(f"Failed to fetch data for {item.facebook_url}. Status code: {response['status_code']}")

        except Exception as e:
            print(f"Error fetching data for {item.facebook_url}. Error: {e}")


    return objects


def filter_out_old_posts(objects: List[LocalWithFB], hours: int):
    """Filter posts based on the given hours.

    If hours is positive, return posts from the last 'hours' hours.
    If hours is negative, return posts older than 'hours' hours.
    """
    now = datetime.now()
    cutoff_time = now - timedelta(hours=abs(hours))

    if hours > 0:
        filtered_list = [item for item in objects if item.fb_post.time >= cutoff_time]
    else:
        filtered_list = [item for item in objects if item.fb_post.time < cutoff_time]

    return filtered_list


def separate_posts(objects: List[LocalWithFB]) -> Tuple[List[LocalWithFB], List[LocalWithFB]]:
    """Separate items based on whether item.fb_post is set or not set.

    :param objects: List of LocalWithFB objects
    :return: A tuple of two lists (posts_set, posts_not_set)
    """
    posts_set = [item for item in objects if item.fb_post is not None and item.fb_post.time is not None]
    posts_not_set = [item for item in objects if item not in posts_set]

    return posts_set, posts_not_set



#*************************
### LANGCHAIN & OPENAI
#*************************

class Tagging(BaseModel):
    """Tag the piece of text with particular info."""
    is_lunch_menu: str = Field(description="text contains lunch menu, should be 'yes' or 'no'")
    is_daily: Optional[str] = Field(description="is the lunch menu only for today,  should be 'yes' or 'no'")

def is_lunch_menu(
        objects: List[LocalWithFB],
        model_name: str,
        template: str,
        chunk_size: int,
) -> List[tuple]:
    """Check if posts have lunch menu, check if lunch menu is daily or weekly"""
    results = []

    model = ChatOpenAI(model_name=model_name,temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", template ),
        ("user", "{input}")
    ])

    tagging_functions = [convert_pydantic_to_openai_function(Tagging)]
    model_with_functions = model.bind(
        functions=tagging_functions,
        function_call={"name": "Tagging"}
    )

    # chain definition
    tagging_chain = prompt | model_with_functions | JsonOutputFunctionsParser()

    # iterate and select items with menu on it
    for item in objects:
        if item.fb_post and item.fb_post.text:
            tagger = tagging_chain.invoke({"input": item.fb_post.text[:chunk_size]})
            if tagger['is_lunch_menu'] == 'yes':
                is_daily = True if tagger['is_daily'] == 'yes' else False
                results.append((item,True, is_daily))
            else:
                results.append((item,False, False))
        else:
            log.warning(f"is_lunch_menu(): there is no text to inspect: {item.facebook_url}")
            results.append((item, False, False))

    return results


class Meal(BaseModel):
    """Information about meals mentioned"""
    meal: Optional[str] = Field(description="Meal")
    price: Optional[str] = Field(description="Price of meal with currency")

class Menu(BaseModel):
    """Information to extract"""
    menu: List[Meal] = Field(description="List of info about meals")


def extract_lunch_menu(
        objects: List[LocalWithFB],
        model_name: str,
        template: str,
        chunk_size: int,
) -> List[tuple]:
    """Check if posts have lunch menu, check if lunch menu is daily or weekly"""
    results = []

    model = ChatOpenAI(model_name=model_name,temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", template ),
        ("user", "{input}")
    ])

    tagging_functions = [convert_pydantic_to_openai_function(Menu)]
    model_with_functions = model.bind(
        functions=tagging_functions,
        function_call={"name": "Menu"}
    )

    # chain definition
    extracting_chain = prompt | model_with_functions | JsonKeyOutputFunctionsParser(key_name="menu")

    # iterate and select items with menu on it
    for item in objects:
        extract = extracting_chain.invoke({"input": item.fb_post.text[:chunk_size]})
        if extract:
            results.append((item,extract))


    return results



###################
# Chroma
###################
def db_connect(db_pth: str, embedding: List[Any]):
    """Return handler to existing Chroma DB"""
    # if collection_name:
    #     return Chroma(persist_directory=db_pth, collection_name=collection_name,embedding_function=embedding)
    # else:
    return Chroma(persist_directory=db_pth, embedding_function=embedding)

def db_create(db_pth: str, embedding, documents):
    """Return connection to DB or create new one if one does not exist"""
    try:
        db = Chroma.from_documents(
            documents,
            embedding=embedding,
            persist_directory=db_pth,
        )
    except InvalidDimensionException:
        Chroma().delete_collection()
        db = Chroma.from_documents(
            documents,
            embedding=embedding,
            persist_directory=db_pth,
        )
    return db


# **************************
# SUPPORT FUNCTIONS ###
# **************************

def count_tokens(model_name, text):
    """Count tokes for given model"""
    encoding = tiktoken.encoding_for_model(model_name)
    prompt_tokens = len(encoding.encode(text))
    return prompt_tokens

def iso_time_to_datetime(iso_datetime):
    """change ISO time to datetime format"""
    return parser.parse(iso_datetime)


def get_path(*args):
    """get path to the config file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, *args)

def save_pickle(obj, pth):
    """"""
    dump(obj, pth)
def load_pickle(pth):
    """"""
    return load(pth)

def load_file(path):
    with open(path) as f:
        return f.read()

def chunks(iterable, size=5):
    """Batch list of elements, for example list of facebook pages to scan,  into chunk size of 5"""
    iterator = iter(iterable)
    for first in iterator:
        yield list(islice(iterator, size))


def date_today():
    """Returns today's date as a string"""
    today = datetime.now().strftime('%Y%m%d')
    # Create a table for today
    return f"{today}"


def split_docs(documents, chunk_size: int, chunk_overlap: int):
    """Split document into chunk_size chunks"""

    r_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "(?<=\. )", " ", ""]
        # default separators for this splitter with separator on '.' added
    )
    splits = r_splitter.split_documents(documents)
    return splits
