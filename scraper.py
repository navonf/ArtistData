from bs4 import BeautifulSoup
from queue import Queue
import grequests
import requests
import threading
import json
import lxml
import re
import time
import json

# public variables
songs_names_list = []
songs_ratings_list = []
base_url = 'https://www.hotnewhiphop.com'
artist_name = ''
artist_data_lock = threading.Lock()

def base_call(artistname):
    # Test data
    # Artist: Chief Keef
    artist = '/' + artistname
    global artist_name

    artist_data = []
    artist_all_songs_page_count = 0

    songs_list_base_url = base_url + artist + '/songs/'
    songs_list_base_req = requests.get(songs_list_base_url)
    songs_list_base_soup = BeautifulSoup(songs_list_base_req.text, 'lxml')

    if 'Songs' in songs_list_base_soup.find('title').string:
        artist_name = songs_list_base_soup.find('title').string[:-6]
    else: artist_name = songs_list_base_soup.find('title').string

    print(artist_name)

    # get the page count so we can iterate through pages.
    artist_all_songs_page_count = get_all_page_count(songs_list_base_soup, artist_data, songs_list_base_url)
    print(artist_data)
    return artist_data


# iterate through the artists with multiple pages.
def iterate_pages(soup, page_count, artist_data):

    for i in range(0, int(page_count)+1):
        get_page_data(soup, artist_data)

        if soup.find('a', class_="next-page", href=True) is not None:
            next_page_url = base_url + soup.find('a', class_="next-page", href=True)['href']
            next_page_req = requests.get(next_page_url)
            soup = BeautifulSoup(next_page_req.text, 'lxml')


def batch_job(worker, soup, artist_data, next_page_urls_list):
    with artist_data_lock:
        curr = next_page_urls_list.get()
        print(curr)
        req = requests.get(curr)
        soup_thread = BeautifulSoup(req.text, 'lxml')

        relevant_songs = list(filter(lambda x: True if artist_name in str(x.find('div', class_="endlessScrollCommon-artist")) else False,
        soup_thread.find_all('div', class_="endlessScrollCommon-title song")))

        songs_on_page = []

        for song in relevant_songs:
            songs_on_page.append(base_url + str(song.find('a', class_="endlessScrollCommon-title-anchor")['href']))

        artist_data.append(songs_on_page)




def threader(q, soup, artist_data, next_page_urls_list):
    while True:
        worker = q.get()
        batch_job(worker, soup, artist_data, next_page_urls_list)
        q.task_done()


def iterate_pages_batch(soup, page_count, artist_data, songs_list_base_url):

    next_page_urls_list = Queue()
    next_page_urls_list.put(songs_list_base_url)


    for i in range(1, int(page_count)+1):
        next_page_urls_list.put(songs_list_base_url + str(i) + '/')

    # TODO: spawn a thread for each link in the list
    #  shared varilable that will be updated by all the threads
    # artist_data_lock = threading.Lock()
    q = Queue()

    for x in range(next_page_urls_list.qsize()):
        t = threading.Thread(target = threader, kwargs={'q' : q, 'soup' : soup, 'artist_data' : artist_data, 'next_page_urls_list' : next_page_urls_list})
        t.daemon = True
        t.start()

    for worker in range(next_page_urls_list.qsize()):
        q.put(worker)

    q.join()



def get_single_page_data(soup, artist_data):
	songs_on_page = list(map(lambda u: base_url + u['href'],
	soup.find_all('a', class_="cover-title endlessScrollCommon-title-anchor song", href=True)))

	reqs = (grequests.get(url) for url in songs_on_page)
	resp = grequests.map(reqs)

	for r in resp:
		song_soup = BeautifulSoup(r.text, 'lxml')
		get_song_data(song_soup, artist_data)


# get singular songs page data, contains up to 20 per page.
def get_page_data(soup, artist_data):
    # filter for the songs that are relevant.
    # Removes songs not by the artist we want.
    relevant_songs = list(filter(lambda x: True if artist_name in str(x.find('div', class_="endlessScrollCommon-artist")) else False,
    soup.find_all('div', class_="endlessScrollCommon-title song")))

    songs_on_page = []

    for song in relevant_songs:
        songs_on_page.append(base_url + str(song.find('a', class_="endlessScrollCommon-title-anchor")['href']))

    reqs = (grequests.get(url) for url in songs_on_page)
    resp = grequests.map(reqs)

    for r in resp:
        song_soup = BeautifulSoup(r.text, 'lxml')
        get_song_data(song_soup, artist_data)


def get_song_data(soup, artist_data):
    data = {}
    data['song'] = soup.find('span', class_="song-info-title").string
    data['rating'] = re.findall('(\d+(\.\d)?%)', str(soup.find('div', class_="interactiveReview-userTooltip-percentage")))[0][0]
    data['link'] = soup.find('meta', property="og:url")['content']

    artist_data.append(data)


# gets all the pages the artist has.
def get_all_page_count(soup, artist_data, songs_list_base_url):
    # find the link in which the page count is contained.
    if soup.find('a', class_="last-page", href=True) is None:
        get_single_page_data(soup, artist_data)
    else:
        page_link = soup.find('a', class_="last-page", href=True)['href']

        # extract the digit in the string.
        page_count = int(re.findall('\d+', page_link)[0])

        # do batch requests if the artist has more than 5 pages
        iterate_pages_batch(soup, page_count, artist_data, songs_list_base_url)
        # else: iterate_pages(soup, page_count, artist_data)


# if __name__ == '__main__':
#     base_call('migos')
