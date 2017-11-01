
# mapIt.py - Launches a map in the browser using an address from the
# command line or clipboard.

import requests
import bs4
import re
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials
import logging


def get_sheet():
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
        final_search = base_url + search_url + '_gear'
        # Downloads the search html
        res = requests.get(final_search)
    elif store == 'banggood':
        base_url = 'https://www.banggood.com/search/'
        # Creates a forLoop to add - the more words we have
        search_url = ''
        for i in range(0, len(name_split)):
            search_url = search_url + name_split[i] + '-'
        # Finishes the full url
        final_search = base_url + search_url + '.html'
        # Downloads the search html
        res = requests.get(final_search)
    # Creates a beautifulsoup object of the page
    product_search_page = bs4.BeautifulSoup(res.text, "html.parser")
    return product_search_page


def get_product_price(store, product_search_page):
    if store == 'gearbest':
        # Select the rank 1(most relevant) product
        product_tag = product_search_page.select(
                    'div.pro_inner.logsss_event_ps')
        for i in range(0, len(product_tag)):
            if re.search("('rank':1,)", str(product_tag[i])):
                rank_1_tag = product_tag[i]
        # Get the rank 1 product page
        rank_1_product = rank_1_tag.select('span.my_shop_price')[0]
        product_price = rank_1_product.get('orgp')
    elif store == 'banggood':
        # Select the rank 1(most relevant) product
        product_tag = product_search_page.select('ul.goodlist_1 li')[0]
        # Get the rank 1 product page
        rank_1_product = product_tag.select('span.price.wh_cn')[0]
        product_price = rank_1_product.get('oriprice')
    return product_price


# # Get the rank 1 product page
# # def get_product_page(page):
# #     # Download the html
# #     res = requests.get(page)
# #     # Creates a BeautifulSoup class
# #     site_page = bs4.BeautifulSoup(res.text, "html.parser")
# #     # Select a html tag and attribute. Using [0] is important
# #     # for choosing the tag
# #     try:
# #         price_tag = site_page.select('b#unit_price')[0]
# #     except:
# #         price_tag = site_page.select('span#unit_price')[0]
# #     # data-orgp is the price value($)
# #     price = price_tag.get('data-orgp')
# #     return price

def batch_update_cells(sheet, col_lenght, first_col, list, last_col):
    logging.debug('Updating cell values')
    cell_list = sheet.range(
        col_lenght + 1, first_col, col_lenght + len(list), last_col)
    for i, val in enumerate(list):
        cell_list[i].value = val
    sheet.update_cells(cell_list)


def main():
    get_sheet()
    logging.basicConfig(level=logging.DEBUG,
                        format=' %(asctime)s - %(levelname)s - %(message)s')
    # logging.disable(logging.CRITICAL)
    logging.debug('Start of program')
    # Initializing sheet
    sheet = get_sheet().worksheet('DB')
    values = sheet.get_all_records()
    col_len = len(values)
    name_list = []
    date = (time.strftime("%d/%m/%Y"))
    # Creates a list of sites
    site = ['gearbest', 'banggood']
    data_list = []
    # Get products names
    for i in range(0, col_len):
        if values[i]['Produtos']:
            name_list.append(values[i]['Produtos'])

    logging.debug('Values %s' % name_list)
    # Fills the lists with values
    for store in site:
        for name in name_list:
            logging.debug('Running get_product_search_page')
            search_page = get_product_search_page(store, name)
            logging.debug('Running get_product_price')
            price = get_product_price(store, search_page)
            data_list.extend([name, price, store, date])
    batch_update_cells(sheet, col_len, 1, data_list, 4)
    logging.debug('End of Program')
if __name__ == "__main__":
    main()
