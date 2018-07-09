from bs4 import BeautifulSoup, SoupStrainer

import grequests
import requests
import json
import lxml
import re
import time

# public variables
songs_names_list = []
songs_ratings_list = []
base_url = 'https://www.hotnewhiphop.com'

def main():
    start = time.time()
    base_call()
    print("Took: ", (time.time() - start) )

def base_call():
    # Test data
    # Artist: Chief Keef
    artist = '/chiefkeef'
    artist_all_songs_page_count = 0

    songs_list_base_url = base_url + artist + '/songs/'
    songs_list_base_req = requests.get(songs_list_base_url)
    songs_list_base_soup = BeautifulSoup(songs_list_base_req.text, 'lxml', parse_only=SoupStrainer('a'))

    # get the page count so we can iterate through pages.
    artist_all_songs_page_count = get_all_page_count(songs_list_base_soup)


# iterate through the artists with multiple pages.
def iterate_pages(soup, page_count):
    for i in range(0, int(page_count)+1):
        get_page_data(soup)

        if soup.find('a', class_="next-page", href=True) is not None:
            next_page_url = base_url + soup.find('a', class_="next-page", href=True)['href']
            # print(next_page_url)
            next_page_req = requests.get(next_page_url)
            soup = BeautifulSoup(next_page_req.text, 'lxml', parse_only=SoupStrainer('a'))
            

# get singular songs page data, contains up to 20.
def get_page_data(soup):
    # gang
    songs_on_page = list(map(lambda u: base_url + u['href'],
        soup.find_all('a', class_="cover-title endlessScrollCommon-title-anchor song", href=True)))

    reqs = (grequests.get(url) for url in songs_on_page)
    resp = grequests.map(reqs)

    for r in resp:
        song_soup = BeautifulSoup(r.text, 'lxml', parse_only=SoupStrainer("span"))
        get_song_data(song_soup)


def get_song_data(soup):
    print(soup.find('span', class_="song-info-title").string)


# gets all the pages the artist has.
def get_all_page_count(soup):

    # find the link in which the page count is contained.
    if soup.find('a', class_="last-page", href=True) is None:
        get_page_data(soup)
    else:
        page_link = soup.find('a', class_="last-page", href=True)['href']
        # extract the digit in the string.
        print("multiple pages")
        iterate_pages(soup, re.findall('\d+', page_link)[0])



if __name__ == "__main__": main()
