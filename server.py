from flask import Flask, redirect, render_template, request, session, flash
from mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt 


app = Flask(__name__)
app.secret_key = 'sneaky sneaky'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
# PASSWORD_REGEX = re.compile(r'^(?=.*[\d])(?=.*[a-z])(?=.*[a#$])[\w\d@#$]{6,12}$')


@app.route("/")
def index():
    mysql = connectToMySQL('registration')
    basics = mysql.query("SELECT * FROM basics")
    print(basics)
    return render_template('index.html', basics = basics)

@app.route("/process", methods=['POST'])
def process():
    password = bcrypt.generate_password_hash(request.form['password'])
    print(password)
    
    valid = True
    if len(request.form['first_name']) < 1:
        valid = False
        flash("First name is required")
    if len(request.form['last_name']) < 1:
        valid = False
        flash("Last name is required")
    if not EMAIL_REGEX.match(request.form['email']):
        valid = False
        flash("Invalid Email address!")
    # if not PASSWORD_REGEX.match(request.form['password']):
    #     valid = False
    #     flash("Invalid password")
    if len(request.form['password']) < 5:
        valid = False
        print("Password must be at least 5 characters")
    if request.form['confirm'] != request.form['password']:
        valid = False
        flash("Passwords must match")
    if request.form['first_name'].isalpha() == False or request.form['last_name'].isalpha() == False:
        valid = False
        flash("Fields must contain no special characters")

    if valid:
        flash("Registration was a success")
        mysql = connectToMySQL('registration')
        query = "INSERT INTO basics (first_name, last_name, email, password) VALUES (%(first)s, %(last)s, %(email)s, %(password)s)"
        
        data = {
            'first': request.form['first_name'],
            'last': request.form['last_name'],
            'email': request.form['email'],
            'password': password
        }
        mysql.query(query, data)
    return redirect("/")

@app.route("/login", methods=['POST'])
def login():
    result = User.query.get(request.form['email'])

    if result:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['id'] = result[0]['id']
            session['name'] = result[0]['first_name']
            session['last'] = result[0]['last_name']
            flash("login success")
            return redirect("/dashboard")
        else:
            flash("You could not be logged in")
            return redirect("/")

@app.route("/dashboard")
def success():
    if 'id' not in session:
        return redirect("/")
    else: 
        mysql = connectToMySQL('registration') 
        query = "SELECT tweet, id AS tweet_id FROM tweets WHERE basic_id = %(id)s ORDER BY created_at DESC"
        data = {
            'id': session['id']
        }
        tweets = mysql.query(query, data)             
        return render_template("dashboard.html", tweets = tweets)

@app.route("/tweet", methods=['POST'])
def tweet():
    if len(request.form['tweet']) < 1 or len(request.form['tweet']) > 255:
        flash("Character length is invalid")
        return redirect("/dashboard")
    else:
        mysql = connectToMySQL('registration')
        query = "INSERT INTO tweets (tweet, basic_id) VALUES (%(tweet)s, %(id)s) "
        data = {
            'tweet': request.form['tweet'],
            'id': session['id']
        }
        mysql.query(query, data)
        return redirect("/dashboard")

@app.route("/tweets/<tweet_id>/delete", methods=['POST'])
def delete(tweet_id):
    mysql = connectToMySQL('registration')
    query = "DELETE FROM registration.tweets WHERE id = %(id)s"
    data = {
        'id': tweet_id
    }
    mysql.query(query, data)
    return redirect("/dashboard")

@app.route("/tweets/<tweet_id>/add_like", methods=['POST'])
def add_like(tweet_id):
    mysql = connectToMySQL('registration')
    query = "INSERT INTO registration.likes (basic_id, tweet_id) VALUES (%(basic_id)s, %(tweet_id)s)"
    data = {
        'basic_id': session['id'],
        'tweet_id': tweet_id
    }
    mysql.query(query, data)
    return redirect("/dashboard")

@app.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect("/")

@app.route("/tweets/<tweet_id>/edit")
def edit_tweet(tweet_id):
    mysql = connectToMySQL('registration')
    query = "SELECT tweet, tweets.id AS tweet_id FROM tweets WHERE id = %(id)s"
    data = {
        'id': tweet_id
    }
    edit = mysql.query(query, data)
    return render_template("/edit.html", edit = edit)

@app.route("/tweets/<tweet_id>/update", methods=['POST'])
def update_tweet(tweet_id):
    if len(request.form['updated_tweet']) < 1 or len(request.form['updated_tweet']) > 255:
        flash("Invalid tweet length")
        return redirect("/tweets/<tweet_id>/edit")
    else:
        mysql = connectToMySQL('registration')
        query = "UPDATE registration.tweets SET tweet = %(updated)s WHERE id = %(id)s"
        data = {
            'updated': request.form['updated_tweet'],
            'id': tweet_id
        }
        mysql.query(query, data)
        return redirect("/dashboard")

@app.route("/users")
def users():
    mysql = connectToMySQL('registration')
    all_users = mysql.query("SELECT id, first_name, last_name, email FROM basics")
    print(all_users)
    return render_template("success.html", users = all_users)
    
# @app.route("/follow")
# def follow():
#     mysql = connectToMySQL('registration')
#     query = 
if __name__ == "__main__":
    app.run(debug=True)