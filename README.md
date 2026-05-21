# BookScout
For when you want to buy your books second hand though Bokbörsen.se , but don't want to look through endless listings and pay a ridiculous amount in delivery fees. 
Input: Your GoodReads library or any other csv file containing the titles and authors you want to search for (Column name "Author" and "Title" is required).
To get your GoodReads library file, go to "My Books" -> Tools (in the left sidebar) -> Import and export -> Export Library -> Download the file

To run the script, follow these insructions:
1. Copy this repository
2. Download your GoodReads library file and place it in this directory
3. In this directory, run "python find_books.py". Additional flags: --bookshelf, --max_price, --columns.

The output:
- A list of the cheapest listings for each book.
- A file containing grouped findings to minimise the amount of sellers to buy from, together with prices and with links to the listings.
