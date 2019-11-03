from flask import Flask, render_template, request
import multiprocessing, pickle
import urllib.request, json
from markupsafe import Markup

#Soham Nagaokar

app = Flask(__name__)
@app.route("/") #Specifies directions for http://0.0.0.0:3000/
def main():
    return render_template('Home.html') #Home.html is used for this address

@app.route('/search_results', methods=['POST']) #Specifies directions for http://0.0.0.0:3000/search_results
def search():
    #The following 4 commands create a list of starting and ending category indicies
    search_indexes = [1]
    for num in range(0,18):
        search_indexes.append((num+1) * 1000)
    search_indexes.append(18419)

    #request.form['var_name'] allows us to get user inputted variables from the html page
    page = int(request.form['page'])
    begin = search_indexes[page-1] #index representing id of first category to be searched
    end = search_indexes[page] #index representing id of last category to be searched
    category = request.form['category']

    p = multiprocessing.Pool() #Pool object that allows us to pool together return values from various threads
    '''
    p.map(a,b) allows us to execute function a for all values in the iterable b. pickle.dumps(obj) will direct all those values from map back to the 
    same place (result). Additionally, it will also allow multiple threads with different values to run concurrently, drastically deceasing runtime.
    '''
    if category == "": #No category specified
        result = pickle.dumps(p.map(index_search, range(begin,end)))
    else: #Category specified
        result = pickle.dumps(p.map(category_search, range(begin,end)))
    result = str(result) #result is casted to a string so we can manipulate it

    old_index = 0 #left bound of QA pair data
    new_index = 0 #right bound of QA pair data
    while new_index >= 0: #As a result of using pickle.dumps, extraneous character data may appear in result. The following code gets rid of that data.
        new_index = result.find('Question: ', old_index)
        result = result.replace(result[old_index:new_index], "")
        old_index = result.find('<br>', old_index) + 4
    result = result[0:result.rfind('>')+1]

    if result == "": #Case where there were no matches
        result = "No search results for Page " + str(page)
    old_results = request.form['old_results'] #Represents data from previous searches
    if old_results != "": #Adds heading to old searches and deletes old heading from old_results
        result += '<br><h3>Previous Page Search Results: </h3><br>'
        old_results = old_results.replace(old_results[0:53], "")

    '''
    The following loop has multiple purposes. First, it retrieves QA pair data from old_results and adds to results. Additionally, our later use of
    the Markup command will add the word Markup to our data, along with other character data, which we remove here. The loop also adds a line break
    between QA pairs, since it's deleted in later code. When the index is negative, there are no more QA pairs to be found, so the loop is exited
    '''
    while True:
        old_index = old_results.find('Question: ', old_index)
        new_index = old_results.find('), Markup(', old_index) - 1
        if old_index < 0 or new_index < 0:
            if 'Question' in old_results:
                old_index = old_results.find('Question: ')
                new_index = old_results.find('), Markup(') - 1
                result += old_results[old_index:new_index] + '<br>'
            break
        result += old_results[old_index:new_index] + '<br>'
        old_results = old_results.replace(old_results[old_index:new_index+12], "")
    result = result.replace("\\", '') #Gets rid of extraneous backslashes
    result = '<h3>Page ' + str(page) + ' Search Results: </h3><br>' + result
    result = Markup(result) #Markup takes each HTML escape character, and transforms it from text into what it was supposed to represent
    result_array = result.split('<br>') #Represents what will become the old_results in the next search
    next_page = page + 1
    #All search term, filter, and page data must be sent to Search.html so that it can be used in the next search
    return render_template('Search.html', output=result, search_terms=request.form['search_terms'],
        old_results=result_array, page=page, next_page=next_page, category=category, value=request.form['value'], year=request.form['year'],
        month=request.form['month'], date_type=request.form['date_type'], day=request.form['day'])

def category_search(index): #used only when a category is specified
    category = request.form['category']

    #The following code will allow us to read directly from the API
    url = 'http://jservice.io/api/category?id=' + str(index)
    response = urllib.request.urlopen(url).read()
    json_obj = str(response, 'utf-8')
    title = json.loads(json_obj)['title']

    result = ""
    if category.lower() == title.lower():
        result = index_search(index)
    return result

def index_search(index): #Returns all QA pairs that satisfy the user inputted parameters
    display = ""

    #The following code will allow us to read directly from the API
    url = 'http://jservice.io/api/category?id=' + str(index)
    response = urllib.request.urlopen(url).read()
    json_obj = str(response, 'utf-8')
    data = json.loads(json_obj)['clues']

    search_terms = request.form['search_terms'] #user inputted terms
    word_list = search_terms.split() #list of search terms
    final_results = [] #Will hold QA data if it satisfies all filters
    for question in data: #Cycles through list of dictonaries that contain question info
        '''
        Each variable that starts with user contains the values that the user inputted for that field. Each variable that starts with question contains
        the value received from the API
        '''
        question_value = question['value']
        user_value = int(request.form['value'])
        airdate = question['airdate']
        question_year = airdate[0:4]
        user_year = request.form['year']
        question_month = airdate[5:7]
        user_month = request.form['month']
        date_type = request.form['date_type']
        question_day = int(airdate[8:10])
        user_day = int(request.form['day'])
        week = [] #Will hold acceptable values for a week filter
        if date_type == "w":
            week = list(range(user_day,user_day+7)) #Assembles acceptable values
            for i, day in enumerate(week): #Loop checks if the day is >31 (which can't exist) and reassigns it if needed
                if day > 31:
                    week[i] = day - 31

        '''
        For each conditional, first we check if the user inputted value is 0 or "", which means no filter was specified by the user and the QA pair
        passes the test. If that's not true, then we check to see if the user inputted value for a field and the value from the API match. If they
        don't, no searching occurs
        '''
        if (user_value == 0 or user_value == question_value) and (user_month == '0' or user_month == question_month) and \
                (date_type == "" or (date_type == "w" and question_day in week) or (date_type == "d" and
                question_day == user_day)) and (user_year == "" or user_year == question_year):
            counter = 0 #will count the number of times any search term appears
            for word in word_list: #loops through each word in search terms
                #For both the question and the answer, if any search term appears, counter is incremented
                for answer_word in question['answer'].split():
                    if answer_word.lower() == word.lower():
                        counter += 1
                for question_word in question['question'].split():
                    if question_word.lower() == word.lower():
                        counter += 1
            if counter > 0: #So at least one search term appeared at least once
                question['count'] = counter #New field is added for counter
                final_results.append(question)

                #The following code bolds each occurence of each search term in both the question and the answer
                unique_terms = set(word_list) #Sets can only have unique terms
                for word in unique_terms:
                    #For the lowercase words
                    question['question'] = question['question'].replace(word, '<b>' + word + '</b>')
                    question['answer'] = question['answer'].replace(word, '<b>' + word + '</b>')
                    #For the capitalized words
                    upper_word = word[0].upper() + word[1:]
                    question['question'] = question['question'].replace(upper_word, '<b>' + upper_word + '</b>')
                    question['answer'] = question['answer'].replace(upper_word, '<b>' + upper_word + '</b>')

    def count_sort(entry): #Sorting algorithim sorts entries by counter
        return entry['count']
    final_results.sort(key=count_sort)
    unique_results = set()
    '''
    QA data is added to a set called unique_results. Since sets can only have unique values, this algorithim also corrects for duplicates that may
    have been accidentally added
    '''
    for new_questions in final_results:
        unique_results.add('Question: ' + new_questions['question'] + "&emsp;" + 'Answer: ' + new_questions['answer'] + \
            '&emsp;' + "<br>")
    for unique_new_question in unique_results: #All unique strings are added to one final string
        display += unique_new_question
    return display

if __name__ == "__main__": #Specifies host and port that program runs on
    app.run(host = '0.0.0.0', port = 3000)