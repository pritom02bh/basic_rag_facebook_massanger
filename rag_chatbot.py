import openai
import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List
from scipy.spatial.distance import cosine
from dotenv import load_dotenv

load_dotenv()

# Load the OpenAI API key
openai.api_key = os.getenv("OpenAI_API")

# Load the embeddings from the CSV file
data = pd.read_csv('data/data.csv')
data['embedding'] = data['embedding'].apply(eval)  # Convert string representation of list back to list

# Define the FastAPI app
app = FastAPI()

class Message(BaseModel):
    sender_id: str
    message: str

def get_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

def find_most_similar(embedding: List[float]) -> str:
    similarities = data['embedding'].apply(lambda x: 1 - cosine(x, embedding))
    most_similar_index = similarities.idxmax()
    return data.loc[most_similar_index, 'text']

def generate_response(message: str) -> str:
    embedding = get_embedding(message)
    most_similar_text = find_most_similar(embedding)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{most_similar_text}\n{message}",
        max_tokens=100
    )
    return response.choices[0].text.strip()

@app.post("/webhook")
async def receive_message(request: Request, message: Message):
    try:
        response_text = generate_response(message.message)
        return {"recipient_id": message.sender_id, "message": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
