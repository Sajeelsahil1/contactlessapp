from flask import Flask, request, jsonify
import os
import logging
from uuid import uuid4  # Ensures unique filenames
from fingerprint_processing import register_fingerprint, verify_fingerprint
from flask_cors import CORS  # Allows API access from other devices

app = Flask(__name__)
CORS(app)  # Enables CORS to allow mobile app access

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mock database (Replace this with a proper database in production)
registered_users = []

# Setup logging
logging.basicConfig(level=logging.INFO)

@app.route("/")
def home():
    return jsonify({"message": "Server is running!"}), 200

@app.route('/register', methods=['POST'])
def register():
    if 'file' not in request.files or 'username' not in request.form:
        return jsonify({'message': 'Missing file or username'}), 400

    file = request.files['file']
    username = request.form['username']
    
    # Generate unique filename to avoid conflicts
    filename = f"{uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    logging.info(f"Registering fingerprint for user: {username}")

    try:
        result = register_fingerprint(filepath, username)
        
        if "success" in result.lower():
            user_id = len(registered_users) + 1  # Generate simple user ID
            registered_users.append({"id": user_id, "username": username})

        return jsonify({'message': result})
    
    except Exception as e:
        logging.error(f"Error during fingerprint registration: {str(e)}")
        return jsonify({'message': 'Error processing fingerprint'}), 500

@app.route('/verify', methods=['POST'])
def verify():
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400

    file = request.files['file']
    
    # Generate unique filename to avoid conflicts
    filename = f"{uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    logging.info("Verifying fingerprint...")

    try:
        match_score, total_users, accuracy, matched_user = verify_fingerprint(filepath)

        if matched_user:
            return jsonify({
                'message': 'Match found!',
                'user': matched_user,
                'accuracy': accuracy
            }), 200
        else:
            return jsonify({'message': 'No match found'}), 401

    except Exception as e:
        logging.error(f"Error during fingerprint verification: {str(e)}")
        return jsonify({'message': 'Error processing fingerprint'}), 500

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({"users": registered_users}), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # Debug mode OFF for security
