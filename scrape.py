from bs4 import BeautifulSoup
import requests
import psycopg2
from datetime import date, datetime
from settings import *

from plotly.offline import plot
from plotly.graph_objs import Scatter
import plotly.express as px


def connect_to_database():
    # connect to postgresql database
    connection = psycopg2.connect(database=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PASSWORD, host=DATABASE_HOST, port=DATABASE_PORT)
    cursor = connection.cursor()

    return cursor, connection

def get_pinned():
    cursor, _ = connect_to_database()

    cursor.execute(f"SELECT product_name FROM pinned_items;")
    pinned_products = cursor.fetchall()
    cursor.execute(f"SELECT url FROM pinned_items;")
    pinned_urls = cursor.fetchall()

    for i in range(len(pinned_products)):
        item_as_list = list(pinned_products[i])
        cursor.execute(f"SELECT price FROM pinned_item_price_records WHERE product_name='{item_as_list[0]}' ORDER BY date;")
        price = cursor.fetchone()
        pinned_products[i] = pinned_products[i] + tuple(price) + pinned_urls[i]

    cursor.close()
    return pinned_products

def get_graph(name):
    cursor, _ = connect_to_database()

    cursor.execute(f"SELECT date, price FROM pinned_item_price_records WHERE product_name='{name}';")
    records = cursor.fetchall()
    zipped_records = list(map(list, zip(*records)))
    dates = zipped_records[0]
    prices = zipped_records[1]

    fig = px.line(x=dates, y=prices, markers=True, width=1000, height=500)
    fig.update_xaxes(type='category')
    fig.update_layout(xaxis_title="Date", yaxis_title="Price ($CAD)")
    prices_graph_div = plot(fig, output_type='div')

    #prices_graph_div = plot([Scatter(x=dates, y=prices)], output_type='div')
    cursor.close()
    return prices_graph_div

def updatePinnedPrices(): # schedule to call this each day to update all pinned prices
    todayDate = date.today().isoformat()
    cursor, connection = connect_to_database()

    cursor.execute("SELECT DISTINCT product_name FROM pinned_items;")

    records = cursor.fetchall()
    for row in records:
        product_name_list = list(row)
        cursor.execute(f"SELECT url FROM pinned_items WHERE product_name='{product_name_list[0]}';")
        url = list(cursor.fetchone())[0]
        page_to_scrape = requests.get(url)
        soup = BeautifulSoup(page_to_scrape.content, 'html5lib')

        cursor.execute(f"SELECT date FROM pinned_item_price_records WHERE product_name='{product_name_list[0]}';")
        dates = cursor.fetchall()

        dates_list = []

        for i in range(len(dates)):
            dates_list.append(list(dates[i])[0].isoformat())

        if len(dates_list) == 0 or todayDate not in dates_list:
            price = soup.findAll("span", attrs={"class":"h2-big"})[0].text
            cursor.execute(f"""INSERT INTO pinned_item_price_records VALUES (DATE '{todayDate}', '{product_name_list[0]}', {price.replace("$", "").replace(",", "")});""")
            connection.commit()
        else:
            print("Price already logged on " + str(todayDate))
    
    cursor.close()
    connection.close()

def saveCurrentPrice(name, price):
    todayDate = date.today()
    cursor, connection = connect_to_database()

    cursor.execute(f"SELECT date FROM pinned_item_price_records WHERE product_name='{name}';")
    dates = cursor.fetchall()
    if len(dates) == 0 or todayDate not in dates[0]:
        cursor.execute(f"INSERT INTO pinned_item_price_records VALUES (DATE '{todayDate.isoformat()}', '{name}', {price});")
        connection.commit()
    else:
        print("Price already logged on " + str(todayDate.isoformat()))

    cursor.close()

def pin(name, price, url):
    currentDT = datetime.now()
    cursor, connection = connect_to_database()

    cursor.execute(f"SELECT COUNT(1) FROM pinned_items WHERE product_name='{name}';")
    results = cursor.fetchone()
    if results[0] >= 1:
        unpin(name)
        return

    cursor.execute(f"INSERT INTO pinned_items VALUES (TIMESTAMP '{currentDT}', '{name}', '{url}');")
    connection.commit()

    saveCurrentPrice(name, price)

    connection.commit()
    cursor.close()
    connection.close()

def unpin(name):
    cursor, connection = connect_to_database()

    cursor.execute(f"DELETE FROM pinned_items WHERE product_name='{name}';")
    connection.commit()

def update_prices(search, cpath):
    cursor, connection = connect_to_database()
    cursor.execute("TRUNCATE TABLE search_results;")
    connection.commit()

    if cpath != "":
        cpath = "&cpath=" + cpath

    # get the canada computers html for the specified search terms
    page_to_scrape = requests.get("https://www.canadacomputers.com/search/results_details.php?language=en&keywords=" + search.replace(" ", "+") + cpath)
    soup = BeautifulSoup(page_to_scrape.content, 'html5lib')

    # the product info is in div tags
    products = soup.select('div.px-0.col-12.productInfoSearch.pt-2')

    today = datetime.now()

    for element in products:
        # get the name and price of each product
        item_name = element.find("span", attrs={"class":["text-dark", "d-block", "productTemplate_title"]})
        variable = item_name.find("a", attrs={"class":["text-dark", "text-truncate_3"]})
        price = element.findAll("span", attrs={"class":["d-block", "mb-0", "pq-hdr-product_price"]})

        # save the product info to the database
        cursor.execute(f"""INSERT INTO search_results VALUES (TIMESTAMP '{today}', '{variable.text}', {price[1].text[1:].replace(",", "")}, '{variable.get('href')}');""")

    connection.commit()

    cursor.execute("SELECT product_name, price, url from search_results;")
    records = cursor.fetchall()
    records.sort(key=lambda x: x[1]) # sort by price

    cursor.close()
    connection.close()
    return records

def get_lowest():
    cursor, _ = connect_to_database()

    cursor.execute("SELECT * FROM search_results WHERE price = (SELECT MIN(price) FROM search_results);")
    min_price = cursor.fetchone()

    cursor.close()
    return min_price

# display the records currently in the db
def view_database():
    cursor, _ = connect_to_database()

    cursor.execute("SELECT * from search_results;")
    records = cursor.fetchall()

    for row in records:
        print(row)
    
    cursor.close()

if __name__ == "__main__":
    cursor, connection = connect_to_database()

    #search = input("\nSearch for a product: ")

    #if search == None or search.strip() == "":
    #    search = "rtx 4070"

    #results = update_prices(search, "")
    #if results != None:
    #    print(update_prices(search, ""))
    #else:
    #    print("No search results found")

    updatePinnedPrices()

    # save database changes and close connection
    connection.commit()
    cursor.close()
    connection.close()
