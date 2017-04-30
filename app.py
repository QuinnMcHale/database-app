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
	return render_template('index.html')

@app.route('/home')
def home():
	return render_template('home.html')

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

	if(data):
		error = "User already exists"
		cursor.close()
		return render_template('registerCustomer.html', error = error)
	else:
		ins = 'INSERT INTO customer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
		cursor.execute(ins, (email, name, password, building, street, city, state, phone, passportNum, passportExp, passportCountry, dob))
		conn.commit()
		cursor.close()
		return render_template('home.html')

@app.route('/registerAgentAuth', methods=['GET', 'POST'])
def registerAgentAuth():
	email = request.form['email']
	origPassword = request.form['password'].encode('latin1')
	password = hashlib.md5(origPassword).hexdigest()
	agentID = request.form['agentID']
	cursor = conn.cursor()
	query = 'SELECT * FROM booking_agent WHERE email = %s'
	cursor.execute(query, (email))
	data = cursor.fetchone()

	if(data):
		error = "User already exists"
		cursor.close()
		return render_template('registerAgent.html', error = error)
	else:
		ins = 'INSERT INTO booking_agent VALUES(%s, %s, %s)'
		cursor.execute(ins, (email, password, agentID))
		conn.commit()
		cursor.close()
		return render_template('home.html')

@app.route('/registerStaffAuth', methods=['GET', 'POST'])
def registerStaffAuth():
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

	if(data):
		error = "User already exists"
		cursor.close()
		return render_template('registerStaff.html', error = error)
	else:
		tempQuery = 'SELECT * FROM airline WHERE airline_name = %s'
		cursor.execute(tempQuery, (airline))
		data = cursor.fetchone()
		if(not data):
			error = "No such airline exists"
			cursor.close()
			return render_template('registerStaff.html', error = error)
		else:
			ins = 'INSERT INTO airline_staff VALUES(%s, %s, %s, %s, %s, %s)'
			cursor.execute(ins, (username, password, firstName, lastName, dob, airline))
			conn.commit()
			cursor.close()
			return render_template('home.html')

@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')

if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)


