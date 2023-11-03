"""
Author: Ali Binkowska
Date: August 2023

"""
import os
os.environ['NUMEXPR_MAX_THREADS'] = '8'
os.environ['NUMEXPR_NUM_THREADS'] = '4'


import warnings
from search.check_fb_of_new_places import check_fb
from search.search_for_new_places import search
from search.collect_menu import collect



_steps = [
    # Uses SerpAPI to query results based on GPS coordinates, upload to DB
    # 'search_for_new_places',

    # Extract FB with Apify, scrap posts, identify new places with lunch, save extracted lunch menu for processing
    # 'check_fb_of_new_places',

    # Recheck pages that were scanned
    # 'recheck_fb_pages'

    # collect daily menu, store records in chromaDB
    'collect_menu'
]


if __name__ == "__main__":
    warnings.filterwarnings("ignore")

    if 'search_for_new_places' in _steps:
        search()

    if 'check_fb_of_new_places' in _steps:
        hours = 336
        processed = 1
        were_processed = False
        check_fb(hours=hours, processed=processed, were_processed_before=were_processed)

    if 'recheck_fb_pages' in _steps:
        hours = 36
        processed = 2
        were_processed = True
        check_fb(hours=hours, processed=processed, were_processed_before=were_processed)

    if 'collect_menu' in _steps:
        collect()
