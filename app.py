from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

app = Flask(__name__)
app.secret_key = 'this is a secret key'

conn = pymysql.connect(host='127.0.0.1',
					   port=8889,
					   user='root',
					   password='root',
					   db='reservation_system',
					   charset='latin1',
					   cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def index():
	if 'username' in session:
		return redirect(url_for('home'))
	else:
		return render_template('index.html')

@app.route('/info')
def info():
	return render_template('info.html')
@app.route('/search')
def search():
	if request.args.get('sourceAirport') == "":
		return redirect(url_for('home'))
	else:
		sourceAirport = request.args.get('sourceAirport')
		destAirport = request.args.get('destAirport')
		date = request.args.get('date')

		cursor = conn.cursor()
		query = "SELECT * FROM flight WHERE departure_airport = %s AND arrival_airport = %s AND departure_time LIKE %s"
		date = '%'+date+'%'
		cursor.execute(query, (sourceAirport, destAirport, date))
		data = cursor.fetchall()
		print(data)
		if not data:
			noFlights = "No flights found"
			cursor.close()
			return render_template('response.html', noFlights = noFlights, username=session["username"])
		else:
			flights = data
			cursor.close()
			if request.args.get('customer') is not None:
				return render_template('searchCustomer.html', flights = flights)
			elif request.args.get('agent') is not None:
				return render_template('searchAgent.html', flights = flights)
			else:
				return render_template('search.html', flights = flights)

@app.route('/purchaseTicket', methods=['GET', 'POST'])
def purchaseTicket():
	if 'username' not in session or request.method == "GET":
		return redirect(url_for('home'))
	else:
		airline = request.form['airline']
		flightNumber = request.form['flightNumber']
		role = session['role']

		cursor = conn.cursor()
		query = "SELECT ticket_id FROM ticket WHERE airline_name = %s AND flight_num = %s AND ticket_id NOT IN (SELECT ticket_id FROM purchases)"
		cursor.execute(query, (airline, flightNumber))
		data = cursor.fetchone()
		if not data:
			noTickets = "No tickets left for this flight"
			cursor.close()
			return render_template('response.html', noTickets = noTickets, username = session['username'])
		else:
			ticket = data
			if role == "customer":
				ins = "INSERT INTO purchases VALUES(%s,%s,NULL,CURDATE())"
				cursor.execute(ins, (ticket["ticket_id"], session['username']))
				conn.commit()
				cursor.close()
				ticketBought = "Successfully purchased ticket"
				return render_template('response.html', ticketBought = ticketBought, username = session['username'])
			else:
				email = request.form['email']
				emailQuery = "SELECT * FROM customer WHERE email = %s"
				cursor.execute(emailQuery, (email))
				email = cursor.fetchone()
				if not email:
					error = "No customer has that email address"
					return render_template('response.html', error = error, username = session['username'])
				else:
					ins = "INSERT INTO purchases VALUES(%s,%s,%s,CURDATE())"
					cursor.execute(ins, (ticket["ticket_id"], email["email"], session["id"]))
					conn.commit()
					cursor.close()
					ticketBought = "Successfully purchased ticket"
					return render_template('response.html', ticketBought = ticketBought, username = session['username'])

@app.route('/status')
def status():
	airline = request.args.get('airline')
	flightNumber = request.args.get('flightNumber')

	cursor = conn.cursor()
	query = "SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s"
	cursor.execute(query, (airline, flightNumber))
	data = cursor.fetchone()
	if not data:
		noFlight = "No flight found"
		cursor.close()
		return render_template('status.html', noFlight = noFlight)
	else:
		flight = data
		cursor.close()
		return render_template('status.html', flight = flight)

@app.route('/home')
def home():
	if 'username' in session:
		username = session['username']
		if session['role'] == "customer":
			cursor = conn.cursor()
			query = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE customer_email = %s"
			cursor.execute(query, (username))
			data = cursor.fetchall()
			cursor.close()
			flights = data
			return render_template('homeCustomer.html', username=username, flights = flights)
		elif session['role'] == "staff":
			return render_template('homeStaff.html', username=username)
		elif session['role'] == "agent":
			cursor = conn.cursor()
			agentID = session['id']
			query = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s"
			cursor.execute(query, (agentID))
			data = cursor.fetchall()
			cursor.close()
			flights = data
			return render_template('homeAgent.html', username=username, flights = flights)
		return render_template('home.html', username=username)
	else:
		return render_template('index.html')

@app.route('/register')
def register():
	return render_template('register.html')

@app.route('/registerCustomer')
def registerCustomer():
	return render_template('registerCustomer.html')

@app.route('/registerAgent')
def registerAgent():
	return render_template('registerAgent.html')

@app.route('/registerStaff')
def registerStaff():
	return render_template('registerStaff.html')

@app.route('/registerCustomerAuth', methods=['GET', 'POST'])
def registerCustomerAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else:
		email = request.form['email']
		name = request.form['name']
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		building = request.form['building']
		street = request.form['street']
		city = request.form['city']
		state = request.form['state']
		phone = request.form['phone']
		passportNum = request.form['passportNum']
		passportExp = request.form['passportExp']
		passportCountry = request.form['passportCountry']
		dob = request.form['dob']

		cursor = conn.cursor()
		query = 'SELECT * FROM customer WHERE email = %s'
		cursor.execute(query, (email))
		data = cursor.fetchone()

		if data:
			error = "User already exists"
			cursor.close()
			return render_template('registerCustomer.html', error = error)
		else:
			ins = 'INSERT INTO customer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
			cursor.execute(ins, (email, name, password, building, street, city, state, phone, passportNum, passportExp, passportCountry, dob))
			conn.commit()
			register = "Succesfully registered user"
			return render_template('index.html', register = register)

@app.route('/registerAgentAuth', methods=['GET', 'POST'])
def registerAgentAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else:
		email = request.form['email']
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		agentID = request.form['agentID']
		cursor = conn.cursor()
		query = 'SELECT * FROM booking_agent WHERE email = %s'
		cursor.execute(query, (email))
		data = cursor.fetchone()

		if data:
			error = "User already exists"
			cursor.close()
			return render_template('registerAgent.html', error = error)
		else:
			ins = 'INSERT INTO booking_agent VALUES(%s, %s, %s)'
			cursor.execute(ins, (email, password, agentID))
			conn.commit()
			cursor.close()
			register = "Succesfully registered user"
			return render_template('index.html', register = register)

@app.route('/registerStaffAuth', methods=['GET', 'POST'])
def registerStaffAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else:
		username = request.form['username']
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		firstName = request.form['firstName']
		lastName = request.form['lastName']
		dob = request.form['dob']
		airline = request.form['airline']

		cursor = conn.cursor()
		query = 'SELECT * FROM airline_staff WHERE username = %s'
		cursor.execute(query, (username))
		data = cursor.fetchone()

		if data:
			error = "User already exists"
			cursor.close()
			return render_template('registerStaff.html', error = error)
		else:
			tempQuery = 'SELECT * FROM airline WHERE airline_name = %s'
			cursor.execute(tempQuery, (airline))
			data = cursor.fetchone()
			if not data:
				error = "No such airline exists"
				cursor.close()
				return render_template('registerStaff.html', error = error)
			else:
				ins = 'INSERT INTO airline_staff VALUES(%s, %s, %s, %s, %s, %s)'
				cursor.execute(ins, (username, password, firstName, lastName, dob, airline))
				conn.commit()
				cursor.close()
				register = "Succesfully registered user"
				return render_template('index.html', register = register)

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/loginCustomer')
def loginCustomer():
	return render_template('loginCustomer.html')

@app.route('/loginStaff')
def loginStaff():
	return render_template('loginStaff.html')

@app.route('/loginAgent')
def loginAgent():
	return render_template('loginAgent.html')

@app.route('/loginCustomerAuth', methods=['GET', 'POST'])
def loginCustomerAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else: 
		email = request.form['email']
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()

		cursor = conn.cursor()
		query = 'SELECT * FROM customer WHERE email = %s AND password = %s'
		cursor.execute(query, (email, password))

		data = cursor.fetchone()
		cursor.close()
		if data:
			session['username'] = email
			session['role'] = "customer"
			return redirect(url_for('home'))
		else:
			error = "Invalid username or password"
			return render_template('loginCustomer.html', error = error)

@app.route('/loginStaffAuth', methods=['GET', 'POST'])
def loginStaffAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else: 
		username = request.form['username']
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()

		cursor = conn.cursor()
		query = 'SELECT * FROM airline_staff WHERE username = %s AND password = %s'
		cursor.execute(query, (username, password))

		data = cursor.fetchone()
		cursor.close()
		if data:
			session['username'] = username
			session['role'] = "staff"
			return redirect(url_for('home'))
		else:
			error = "Invalid username or password"
			return render_template('loginStaff.html', error = error)

@app.route('/loginAgentAuth', methods=['GET', 'POST'])
def loginAgentAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else:
		email = request.form['email']
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()

		cursor = conn.cursor()
		query = 'SELECT * FROM booking_agent WHERE email = %s AND password = %s'
		cursor.execute(query, (email, password))

		data = cursor.fetchone()
		cursor.close()
		if data:
			session['username'] = email
			session['role'] = "agent"
			session['id'] = data["booking_agent_id"]
			return redirect(url_for('home'))
		else:
			error = "Invalid username or password"
			return render_template('loginAgent.html', error = error)

@app.route('/commission')
def commission():
	if 'username' not in session or session['role'] != "agent":
		return redirect(url_for('home'))
	else:
		username = session['username']
		agentID = session['id']
		cursor = conn.cursor()
		query1 = "SELECT SUM(price*.10) AS SUM FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s"
		cursor.execute(query1, (agentID))
		totalCommission = cursor.fetchone()
		query2 = "SELECT AVG(price*.10) FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s"
		cursor.execute(query2, (agentID))
		averageCommission = cursor.fetchone()
		query3 = "SELECT COUNT(price) FROM purchases AS COUNT NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s AND purchase_date BETWEEN NOW() - INTERVAL 30 DAY AND NOW()"
		cursor.execute(query3, (agentID))
		lastThirtyDays = cursor.fetchone()
		return render_template("commission.html", username = username, totalCommission = totalCommission["SUM"], averageCommission = averageCommission["AVG(price*.10)"], lastThirtyDays = lastThirtyDays["COUNT(price)"])
@app.route('/commissionDetailed')
def commissionDetailed():
	if 'username' not in session or request.args.get('start') == "" or session['role'] != "agent":
		return redirect(url_for('commission'))
	else:
		username = session['username']
		agentID = session['id']
		start = request.args.get('start')
		end = request.args.get('end')

		cursor = conn.cursor()
		query1 = "SELECT SUM(price*.10) AS SUM FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s AND purchase_date BETWEEN %s AND %s"
		cursor.execute(query1, (agentID, start, end))
		totalCommission = cursor.fetchone()
		if totalCommission["SUM"] is None:
			totalCommission["SUM"] = 0
		query2 = "SELECT COUNT(price) FROM purchases AS COUNT NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s AND purchase_date BETWEEN %s AND %s"
		cursor.execute(query2, (agentID, start, end))
		dateRange = cursor.fetchone()
		return render_template("commissionDetailed.html", start = start, end = end, totalCommission = totalCommission["SUM"], dateRange = dateRange["COUNT(price)"])

@app.route('/logout')
def logout():
	session.pop('username')
	session.pop('role')
	return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)


