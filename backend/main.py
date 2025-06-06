from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import openai
import os
import json

app = FastAPI()

# Serve React build from /frontend/build
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

openai.api_key = os.getenv("OPENAI_API_KEY")
dds_api_url = "https://dds-apife.filmbankconnect.com/arts/catalogue/v1/all-contents"

@app.post("/match-movies")
async def match_movies(request: Request):
    data = await request.json()
    search_term = data.get("searchTerm")

    async with httpx.AsyncClient() as client:
        response = await client.get(dds_api_url)
        all_movies = response.json()

    titles = [item["title"] for item in all_movies if "title" in item]

    prompt = f"""
You are a movie classification assistant. A user has entered the term: "{search_term}".

Here is a list of movie titles:
{chr(10).join(titles)}

From this list, return only the titles that clearly relate to the term, with a 1-sentence reason per match. Be strict—only return strong matches.

Respond in this format:
[
  {{"title": "...", "reason": "..."}},
  ...
]
"""

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
    )

    reply = completion.choices[0].message.content.strip()

    try:
        result = json.loads(reply)
    except:
        result = []

    return {"matches": result}
