from flask import Flask, redirect, render_template, request, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_migrate import Migrate
import re
from flask_bcrypt import Bcrypt 

app = Flask(__name__)
app.secret_key = 'sneaky sneaky'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

likes_table = db.Table('likes', db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='cascade'), primary_key = True), db.Column('tweet_id', db.Integer, db.ForeignKey('tweets.id', ondelete='cascade'), primary_key = True))

followers_table = db.Table('followers', db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key = True), db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key = True), db.Column('created_at', db.DateTime, server_default = func.now()))

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    email = db.Column(db.String(45))
    password = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, server_default = func.now())
    updated_at = db.Column(db.DateTime, server_default = func.now(), onupdate = func.now())
    tweets_this_user_likes = db.relationship('Tweet', secondary=likes_table)
    followers = db.relationship('User', secondary=followers_table, primaryjoin=id==followers_table.c.followed_id, secondaryjoin=id==followers_table.c.follower_id, backref='following')

    def name(self):
        return self.first_name +" "+ self.last_name

class Tweet(db.Model):
    __tablename__ = 'tweets'
    id = db.Column(db.Integer, primary_key = True)
    tweet = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='cascade'), nullable = False)
    user = db.relationship('User', foreign_keys=[user_id], backref="user_tweets")
    created_at = db.Column(db.DateTime, server_default = func.now())
    updated_at = db.Column(db.DateTime, server_default = func.now(), onupdate = func.now())

@app.route("/")
def index():
    return render_template('index.html')

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
        new_user = User(first_name = request.form['first_name'], last_name = request.form['last_name'], email = request.form['email'], password = password)
        db.session.add(new_user)
        db.session.commit()
    return redirect("/")

@app.route("/login", methods=['POST'])
def login():
    result = User.query.filter_by( email = request.form['email'])
    print(result)
    if result:
        if bcrypt.check_password_hash(result[0].password, request.form['password']):
            session['id'] = result[0].id
            session['name'] = result[0].first_name
            session['last'] = result[0].last_name
            flash("login success")
            return redirect("/dashboard")
        else:
            flash("You could not be logged in")
            return redirect("/")
    else:
        flash("Something Went Wrong")
        return redirect("/")

@app.route("/dashboard")
def success():
    if 'id' not in session:
        return redirect("/")
    else: 
        logged_in_user = User.query.get(session['id']) 
        approved_users_ids = [user.id for user in logged_in_user.following]+[logged_in_user.id]
        tweets=Tweet.query.filter(Tweet.user_id.in_(approved_users_ids)).all()                  
        return render_template("dashboard.html", tweets = tweets)

@app.route("/tweet", methods=['POST'])
def tweet():
    if len(request.form['tweet']) < 1 or len(request.form['tweet']) > 140:
        flash("Character length is invalid")
        return redirect("/dashboard")
    else:        
        new_tweet = Tweet(tweet = request.form['tweet'], user_id = session['id'])
        db.session.add(new_tweet)
        db.session.commit()
        return redirect("/dashboard")

@app.route("/tweets/<tweet_id>/delete", methods=['POST'])
def delete(tweet_id):
    delete_me = Tweet.query.get(request.form['tweet_id'])
    db.session.delete(delete_me)
    db.session.commit()
    return redirect("/dashboard")

@app.route("/tweets/<tweet_id>/add_like", methods=['POST'])
def add_like(tweet_id):
    posted_tweet = Tweet.query.get(request.form['tweet_id'])
    user_likes = User.query.get(session['id'])
    user_likes.tweets_this_user_likes.append(posted_tweet)
    db.session.commit()
    return redirect("/dashboard")

@app.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect("/")

@app.route("/tweets/<tweet_id>/edit")
def edit_tweet(tweet_id):
    if 'id' not in session:
        return redirect("/dashboard")
    else:
        edit = Tweet.query.get(tweet_id)        
        return render_template("/edit.html", edit = edit)

@app.route("/tweets/<tweet_id>/update", methods=['POST'])
def update_tweet(tweet_id):
    if len(request.form['updated_tweet']) < 1 or len(request.form['updated_tweet']) > 140 or request.form['updated_tweet'].isspace():
        flash("Invalid tweet length")
        return redirect("/tweets/<tweet_id>/edit")
    else:
        update_tweet = Tweet.query.get(tweet_id)
        update_tweet.tweet = request.form['updated_tweet']
        db.session.commit()
        return redirect("/dashboard")

@app.route("/users")
def all_users():
    if 'id' not in session:
        flash("Login to see all the fun")
        return redirect("/")
    else:
        users = User.query.all()
        return render_template("success.html", users = users)

@app.route("/follow/<user_id>", methods=['POST'])
def follow_user(user_id):
    if 'id' not in session:
        flash("Log in to see what's happening")
        return redirect("/")
    else:
        follower = User.query.get(session['id'])
        followed = User.query.get(user_id)
        followed.followers.append(follower)
        db.session.commit()
        return redirect("/users")

if __name__ == "__main__":
    app.run(debug=True)