from termcolor import colored

import torch
import requests
import io
import os
import json

from fastapi import FastAPI
import uvicorn

from PIL import Image
import clip

import get_emoji as emotes


print(colored("Server Initialization ...", "magenta"))

# ------------------------------------------
# REMEMBER: Change these settings to local values

SERVER_PORT = 9995

#######################################################

# Load the model
print("Loading model...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load('ViT-B/32', device)
# model, preprocess = clip.load('ViT-B/16', device)

# Precompute/Load emoji embeddings
print("Encoding Emojis")
encoded_name = 'data/emoji_features32_text.pt'
def encode_emojis(emojis, path=encoded_name):
    print("Precomputed embeddings not found! Generating precomputed embeddings!\nNOTE: This may take over 10 minutes.")
    text_inputs = torch.cat([clip.tokenize(emojis)]).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_inputs)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        if not os.path.isdir('data'):
            os.mkdir('data')
        torch.save(text_features, path)

def load_emojis(path=encoded_name):
    with torch.no_grad():
        print("Loading precomputed embeddings...")
        return torch.load(path)

if os.path.exists(encoded_name):
    text_features = load_emojis()
else:
    encode_emojis(emotes.emotes)

#######################################################

app = FastAPI()


@app.route("/")
def home():
    return "<h1>CLIP Emote Classifier Service Running!</h1>"


###########################

def fetch(url):
    if str(url).startswith('http://') or str(url).startswith('https://'):
        r = requests.get(url)
        r.raise_for_status()
        fd = io.BytesIO()
        fd.write(r.content)
        fd.seek(0)
        return fd
    print("WARNING: NOT AN URL")
    raise
    # return open(url, 'rb')

def react_image(path):
    global preprocess, text_features

    if path is None or path == '':
        print("Error: No input received!")
        return ["NO_INPUT", '0']

    img = Image.open(fetch(path))

    img_in = preprocess(img).unsqueeze(0).to(device)

    # Calculate features
    print("Running model...")
    with torch.no_grad():
        image_features = model.encode_image(img_in)

    # Pick the most similar label for the image
    print("Reading results...")
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)
    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

    accuracies, indices = similarity[0].topk(5)

    for prediction in zip(indices, accuracies):
        accuracy = round(100 * prediction[1].item(), 2)
        print("\nPrediction:", emotes.emotes[prediction[0]], '('+emotes.raw_emojis[prediction[0]]+')' + ', with accuracy ' + str(accuracy))

    # print("INDEX: ", index)
    # print("Prediction accuracy: " + accuracy + "%")
    # print("\nNext prediction:", emotes.emotes[index2], '('+emotes.raw_emojis[index2]+')')
    # print("Prediction accuracy: " + accuracy2 + "%")

    return [(emotes.emotes[prediction[0]], emotes.raw_emojis[prediction[0]], round(100 * prediction[1].item(), 2)) for prediction in zip(indices, accuracies)]


@app.get("/engines/react_emote")
async def caption_image_(url: str):
    if url.find('?') != -1:
        url = url[:url.find('?')]
    return react_image(url)

############################

print(colored("Model startup complete! Starting web service....", "green"))

print(colored("Ready to Serve!", "green"))

uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
print(colored("All done!", "green"))
