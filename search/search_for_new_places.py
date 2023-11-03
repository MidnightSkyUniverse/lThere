"""
author: Ali Binkowska
Date: August 2023

Collect grid search results based on given coordinates (currently Wroclaw).
Store search results to local file. Using SerpAPI
"""
import logging
import yaml

from .utils import (
    get_path,
    generate_grid_points,
    serpapi_query,
)
from database.utils import (
    insert_search_results,
    clean_db_of_places,
)

with open('config.yaml') as f:
    cfg =  yaml.load(f, Loader=yaml.FullLoader)

logging.basicConfig(filename='app.log', level=logging.INFO)
log = logging.getLogger()

def search():

    # Generate grid points for search
    grid_points = generate_grid_points(cfg['coordinates']['Wroclaw'])

    # Collect results
    all_results = []
    for lat, lon in grid_points:
        local_results = serpapi_query(lat, lon)
        log.info(f"search: local_results amount: {len(local_results)}")
        all_results.extend(local_results)


    db_name = get_path('..', cfg['db']['dir'], cfg['db']['file'])
    try:
        insert_search_results(data=all_results, db_name=db_name)
        # log.info(f"Search results has been stored to DB {db_name}")
    except Exception as err:
        log.error(f"Error when inserting data to DB: {err}")
        raise

    # For now separate step to clean DB of places that are not serving food
    types_patterns = cfg['TYPES_OF_PLACES']
    try:
        clean_db_of_places(db_name=db_name, types_patterns=types_patterns)
        log.info(f"DB {db_name} has been cleaned up")
    except Exception as err:
        log.error(f"Error when cleaning DB: {err}")
        raise

