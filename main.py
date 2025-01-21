import tweepy
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables from .env file
load_dotenv()

# Configuration for Twitter API
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Flask and database configuration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///poems.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Twitter API client
class TwitterClient:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET,
        )

    def post_status(self, content):
        if len(content) <= 280:
            response = self.client.create_tweet(text=content)
            if response.data:
                print(f"Tweet posted successfully: {response.data['id']}")
            else:
                raise Exception("Failed to post tweet.")
        else:
            raise Exception(f"Poem too long to post on Twitter: {len(content)}")


twitter_client = TwitterClient()


# Database model
class Poem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    is_posted = db.Column(db.Boolean, default=False)


# Initialize the database
with app.app_context():
    db.create_all()


def post_poem_to_twitter(poem):
    content = f"{poem.content}\n\n- {poem.author} ({poem.source})"
    twitter_client.post_status(content)
    poem.is_posted = True
    db.session.commit()


@app.route("/poems", methods=["GET"])
def get_poems():
    poems = Poem.query.all()
    return jsonify(
        [
            {
                "id": poem.id,
                "title": poem.title,
                "content": poem.content,
                "author": poem.author,
                "source": poem.source,
                "is_posted": poem.is_posted,
            }
            for poem in poems
        ]
    )


@app.route("/poems/tweetrandom", methods=["POST"])
def tweet_random():
    post_daily_poem()
    return jsonify({"message": "Poem tweeted successfully."})


@app.route("/poems/bulk", methods=["POST"])
def add_multiple_poems():
    data = request.json
    new_poems = [
        Poem(
            title=poem["title"],
            content=poem["content"],
            author=poem["author"],
            source=poem["source"],
        )
        for poem in data
    ]
    db.session.bulk_save_objects(new_poems)
    db.session.commit()
    return jsonify({"message": f"{len(new_poems)} poems added successfully."})


@app.route("/poems", methods=["POST"])
def add_poem():
    data = request.json
    new_poem = Poem(
        title=data["title"],
        content=data["content"],
        author=data["author"],
        source=data["source"],
    )
    db.session.add(new_poem)
    db.session.commit()
    return jsonify({"message": "Poem added successfully."})


@app.route("/poems/<int:poem_id>", methods=["DELETE"])
def delete_poem(poem_id):
    poem = Poem.query.get(poem_id)
    if not poem:
        return jsonify({"error": "Poem not found."}), 404
    db.session.delete(poem)
    db.session.commit()
    return jsonify({"message": "Poem deleted successfully."})


@app.route("/poems/reset", methods=["POST"])
def reset_is_posted():
    poems = Poem.query.all()
    for poem in poems:
        poem.is_posted = False
    db.session.commit()
    return jsonify({"message": "All poems have been reset to not posted."})


@app.route("/poems/<int:poem_id>", methods=["PUT"])
def update_poem(poem_id):
    data = request.json
    poem = Poem.query.get(poem_id)
    if not poem:
        return jsonify({"error": "Poem not found."}), 404
    poem.title = data["title"]
    poem.content = data["content"]
    poem.author = data["author"]
    poem.source = data["source"]
    poem.is_posted = data.get("is_posted", poem.is_posted)
    db.session.commit()
    return jsonify({"message": "Poem updated successfully."})


def post_daily_poem():
    poems = Poem.query.filter_by(is_posted=False).all()
    if poems:
        poem = random.choice(poems)
        post_poem_to_twitter(poem)

# Schedule daily posting
scheduler = BackgroundScheduler()
scheduler.add_job(post_daily_poem, "cron", hour=9, timezone="GMT")
scheduler.start()
if __name__ == "__main__":
    # Schedule daily poem posting (using a scheduler like cron or an external library)
    app.run(debug=True)
