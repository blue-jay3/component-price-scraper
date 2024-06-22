from flask import Flask, render_template, request
from scrape import update_prices
from waitress import serve

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/prices')
def get_lowest_price():
    item = request.args.get('search')

    if item == None or item.strip() == "":
        item = "rtx 4070"

    item_info = update_prices(item, "")

    if item_info != None and item_info != []:
        return render_template(
            'prices.html',
            title=item,
            name=item_info[1].upper(),
            price="$" + str(item_info[2])
        )
    else:
        return render_template(
            'prices.html',
            title=item,
            name="No results found",
            price="please try again"
        )

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000) # run on localhost port 8000