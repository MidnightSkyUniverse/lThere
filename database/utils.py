import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Tuple

from dotenv import load_dotenv
load_dotenv()

from class_utils import (
    LocalResult,
    FBPost,
    LocalWithFB
)
from database.sql_queries import (
    select_unprocessed_facebook_urls,
    select_processed_facebook_urls,
    select_fb_for_daily_scrapping,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


# ********************
# Vectorstore Functions
# ********************

### sqlite3 operations functions
@contextmanager
def get_facebook_for_processing(db_name: str, processed: bool) -> Tuple[List[str], List[str]]:
    """return facebook pages registered in DB that has /processed equal NULL"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        # Query to get place_id and facebook_url where facebook_url is not null or empty
        if not processed:
            cursor.execute(select_unprocessed_facebook_urls())
        else:
            cursor.execute(select_processed_facebook_urls())

        rows = cursor.fetchall()

        local_with_fb_list = []
        for row in rows:
            if row[0] is not None and row[1] is not None:
                item = LocalWithFB(place_id=str(row[0]), facebook_url=row[1])
                local_with_fb_list.append(item)


        yield local_with_fb_list


@contextmanager
def get_fb_for_daily_scraping(db_name: str) -> List[LocalWithFB]:
    """return facebook pages registered in DB that are
    confirmed to have menu and requrie further processing"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        # Query to get place_id and facebook_url where facebook_url is not null or empty
        cursor.execute(select_fb_for_daily_scrapping())
        rows = cursor.fetchall()

        local_with_fb_list = []
        for row in rows:
            if row[0] is not None and row[1] is not None:
                item = LocalWithFB(place_id=str(row[0]), facebook_url=row[1])
                local_with_fb_list.append(item)

        yield local_with_fb_list




@contextmanager
def insert_fb_posts_into_db(
        db_name: str, db_table: str,
        fb_posts: list[FBPost],
        facebook_urls: list[str], ids: List[str],  # Changed place_ids to List[str] to match place_id type
):
    # Connect to the SQLite database (change the database name accordingly)
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        for url, local_result_id in zip(facebook_urls, ids):  # Renamed id to place_id for clarity

            posts = [x for x in fb_posts if x.facebook_url == url]

            if len(posts) > 0:
                for post in posts:
                    # print(f"Inserting post: {post.dict()}")
                    try:
                        # Insert each FBPost object into the FBPosts table
                        cursor.execute(f"""
                            INSERT INTO {db_table} (post_url, time, text, post_id, local_result_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, (post.url, post.time, post.text, post.post_id, local_result_id))
                    except sqlite3.Error as e:
                        log.error(f"Database error: {e}")


@contextmanager
def update_places_with_status(db_name: str, results: List[Tuple[LocalWithFB,bool, bool]], processed: int) -> None:
    try:
        # Connect to the SQLite database
        with get_db_connection(db_name) as conn:
            cursor = conn.cursor()

            # Loop through the results to update the database
            # for local_result_id, has_lunch_menu, example_post_id in results:
            for item, is_lunch, is_daily in results:
                # Prepare SQL query
                sql_query = """
                UPDATE LocalResults
                SET processed = ?,
                    has_lunch_menu = ?
                WHERE id = ?
                """
                # Execute SQL query
                cursor.execute(sql_query, (processed, is_lunch, item.place_id))

                if is_lunch:
                    """Only if there is lunch menu, update whether menu is published daily"""
                    sql_query = """
                            UPDATE LunchSpecs
                            SET menu_frequency = ?
                            WHERE local_result_id = ?
                            """

                    frequency = 'daily' if is_daily else None
                    cursor.execute(sql_query, (frequency, item.place_id))

    except sqlite3.Error as e:
        log.error(f"SQLite error: {e}")
        raise


@contextmanager
def insert_search_results(db_name:str,data: List[LocalResult]):
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        # SQL for inserting into LocalResults
        insert_local_results_sql = """
           INSERT INTO LocalResults (title, place_id, rating, reviews, price, type, address, open_state, phone, 
                                     website, facebook_url, instagram_url, reviews_link, photos_link)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
           """

        # SQL for inserting into other tables
        insert_gps_coordinates_sql = """
           INSERT INTO GpsCoordinates (local_result_id, latitude, longitude)
           VALUES (?, ?, ?);
           """

        insert_operating_hours_sql = """
           INSERT INTO OperatingHours (local_result_id, day, hours)
           VALUES (?, ?, ?);
           """

        insert_service_options_sql = """
           INSERT INTO ServiceOptions (local_result_id, option_name, option_value)
           VALUES (?, ?, ?);
           """

        insert_types_sql = """
           INSERT INTO Types (local_result_id, type)
           VALUES (?, ?);
           """

        for result in data:

            website = result.website
            facebook_url = None
            instagram_url = None
            latitude = result.gps_coordinates.latitude
            longitude = result.gps_coordinates.longitude

            if "facebook.com" in website:
                facebook_url = website
                website = None
            elif "instagram.com" in website:
                instagram_url = website
                website = None

            # Insert into LocalResults
            try:
                cursor.execute(insert_local_results_sql, (
                    result.title, result.place_id, result.rating, result.reviews,
                    result.price, result.type, result.address, result.open_state,
                    result.phone, website, facebook_url, instagram_url, result.reviews_link, result.photos_link
                ))
            except sqlite3.IntegrityError:
                log.warning(f"Duplicate place_id found for {result.title}. Skipping insertion.")
                continue

            # Get the last inserted ID
            last_row_id = cursor.lastrowid

            # Insert into GpsCoordinates
            cursor.execute(insert_gps_coordinates_sql, (
                last_row_id, latitude, longitude
            ))

            # Insert into OperatingHours
            for day, hours in result.operating_hours.items():
                cursor.execute(insert_operating_hours_sql, (
                    last_row_id, day, hours
                ))

            # Insert into ServiceOptions
            for option_name, option_value in result.service_options.items():
                cursor.execute(insert_service_options_sql, (
                    last_row_id, option_name, option_value
                ))

            # Insert into Types
            for t in result.types:
                cursor.execute(insert_types_sql, (
                    last_row_id, t
                ))


@contextmanager
def clean_db_of_places(db_name: str, types_patterns: List[str]):

    # Connect to the SQLite database
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        # Step 1: Identify local_result_ids that do not have any type in TYPES_OF_PLACES
        cursor.execute('SELECT DISTINCT local_result_id FROM Types')
        all_local_result_ids = [row[0] for row in cursor.fetchall()]

        to_remove_ids = []
        for local_result_id in all_local_result_ids:
            cursor.execute('SELECT type FROM Types WHERE local_result_id = ?', (local_result_id,))
            types = [row[0] for row in cursor.fetchall()]
            if not any(allowed_type in types for allowed_type in types_patterns):
                to_remove_ids.append(local_result_id)

        # Step 2: Delete the corresponding rows from all tables
        for local_result_id in to_remove_ids:
            cursor.execute('DELETE FROM LocalResults WHERE id = ?', (local_result_id,))
            cursor.execute('DELETE FROM GpsCoordinates WHERE local_result_id = ?', (local_result_id,))
            cursor.execute('DELETE FROM OperatingHours WHERE local_result_id = ?', (local_result_id,))
            cursor.execute('DELETE FROM ServiceOptions WHERE local_result_id = ?', (local_result_id,))
            cursor.execute('DELETE FROM Types WHERE local_result_id = ?', (local_result_id,))


### CONNECT, CREATE & DROP DB ###from contextlib import contextmanager

@contextmanager
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    try:
        yield conn
    except sqlite3.Error as e:
        log.error(f"SQLite error: {e}")
        conn.rollback()
    finally:
        conn.commit()
        conn.close()


@contextmanager
def create_database_from_schema(db_name, schema_file):
    """ Create DB"""
    # Connect to the SQLite database
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        # Read the schema from the file
        with open(schema_file, 'r') as f:
            schema = f.read()

        # Execute the schema to create the tables
        cursor.executescript(schema)


@contextmanager
def update_database(db_name):
    """
    Add new columns to store inforaation about FB pages
    :param db_name:
    :return:
    """
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        schema_changes = [
            # "ALTER TABLE LocalResults ADD COLUMN processed INTEGER DEFAULT 0",
            # "ALTER TABLE LocalResults ADD COLUMN has_lunch_menu INTEGER DEFAULT 0",
            # "ALTER TABLE LocalResults ADD COLUMN menu_frequency TEXT",
        ]

        # Execute each schema change separately
        for change in schema_changes:
            cursor.execute(change)


@contextmanager
def drop_tables(db_name):
    """ Drop DB"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()

        # Drop tables
        cursor.execute("DROP TABLE IF EXISTS Types;")
        cursor.execute("DROP TABLE IF EXISTS ServiceOptions;")
        cursor.execute("DROP TABLE IF EXISTS OperatingHours;")
        cursor.execute("DROP TABLE IF EXISTS GpsCoordinates;")
        cursor.execute("DROP TABLE IF EXISTS LocalResults;")
        cursor.execute("DROP TABLE IF EXISTS FBPosts;")
        cursor.execute("DROP TABLE IF EXISTS LunchSpecs;")