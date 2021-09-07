# By Albert (Technobird22) for non profit. The model code is not mine
'''Respond to given model prompts'''

import os

import time
import random
import requests

import discord

from dotenv import load_dotenv

import presets
import interfacer

async def fetch(url, extension):
    temp_id = 0
    temp_filename = "temp/image_" + str(temp_id) + extension
    while os.path.isfile(temp_filename):
        print("Trying name:", temp_filename)
        temp_id += 1
        temp_filename = "temp/image_" + str(temp_id) + extension
    print("Downloading image as '" + temp_filename + "'.")

    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise()

        file = open(temp_filename, "wb")
        file.write(response.content)
        file.close()
        print("Successfully downloaded file.")
    except:
        print("Error downloading or saving file.")
        raise

async def react_image(message, attachment):
    global client

    print("Connecting to API...")
    
    result = await interfacer.react_image(attachment)

    print("Prediction result:", result)

    print("Reacting...")
    for cur_reaction in result[:2]:
        await message.add_reaction(cur_reaction[1])
    print("Done.")
    return

async def start_typing(message):
    global client

    await client.change_presence(activity=discord.Game(name='with AI | THINKING...'))
    async with message.channel.typing():
        time.sleep(0.1)

async def discord_announce(msg):
    return

    global client

    await client.get_user(presets.OWNER_ID).send(msg)
    for cur_channel in presets.announcement_channels:
        if client.get_channel(cur_channel) == None:
            print("ERROR! Channel '" + str(cur_channel) + "' not found!")
            continue
        await client.get_channel(cur_channel).send(msg)

def init_discord_bot():
    global client, START_TIME

    client.change_presence(activity=discord.Game(name='with AI | Connecting...'))

    @client.event
    async def on_ready():
        joined_servers = "\n".join(("+ Connected to server: '" + guild.name + "' (ID: " + str(guild.id) + ").") for guild in client.guilds)
        elapsed_time = str(round(time.time() - START_TIME, 1))
        await client.get_user(presets.OWNER_ID).send("**Bot loaded in " + elapsed_time +" seconds! Time: " \
        + str(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())) + "**```diff\n" + joined_servers + "```")
        print(joined_servers)

        await client.change_presence(activity=discord.Game(name='with AI | READY'))
        await discord_announce('**Bot is** `READY`!')

    @client.event
    async def on_message(message):
        global history, TARGET_CHANNEL, rem_msgs

        START_TIME = time.time()

        if message.author == client.user:
            return
        
        # Crawl n' react ALL [messages]
        if str(message.content) != ".cnra" or str(message.author) != presets.OWNER_TAG:
            return

        print("Crawlin...")


        for chnl in message.guild.text_channels:
            print('-'*30+"\nIn channel '" + chnl.name + "':")
            try:
                async for cur_message in chnl.history(limit=1, oldest_first=False):
                    pass
                print("Perms sufficient!")
            except:
                print("Not allowed to access channel!\nSkipping...")
                continue

            async for cur_message in chnl.history(limit=None, oldest_first=False):
                print('='*50)
                print("Message: '", cur_message.content, "';       Current reactions:", cur_message.reactions)
                if len(cur_message.reactions) != 0:
                    print("Skipping...")
                    continue

                try:
                    if len(cur_message.attachments) != 0: # Contains attachment
                        print("Reacting...")
                        print("Received attachment(s):", cur_message.attachments)
                        IMAGE_EXTS = ['.png', '.jpg']
                        for attachment in cur_message.attachments:
                            if attachment.filename[-4:].lower() in IMAGE_EXTS:
                                print("Reacting to image:", str(attachment.url))

                                await react_image(cur_message, attachment.url)
                except discord.errors.HTTPException:
                    print("Error emote not found...")
                    pass

def start_all():
    '''Start everything to run model'''
    global client, TARGET_CHANNEL, START_TIME, SELF_TAG, history, rem_msgs

    START_TIME = time.time()
    rem_msgs = 0
    history = "\n"

    print("[INFO] Starting script...", flush=True)
    print("[INFO] Initializing Discord stuff...", flush=True)

    # Initialize discord stuff
    load_dotenv()

    client = discord.Client()

    print("[OK] Initialized Discord stuff!", flush=True)

    # Start Model
    print("[INFO] Starting model...", flush=True)
    interfacer.initialise()
    print("[OK] Started model", flush=True)

    # Run Discord bot
    print("[INFO] Initializing Discord bot...", flush=True)
    init_discord_bot()
    print("[OK] Initialized Discord bot!", flush=True)

    # Get discord tokens
    print("[INFO] Getting Discord token...", flush=True)
    token = os.getenv('DISCORD_TOKEN')
    TARGET_CHANNEL = [103, 101, 110, 101, 114, 97, 108]
    print("[OK] Got Discord token!", flush=True)

    print("[OK] Running Discord bot...", flush=True)
    client.run(token)

if __name__ == "__main__":
    start_all()
