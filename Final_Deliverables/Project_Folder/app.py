from flask import Flask, flash,session,render_template,url_for,request,redirect, abort
import ibm_db
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


app = Flask(__name__)

app.secret_key = ''

mail_api = ""

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
        #print(account)
        if account:
            session['loggedin'] = True
            session['id'] = account['EMAIL']
            userid = account['USERNAME']
            session['username'] = account['USERNAME']
            #print(session)

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
        sql = "SELECT * FROM users WHERE username =? OR EMAIL = ?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        #print(account)
        if account:
            msg = 'Account already exists username or mail already taken!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+',email):
            msg = "invalid email address !"
        elif not re.match(r'[A-Za-z0-9]+',username):
            msg = "Name must contain only Characters and Numbers !"
        elif re.search(r'[!@#$%&]', password) is None:
            msg = "Password must contain atleast one special character"
        elif re.search(r'\d', password) is None:
            msg = "Password must contain atleast one digit"
        elif re.search(r'[A-Z]', password) is None:
            msg = "Password must contain atleast one uppercase letter"
        elif not re.match(r'[A-za-z0-9 !@#$%&]{6}',password):
            msg = "Password length must be atleast 6 characters long"
        else:
            insert_sql = "INSERT INTO users VALUES (?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt,1,username)
            ibm_db.bind_param(prep_stmt,2,email)
            ibm_db.bind_param(prep_stmt,3,password)
            ibm_db.execute(prep_stmt)

            insert_data = "INSERT INTO EXPENSE_TABLE VALUES (0,0,0,0,0,?,0)"
            data_stmt = ibm_db.prepare(conn, insert_data)
            ibm_db.bind_param(data_stmt,1,username)
            ibm_db.execute(data_stmt)

        
            
            msg = 'You have successfully registered ! , Please click login to continue.'

    elif request.method == 'GET':
        msg = 'Please fill out the form !'

    return render_template('register.html', msg=msg)


@app.errorhandler(500)
def internal_error(error):
    return render_template('log_err.html'), 500



@app.route('/dashboard', methods = ['POST', 'GET'])
def Dashboard():
    global bal , Inc , exp

    if session['loggedin'] == True:


        sql3 = "SELECT * FROM Expense_Table WHERE USERID = ?;"
        stmt2 = ibm_db.prepare(conn,sql3)
        ibm_db.bind_param(stmt2,1,session['username'])
        ibm_db.execute(stmt2)
        record = ibm_db.fetch_assoc(stmt2)
        #print(record)

        bal = "₹" + str(record['BALANCE'])
        Inc = "₹" + str(record['INCOME'])
        exp = "₹" + str(record['EXPENSE'])

        
        if request.method == 'POST':
            amount = int(request.form['rupee'])
            limit = request.form['bal_limit']
            detail = request.form['transaction_for']
            if amount > 0:
                sql = "UPDATE Expense_Table SET inc = ? , income = income + ? WHERE USERID = ?"
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt,1,amount)
                ibm_db.bind_param(stmt,2,amount)
                ibm_db.bind_param(stmt,3,session['username'])
                ibm_db.execute(stmt)

                transact_sql = "INSERT INTO TRANSACTION_TABLE VALUES (?,?,?,0)"
                transact_stmt = ibm_db.prepare(conn,transact_sql)
                ibm_db.bind_param(transact_stmt,1,session['username'])
                ibm_db.bind_param(transact_stmt,2,detail)
                ibm_db.bind_param(transact_stmt,3,amount)
                ibm_db.execute(transact_stmt)

            elif amount < 0:
                sql = "UPDATE Expense_Table SET exp = ? , expense = expense + ? WHERE USERID = ?"
                stmt = ibm_db.prepare(conn,sql)
                ibm_db.bind_param(stmt,1,abs(amount))
                ibm_db.bind_param(stmt,2,abs(amount))
                ibm_db.bind_param(stmt,3,session['username'])
                ibm_db.execute(stmt)

                transact_sql = "INSERT INTO TRANSACTION_TABLE VALUES (?,?,0,?)"
                transact_stmt = ibm_db.prepare(conn,transact_sql)
                ibm_db.bind_param(transact_stmt,1,session['username'])
                ibm_db.bind_param(transact_stmt,2,detail)
                ibm_db.bind_param(transact_stmt,3,abs(amount))
                ibm_db.execute(transact_stmt)
            
            if bool(limit) != False and int(limit) > 0:
                sql_limit = "UPDATE EXPENSE_TABLE SET BAL_LIMIT = ? WHERE USERID = ?"
                stmt_limit = ibm_db.prepare(conn,sql_limit)
                ibm_db.bind_param(stmt_limit,1,limit)
                ibm_db.bind_param(stmt_limit,2,session['username'])
                ibm_db.execute(stmt_limit)

            sql2 = "UPDATE Expense_Table SET balance = income - expense WHERE USERID = ?"
            stmt = ibm_db.prepare(conn,sql2)
            ibm_db.bind_param(stmt,1,session['username'])
            ibm_db.execute(stmt)

            up_sql = "SELECT * FROM Expense_Table WHERE USERID = ?;"
            up_stmt = ibm_db.prepare(conn,up_sql)
            ibm_db.bind_param(up_stmt,1,session['username'])
            ibm_db.execute(up_stmt)
            limit_info = ibm_db.fetch_assoc(up_stmt)

            bal_limit = limit_info['BALANCE'] #balance
            update_exp_limit = limit_info['BAL_LIMIT'] #expense limit
            update_exp = limit_info['EXPENSE']  #total expense
            
            if amount < 0:
                if record['EXPENSE'] >= record['BAL_LIMIT']:
                    message = Mail(
                        from_email='',
                        to_emails=session['id'],
                        subject='Expense Alert Mail',
                        html_content='<p>You have exceeded your expense limit.</p><br><p>Your Available Balance is <strong>RS.  %s</strong></p><br><p>Note: You can Re-Update Your Expense limit in Dashboard.</p>'%bal_limit
                    )
                    try:
                        sg = SendGridAPIClient(mail_api)
                        response = sg.send(message)
                        print(response.status_code)
                        print(response.body)
                        print(response.headers)
                    except Exception as e:
                        print(e.message)


            return redirect(url_for('Dashboard'))

        
                
        return render_template('dashboard.html',balance =  bal, income = Inc, expense = exp)
    

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
    msg = ''
    if request.method == "POST":
        pswd = request.form['res_pswd']

        if re.search(r'[!@#$%&]', pswd) is None:
            msg = "Password must contain atleast one special character"
        elif re.search(r'\d', pswd) is None:
            msg = "Password must contain atleast one digit"
        elif re.search(r'[A-Z]', pswd) is None:
            msg = "Password must contain atleast one uppercase letter"
        elif not re.match(r'[A-za-z0-9 !@#$%&]{6}',pswd):
            msg = "Password length must be atleast 6 characters long"
        else:
            sql = 'UPDATE USERS SET PASSWORD = ?  WHERE EMAIL = ?'
            stmt = ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,pswd)
            ibm_db.bind_param(stmt,2,mail_id)
            ibm_db.execute(stmt)

            return redirect(url_for('login'))

    return render_template('reset_pwd.html', msg = msg)

@app.route('/history')
def history():
    result_tuple = []
    
    if session['loggedin'] == True:
        sql = "SELECT * FROM TRANSACTION_TABLE WHERE USERID = ?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session['username'])
        ibm_db.execute(stmt)
        result = ibm_db.fetch_tuple(stmt)
        while result != False:
            result_tuple.append(result)
            result = ibm_db.fetch_tuple(stmt)

        #print(result_tuple)



        return render_template('history.html' , data = result_tuple)
    else:
        return "<h1>Login to Continue.</h1>"

@app.route('/logout')
def logout():

    session.pop('username')
    session.pop('loggedin')
    session.pop('id')
    


    #print(session)

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0' , port=5000)
