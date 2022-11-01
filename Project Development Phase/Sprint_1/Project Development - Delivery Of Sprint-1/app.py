from flask import Flask, flash,session,render_template,url_for,request,redirect
import ibm_db
import re

app = Flask(__name__)

app.secret_key = 'qwwe'

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
    return render_template('landing_page.html')

@app.route('/login', methods=['POST','GET'])
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
            print(session)

            return redirect(url_for('Dashboard'))

        else:
            msg = 'Incorrect username or password !'

    return render_template('login.html', msg=msg)


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

    return render_template('register.html', msg=msg)



@app.route('/dashboard', methods = ['POST', 'GET'])
def Dashboard():

    return render_template('index.html')

@app.route('/password-mail' , methods = ['GET', 'POST'])
def res_mail():
    global mail_id
    msg1 = ''
    if request.method == 'POST':
        mail_id = request.form['email']
        

        if not re.match(r'[^@]+@[^@]+\.[^@]+',mail_id):
            msg = 'Invalid Mail Address'
        else:
            sql = "SELECT * FROM USERS WHERE EMAIL = ?"
            stmt_reset = ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt_reset,1,mail_id)
            ibm_db.execute(stmt_reset)
            acc = ibm_db.fetch_assoc(stmt_reset)

            if acc == False:
                msg1 = 'Mail id is not a registered id'
            else:
                
                return redirect(url_for('res_pwd'))

    return render_template('reset_via_mail.html', msg = msg1)

@app.route('/password-reset', methods = ['GET', 'POST'])
def res_pwd():
    if request.method == "POST":
        pswd = request.form['res_pswd']

        sql = 'UPDATE USERS SET PASSWORD = ?  WHERE EMAIL = ?'
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,pswd)
        ibm_db.bind_param(stmt,2,mail_id)
        ibm_db.execute(stmt)

        return redirect(url_for('login'))

    return render_template('reset_pwd.html')



if __name__ == '__main__':
    app.run(debug=True)
