# Note: Download gist as 'emojis.json'
# https://gist.github.com/oliveratgithub/0bf11a9aff0d6da7b46f1490f86a71eb

import json

raw_emojis = []
emotes = []
discord_emote = []

get_discord_emote = {}

print("Grabbing emojis...")
with open("emojis.json", encoding='utf-8') as emojis:
    data = json.load(emojis)
    for emoji in data['emojis']:
        # print(emoji['name'] + ": " + emoji['shortname'])
        raw_emojis.append(emoji['emoji'])
        emotes.append(emoji['shortname'])
        discord_emote.append(emoji['shortname'])

        get_discord_emote[emoji['name']] = emoji['shortname']
print("Created emote list!")

print(discord_emote)
