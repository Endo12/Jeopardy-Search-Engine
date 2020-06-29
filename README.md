# Jeopardy Search Engine
A web application that allows the user to search through every Jeopardy question. Filters such as category, date (including, year, month, week, and day) and difficulty can be selected to narrow the search. Searches are returned in pages which return matching searches from 1000 categories at a time to improve runtime and user experience. Further information about searching can be found at the application home page.

API Link: http://jservice.io/

The app is locally hosted at http:/0.0.0.0.3000

## Back End
The back end of the application runs on Python, and Flask was used as a web framework so that I could retrieve data from the Jeopardy API (specifically, I used json commands). For each category, the algorithm crosschecks the question's data with the inputted search terms and filters to determine if that question should be returned. The multiprocessing.Pool object was used to retrieve the data from multiple categories simultaneously to improve runtime, and results to be returned that are from the same category will appear higher if they have more instances of the search terms.


## Front End
The front end of the application was written in HTML.
