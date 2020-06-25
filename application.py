import os
import requests

from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

class Book:
    def __init__(self, isbn, title, author, year):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year

        
class Review:
    def __init__(self, rating, review, user):
        self.rating = rating
        self.review = review
        self.user = user
        

@app.route("/", methods=["GET", "POST"])
def index():
    ''' homepage '''
    
    # load search page
    if request.method == "GET":
        # check user session
        try:
            id = session["user_id"]
        except:
            return redirect("/login")

        # generate search page
        return render_template("index.html")
    
    # search and display results
    if request.method == "POST":
        
        # confirm search terms
        if not request.form.get("search"):
            return render_template("error.html", error="search field blank", back="/")
        
        # search function
        search = request.form.get("search")
        term = request.form.get("term")
        
        results = []
        rows = db.execute("SELECT * FROM books WHERE " + term + " ILIKE '%" + search + "%'").fetchall()
        for row in rows:
            results.append(Book(row["isbn"], row["title"], row["author"], row["year"]))
        
        # load results template passing in result list of Books
        return render_template("results.html", results=results, search=search, term=term)

    
@app.route("/book/<isbn>", methods=["GET", "POST"])
def book(isbn):
    
    # load book page
    if request.method == "GET":
        
        # generate book stats page
        row = db.execute("SELECT * FROM books WHERE isbn = '" + isbn + "'").fetchone()
        book = Book(row["isbn"], row["title"], row["author"], row["year"])
        
        # load reviews
        reviews = None
        rows = db.execute("SELECT * FROM reviews JOIN users ON reviews.id = users.id WHERE isbn = '" + isbn + "'").fetchall()
        if rows:
            reviews = []
            for row in rows:
                reviews.append(Review(row["rating"], row["review"], row["username"]))
            
        # pull goodreads data from api
        try:
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "IpPRn9WLTVI025rCVjGw", "isbns": isbn})
            goodreads = (res.json())["books"][0]
        except:
            goodreads = None
        
        return render_template("book.html", book=book, goodreads=goodreads, reviews=reviews)
    
    # add review
    if request.method == "POST":
        if not request.form.get("review"):
            return render_template("error.html", error="please write your review in the text box", back=("/book/" + isbn))
        
        review = request.form.get("review")
        rating = request.form.get("rating")
        
        try:
            db.execute("INSERT INTO reviews (isbn, rating, review, id) VALUES (:isbn, :rating, :review, :id)", {"isbn": isbn, "rating": rating, "review": review, "id": session["user_id"]})
            db.commit()
        except:
            return render_template("error.html", error="you have already reviewed this book", back=("/book/" + isbn))
        
        return redirect("/book/" + isbn)
        
@app.route("/account", methods=["GET", "POST"])
def account():
    ''' reset or delete account '''

    # load account page
    if request.method == "GET":
        # check user session
        try:
            id = session["user_id"]
        except:
            return redirect("/login")
        return render_template("account.html")
    
    if request.method == "POST":
        # reset account
        if request.form.get("account") == "reset":
            db.execute("DELETE FROM reviews WHERE id = :id", {"id": session["user_id"]})
            db.commit()
            return redirect("/")
            
        # delete account
        if request.form.get("account") == "delete":
            db.execute("DELETE FROM reviews WHERE id = :id", {"id": session["user_id"]})
            db.execute("DELETE FROM users WHERE id = :id", {"id": session["user_id"]})
            db.commit()
            session.clear()
            return redirect("/login")
            
            
@app.route("/login", methods=["GET", "POST"])
def login():
    ''' log in page '''

    # forget any previous user
    session.clear()

    # login user
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("error.html", error="must provide username", back="/login")
        if not request.form.get("password"):
            return render_template("error.html", error="must provide password", back="/login")
        
        username = request.form.get("username")
        password = request.form.get("password")
        
        # save user session
        try:
            result = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()
            if password != result[0]["password"]:
                raise ValueError
            session["user_id"] = result[0]["id"]
            print(session["user_id"])
        except:
            return render_template("error.html", error="invalid username and/or password", back="/login")
        
        # redirect to home page
        return redirect("/")
            
    # generate login template
    if request.method == "GET":
        return render_template("login.html")


@app.route("/logout")
def logout():
    ''' logout and redirect '''
    
    # forget user and return to login
    session.clear()
    return redirect("/login")
    
    
@app.route("/register", methods=["GET", "POST"])
def register():
    ''' register new user '''

    # check valid usage
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("error.html", error="must provide username", back="/register")
        if not request.form.get("password"):
            return render_template("error.html", error="must provide password", back="/register")
        if not request.form.get("confirmation"):
            return render_template("error.html", error="please re-enter password", back="/register")
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("error.html", error="passwords do not match", back="/register")
        
        username = request.form.get("username")
        password = request.form.get("password")
        
        # add user to database
        try:
            db.execute("INSERT INTO users (username, password) VALUES(:username, :password)", {"username": username, "password": password})
            db.commit()
        except:
            return render_template("error.html", error="username taken", back="/register")
        
        # save user session
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone()["id"]
        
        # redirect to home
        return redirect("/")
        
    # generate register template
    if request.method == "GET":
        return render_template("register.html")
    
    
@app.route("/api/<isbn>")
def api(isbn):
    ''' returns json object with book and review data, else 404 not found'''
    
    try:
        row = db.execute("SELECT * FROM books WHERE isbn = '" + isbn + "'").fetchone()
        book = Book(row["isbn"], row["title"], row["author"], row["year"])
        count = db.execute("SELECT COUNT(*) FROM reviews WHERE isbn = '" + isbn + "'").fetchone()[0]
        average = round(float(db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = '" + isbn + "'").fetchone()[0]), 3)
        print(count, average)

        return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": count,
            "average_score": average
            })
    except:
        return render_template('error.html', error='404 - isbn not found', back="/login"), 404