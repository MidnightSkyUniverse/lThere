"""
author: Ali Binkowska
Date: August 2023
Description: collect daily menu, store it in todays vector DB
"""

import logging

import yaml
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings

from database.utils import (
    get_fb_for_daily_scraping,
)
from search.utils import (
    chunks,
    extract_lunch_menu,
    fb_posts_scrapper,
    filter_out_old_posts,
    get_path,
    load_file,
    db_create,
    date_today,
    separate_posts,
)

with open('config.yaml') as f:
    cfg =  yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(
    level=logging.INFO, format="(%(levelname)s) : %(asctime)s :  %(message)s",
    datefmt='%m/%d %H:%M:%S'
)
log = logging.getLogger()


from langchain.schema.document import Document

def create_document(meal, price, url):
    page_content = meal
    metadata = {'price': price, 'url': url}
    return Document(page_content=page_content, metadata=metadata)


def collect():
    """
    Scrap daily menu, create CMS entry tables
    """
    # Create today's collection in vector DB
    db_name = get_path('..', cfg['db']['dir'], cfg['db']['file'])
    vector_db_pth = get_path('..', cfg['db']['dir'], cfg['db']['vector_db'])
    embedding = SentenceTransformerEmbeddings(model_name=cfg['embedding_model_name'])


    with get_fb_for_daily_scraping(db_name=db_name) as objects:
        if not objects:
            log.info(f"Collect: No facebook pages  to scrap. END")
            return

        template_extract = load_file(get_path('..', cfg['prompts']['dir'], cfg['prompts']['extract_menu']))
        log.info(f"Exported {len(objects)} for FB scrapping")
        for batch_objects in chunks(objects, size=1):

            initial_results = fb_posts_scrapper(batch_objects)
            # separate posts that were correctly scrapped from those being empty records
            scrapped, empty = separate_posts(initial_results)
            # filter posts that have less than 14 days
            for post in scrapped:
                log.info(f"scrapped: {post.facebook_url}")
                log.info(f"scrapped: {post.fb_post.text}")
                log.info(f"scrapped: {post.fb_post.time}")
            posts_to_check = filter_out_old_posts(scrapped, 7)

            log.info(f"posts fetched: {len(initial_results)}")
            log.info(f"posts filtered: {len(posts_to_check)}")

            if posts_to_check:

                results = extract_lunch_menu(
                    objects=posts_to_check,
                    model_name=cfg['model_name'],
                    template=template_extract,
                    chunk_size=cfg['chunk_size']['extract_lunch'],
                )
                log.info(f"posts with menu: {len(results)}")

                documents = []  # List to hold Document instances

                for item, meals in results:
                    for meal_info in meals:
                        if meal_info['meal']:
                            url = item.fb_post.facebook_url
                            meal = meal_info['meal']
                            if meal_info['price']:
                                price = meal_info['price']

                            document = create_document(meal, price, url)
                            documents.append(document)

                for x in documents:
                    log.info(x)

                try:
                    vector_db = db_create(vector_db_pth + date_today(), embedding, documents)
                except:
                    raise

                log.info(("There are", vector_db._collection.count(), "in the collection"))
            else:
                log.info("No recent posts were captured")

