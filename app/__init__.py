from flask import Flask
from app.webhook.routes import webhook  # This pulls in your routes
from app.extensions import mongo

def create_app():
    app = Flask(__name__)
    
    # Your MongoDB Atlas URI
    app.config["MONGO_URI"] = "mongodb+srv://ashish:test@cluster0.g2kuklf.mongodb.net/github_events?appName=Cluster0"
    
    mongo.init_app(app)

    # REGISTERING THE BLUEPRINT
    # This tells Flask: "Everything in the webhook folder should start with /webhook"
    app.register_blueprint(webhook)

    return app