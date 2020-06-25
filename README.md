# Project 1

Web Programming with Python and JavaScript

Book review application built with Flask

## User Registration & Login

These routes generate login and registration pages with `GET` requests, and make SQL checks and additions with `POST` request. There is also Python/SQL logic to ensure proper usage: a unique username, matching passwords, all fields filled out.

## Account

Once logged in, the account route will allow users to reset their account (clearing all reviews) or delete (clearing reviews and deleting from user database)

## Search

The index page of this application lets users search the database of books by ISBN, Title, or Author. The search will yield any matches for the string in the database, but must be specified which type of search. The results are listed in a table, with a link by ISBN to a custom book page per entry.

## Book

From the search results, you can enter book pages by unique ISBN. This page holds the stored reviews in the database, info from Goodreads API, and a form to enter a review. The user is allowed to review each book only once, ensure by unique values for ISBN and session id within the SQL database.

## API

By changing the route to `API/<ISBN>` the user can pull JSON data from the site in the following format:

{
    "title": Title,
    "author": Author,
    "year": Year,
    "isbn": ISBN,
    "review_count": Number of Reviews,
    "average_score": Average Score
}

## Error

A custom error route with a programmable message a return button.