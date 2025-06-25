import pytest
from app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_add_movies_route(client):
    # Test the add_movies route with different input data

    # Test valid data
    valid_data = {
        'title': 'Test Movie',
        'releaseYear': 2023,
        'characters': 'Character A, Character B',
        'boxOffice': 1000000,
        'runtime': 120,
        'director': 'Director X',
        'producers': 'Producer Y, Producer Z'
    }
    response_valid = client.post('/add_movies', data=valid_data)
    assert response_valid.status_code == 302  # Check the status code for a successful redirect

def test_view_data_route(client):
    # Test view_data route
    response = client.get('/view_data')
    assert response.status_code == 200  # Check for successful loading of the page
    assert b'Movies Data' in response.data  # Check for a specific element in the page content
    assert b'The Incredible Hulk' in response.data
    assert b'Tony Stark/Iron Man' in response.data
    assert b'James Gunn' in response.data

    # Ensure no error message for successful data retrieval
    assert b'Error' not in response.data

def test_filter_movies_route(client):
    # Test filter_movies route without a category
    response = client.get('/filter_movies')
    assert response.status_code == 200  # Check for successful loading of the page

    # Test filter_movies route with a category parameter
    response_with_category = client.get('/filter_movies?category=Action')
    assert response_with_category.status_code == 200  # Check for successful loading of the page
    assert b'Action' in response_with_category.data  # Check for the category in the page content
    assert b'No movies available' not in response.data  # Ensure movies are available

    # Test filter_movies route with a non-existent category parameter
    response_invalid_category = client.get('/filter_movies?category=NonExistent')
    assert response_invalid_category.status_code == 200  # Check for successful loading
    assert b'No movies found' in response_invalid_category.data  # Check for appropriate message

def test_latest_movies_route(client):
    # Test find_out_more route
    response = client.get('/find_out_more')
    assert response.status_code == 200  # Check for successful loading of the page
    assert b'Superhero' in response.data  # Check for a specific element in the page content
    assert b'Oops! Sorry' not in response.data  # Ensure no error message for non-existent data

    # Optionally, check for movie details in the response data
    assert b'Iron Man 2' in response.data 
