# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, json
import os
from pymongo import MongoClient, errors
import plotly.express as px
from collections import Counter
from bson import ObjectId
import pandas as pd
from pymongo.errors import PyMongoError
import matplotlib.pyplot as plt
import io
import base64
## import pkg_resources

# Create a Flask web application
app = Flask(__name__)

# Connect to the MongoDB database and create the collections
client = MongoClient('localhost', 27017)
db = client['MyMoviesDB']
movies_collection = db['movies']
characters_collection = db['characters']
directors_collection = db['directors']
cinemas_collection = db['cinemas']

# Get a list of installed packages and their versions
## installed_packages = [pkg.key for pkg in 
## pkg_resources.working_set]
# Filter the list to include only Flask-related packages
## flask_related_packages = [pkg for pkg in installed_packages
## if 'flask' in pkg.lower()]
# Print the list of Flask-related packages
##for pkg in flask_related_packages:
## print(pkg)

# Set the IMAGE_BASE_URL in the context of rendering templates
@app.context_processor
def inject_image_base_url():
    return dict(IMAGE_BASE_URL="/static/")

# Define the insert_data route for inserting data into the database
@app.route('/', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        try:
            file_path = os.path.join(app.root_path, 'static', 'movies.json')
            with open(file_path, 'r') as file:
                data = json.load(file)

            error_messages = []  # To store multiple error messages

            # Check if "movies" data already exists in the movies collection
            for movie in data['movies']:
                existing_movie = movies_collection.find_one(
                    {"title": movie["title"]})
                if existing_movie:
                    error_messages.append(
                        ("Movie", "'{}' already exists in the database".format(movie["title"])))
                else:
                    movies_collection.insert_one(movie)

            # Check if "characters" data already exists in the characters collection
            for character in data['characters']:
                existing_character = characters_collection.find_one(
                    {"name": character["name"]})
                if existing_character:
                    error_messages.append(
                        ("Character", "'{}' already exists in the database".format(character["name"])))
                else:
                    characters_collection.insert_one(character)

            # Check if "directors" data already exists in the directors collection
            for director in data['directors']:
                existing_director = directors_collection.find_one(
                    {"name": director["name"]})
                if existing_director:
                    error_messages.append(
                        ("Director", "'{}' already exists in the database".format(director["name"])))
                else:
                    directors_collection.insert_one(director)

            # Check if "cinemas" data already exists in the directors collection
            for cinema in data['cinemas']:
                existing_cinema = cinemas_collection.find_one(
                    {"cinema_name": cinema["cinema_name"]})
                if existing_cinema:
                    error_messages.append(
                        ("Cinema", "'{}' already exists in the database".format(cinema["cinema_name"])))
                else:
                    cinemas_collection.insert_one(cinema)

            if error_messages:
                return render_template('index.html', message=error_messages)
            else:
                # Redirect to the view_data route after successful data insertion
                return redirect(url_for('view_data', message='Data added from file to MongoDB'))
        except Exception as e:
            return "Error while adding data from file: {}".format(e), 500

    return render_template('index.html')

# Query 5 - Iterate over result sets
# Define the view_data route to display data from the database
@app.route('/view_data', methods=['GET'])
def view_data():
    try:
        message = request.args.get('message')
        # Retrieve data from the movies, characters, and directors collections
        movies_data = list(movies_collection.find({}))
        characters_data = list(characters_collection.find({}))
        directors_data = list(directors_collection.find({}))

        # Pass the data to the template for rendering
        return render_template('view_data.html', movies_data=movies_data, characters_data=characters_data, directors_data=directors_data, message=message)
    except PyMongoError as mongo_error:
        # Handle MongoDB-related errors
        return render_template('error.html', message=f'MongoDB Error: {mongo_error}', movies_data=None, characters_data=None, directors_data=None)
    except Exception as e:
        # Handle other unexpected errors
        return render_template('error.html', message=f'Error: {e}', movies_data=None, characters_data=None, directors_data=None)

# Route for adding a movie
@app.route('/add_movies', methods=['GET', 'POST'])
def add_movies():
    if request.method == 'POST':
        try:
            # Retrieve form data
            title = request.form.get('title')
            release_year = int(request.form.get('releaseYear'))
            characters = request.form.get('characters')
            runtime = int(request.form.get('runtime'))
            category = request.form.get('category')
            producers = request.form.get('producers')
            image_filename = request.form.get('image_filename')

            # Splits categories into an array
            categories_list = category.split(', ')

            # Create a dictionary with the movie data
            movie_data = {
                "title": title,
                "releaseYear": release_year,
                # Convert characters to a list
                "characters": characters.split(', '),
                "runtime": runtime,
                "category": categories_list,
                # Convert producers to a list
                "producers": producers.split(', '),
                "image_filename" : image_filename
            }

            # Insert the movie data into the MongoDB collection
            movies_collection.insert_one(movie_data)

            # Redirect the user to the view_data route with a success message
            return redirect(url_for('view_data', message='Movie added successfully'))

        except ValueError as ve:
            # Handle errors related to incorrect data format
            return render_template("add_movies.html", message=f"Error: Incorrect data format - {ve}")

        except KeyError as ke:
            # Handle errors related to missing fields
            return render_template("add_movies.html", message=f"Error: Missing field - {ke}")

        except Exception as e:
            # Handle other unexpected errors
            return render_template("error.html", message=f"Error: {e}")

    return render_template("add_movies.html")

# Query 2 - match values in an array
# Define the filter_movies route to filter movies based on the category
@app.route('/filter_movies', methods=['GET'])
def filter_movies():
    try:
        category_filter = request.args.get('category')

        if category_filter:
            # Query the 'movies_collection' to find movies matching the category
            filtered_movies = list(movies_collection.find(
                {"category": category_filter}))
        else:
            # If no category parameter is provided, fetch all movies
            filtered_movies = list(movies_collection.find({}))

        if not filtered_movies:
            message = "No movies found for the category: '{}'".format(
                category_filter) if category_filter else "No movies available."
        else:
            message = None

        return render_template('filter_movies.html', data=filtered_movies, message=message, category_filter=category_filter)
    except Exception as e:
        return render_template('error.html', message='Error: {}'.format(e), data=None)

# Query 1 - Select only necessary fields
@app.route('/latest_movies', methods=["GET"])
def latest_movies():
    try:
        # Condition: Select movies released after 2010 in the "Superhero" category
        condition = {
            "releaseYear": {"$gte": 2010},
            "category": "Superhero"
        }
        # Projection: Only select title, releaseYear, and category
        projection = {"_id": 0, "title": 1, "releaseYear": 1, "category": 1}

        filtered_movies = list(db.movies.find(condition, projection))

        # Extract release years
        release_years = [movie["releaseYear"] for movie in filtered_movies]

        # Count movies per year
        movies_per_year = dict(Counter(release_years))

        # Create a bar chart
        fig = px.bar(x=list(movies_per_year.keys()), y=list(
            movies_per_year.values()), labels={'x': 'Release Year', 'y': 'Number of Movies'})
        # Set the color of the bars to bootstrap danger
        fig.update_traces(marker_color='#DC3545')
        fig.update_layout(xaxis={'type': 'category'})

        # Convert the chart to HTML
        chart_html = fig.to_html(full_html=False)

        return render_template("latest_movies.html", filtered_movies=filtered_movies, chart_html=chart_html)

    except PyMongoError as mongo_error:
        # Handle MongoDB-related errors
        return render_template("error.html", message=f"MongoDB Error: {mongo_error}")

    except Exception as e:
        # Handle other unexpected errors
        return render_template("error.html", message=f"Error: {e}")

# Create the text index on 'title' field during app initialization
try:
    movies_collection.create_index([('title', 'text')])
except errors.OperationFailure as mongo_error:
    # Handle MongoDB-related errors during index creation
    print(f"MongoDB Error: {mongo_error}")
except Exception as e:
    # Handle other unexpected errors during index creation
    print(f"Error: {e}")

# Perform text search - Query 9
@app.route('/find_title_elements', methods=['GET'])
def find_title_elements():

    try:
        # Retrieve the search keyword from the URL query parameters
        keyword = request.args.get('keyword')

        if keyword:
            # If a keyword is provided, perform the text search
            # Find movies that match the text search query
            titles = movies_collection.find({'$text': {'$search': keyword}})

            # Convert the cursor to a list of dictionaries
            title_list = list(titles)

            if not title_list:
                # If no titles are found, display the error message with the keyword passed in the search
                return render_template("title_elements.html", title_list=title_list, message=f"Oops! Sorry, there aren't any movie titles containing the word '{keyword}'.")

            # Display the matching titles and include the number of titles found in the message
            num_of_titles = len(title_list)
            message = f"Yay, there are {num_of_titles} movie titles containing the word '{keyword}'!"
            return render_template("title_elements.html", title_list=title_list, message=message)
        else:
            # If no keyword is provided, don't display anything initially
            return render_template("title_elements.html")

    except PyMongoError as mongo_error:
        # Handle MongoDB-related errors
        return render_template("error.html", message=f"MongoDB Error: {mongo_error}")

    except Exception as e:
        # Handle other unexpected errors
        return render_template("error.html", message=f"Error: {e}")

@app.route('/compare_characters', methods=['GET'])
def compare_characters():
    try:
        # Fetch all characters from the collection
        all_characters = list(characters_collection.find({}))

        # Get the selected character names from the form
        selected_characters = request.args.getlist('characters[]')

        # Filter characters based on the selected ones
        filtered_characters = list(characters_collection.find({"name": {"$in": selected_characters}}))

        return render_template('compare_characters.html', characters=all_characters, selected=filtered_characters)

    except PyMongoError as mongo_error:
        return render_template('error.html', message='MongoDB Error: {}'.format(mongo_error), characters=None, selected=None)

    except Exception as e:
        return render_template('error.html', message='Error: {}'.format(e), characters=None, selected=None)


# Query 3 - Match array elements with multiple criteria
@app.route('/popular_cinemas', methods=["GET"])
def popular_cinemas():
    try:
        # Define the query to filter cinemas in London
        query = {
            "location.city": {"$regex": "London", "$options": "i"},
            "monthly_sales": {"$gt": 50000}
        }
        # Fetch cinemas that match the criteria
        london_cinemas = list(db.cinemas.find(query))

        # Collect movies shown in London cinemas
        movies_shown_in_london = []
        for cinema in london_cinemas:
            movies_shown_in_london.extend(cinema['movies_shown'])

        # Fetch movie details for the movies shown in London cinemas
        query_movies = {"title": {"$in": movies_shown_in_london}}
        london_movies = list(db.movies.find(query_movies))

        return render_template("popular_cinemas.html", cinemas=london_cinemas, movies=london_movies)

    except PyMongoError as mongo_error:
        return render_template("error.html", message='MongoDB Error: {}'.format(mongo_error))

    except Exception as e:
        return render_template("error.html", message='Error: {}'.format(e))

# Query 4 - Match arrays containing all specified elements (hard coded)
@app.route('/amenities', methods=["GET"])
def amenities():
    try:
        # Query to find cinemas with predefined amenities
        query_predefined = {"amenities": {"$all": ["Bar", "Arcade"]}}
        amenities = list(db.cinemas.find(query_predefined))

        # Query 8 -  Match arrays with all elements specified (dynamic)
        # Get the user input from the query parameters
        input_amenities = request.args.getlist('amenity')

        # Use the user input in the query
        query_user_input = {"amenities": {"$all": input_amenities}}
        input_amenities_cinemas = list(db.cinemas.find(query_user_input))

        # Extract unique amenities from all cinemas data
        all_amenities = db.cinemas.distinct("amenities")
        unique_amenities = list(set(all_amenities))

        return render_template("amenities.html", amenities=amenities, input_amenities_cinemas=input_amenities_cinemas, unique_amenities=unique_amenities)

    except PyMongoError as mongo_error:
        return render_template("error.html", message='MongoDB Error: {}'.format(mongo_error))

    except Exception as e:
        return render_template("error.html", message='Error: {}'.format(e))

# Query 10 - Perform a left outer join
@app.route('/movies_by_cinema', methods=["GET"])
def movies_by_cinema():
    try:
        # Define the pipeline for the aggregation
        pipeline = [
            {
                '$lookup': {
                    'from': 'cinemas',
                    'localField': 'cinema_id',
                    'foreignField': 'cinema_name',
                    'as': 'cinema_details'
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'title': 1,
                    'cinema_id': 1,
                    'image_filename': 1,
                    'characters': 1,
                    'cinema_details': {
                        'cinema_name': 1,
                        'employees': 1,
                        'monthly_sales': 1,
                        'location': 1,
                        'amenities': 1
                    }
                }
            }
        ]

        # Perform the aggregation
        results = list(movies_collection.aggregate(pipeline))

        # Render the HTML template and pass the processed data to it
        return render_template('cinema_details.html', movies=results)

    except PyMongoError as mongo_error:
        return render_template("error.html", message='MongoDB Error: {}'.format(mongo_error))

    except Exception as e:
        return render_template("error.html", message='Error: {}'.format(e))

# Query 11 - Data Transformations
# Average box office earnings for each cinema location across different years
@app.route('/transform_data', methods=['GET'])
def transform_data():
    # Aggregation pipeline to transform data
    pipeline = [
        {
            '$lookup': {
                'from': 'cinemas',  # Join with the 'cinemas' collection
                'localField': 'cinema_id',  # Field in 'movies' collection
                'foreignField': 'cinema_name',  # Field in 'cinemas' collection
                'as': 'cinema_info'  # Alias for the joined data
            }
        },
        {
            '$unwind': '$cinema_info'  # Unwind the 'cinema_info' array
        },
        {
            '$group': {
                '_id': {  # Group by city, country, and year
                    'city': '$cinema_info.location.city',
                    'country': '$cinema_info.location.country',
                    'year': '$releaseYear'
                },
                # Calculate average box office
                'averageBoxOffice': {'$avg': '$boxOffice'}
            }
        },
        {
            # Sort by year, city, and country
            '$sort': {'_id.year': 1, '_id.city': 1, '_id.country': 1}
        }
    ]

    # Perform aggregation using the pipeline
    try:
        transformed_data = list(movies_collection.aggregate(pipeline))

         # Prepare data for the chart
        chart_labels = []
        chart_values = []
        for data in transformed_data:
            label = f"{data['_id']['city']}, {data['_id']['country']} - {data['_id']['year']}"
            chart_labels.append(label)
            chart_values.append(data['averageBoxOffice'])

        # Create a pie chart using Matplotlib
        plt.figure(figsize=(14, 14))
        plt.pie(chart_values, labels=chart_labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Average Box Office Earnings per Cinema Location')

        # Rotate labels for better readability
        plt.xticks(rotation=90)

        # Save the Matplotlib plot as an image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        return render_template('transformed_data.html', transformed_data=transformed_data, plot_url=plot_url)

    except Exception as e:
        return render_template('error.html', message='Error during aggregation: {}'.format(e))

# Query 12 - Deconstruct array into separate documents
@app.route('/deconstruct_characters', methods=['GET'])
def deconstruct_complex():
    try:
        pipeline = [
            {
                '$match': {
                    # Match documents with release year greater than or equal to 2010
                    'releaseYear': {'$gte': 2010}
                }
            },
            {
                '$unwind': '$characters'  # Deconstruct the 'characters' array
            },
            {
                '$project': {
                    '_id': 0,  # Exclude '_id' field from the output
                    'movie_title': '$title',  # Include 'title' field as 'movie_title'
                    'character': '$characters',  # Include 'characters' field as 'character'
                    'releaseYear': '$releaseYear'  # Include 'releaseYear' field as 'releaseYear'
                }
            },
            {
                '$sort': {'releaseYear': 1}  # Sort by releaseYear
            }
        ]
        result = list(movies_collection.aggregate(pipeline))

        # Create a bar chart
        character_counts_per_year = {}
        for movie in result:
            year = movie.get('releaseYear')
            if year in character_counts_per_year:
                character_counts_per_year[year] += 1
            else:
                character_counts_per_year[year] = 1

        fig = px.bar(x=list(character_counts_per_year.keys()), y=list(character_counts_per_year.values()),
                     labels={'x': 'Release Year', 'y': 'Number of Characters'})
        fig.update_traces(marker_color='#DC3545')
        fig.update_layout(xaxis={'type': 'category'})

        # Convert the chart to HTML
        character_chart_html = fig.to_html(full_html=False)
        return render_template('deconstruct_characters.html', result=result, character_chart_html=character_chart_html)
    
    except PyMongoError as e:
        # Handling PyMongo specific errors
        error_message = f"PyMongo Error: {e}"
        return render_template('error.html', message=error_message), 500
    
    except Exception as e:
        # Catch-all for other exceptions
        error_message = f"An error occurred: {e}"
        return render_template('error.html', message=error_message), 500

# Query 15 - Conditional update
@app.route('/conditional_update', methods=['GET', 'POST'])
def conditional_update():
    if request.method == 'POST':
        try:
            # Update characters who appeared in movies "Iron Man" and "The Incredible Hulk" to add "Spinoff Show"
            characters_collection.update_many(
                {"movies": {"$in": ["Iron Man", "The Incredible Hulk"]}, "appearances": {
                    "$gt": 5}},
                {"$addToSet": {"movies": "Spinoff Show"}}
            )

            # Update cinemas in Paris with monthly sales > 50000 to increase employees by 5
            cinemas_collection.update_many(
                {"location.city": "Paris", "monthly_sales": {"$gt": 50000}},
                {"$inc": {"employees": 5}}
            )

            return redirect(url_for('view_data', message="Conditional updates completed successfully!"))

        except PyMongoError as e:
            error_message= f"PyMongo Error: {e}"
            return render_template('error.html', message=error_message), 500

        except Exception as e:
            error_message = f"An eror occured: {e}"
            return render_template('error.html', message=error_message), 500

    return render_template("conditionalUpdate.html")

# Query 6 - Embedded arrays & 14 - Aggregation expressions
@app.route('/view_reviews', methods=['GET'])
def view_reviews():
    try:
        # Aggregate to count the total number of reviews
        reviews_count_pipeline = [
            {
                '$match': {
                    'reviews': {'$exists': True, '$type': 'array'},  # Filter to select documents where 'reviews' is an array
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'reviewsCount': {'$size': '$reviews'}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'totalReviews': {'$sum': '$reviewsCount'}
                }
            }
        ]

        # Aggregate to calculate average rating for each movie
        average_rating_pipeline = [
            {
                '$project': {
                    'title': 1,
                    'reviews': 1,
                    'averageRating': {'$avg': '$reviews.stars'},  # Calculate the average of stars in reviews
                    'image_filename': 1
                }
            }
        ]

        # Execute the aggregation pipelines
        total_reviews_count = list(movies_collection.aggregate(reviews_count_pipeline))
        movies_with_reviews = list(movies_collection.aggregate(average_rating_pipeline))

    except PyMongoError as e:
        # Handling PyMongo specific errors
        error_message = f"PyMongo Error: {e}"
        return render_template('error.html', message=error_message), 500
    
    except Exception as e:
        # Catch-all for other exceptions
        error_message = f"An error occurred: {e}"
        return render_template('error.html', message=error_message), 500

    return render_template("view_reviews.html", movies_with_reviews=movies_with_reviews, total_reviews_count=total_reviews_count[0]['totalReviews'])

    
# Query 7 -  Match elements in arrays with criteria
# Define a Flask route to fetch thrilling reviews
@app.route('/thrilling_reviews', methods=['GET'])
def thrilling_reviews():
    try:
        # Query the movies collection to find movies with thrilling reviews matching specific criteria
        thrilling_reviews = movies_collection.find({
            # Match movies containing at least one review meeting the criteria
            "reviews": {
                "$elemMatch": {
                    "comment": {"$regex": "thrilling", "$options": "i"},  # Search for "thrilling" in comments (case-insensitive)
                    "stars": {"$gt": 3}  # Retrieve reviews with stars greater than 3
                }
            }
        }, {
            "_id": 0,  # Exclude the document IDs from the results
            "title": 1,  # Include only the movie title in the results
            "image_filename": 1,
            "reviews": 1
        })

        # Render the thrilling_reviews.html template with the fetched data
        return render_template("thrilling_reviews.html", thrilling_reviews=thrilling_reviews)

    except PyMongoError as e:
        # Handling PyMongo specific errors
        error_message = f"PyMongo Error: {e}"
        return render_template('error.html', message=error_message), 500
    
    except Exception as e:
        # Catch-all for other exceptions
        error_message = f"An error occurred: {e}"
        return render_template('error.html', message=error_message), 500


# Query 13 - Map Reduce
@app.route('/map_reduce')
def map_reduce():
    try:
        pipeline = [
            {"$unwind": "$location"},
            {"$group": {"_id": "$location.country", "total_movies": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        results = list(cinemas_collection.aggregate(pipeline))

        # Extract data for the table
        country_data = [{'country': result['_id'], 'total_movies': result['total_movies']} for result in results]

        # Extract data for the pie chart
        countries = [result['_id'] for result in results]
        movie_counts = [result['total_movies'] for result in results]

        # Create a pie chart using Matplotlib
        plt.figure(figsize=(8, 6))
        plt.pie(movie_counts, labels=countries, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Movies Shown per Country')

        # Save the Matplotlib plot as an image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        return render_template('map_reduce.html', country_data=country_data, plot_url=plot_url)
        
    except PyMongoError as e:
        # Handling PyMongo specific errors
        error_message = f"PyMongo Error: {e}"
        return render_template('error.html', message=error_message), 500
    
    except Exception as e:
        # Catch-all for other exceptions
        error_message = f"An error occurred: {e}"
        return render_template('error.html', message=error_message), 500

# Start the Flask application when the script is run
if __name__ == '__main__':
    app.run(debug=True)
