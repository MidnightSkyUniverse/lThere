import os
import requests
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('CRAWLBASE_API_KEY_2')

def get_crawlbase_account_info(token: str):
    """Check crawlbase usage"""

    url = f"https://api.crawlbase.com/account?token={token}&product=crawling-api"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print(f"Error: {response.status_code} - {response.text}")


get_crawlbase_account_info(token)
