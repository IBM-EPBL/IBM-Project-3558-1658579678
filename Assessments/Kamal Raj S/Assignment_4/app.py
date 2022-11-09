from flask import Flask,render_template, session, request
import ibm_db
import re

app = Flask(__name__)

app.secret_key = 'a'

hostname = ""
uid = ""
pwd = ""
driver = ""
db = ""
port = ""
protocol = ""
cert = ""

dsn = (
    "DATABASE={0};"
    "HOSTNAME={1};"
    "PORT={2};"
    "UID={3};"
    "SECURITY=SSL;"
    "SSLServerCertificate={4};"
    "PWD={5};"
     ).format(db,hostname,port,uid,cert,pwd)

conn = ibm_db.connect(dsn,'','')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    global userid
    msg = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        sql = "SELECT * FROM users WHERE username =? AND password =?"
        stmt =  ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,password)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['loggedin'] = True
            session['id'] = account['USERNAME']
            userid = account['USERNAME']
            session['username'] = account['USERNAME']
            msg = 'logged in successfully !'

            return render_template('dashboard.html', msg = msg)

        else:
            msg = 'Incorrect username or password !'

    return render_template('login.html', msg = msg)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        sql = "SELECT * FROM users WHERE username =?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+',email):
            msg = "invalid email address !"
        elif not re.match(r'[A-Za-z0-9]+',username):
            msg = "Name must contain only Characters and Numbers !"
        else:
            insert_sql = "INSERT INTO users VALUES (?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt,1,username)
            ibm_db.bind_param(prep_stmt,2,email)
            ibm_db.bind_param(prep_stmt,3,password)
            ibm_db.execute(prep_stmt)
            
            msg = 'You have successfully registered !'

    elif request.method == 'GET':
        msg = 'Please fill out the form !'

    return render_template('register.html', msg = msg)

@app.route('/dashboard')
def dash():
     return render_template('dashboard.html')

@app.route('/apply', methods = ['GET', 'POST'])
def apply():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        qualification = request.form['qualification']
        skills = request.form['skills']
        jobs = request.form['s']
        sql = 'SELECT * FROM users WHERE username =?'
        insert_sql = "INSERT INTO job VALUES (?,?,?,?,?)"
        prep_stmt = ibm_db.prepare(conn,insert_sql)
        ibm_db.bind_param(prep_stmt,1,username)
        ibm_db.bind_param(prep_stmt,2,email)
        ibm_db.bind_param(prep_stmt,3,qualification)
        ibm_db.bind_param(prep_stmt,4,skills)
        ibm_db.bind_param(prep_stmt,5,jobs)
        ibm_db.execute(prep_stmt)

        msg = 'you have successfully applied for the job !'
        session['loggedin'] = True
    elif request.method == 'GET':
        msg = "Please fill out the form !"

    return render_template('apply.html', msg = msg)

@app.route('/display')
def display():

    print(session["username"], session['id'])
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM job WHERE userid = % s',(session['id']) )

    account = cursor.fetchone()

    print("accountdisplay", account)

    return  render_template('display.html', account = account)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    return render_template('home.html')

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
