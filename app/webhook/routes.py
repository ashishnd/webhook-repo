from flask import Blueprint, request, jsonify, render_template
from app.extensions import mongo
from datetime import datetime

# Define the blueprint
webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

# --- UI & API ROUTES FOR ASSESSMENT ---

@webhook.route('/ui')
def show_ui():
    """Renders the dashboard for the 15-second polling requirement."""
    return render_template('dashboard.html')

@webhook.route('/api/events')
def get_events():
    """Provides the latest 10 events from MongoDB in JSON format."""
    # Fetch latest 10 events, sorted by most recent first
    events = list(mongo.db.actions.find().sort("_id", -1).limit(10))
    for e in events:
        e['_id'] = str(e['_id'])  # Convert ObjectId to string for JSON compatibility
    return jsonify(events)

# --- WEBHOOK RECEIVER LOGIC ---

@webhook.route('/receiver', methods=['POST', 'GET'])
def receiver():
    # Verification check for browser testing
    if request.method == 'GET':
        return "<h1>Flask is alive and reachable!</h1><p>The bridge is open.</p>", 200

    # GitHub's "POST" request handling
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Identify the type of event using GitHub's headers
    event_type = request.headers.get('X-GitHub-Event')
    
    event_doc = None
    # Formatting timestamp as required: "1st April 2021 - 9:30 PM UTC"
    timestamp = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    # CASE A: PUSH EVENT
    if event_type == "push":
        author = data.get('pusher', {}).get('name')
        to_branch = data.get('ref', '').split('/')[-1]
        event_doc = {
            "author": author,
            "type": "PUSH",
            "from_branch": None,
            "to_branch": to_branch,
            "timestamp": timestamp
        }

    # CASE B: PULL REQUEST (or MERGE)
    elif event_type == "pull_request":
        action = data.get('action')
        pr_data = data.get('pull_request', {})
        author = pr_data.get('user', {}).get('login')
        from_branch = pr_data.get('head', {}).get('ref')
        to_branch = pr_data.get('base', {}).get('ref')

        # Check if it's a Merge (PR closed + merged status is true)
        if action == "closed" and pr_data.get('merged') == True:
            event_doc = {
                "author": author,
                "type": "MERGE",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
        # Standard Pull Request
        elif action == "opened":
            event_doc = {
                "author": author,
                "type": "PULL_REQUEST",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }

    # Save to MongoDB if we recognized the event
    if event_doc:
        mongo.db.actions.insert_one(event_doc)
        print(f"Saved {event_doc['type']} by {event_doc['author']}")
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "success", "message": "Event ignored"}), 200