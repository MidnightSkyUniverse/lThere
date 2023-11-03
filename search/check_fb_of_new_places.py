"""
author: Ali Binkowska
Date: August 2023
"""
import logging
import yaml

from .utils import (
    get_path,
    load_file,
    is_lunch_menu,
    chunks,
    fb_posts_scrapper,
    separate_posts,
    filter_out_old_posts,
)

from database.utils import (
    get_facebook_for_processing,
    update_places_with_status,
)

logging.basicConfig(level=logging.INFO, format="(%(levelname)s):  %(message)s")
log = logging.getLogger()

with open('config.yaml') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)


def check_fb(hours:int, processed:int, were_processed_before: bool):
    """
    First the function gets URLs from DB. Since for the time being, DB does not keep
    information whether the place offers lunch, I load a list manually for a scan with Apify
    """
    db_name = get_path('..', cfg['db']['dir'], cfg['db']['file'])

    with get_facebook_for_processing(db_name=db_name, processed=were_processed_before) as objects:
        if not objects:
            log.info(f"No new FB pages to scrap")
            return

        template = load_file(get_path('..', cfg['prompts']['dir'], cfg['prompts']['tag']))
        log.info(f"Exported {len(objects)} for FB scrapping")
        for batch_objects in chunks(objects, size=3):

            initial_results = fb_posts_scrapper(batch_objects)
            # separate posts that were correctly scrapped from those being empty records
            scrapped, empty = separate_posts(initial_results)
            # filter posts that have less than 14 days
            for post in scrapped:
                log.info(f"scrapped: {post.facebook_url}")
                log.info(f"scrapped: {post.fb_post.text}")
                log.info(f"scrapped: {post.fb_post.time}")
            posts_to_check = filter_out_old_posts(scrapped, hours)

            log.info(f"sites scrapped: {len(scrapped)}")
            log.info(f"sites empty: {len(empty)}")
            log.info(f"sites passed to LLM: {len(posts_to_check)}")

            # Pass posts to LLM
            results = is_lunch_menu(
                objects=posts_to_check,
                model_name=cfg['model_name'],
                template=template,
                chunk_size=cfg['chunk_size']['is_lunch'],
            )

            # Update database LocalResults:processed for the current batch
            # processed = 1 means it's first check of the FB
            update_places_with_status(db_name, results, processed=processed)
            log.info(f"Updated LocalResults:processed for {len(results)} LLM check records")

            # Handle the records that were not passed to LLM
            # Find sites that returned no results and mark them like the sites that failed LLM check
            results_empty = []
            for item in empty:
                results_empty.append((item, False, False))
            update_places_with_status(db_name, results_empty, processed=processed)
            log.info(f"Updated LocalResults:processed for {len(results_empty)} empty records")

            # Find sites that have posts older than 14 days and exclude them completely
            posts_too_old = filter_out_old_posts(scrapped, -24*14)
            results_old = []
            for item in posts_too_old:
                results_old.append((item, False, False))
            update_places_with_status(db_name, results_old, processed=9)
            log.info(f"Updated LocalResults:processed for {len(results_old)} old records")



