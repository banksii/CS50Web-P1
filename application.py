import os
import requests

from flask import Flask, session, render_template, request, url_for, redirect, flash, jsonify
from flask_session import Session
from flask_bcrypt import Bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
bcrypt = Bcrypt(app)

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

# goodreads API key
KEY = "" 

@app.route("/")
def index():

    return render_template("index.html") #print("Project 1: TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        name = request.form.get("username") # take the request the user made, access the form,
        pwd = request.form.get("password")

        if name == "" or pwd == "":
            flash('please enter a username and password')
            return render_template("login.html")

        row = db.execute("SELECT * FROM users WHERE name = :name", {"name": name}).fetchone()

        if  row:
            if bcrypt.check_password_hash(row.hash.tobytes(), pwd): #hash is returned from database as memoryview object.  Need to use 'tobytes' to conver to string
                session["id"] = row.id
                #flash(session["id"])
                return redirect(url_for("search"))
            else: 
                flash('incorrect password')
                return render_template("login.html")
        else:     
            flash('no such user')
            return render_template("login.html")
    
    elif request.method == 'GET':
        return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():

    name = request.form.get("username") # take the request the user made, access the form,
    pwd = request.form.get("password")
    conf = request.form.get("confirmation")
    # validate submission
    if name == "" or pwd == "" or conf == "":
        flash('please complete the form')
        return render_template("index.html")

    # check password and confirmation match
    elif pwd != conf:
        flash('password and confirmation do not match')
        return render_template("index.html")


    # check if username is available
    elif db.execute("SELECT * FROM users WHERE name = :name", {"name": name}).rowcount != 0:
        flash('username is already taken, please choose a different one')
        
        return render_template("index.html")

    else:
        # hash password
        pwdhash = bcrypt.generate_password_hash(pwd)
        #add new user
        res = db.execute("INSERT INTO users (name, hash) VALUES(:name, :pwdhash) RETURNING id", {"name": name, "pwdhash": pwdhash}).fetchone()
        db.commit()

        #flash(res[0])
        # store id in session
        session["id"] = res[0]
        flash('user successfully registered!')
        return redirect(url_for("search"))

@app.route("/logout", methods=["GET"])
def logout():
    del session["id"] #clear session id
    #flash('You were logged out.')
    #flash(session["id"])
    
    return redirect(url_for("login"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == 'POST':
        query = request.form.get("search")
        if query == "":
            return render_template("search.html")
        
        books = db.execute("SELECT * FROM books WHERE author ILIKE :query OR isbn ILIKE :query OR title ILIKE :query", {"query": "%" + query + "%"}).fetchall()
        if books == []:
            flash("no results")
            return render_template("search.html")
        else:
            #for book in books:
                #flash(book)
            return render_template("search.html", books=books)

    return render_template("search.html")


@app.route("/book/<int:book_id>")
def book(book_id):

    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        flash("Book does not exist in the database.")
        return redirect(url_for("search"))

    # get any reviews for this book from database
    reviews = db.execute("SELECT review, rating FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

    # get rating from goodreads.com
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": book.isbn})

    if res.status_code != 200:
        return render_template("book.html", book=book, reviews=reviews, gr_rating="not available", gr_count="N/A")

    # get JSON object and get first book in list of books returned (should only be one returned)
    gr_data = res.json()["books"][0]

    if book.isbn == gr_data["isbn"]:
        gr_rating = gr_data["average_rating"]
        gr_count = gr_data["work_ratings_count"]
    else:
        gr_rating = "not available"
        gr_count = "N/A"

    return render_template("book.html", book=book, reviews=reviews, gr_rating=gr_rating, gr_count=gr_count)


@app.route("/addreview", methods=["POST"])
def review():

    if "id" not in session:
        flash("you must be logged in to leave a review")
        return redirect(request.referrer)

    review_text = request.form.get("review")
    book_id = request.form.get("book_id") #this is the id of the book page obtained from a hidden input element
    rating = request.form.get("rating")
    if review_text == "" or rating is None:
        flash("Review form is empty or no rating selected")
        return redirect(request.referrer)   #this returns the user to the book page
    else:
        #check to see if there is already a review for this book by this user
        res = db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id", {"book_id": book_id, "user_id": session["id"]}).fetchone()
        if res is None:
            db.execute("INSERT INTO reviews (book_id, user_id, rating, review) VALUES(:book_id, :user_id, :rating, :review) RETURNING review_date",\
                {"book_id": book_id, "user_id": session["id"], "rating": rating, "review": review_text}).fetchone()
            db.commit()
            flash("Review added!")
            return redirect(url_for('book', book_id=book_id)) 
        else: #if a review has already been submitted flash a message and send the used back to book detail page
            flash("you have already submitted a review for this title")
            return redirect(request.referrer)

@app.route("/api/<isbn>")
def books_api(isbn):

    # returns details on a book

    #book = db.execute("SELECT title, author, year, rating FROM books JOIN reviews ON reviews.book_id = books.id WHERE isbn = :isbn", {"isbn": isbn})#.fetchall()
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    
    if book is None:
        return jsonify({"error": "ISBN not found"}), 404

    # get reviews for book
    reviews = db.execute("SELECT rating FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()

    review_count = len(reviews)
    review_sum = 0
    average_score = 0
    
    if review_count != 0:
        for row in reviews:
            review_sum += row.rating
        average_score = review_sum / review_count



    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": isbn,
        "review_count": review_count,
        "average_score": average_score
        })
