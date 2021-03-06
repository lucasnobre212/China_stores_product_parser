#! python3.
# mapIt.py - Launches a map in the browser using an address from the
# command line or clipboard.

import requests
import bs4
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
import logging
import queue
from threading import Thread


def get_spreadsheet():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name(
                                    'client_secret.json', scope)
    client = gspread.authorize(creds)
    sh = client.open("Cópia de LMP")
    return sh


# Returns the beautifulsoup object of the product search page
def get_product_search_page(store, name):
    # Split the string, making it a list of words
    name_split = name.split()
    if store == 'gearbest':
        base_url = 'https://www.gearbest.com/'
        # Creates a forLoop to add - the more words we have
        search_url = ''
        for i in range(0, len(name_split)):
            search_url = search_url + name_split[i] + '-'
        # Finishes the full url
        product_search_page = base_url + search_url + '_gear'
    elif store == 'banggood':
        base_url = 'https://www.banggood.com/search/'
        # Creates a forLoop to add - the more words we have
        search_url = ''
        for i in range(0, len(name_split)):
            search_url = search_url + name_split[i] + '-'
        # Finishes the full url
        product_search_page = base_url + search_url + '.html'
    return product_search_page


def download_page(html):
    # Downloads the search html
    res = requests.get(html)
    # Creates a beautifulsoup object of the page
    product_search_page_object = bs4.BeautifulSoup(res.text, "html.parser")
    return product_search_page_object


def get_product_price(store, product_search_page):
    if store == 'gearbest':
        # Select the rank 1(most relevant) product
        rank_1_product = product_search_page.select(
                    'div.pro_inner.logsss_event_ps span.my_shop_price')[0]
        product_price = rank_1_product.get('orgp')
    elif store == 'banggood':
        # Select the rank 1(most relevant) product
        rank_1_product = product_search_page.select(
            'ul.goodlist_1 li span.price.wh_cn')[0]
        # Get the rank 1 product page
        product_price = rank_1_product.get('oriprice')
    return product_price


def get_product_values(site, name_list, date):
    # Set queue to use in thread
    q = queue.Queue()
    page_list = []
    for store in site:
        for name in name_list:
            search_page_html = get_product_search_page(store, name)
            q.put((search_page_html, store, name, date))
        for i in range(5):
            t = DownloadWorker(q)
            t.setDaemon(True)
            t.start()
    # Finishes all threads
    q.join()


def batch_update_cells(sheet, col_lenght, first_col, list, last_col):
    logging.debug('Updating cell values')
    cell_list = sheet.range(
        col_lenght + 2, first_col, col_lenght + len(list), last_col)
    for i, val in enumerate(list):
        cell_list[i].value = val
    sheet.update_cells(cell_list)


class DownloadWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
    def run(self):
        while True:
            global data_list
            link, store, name, date = self.queue.get()
            search_page = download_page(link)
            logging.debug(store)
            price = get_product_price(store, search_page)
            data_list.extend([name, price, store, date])
            self.queue.task_done()


def main():
    global data_list
    logging.basicConfig(level=logging.DEBUG,
         format=' %(asctime)s - %(levelname)s - %(message)s')
    # Start important variables
    site = ['gearbest', 'banggood']
    name_list = []
    data_list = []
    date = (time.strftime("%d/%m/%Y"))

    # Start reading and manipulating sheet values
    sheet = get_spreadsheet().worksheet('DB')
    values = sheet.get_all_records()
    col_len = len(values)
    # Get products names list
    for i in range(0, col_len):
        if values[i]['Produtos']:
            name_list.append(values[i]['Produtos'])
    # Creates threads and populate data_list
    get_product_values(site, name_list, date)
    # Update cells
    batch_update_cells(sheet, col_len, 1, data_list, 4)

if __name__ == "__main__":
    main()