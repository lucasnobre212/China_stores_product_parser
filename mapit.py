
# mapIt.py - Launches a map in the browser using an address from the
# command line or clipboard.

import requests
import bs4
import re
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name(
                                'client_secret.json', scope)
client = gspread.authorize(creds)
# Initializing sheet
sh = client.open("Cópia de LMP")
sheet = sh.worksheet('DB')
name_sheet = sh.worksheet('Produtos')
# Get name column from Produtos worksheet
name_col_original = name_sheet.col_values(1)
# Removes blank strings
name_col = list(set(filter(None, name_col_original)))
name_col.remove('Nome')
# Get nem column from DB worksheet
db_name_col_original = sheet.col_values(1)

# System date
# dd/mm/yyyy format
date = (time.strftime("%d/%m/%Y"))

# Creates a list of sites
site = ['gearbest', 'banggood']


def get_col_lenght(col):
    col_lenght = len(list(filter(None, col)))
    return col_lenght


# Returns the beautifulsoup object of the product search page
def get_product_search_page(store, name):
    print('Running get_product_search_page')
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


def get_product(store, product_search_page):
    print("Running get_product")
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

def update_cell(name, value, store, date):
    db_name_col_lenght = get_col_lenght(db_name_col_original)
    sheet.update_cell(db_name_col_lenght + 1, 1, name)
    sheet.update_cell(db_name_col_lenght + 1, 2, value)
    sheet.update_cell(db_name_col_lenght + 1, 9, store)
    sheet.update_cell(db_name_col_lenght + 1, 10, date)


def main():
    db_name_col_lenght = get_col_lenght(db_name_col_original)
    for store in site:
        print("searching for store:" + store)
        for name in name_col:
            price = get_product(store, get_product_search_page(store, name))
            print("Updating cells")
            update_cell(name, price, store, date)
            db_name_col_lenght = db_name_col_lenght + 1

if __name__ == "__main__":
    main()
