import flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

import json
import logging
import base64

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
	db = dbclient.clubmanager
	collection = db.accounts
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
	return flask.render_template('splash.html')

@app.route("/sign_up", methods=['GET','POST'])
def create():
	app.logger.debug("Account Creation page entry")
	return flask.render_template('signup.html')
	
@app.route("/login")
def login():
	app.logger.debug("Login page entry")
	return flask.render_template('login.html')

@app.route("/dashboard")
def landing():
	app.logger.debug("Dashboard page entry")
	app.logger.debug("Getting accounts now")
	flask.session['accounts'] = get_accounts()
	return flask.render_template('main.html')

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

@app.route("/_sign_up", methods=["POST"])
def create_account():
	"""
	Creates and inserts a new account into the database
	"""
	
	print("Getting account information...")
	first = request.form.get('RegisterFirstNameInput', '', type=str)
	last = request.form.get('RegisterLastNameInput', '', type=str)
	email = request.form.get('RegisterEmailInput', '', type=str)
	phone = request.form.get('RegisterPhoneInput', '', type=str)
	s_id = request.form.get('RegisterIDInput', '', type=str)
	status = request.form.get('RegisterStatusInput', '', type=str)
	referral = request.form.get('RegisterReferInput', '', type=str)
	pwd = request.form.get('RegisterPasswordInput', '', type=str)
	confirm = request.form.get('LoginRepeatInput', '', type=str)
	sum_name = request.form.get('RegisterSumNameInput', '', type=str)
	
	
	#Clears any excess whitespace
	first.strip()
	last.strip()
	email.strip()
	phone.strip()
	s_id.strip()
	sum_name.strip()
	
	insert_account(first, last, email, phone, s_id, status, pwd, sum_name, referral)

	return flask.redirect("/login")

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
	
@app.route("/_login", methods=["POST"])
def login_user():
	"""
	Login user
	"""
	input_email = request.form.get('LoginEmailInput')
	input_pwd = request.form.get('LoginPasswordInput')
	
	account = collection.find_one({"email": input_email})
	pwd = account["pwd"]
	pwd = (base64.b64decode(pwd)).decode('ascii')
	
	if input_pwd == pwd:
		flask.session['user'] = account
		return flask.redirect("/dashboard")
	
	flask.flash("Invalid credentials")
	return flask.redirect("/login")
	
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

def insert_account(first, last, email, phone, s_id, status, pwd, sum_name, referral):
	"""
	Inserts an account into the database
	"""
	date = arrow.utcnow().format('MM/DD/YYYY')
	dt = arrow.get(date, 'MM/DD/YYYY').replace(tzinfo='local')
	iso_dt = dt.isoformat()

	print("*** Account")
	print("***")
	print("*** {}".format(date))
	print("*** {} {}".format(first, last))
	print("*** {} {}".format(phone, email))
	print("*** {}".format(status))
	print("*** {}".format(s_id))
	
	#Input checking
	if collection.find_one({"email": email}) or first == '' or last == '' or pwd == '':
		if collection.find_one({"email": email}):
			flask.flash("Account already registered.")
			return flask.redirect("/login")
		if first == '':
			flask.flash("No first name given.")
		if last == '':
			flask.flash("No last name given.")
		if pwd == '':
			flask.flash("No password given.")
		return flask.redirect("/sign_up")
	
	print("Encrypting password")
	pwd = base64.b64encode(pwd.encode('ascii'))
	
	print("Compiling account from data")
	account = {
			"type" :  "account",
			"date" : iso_dt,
			"first"	: first,
			"last" : last,
			"email" : email,
			"phone" : phone,
			"s_id" : s_id,
			"status" : status,
			"sum_name" : sum_name,
			"pwd" : pwd,
			"referral" : referral,
			"role" : "user",
			"major" : "",
			"avail" : "",
			"quote" : ""
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
