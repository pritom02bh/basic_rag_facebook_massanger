import os
import openai
import pandas as pd
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load environment variables
openai.api_key = os.getenv("OpenAI_API")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Load CSV data
df = pd.read_csv('data.csv')

def preprocess_prompt(prompt):
    # Modify this function to preprocess the prompt
    # Example: Add a predefined context or any other preprocessing steps
    predefined_context = "You are a helpful assistant."
    return f"{predefined_context}\n{prompt}"

def find_best_response(user_input):
    # Preprocess the user input
    processed_prompt = preprocess_prompt(user_input)
    # Implement your RAG logic here to find the best response
    return "This is a placeholder response based on the processed prompt."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    response = find_best_response(user_input)
    return jsonify({"response": response})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get("hub.verify_token")
        if token == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification token mismatch", 403

    if request.method == 'POST':
        data = request.json
        for entry in data['entry']:
            for message in entry['messaging']:
                if message.get('message'):
                    sender_id = message['sender']['id']
                    user_input = message['message']['text']
                    response = find_best_response(user_input)
                    send_message(sender_id, response)
        return "Message Processed", 200

def send_message(recipient_id, message_text):
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post("https://graph.facebook.com/v10.0/me/messages", params=params, headers=headers, json=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
