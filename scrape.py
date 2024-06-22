from bs4 import BeautifulSoup
import requests
import psycopg2
from datetime import datetime
from settings import *

# get the canada computers html for the specified search terms
search = "rtx 4070"
page_to_scrape = requests.get("https://www.canadacomputers.com/search/results_details.php?language=en&keywords=" + search.replace(" ", "+") + "&cpath=43")
soup = BeautifulSoup(page_to_scrape.content, 'html5lib')

# connect to postgresql database
connection = psycopg2.connect(database=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD, host=DATABASE_HOST, port=DATABASE_PORT)
cursor = connection.cursor()

def update_prices():
    # the product info is in div tags
    products = soup.select('div.px-0.col-12.productInfoSearch.pt-2')

    today = datetime.now()

    for element in products:
        # get the name and price of each product
        item_name = element.find("span", attrs={"class":["text-dark", "d-block", "productTemplate_title"]})
        variable = item_name.find("a", attrs={"class":["text-dark", "text-truncate_3"]})
        price = element.findAll("span", attrs={"class":["d-block", "mb-0", "pq-hdr-product_price"]})

        # save the product info to the database
        if search in variable.text.lower():
            cursor.execute(f"""INSERT INTO price_records VALUES (TIMESTAMP '{today}', '{variable.text}', {price[1].text[1:].replace(",", "")});""")

# display the records currently in the db
def view_database():
    cursor.execute("SELECT * from price_records;")
    records = cursor.fetchall()

    for row in records:
        print(row)

view_database()

# save database changes and close connection
connection.commit()
cursor.close()
connection.close()
