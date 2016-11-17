import flask
from flask import render_template
from flask import request
from flask import url_for

import json
import logging

# Date Handling
import arrow
import datetime
from dateutil import tz

# Mongo Database
from pymongo import MongoClient
from bson import ObjectId

#########
#
# GLOBALS
#
#########


import CONFIG

app = flask.Flask(__name__)

print("Entering Setup")

try:
	dbclient = MongoClient(CONFIG.MONGO_URL)
	db = dbclient.**TBD**
	collection = db.**TBD**

except:
	print("Failure to open database. Is the Mongo server running? Correct Password?")
	sys.exit(1)

import uuid
app.secret_key = str(uuid.uuid4())

#######
#
# PAGES
#
#######

@app.route("/")
@app.route("/index")
def index():
	app.logger.debug("Main page entry")
	app.logger.debug("Getting data now")
	flask.session['accounts'] =  get_accounts()
	
	return flask.render_template('index.html')

@app.route("/create")
def create():
	app.logger.debug("Account Creation page entry")
	return flask.render_template('create.html')

@app.errorhandler(404)
def page_not_found(error):
	app.logger.debug("Page not found")
	return flask.render_template('page_not_found.html', badurl=request.base_url, linkback=url_for("index")), 404

####################
#
# TEMPLATE FUNCTIONS
#
####################

@app.template_filter('humanize')
def humanize_arrow_date(date):
	"""
	Output should be "today", "yesterday", "in X days", etc.
	Arrow will try to humanize down to the minute, so we need to catch 'today'
	as a special case.
	"""

	try:
		then = arrow.get(date).to('local')
		now = arrow.utcnow().to('local')
		if then.date() == now.date():
			human = "Today"
		else:
			human = then.humanize(now)
			if human == "in a day":
				human = "Tomorrow"
	except:
		human = date
	return human

@app.route("/_create")
def create_account():
	"""
	Creates and inserts a new account into the database
	"""
	
	print("Getting account information...")
	date = request.args.get('date', 0, type=str)
	first = request.args.get('first', 0, type=str)
	last = request.args.get('last', 0, type=str)
	s_id = request.args.get('s_id', 0, type=str)
	status = request.args.get('status', 0, type=str)
	sum_name = request.args.get('sum_name', 0, type=str)
	referral = request.args.get('refer', 0, type=str)

	print("Inserting new account...")
	insert_account(date, first, last, s_id, status, sum_name, referral)

	return flask.redirect("/index")

@app.route("/_delete")
def delete_account():
	"""
	Deletes accounts by accountID
	"""

	print("Getting account id...")
	accountID = request.args.get('accountID', 0, type=str)
	print("The account ID is " + accountID)
	print("Deleting account...")

	account =  collection.find_one({"_id": ObjectId(accountID)})
	collection.remove(account)
	print("Deleted! Redirecting to **TBD**.")

	return flask.redirect("/**TBD**")

######################
#
# SUPPORTING FUNCTIONS
#
######################

def get_accounts():
	"""
	Returns all accounts in the database, in a form that
	can be inserted directly in the 'session' object.
	"""
	
	print("get_accounts() started.")
	accounts = []
	for account in collection.find({"type" : "account"}):
		account['date'] = arrow.get(account['date']).isoformat()
		account['_id'] = str(account['_id'])
		accounts.append(account)

	accounts.sort(key=lambda a: a["date"])
	return accounts

def insert_account(date, first, last, s_id, status, sum_name, referral):
	"""
	Inserts an account into the database
	"""

	print("*** Inserting account")
	print("***")
	print("*** {} {}".format(first, last))
	print("*** {}".format(s_id))

	dt = arrow.get(date, 'MM/DD/YYYY').replace(tzinfo='local')
	iso_dt = dt.isoformat()
	
	print("Complining account from data")
	account = {
			"type" :  "account",
			"date" : iso_dt,
			"first"	: first,
			"last" : last,
			"s_id" : s_id,
			"status" : status,
			"sum_name" : sum_name,
			"referral" : referral
		}
	collection.insert(account)
	print("Account has been inserted into the database.")

	return

if __name__ == "__main__":
	app.debug=CONFIG.DEBUG
	app.logger.setLevel(logging.DEBUG)

	if CONFIG.DEBUG:
		# Reachable only from the same computer
		app.run(port=CONFIG.PORT)
	else:
		# Reachable from anywhere
		app.run(port=CONFIG.PORT,host="0.0.0.0")
