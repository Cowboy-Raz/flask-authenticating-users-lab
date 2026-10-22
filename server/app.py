#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User, ArticlesSchema, UserSchema

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class ClearSession(Resource):

    def delete(self):

        session['page_views'] = None
        session['user_id'] = None

        return {}, 204

class IndexArticle(Resource):

    def get(self):
        articles = [ArticlesSchema().dump(article) for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):

    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:

            article = Article.query.filter(Article.id == id).first()
            # Fix: the starter called .dump() on the class (ArticlesSchema.dump),
            # which crashes when an article is opened in the browser.
            # .dump() needs a schema instance: ArticlesSchema().
            article_json = ArticlesSchema().dump(article)

            return make_response(article_json, 200)

        return {'message': 'Maximum pageview limit reached'}, 401

class Login(Resource):

    def post(self):
        # Get the username the React login form sent as JSON.
        username = request.get_json().get('username')

        # Look up the user by username (usernames are unique in the User model).
        user = User.query.filter(User.username == username).first()

        # Challenge: if no user has that username, don't log anyone in.
        # 401 Unauthorized tells the client the login attempt failed.
        if not user:
            return {'error': 'Invalid username'}, 401

        # Remember who is logged in. Flask stores this in the signed
        # session cookie, so it's sent back with every later request.
        session['user_id'] = user.id

        # Return the logged-in user as JSON with a 200 OK.
        return UserSchema().dump(user), 200

class Logout(Resource):

    def delete(self):
        # Log out by removing the user's id from the session.
        session['user_id'] = None

        # 204 No Content: success, with no data in the response body.
        return {}, 204

class CheckSession(Resource):

    def get(self):
        # session.get() returns None instead of raising a KeyError
        # when 'user_id' isn't in the session.
        user_id = session.get('user_id')

        # If someone is logged in, return their user record with a 200.
        # This is what keeps the user logged in after a page refresh.
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return UserSchema().dump(user), 200

        # Nobody is logged in: return no data and 401 Unauthorized.
        return {}, 401

api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

if __name__ == '__main__':
    app.run(port=5555, debug=True)