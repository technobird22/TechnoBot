'''Main file'''

from inspect import indentsize
import os

import time
import random
import asyncio

import discord

from dotenv import load_dotenv

import presets
import interfacer
import processor

async def start_typing(message):
    global client

    await client.change_presence(activity=discord.Game(name='with AI | THINKING...'))
    async with message.channel.typing():
        await asyncio.sleep(0.1)

async def discord_announce(msg):
    return

    global client

    await client.get_user(presets.OWNER_ID).send(msg)
    for cur_channel in presets.announcement_channels:
        if client.get_channel(cur_channel) == None:
            print("ERROR! Channel '" + str(cur_channel) + "' not found!")
            continue
        await client.get_channel(cur_channel).send(msg)

async def finish():
    global client

    await client.change_presence(activity=discord.Game(name='with AI | READY'))

def init_discord_bot():
    global client, START_TIME, clean_start

    clean_start = presets.SEND_INIT_MESSAGE
    # client.change_presence(activity=discord.Game(name='with AI | Connecting...'))

    @client.event
    async def on_ready():
        global bot_start_msg, clean_start

        clean_start = presets.SEND_INIT_MESSAGE

        joined_servers = "\n".join(("+ Connected to server: '" + guild.name + "' (ID: " + str(guild.id) + ").") for guild in client.guilds)
        elapsed_time = str(round(time.time() - START_TIME, 1))
        print(joined_servers)

        await asyncio.sleep(1)

        await finish()
        await discord_announce('**Bot is** `READY`!')
        bot_start_msg = "**Initialised in " + elapsed_time +" seconds! Current Time: " \
        + str(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())) + " UTC**\nServers: ```diff\n" + joined_servers + "```"

        print("[OK] Initialised!")

    @client.event
    async def on_message(message):
        global history, clean_start

        START_TIME = time.time()

        if message.author == client.user:
            return

        print("="*50)
        print("Message from: '" + str(message.author) + "' saying '" + str(message.content) + "'.\nAttachments: '" + str(message.attachments) + '.')


        if str(message.channel).startswith('Direct Message with ') and presets.IGNORE_DIRECT_MESSAGE and not str(message.channel) == 'Direct Message with ' + presets.OWNER_TAG:
            print("Ignoring Direct message.")
            return

        # print('URLS:', processor.get_urls(message.content))

        for url in ([attachment.url for attachment in message.attachments] + processor.get_urls(message.content)):
            if await processor.is_url_img(url):
                print("Reacting to image:", url)
                await processor.react_image(message, url)

        if len(message.content) == 0: # Attachment only
            return

        if str(message.channel) not in presets.ALLOWED_CHANNELS:
            print("[x] REJECTING MESSAGE FROM CHANNEL: " + str(message.channel) + "...")



        OUTPUT_MESSAGE = "You shouldn't be seeing this... Please contact '" + presets.OWNER_TAG + "' on Discord to report this.\nThanks :)"

        # User commands
        if message.content.startswith(".goose"):
            await start_typing(message)
            goose_id = str(random.randint(0, 1000)).zfill(4)
            print("Getting Goose... HONK!   ID:", goose_id)
            OUTPUT_MESSAGE = presets.get_goose(goose_id)

        # Info
        elif message.content == ".about" or message.content == ".info":
            # await start_typing(message)
            print("\nPrinting about... ")
            OUTPUT_MESSAGE = presets.about_message
            await asyncio.sleep(1)

        # Commands that require power ('!')
        elif str(message.author.id) == presets.OWNER_ID and clean_start:
            global bot_start_msg
            vowels = ['a', 'e', 'i', 'o', 'u']
            quote = random.choice(presets.QUOTES)
            SPACER = "~~-" + ' '*160 + "-~~"
            SMOL_SPACER = "~~-" + ' '*50 + "-~~"

            clean_start = 0
            await message.author.send(SPACER + '\n**' + random.choice(presets.GREETINGS) + ' ' + presets.OWNER_NAME + '!** :)' + "\nJust finished starting up " + random.choice(presets.START_EMOTES) + "\nHope you're doing well")
            await message.author.send(SMOL_SPACER + '\n' + bot_start_msg)
            await message.author.send(SPACER + "\n**__Error log:__** `Empty :)`" + '\n' + 
                "**__Unfinished request queue:__** *(`0` pending)* `Nothing here! :)`")
            await message.author.send(SPACER + "\n> ***" + quote[1] + "***\n            *- " + quote[0] + "*")
            positive_descriptor = random.choice(presets.GOOD_THINGS)
            if positive_descriptor[0].lower() in vowels:
                indefinite_article = "an "
            else:
                indefinite_article = "a "
            await message.author.send(SPACER + "\nHave " + indefinite_article + positive_descriptor + " day!")

            if str(message.channel) != "Direct Message with " + presets.OWNER_TAG:
                msg_alert = await message.channel.send("<@!"+presets.OWNER_ID+"> Psst. Check your DMs " + random.choice(presets.START_EMOTES))
                await asyncio.sleep(5)
                await msg_alert.delete()
            return

        elif str(message.author) in presets.POWERFUL and message.content[0] == '!':
            command = message.content[1:]
            if(command == "clearhist"):
                await start_typing(message)
                print("Clearing history...")
                await message.channel.send("> Clearing chat history...")
                print('='*30, "DUMP OF CURRENT HISTORY: ", '='*30, '\n' + history)
                history = ""
                OUTPUT_MESSAGE = "> Cleared history!"

            elif(command == "stop"):
                print("Stopping bot")
                await discord_announce('**Bot is** `STOPPING`!')
                await client.change_presence(activity=discord.Game(name='with AI | STOPPING'))
                print('='*30, "DUMP OF CURRENT HISTORY: ", '='*30, '\n' + history)
                
                discord_announce('**Bot is** `STOPPING`!')
                client.change_presence(activity=discord.Game(name='with AI | STOPPING'))
                await asyncio.sleep(5)
                raise KeyboardInterrupt

            else:
                await finish()
                # OUTPUT_MESSAGE = "Error! Invalid command!\nPlease check your spelling and try again!"
                return

        # Reply to a message
        else:
            try:
                await message.channel.send(presets.PRESET_RESPONSES[str(message.content)])
                await finish()
                return
            except KeyError:
                pass

            if str(message.channel) in presets.ADVENTURE_CHANNELS:
                print("Text adventure mode...")
                OUTPUT_MESSAGE = await processor.adventure(message)

            elif message.content[:9] == ".complete" or message.content[:9] == ".continue":
                in_text = message.content[10:]

                await client.change_presence(activity=discord.Game(name='with AI | Thinking...'))
                OUTPUT_MESSAGE = await processor.complete(in_text, message, length=128, temp=0.8, top_p=0.9)

            else:
                await finish()
                return

        if OUTPUT_MESSAGE == "NO_OUTPUT":
            await finish()
            return

        LEN_CAP = 1950
        while len(OUTPUT_MESSAGE) >= LEN_CAP:
            elapsed_time = str(round(time.time() - START_TIME, 2))
            await message.reply(OUTPUT_MESSAGE[:LEN_CAP],
                    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
            print("BOT Response: '" + OUTPUT_MESSAGE + "'. Responded in " + elapsed_time + " seconds.")
            if len(OUTPUT_MESSAGE) >= LEN_CAP:
                OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]

        elapsed_time = str(round(time.time() - START_TIME, 2))
        await message.reply(OUTPUT_MESSAGE[:LEN_CAP],
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
        print("BOT Response: '" + OUTPUT_MESSAGE + "'. Responded in " + elapsed_time + " seconds.")
        await finish()

def start_all():
    '''Start everything to run model'''
    global client, START_TIME, history

    START_TIME = time.time()
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
    print("[OK] Got Discord token!", flush=True)

    print("[OK] Running Discord bot...", flush=True)
    client.run(token)

if __name__ == "__main__":
    start_all()
