from pymongo import MongoClient
import flask
from flask import request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = True

client = MongoClient('mongodb+srv://binge_user:j5zK0ITpZzbbRkbR@bingedb.srj5f.gcp.mongodb.net/bingedb?retryWrites=true&w=majority')

# client = MongoClient('mongodb://admin:admin@localhost:5151/bingedb?authSource=admin')  # @TODO

db = client.bingedb


def form_genre_string(array):
    string = ''
    for value in array:
        string += ' genre=' + str(value)
    return string

def get_release_year(release_date):
    if release_date != '':
        return 'released_on=' + release_date[0:4]
    else:
        return ''

def get_original_language(original_language):
    if original_language:
        return 'original_language=' + original_language
    else:
        return ''

def combine_features(row):
    movie_detail_string = row['title'] + ' ' + get_release_year(row.get('release_date', '')) + ' is_adult=' + str(row['adult']) + ' ' + form_genre_string(
        row['genre_ids']) + ' ' + get_original_language(row.get('original_language', ''))
    return movie_detail_string.lower()


def get_index_by_title(title, movies):
    for movie in movies:
        if movie['title'].lower() == title:
            return movie['index']


def get_movie_by_index(index, movies):
    return movies[index]['title']


@app.route('/search', methods=['POST'])
def home():
    movies_model = db.movies

    get_all_movies = movies_model.find({}, {'title': 1, 'release_date': 1, 'adult': 1, 'genre_ids': 1})[0:6000]

    combined_features = []
    movie_by_index = []

    for i, movie in enumerate(get_all_movies):
        combined_features.append(combine_features(movie))
        movie['index'] = i
        movie_by_index.append(movie)

    cv = CountVectorizer()
    count_matrix = cv.fit_transform(combined_features)

    cosine_sim = cosine_similarity(count_matrix)

    recommendation_for_title = request.json.get('name')

    movie_index = get_index_by_title(recommendation_for_title.lower(), movie_by_index)

    similar_movies = list(enumerate(cosine_sim[movie_index]))

    sorted_similar_movies = sorted(similar_movies, key=lambda x: x[1], reverse=True)[1:]

    top_fifty_movies = []

    i = 0
    for element in sorted_similar_movies:
        top_fifty_movies.append(get_movie_by_index(element[0], movie_by_index))
        i = i + 1
        if i >= 10:
            break

    response = flask.jsonify(top_fifty_movies)
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
