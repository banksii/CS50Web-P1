# Project 1

Web Programming with Python and JavaScript

This is a web app designed to meet the requirements of Project 1

Application.py - this contains all the code to run the web app.  I made use of the flask_bcrypt package for hashing password, hence this has been added to the requirements.txt file.  A brief description of the routes:
	index - this is the homepage and renders index.html, which also contains the form to register new users
	login - this route accepts both GET and POST requets.  A GET request renders the login page, login.html.  A POST request receives data from the login form and processes it accordingly.  If successfully logged in the user is transferred to the book search page
	register - this route accepts POST method and receives data from the registration form on index.html.  Once registered a user is transferred to the book search page
	logout - this route logs the user out by clearing SESSION["id"] and returning the user to the login page
	search - this route accepts POST and GET methods.  A GET request renders search.html, which contains a single search bar where the user can search by Title, Author or ISBN.  POST requests receive the data from the search form.  The database of books is searched using the ILIKE query such that if a full Title, Author or ISBN is not provided, close matches are returned.  The results are rendered underneath the search bar on search.html, with each result providing a link to the book.html page where further details on the book are presented.
	book - this route renders book.html which provides further information on a book found via the search page.  The route accepts an integer as an argument which corresponds to the unique id of the book in question.  The details of said book are retrieved from the database.  A request is then sent to the goodreads.com api to retrieve the required details.  All of this informtaion is then rendered using book.html template, which also includes a form to leave a review
	review - this route receives POST data from the review and rating form on book.html.  After checking that the user is looged in and has not reviewed the book before, the review is saved in the database
	booksapi - this provides the api functionallity allowing external requests to find books in the database by ISBN

The postgreSQL database consits of 3 tables:
	users - holds list of usernames and password hashes and a unique user ID
	books - contains the list of books provided in books.csv, which was imported using import.py.
	reviews - stores any reviews and ratings left by users.  Alongside each review the user_id and book_id are stored such that each book can be reviewed only once by each user.  The date of the review is automatically stored by way of a timestap column 
