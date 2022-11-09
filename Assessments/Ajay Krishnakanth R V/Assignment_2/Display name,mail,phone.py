from flask import Flask,render_template,request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods = ["POST" , "GET"])
def login():
    if request.method == "POST":
        user = request.form["nm"]
        mail = request.form["mail"]
        phone = request.form["phone"]
        return render_template('index.html', x = user , y = mail , z = phone)
    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run(debug= True)