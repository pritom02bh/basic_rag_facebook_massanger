import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
from rag_chatbot import generate_response

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

class FacebookMessage(BaseModel):
    object: str
    entry: list

def send_message(recipient_id: str, message_text: str):
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post("https://graph.facebook.com/v12.0/me/messages", params=params, headers=headers, json=data)
    if response.status_code != 200:
        print("Unable to send message: " + response.text)

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("Webhook verified")
            return challenge
        else:
            raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def webhook(request: Request, body: FacebookMessage):
    if body.object == "page":
        for entry in body.entry:
            for event in entry["messaging"]:
                if "message" in event:
                    sender_id = event["sender"]["id"]
                    message_text = event["message"]["text"]
                    response_text = generate_response(message_text)
                    send_message(sender_id, response_text)
    return "EVENT_RECEIVED"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
