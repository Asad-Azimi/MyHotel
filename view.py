"""Web front-end for MyHotel (Flask).

Run with:  python view.py   then open http://127.0.0.1:5001/
"""

# third party modules
import pymysql
from flask import Flask, render_template, request, send_from_directory, redirect

# project modules
import config
from logic import Database


# instantiate application and database object
app = Flask(__name__)
db = Database(config)

# configure the web app according to the config object
app.host = config.APP_HOST
app.port = config.APP_PORT
app.debug = config.APP_DEBUG


@app.route('/', methods=['GET'])
def index():
    """Display the main page with the form and the current line"""
    return render_template('index.html')

# hotels.html

@app.route('/hotels')
def hotels():
    return render_template('hotels.html', hotels=db.get_hotels())


@app.route('/hotels/add', methods=['POST'])
def hotel_add():
    return

# lists.html

@app.route('/lists')
def lists():
    return render_template('lists.html', features=db.get_features(), amenities=db.get_amenities())

# guests.html

@app.route('/guests')
def guests():
    return render_template('guests.html', persons=db.get_persons(), frequent=db.get_frequent_customers())

# reserve.html (making a reservation)


# search.html (queries 1, 2)


# nearby.html (query 3)


# reservations.html (query 4)


# charges.html (query 5)


# late.html (query 6)


# reservation.html (query 8)




@app.route('/resources/<path:path>')
def send_resources(path):
    """Serve CSS, images, etc."""
    return send_from_directory('resources', path)


if __name__ == '__main__':
    app.run(host=app.host, port=app.port, debug=app.debug)
