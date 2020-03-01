import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None) #skip header
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (author, isbn, title, year) VALUES (:author, :isbn, :title, :year)",
                    {"author": author, "isbn": isbn, "title": title, "year": year})
        #print(f"Added book from {author} titled {title} published in {year}.")
    db.commit()

if __name__ == "__main__":
    main()
