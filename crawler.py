import requests
import re
from bs4 import BeautifulSoup
import sqlite3

# TODO: Organize / refactor this code!!!

# This script assumes you already have Tor installed and running

# Snagged from StackOverflow, haven't tested it!
def get_tor_session():
    session = requests.session()
    # My Tor daemon is on port 9150
    # On your computer, it's more likely 9050
    session.proxies = {'http':  'socks5h://127.0.0.1:9150',
                       'https': 'socks5h://127.0.0.1:9150'}
    return session

def get_url_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Get the title of the web page
    title = soup.title.string

    # Find all the visible text within the web page
    visible_text = soup.get_text()

    return title, visible_text


def initialize_onion_db_conn():
    conn = sqlite3.connect('onion_service_data.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS onion_services (
            onion_url TEXT PRIMARY KEY,
            dead_link INTEGER,
            title TEXT,
            content TEXT,
            last_crawled DATE
        )
    ''')

    return conn

# We start out with the URL for tor.taxi, a Tor link aggregator
seed_url = "tortaxi2dev6xjwbaydqzla77rrnth7yn2oqzjfmiuwn5h6vsk2a4syd.onion"

# This regular expression will help us extract Tor links to crawl
# ChatGPT actually wrote this regex for me!
onion_regex = re.compile("[a-z0-9]+.onion")

# TODO: (next video) Find link that we haven't searched in the longest time
def crawl(url, session=None, conn=None):
    try:
        if session is None:
            session = get_tor_session()
        if conn is None:
            conn = initialize_onion_db_conn()
    except:
        print('its breaking in the boilerplate')
    
    cursor = conn.cursor()

    try:
        html = session.get('http://' + url).text
        title, content = get_url_content(html)
        row = (url, 0, title, content, None)
        cursor.execute('''
            INSERT OR REPLACE INTO onion_services (onion_url, dead_link, title, content, last_crawled)
            VALUES (?, ?, ?, ?, ?)
        ''', row)
        conn.commit()

        links = onion_regex.findall(html)
        # TODO: (next video) filter out links that are already in database!
        # Add the links to the database, instead of recursing on all of them!
        # Finally, I'll be able to run various instances of crawl using multiprocessing
        # (and explain why multiprocessing instead of threading, GIL)
        for l in links:
            print(l)
            crawl(l, session, conn)
    except Exception as e:
        print('dead url:', url)
        row = (url, 1, None, None, None)
        cursor.execute('''
            INSERT OR REPLACE INTO onion_services (onion_url, dead_link, title, content, last_crawled)
            VALUES (?, ?, ?, ?, ?)
        ''', row)
        conn.commit()

crawl(seed_url)
