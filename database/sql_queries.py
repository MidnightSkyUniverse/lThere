"""
author: Ali Binkowska
Date: September 2023
Description: SQL queries for SQLite3 database management
"""

def select_unprocessed_facebook_urls():
    return """
        SELECT id, facebook_url FROM LocalResults
        WHERE processed is NULL and facebook_url!=''
        """

def select_processed_facebook_urls():
    return  """
        SELECT 
            id, 
            facebook_url 
        FROM 
            LocalResults
        WHERE 
            processed = 1 
            AND has_lunch_menu = 0 
            AND facebook_url != '';
        """

# def select_new_places_with_menu():
#     return """
#         SELECT LocalResults.id
#         FROM LocalResults
#         LEFT JOIN LunchSpecs ON LocalResults.id = LunchSpecs.local_result_id
#         WHERE LocalResults.has_lunch_menu = 1 AND LunchSpecs.menu_frequency IS NULL;
#     """

def select_fb_for_daily_scrapping():
    return """
        SELECT LocalResults.id, LocalResults.facebook_url
        FROM LocalResults
        LEFT JOIN LunchSpecs ON LocalResults.id = LunchSpecs.local_result_id
        WHERE LocalResults.has_lunch_menu = 1; 
    """
        #AND LunchSpecs.menu_frequency='daily';

def select_fb_post_by_id(table_name):
    return f"""
        SELECT *
        FROM {table_name}
        WHERE local_result_id = ?
    """

def select_local_results():
    return """
        SELECT LocalResults.title, LocalResults.website, LocalResults.facebook_url, LocalResults.instagram_url,
               LocalResults.phone, LocalResults.address, GpsCoordinates.latitude, GpsCoordinates.longitude,
               LocalResults.id
        FROM LocalResults
        LEFT JOIN GpsCoordinates ON LocalResults.id = GpsCoordinates.local_result_id
        WHERE LocalResults.id = ?;
        """

def select_lunch_specs():
    return """
       SELECT LocalResults.id, LunchSpecs.lunch_hours, LunchSpecs.lunch_price_range
        FROM LunchSpecs
        LEFT JOIN LocalResults ON LocalResults.id = LunchSpecs.local_result_id
        WHERE LocalResults.id = ?;
        """

def insert_or_update_lunch_specs():
    return """
        INSERT INTO LunchSpecs (lunch_price_range, lunch_hours, menu_frequency, local_result_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(local_result_id) DO UPDATE SET
            lunch_price_range = excluded.lunch_price_range,
            lunch_hours = excluded.lunch_hours,
            menu_frequency = excluded.menu_frequency;
    """

