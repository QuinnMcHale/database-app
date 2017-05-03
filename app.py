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

def filter(text):
    return (
        text.replace("&", "&amp;").
        replace('"', "&quot;").
        replace("<", "&lt;").
        replace(">", "&gt;")
    )

@app.route('/info')
def info():
	return render_template('info.html')
@app.route('/search')
def search():
	if request.args.get('sourceAirport') is None:
		return redirect(url_for('home'))
	else:
		sourceAirport = filter(request.args.get('sourceAirport'))
		destAirport = filter(request.args.get('destAirport'))
		date = filter(request.args.get('date'))

		cursor = conn.cursor()
		query = "SELECT * FROM flight WHERE departure_airport = %s AND arrival_airport = %s AND departure_time LIKE %s AND departure_time BETWEEN NOW() AND NOW() + INTERVAL 1 YEAR"
		date = '%'+date+'%'
		cursor.execute(query, (sourceAirport, destAirport, date))
		data = cursor.fetchall()
		print(data)
		if not data:
			noFlights = "No flights found"
			cursor.close()
			if 'username' not in session:
				username = "Guest"
			else:
				username = session["username"]
			return render_template('response.html', noFlights = noFlights, username=username)
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
		airline = filter(request.form['airline'])
		flightNumber = filter(request.form['flightNumber'])
		role = filter(session['role'])

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
				email = filter(request.form['email'])
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
	airline = filter(request.args.get('airline'))
	flightNumber = filter(request.args.get('flightNumber'))

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
			query = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE customer_email = %s AND departure_time BETWEEN NOW() AND NOW() + INTERVAL 1 YEAR"
			cursor.execute(query, (username))
			data = cursor.fetchall()
			cursor.close()
			flights = data
			return render_template('homeCustomer.html', username=username, flights = flights)
		elif session['role'] == "staff":
			airline = session['company']
			cursor = conn.cursor()
			query = "SELECT * FROM flight WHERE airline_name = %s AND departure_time BETWEEN NOW() AND NOW() + INTERVAL 30 DAY"
			cursor.execute(query, (airline))
			data = cursor.fetchall()
			cursor.close()
			flights = data
			return render_template('homeStaff.html', username=username, airline=airline, flights = flights)
		elif session['role'] == "agent":
			cursor = conn.cursor()
			agentID = session['id']
			query = "SELECT * FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE booking_agent_id = %s AND departure_time BETWEEN NOW() AND NOW() + INTERVAL 1 YEAR"
			cursor.execute(query, (agentID))
			data = cursor.fetchall()
			cursor.close()
			flights = data
			return render_template('homeAgent.html', username=username, flights = flights)
	else:
		return render_template('index.html')

@app.route('/newFlight', methods=['GET', 'POST'])
def newFlight():
	if request.method == "GET" or session.get('role') != "staff":
		return redirect(url_for('home'))
	else:
		airline = filter(request.form["airline"])
		flightNumber = filter(request.form["flightNumber"])
		departureAirport = filter(request.form["departureAirport"])
		departureTime = filter(request.form["departureTime"])
		arrivalAirport = filter(request.form["arrivalAirport"])
		arrivalTime = filter(request.form["arrivalTime"])
		price = filter(request.form["price"])
		status = filter(request.form["status"])
		airplaneID = filter(request.form["airplaneID"])

		cursor = conn.cursor()
		ins = 'INSERT INTO flight VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
		cursor.execute(ins, (airline, flightNumber, departureAirport, departureTime, arrivalAirport, arrivalTime, price, status, airplaneID))
		conn.commit()
		cursor.close()
		newFlight = "Successfully created new flight"
		return render_template('response.html', newFlight = newFlight, username = session['username'])

@app.route('/allFlights')
def allFlights():
	if session.get('role') != "staff":
		return redirect(url_for('home'))
	else:
		airline = session['company']
		cursor = conn.cursor()
		query = 'SELECT * FROM flight WHERE airline_name = %s'
		cursor.execute(query, (airline))
		data = cursor.fetchall()
		flights = data
		cursor.close()
		return render_template('allFlights.html', flights = flights, airline = airline)

@app.route('/allFlightsFiltered')
def allFlightsFiltered():
	if session.get('role') != "staff" or request.args.get('start') is None:
		return redirect(url_for('home'))
	else:
		if request.args.get('date') == "yes":
			start = filter(request.args.get('start'))
			end = filter(request.args.get('end'))
			airline = session['company']

			cursor = conn.cursor()
			query = "SELECT * FROM flight WHERE airline_name = %s AND departure_time BETWEEN %s AND %s"
			cursor.execute(query, (airline, start, end))
			data = cursor.fetchall()
			flights = data
			cursor.close()
			return render_template('allFlightsFiltered.html', flights = flights, airline = airline)
		elif request.args.get('airport') == "yes":
			start = filter(request.args.get('start'))
			end = filter(request.args.get('end'))
			airline = session['company']

			cursor = conn.cursor()
			query = "SELECT * FROM flight WHERE airline_name = %s AND departure_airport = %s AND arrival_airport = %s"
			cursor.execute(query, (airline, start, end))
			data = cursor.fetchall()
			flights = data
			cursor.close()
			return render_template('allFlightsFiltered.html', flights = flights, airline = airline)
@app.route('/flightCustomers')
def flightCustomers():
	if session.get('role') != "staff" or request.args.get('airline') is None:
		return redirect(url_for('home'))
	else:
		airline = request.args.get('airline')
		flightNumber = request.args.get('flightNumber')

		cursor = conn.cursor()
		query = "SELECT * FROM purchases NATURAL JOIN ticket WHERE airline_name = %s AND flight_num = %s"
		cursor.execute(query, (airline, flightNumber))
		data = cursor.fetchall()
		cursor.close()
		return render_template('customers.html', customers = data, airline = airline, flightNumber = flightNumber)

@app.route('/changeStatus')
def changeStatus():
	if session.get('role') != "staff" or request.args.get('flightNumber') is None:
		return redirect(url_for('home'))
	else:	
		airline = session['company']
		status = filter(request.args.get('status'))
		flightNumber = filter(request.args.get('flightNumber'))

		cursor = conn.cursor()
		query = "UPDATE flight SET status = %s WHERE airline_name = %s AND flight_num = %s"
		cursor.execute(query, (status, airline, flightNumber))
		conn.commit()
		cursor.close()
		statusChange = "Flight's status successfully changed."
		return render_template('response.html', statusChange = statusChange, username = session['username'])

@app.route('/allAirplanes')
def allAirplanes():
	if session.get('role') != "staff":
		return redirect(url_for('home'))
	else:
		airline = session['company']
		cursor = conn.cursor()
		query = "SELECT * FROM airplane WHERE airline_name = %s"
		cursor.execute(query, (airline))
		data = cursor.fetchall()
		cursor.close()
		return render_template('airplanes.html', airline = airline, airplanes = data)

@app.route('/addAirplane', methods=['GET', 'POST'])
def addAirplane():
	if session.get('role') != "staff" or request.method == "GET" or request.form["airplaneID"] is None:
		return redirect(url_for('home'))
	else:
		airline = session['company']
		airplaneID = filter(request.form["airplaneID"])
		seats = filter(request.form["seats"])

		cursor = conn.cursor()
		query = "SELECT * FROM airplane WHERE airline_name = %s AND airplane_id = %s"
		cursor.execute(query, (airline, airplaneID))
		data = cursor.fetchone()
		if(data):
			airplaneExists = "Airplane already exists"
			cursor.close()
			return render_template('response.html', airplaneExists = airplaneExists, username = session['username'])
		else:
			ins = "INSERT INTO airplane VALUES(%s, %s, %s)"
			cursor.execute(ins, (airline, airplaneID, seats))
			conn.commit()
			cursor.close()
			newAirplane = "Airplane successfully added"
			return render_template('response.html', newAirplane = newAirplane, username = session['username'])

@app.route('/addAirport', methods=['GET', 'POST'])
def addAirport():
	if session.get('role') != "staff" or request.method == "GET" or request.form["name"] is None:
		return redirect(url_for('home'))
	else:
		name = filter(request.form['name'])
		city = filter(request.form['city'])
		cursor = conn.cursor()
		query = "SELECT * FROM airport WHERE airport_name = %s"
		cursor.execute(query, (name))
		data = cursor.fetchone()
		if(data):
			airportExists = "Airport already exists"
			cursor.close()
			return render_template('response.html', airportExists = airportExists, username = session['username'])
		else:
			ins = "INSERT INTO airport VALUES(%s, %s)"
			cursor.execute(ins, (name, city))
			conn.commit()
			cursor.close()
			newAirport = "Airport successfully added"
			return render_template('response.html', newAirport = newAirport, username = session['username'])

@app.route('/allAgents')
def allAgents():
	if session.get('role') != "staff":
		return redirect(url_for('home'))
	else:
		cursor = conn.cursor()
		query1 = "SELECT * FROM booking_agent"
		cursor.execute(query1)
		allAgents = cursor.fetchall()
		query2 = "SELECT COUNT(price) AS count, booking_agent.email, booking_agent.booking_agent_id FROM purchases NATURAL JOIN ticket NATURAL JOIN flight NATURAL JOIN booking_agent WHERE purchase_date BETWEEN NOW() - INTERVAL 30 DAY AND NOW() GROUP BY booking_agent.email ORDER BY COUNT(price) DESC LIMIT 5"
		cursor.execute(query2)
		topFiveMonth = cursor.fetchall()
		query3 = "SELECT COUNT(price) AS count, booking_agent.email, booking_agent.booking_agent_id FROM purchases NATURAL JOIN ticket NATURAL JOIN flight NATURAL JOIN booking_agent WHERE purchase_date BETWEEN NOW() - INTERVAL 1 YEAR AND NOW() GROUP BY booking_agent.email ORDER BY COUNT(price) DESC LIMIT 5"
		cursor.execute(query3)
		topFiveYear = cursor.fetchall()
		query4 = "SELECT SUM(price*.10) AS sum, booking_agent.email, booking_agent.booking_agent_id FROM purchases NATURAL JOIN ticket NATURAL JOIN flight NATURAL JOIN booking_agent WHERE purchase_date BETWEEN NOW() - INTERVAL 1 YEAR AND NOW() GROUP BY booking_agent.email ORDER BY SUM(price*.10) DESC LIMIT 5"
		cursor.execute(query4)
		topFiveCom = cursor.fetchall()
		cursor.close()
		return render_template('allAgents.html', agents = allAgents, topFiveMonth = topFiveMonth, topFiveYear = topFiveYear, topFiveCom = topFiveCom)

@app.route('/customerInfo')
def customerInfo():
	if session.get('role') != "staff":
		return redirect(url_for('home'))
	else:
		airline = session['company']
		cursor = conn.cursor()
		query1 = "SELECT COUNT(ticket_id) as count, customer_email FROM purchases NATURAL JOIN ticket NATURAL JOIN flight WHERE airline_name = %s AND purchase_date BETWEEN NOW() - INTERVAL 1 YEAR AND NOW() GROUP BY customer_email ORDER BY COUNT(ticket_id) DESC LIMIT 5"
		cursor.execute(query1,(airline))
		customers = cursor.fetchall()
		cursor.close()
		return render_template('customerInfo.html', customers = customers)
@app.route('/flightsTaken')
def flightsTaken():
	if session.get('role') != "staff" or request.args.get('email') is None:
		return redirect(url_for('home'))
	else:
		email = filter(request.args.get('email'))
		airline = session['company']

		cursor = conn.cursor()
		query = "SELECT * FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE customer_email = %s AND airline_name = %s"
		cursor.execute(query,(email,airline))
		flights = cursor.fetchall()
		cursor.close()
		return render_template('flightsTaken.html', flights = flights, email = email)

@app.route('/viewReports')
def viewReports():
	if session.get('role') != "staff":
		return redirect(url_for('home'))
	else:
		airline = session['company']

		cursor = conn.cursor()
		query1 = "SELECT COUNT(ticket_id) as count FROM purchases NATURAL JOIN ticket WHERE airline_name = %s AND purchase_date BETWEEN NOW() - INTERVAL 1 YEAR AND NOW()"
		cursor.execute(query1, (airline))
		lastYear = cursor.fetchone()
		query2 = "SELECT COUNT(ticket_id) as count FROM purchases NATURAL JOIN ticket WHERE airline_name = %s AND purchase_date BETWEEN NOW() - INTERVAL 30 DAY AND NOW()"
		cursor.execute(query2, (airline))
		lastMonth = cursor.fetchone()
		cursor.close()
		return render_template('viewReports.html', lastYear = lastYear, lastMonth = lastMonth)
@app.route('/viewReportsDate')
def viewReportsDate():
	if session.get('role') != "staff" or request.args.get('start') is None:
		return redirect(url_for('home'))
	else:
		airline = session['company']
		start = filter(request.args.get('start'))
		end = filter(request.args.get('end'))
		cursor = conn.cursor()
		query = "SELECT COUNT(ticket_id) as count FROM purchases NATURAL JOIN ticket WHERE airline_name = %s AND purchase_date BETWEEN %s AND %s"
		cursor.execute(query,(airline,start,end))
		date = cursor.fetchone()
		cursor.close()
		return render_template('viewReportsDate.html', date = date, start = start, end = end)
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
		email = filter(request.form['email'])
		name = filter(request.form['name'])
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		building = filter(request.form['building'])
		street = filter(request.form['street'])
		city = filter(request.form['city'])
		state = filter(request.form['state'])
		phone = filter(request.form['phone'])
		passportNum = filter(request.form['passportNum'])
		passportExp = filter(request.form['passportExp'])
		passportCountry = filter(request.form['passportCountry'])
		dob = filter(request.form['dob'])

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
			cursor.close()
			register = "Succesfully registered user"
			return render_template('index.html', register = register)

@app.route('/registerAgentAuth', methods=['GET', 'POST'])
def registerAgentAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else:
		email = filter(request.form['email'])
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		agentID = filter(request.form['agentID'])
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
		username = filter(request.form['username'])
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		firstName = filter(request.form['firstName'])
		lastName = filter(request.form['lastName'])
		dob = filter(request.form['dob'])
		airline = filter(request.form['airline'])

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
		email = filter(request.form['email'])
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
		username = filter(request.form['username'])
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
			session['company'] = data["airline_name"]
			return redirect(url_for('home'))
		else:
			error = "Invalid username or password"
			return render_template('loginStaff.html', error = error)

@app.route('/loginAgentAuth', methods=['GET', 'POST'])
def loginAgentAuth():
	if request.method == "GET":
		return redirect(url_for('home'))
	else:
		email = filter(request.form['email'])
		origPassword = request.form['password'].encode('latin1')
		password = hashlib.md5(origPassword).hexdigest()
		agentID = filter(request.form['id'])

		cursor = conn.cursor()
		query = 'SELECT * FROM booking_agent WHERE email = %s AND password = %s AND booking_agent_id = %s'
		cursor.execute(query, (email, password, agentID))

		data = cursor.fetchone()
		cursor.close()
		if data:
			session['username'] = email
			session['role'] = "agent"
			session['id'] = data["booking_agent_id"]
			return redirect(url_for('home'))
		else:
			error = "Invalid username or password or booking agent ID"
			return render_template('loginAgent.html', error = error)

@app.route('/commission')
def commission():
	if 'username' not in session or session.get('role') != "agent":
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
		return render_template("commission.html", username = username, totalCommission = totalCommission["SUM"], averageCommission = "{0:.2f}".format(averageCommission["AVG(price*.10)"]), lastThirtyDays = lastThirtyDays["COUNT(price)"])
@app.route('/commissionDetailed')
def commissionDetailed():
	if 'username' not in session or request.args.get('start') is None or session.get('role') != "agent":
		return redirect(url_for('commission'))
	else:
		username = session['username']
		agentID = session['id']
		start = filter(request.args.get('start'))
		end = filter(request.args.get('end'))

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
	if 'company' in session:
		session.pop('company')
	if 'id' in session:
		session.pop('id')
	return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)


