from flask import Flask, redirect, render_template, request, url_for
from markupsafe import Markup
from scrape import update_prices, pin, get_graph, get_pinned
from waitress import serve

app = Flask(__name__)
current_search = ""
current_category = ""

@app.route('/')
@app.route('/index')
def index():
    pinned_records = get_pinned()
    return render_template('index.html', pinned=pinned_records)

@app.route('/pin') # ?
def pin_item():
    name = request.args.get('product_name')
    price = request.args.get('product_price')
    url = request.args.get('product_url')
    search_terms = request.args.get('search_terms')
    selected_category = request.args.get('selected_category')
    current_page = request.args.get('current_page')
    pin(name, price, url)
    return redirect(url_for(current_page, search=search_terms, category=selected_category)) #

@app.route('/graph')
def show_graph():
    item_name = request.args.get('product_name')
    graph_div = Markup(get_graph(item_name))

    return render_template('graph.html', graph=graph_div, name=item_name)

@app.route('/prices')
def get_lowest_price():
    item = request.args.get('search')
    cpath = request.args.get('category')

    if item == None or item.strip() == "": # update
        current_search = "rtx 4070"
        current_category = ""
    else:
        current_search = item
        current_category = cpath if cpath != None else ""

    item_info = update_prices(current_search, current_category)

    if item_info != None and item_info != []:
        return render_template(
            'prices.html',
            title=current_search,
            category=current_category,
            records=item_info
        )
    else: # fix
        return render_template(
            'prices.html',
            title=item,
            name="No results found",
            price="please try again"
        )

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000) # run on localhost port 8000