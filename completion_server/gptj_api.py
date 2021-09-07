from termcolor import colored

import requests
import io
import os
import json

from fastapi import FastAPI
import uvicorn

import gptj_connect

print(colored("Server Initialization ...", "magenta"))

# ------------------------------------------
# REMEMBER: Change these settings to local values

SERVER_PORT = 9995

#######################################################

#######################################################

app = FastAPI()


@app.route("/")
def home():
    return "<h1>GPTJ Continuation (redirect) Service Running!</h1>"


###########################

@app.get("/engines/completion")
async def completion(query_text: str):
    print("Completing text:", query_text)
    return gptj_connect.query(query_text)

############################

print(colored("Model startup complete! Starting web service....", "green"))

print(colored("Ready to Serve!", "green"))

uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
print(colored("All done!", "green"))
