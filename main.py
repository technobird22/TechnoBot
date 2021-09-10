# By Albert (Technobird22) for non profit. The model code is not mine
'''Respond to given model prompts'''

from inspect import indentsize
import os

import time
import random
import requests
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

        time.sleep(1)

        await client.change_presence(activity=discord.Game(name='with AI | READY'))
        await discord_announce('**Bot is** `READY`!')
        bot_start_msg = "**Initialised in " + elapsed_time +" seconds! Current Time: " \
        + str(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())) + " UTC**\nServers: ```diff\n" + joined_servers + "```"

        print("[OK] Initialised!")

    @client.event
    async def on_message(message):
        global history, TARGET_CHANNEL, rem_msgs, clean_start

        START_TIME = time.time()

        if message.author == client.user:
            return

        print("="*50)
        print("Message from: '" + str(message.author) + "' saying '" + str(message.content) + "'.\nAttachments: '" + str(message.attachments) + '.')

        print('URLS:', processor.get_urls(message.content))

        for url in ([attachment.url for attachment in message.attachments] + processor.get_urls(message.content)):
            if processor.is_url_img(url):
                print("Reacting to image:", url)
                await processor.react_image(message, url)

        if len(message.content) == 0: # Attachment only
            return

        if str(message.channel) not in presets.ALLOWED_CHANNELS:
            print("[x] REJECTING MESSAGE FROM CHANNEL: " + str(message.channel) + "...")



        OUTPUT_MESSAGE = "You shouldn't be seeing this... Please contact '" + presets.OWNER_TAG + "' on Discord to report this.\nThanks :)"

        # User commands
        # if message.content.startswith(".complete"):
        #     await start_typing(message)
        #     print("\nGetting completion... ")
        #     result = await interfacer.complete(message.content[10:])
        #     print("RESULT:", result)
        #     OUTPUT_MESSAGE = '*' + message.content[10:] + '*' + '`' + result[0] + '`'

        # Info
        if message.content == ".about" or message.content == ".info" or message.content == ".help":
            await start_typing(message)
            print("\nPrinting about... ")
            OUTPUT_MESSAGE = presets.about_message
            time.sleep(1)

        # Commands that require power ('!')
        elif str(message.author.id) == presets.OWNER_ID and clean_start:
            global bot_start_msg
            vowels = ['a', 'e', 'i', 'o', 'u']
            quote = random.choice(presets.QUOTES)
            SPACER = "~~-" + ' '*160 + "-~~"
            SMOL_SPACER = "~~-" + ' '*50 + "-~~"

            clean_start = 0
            await message.author.send(SPACER + '\n**' + random.choice(presets.GREETINGS) + ' ' + presets.OWNER_NAME + '!** :)' + "\nJust finished starting up " + random.choice(presets.START_EMOTES) + "\nHope you're doing well")
            # await message.author.send(":fox:")
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
                time.sleep(5)
                raise KeyboardInterrupt
                exit()

            elif command.startswith("len"):
                print("changing output length")
                try:
                    intlen = int(command[4:])
                    await message.channel.send('Changing output length to `' + command[4:] + '`!')
                except:
                    print("Invalid int")
                    await message.channel.send('Hmm, was `' + command[4:] + '` a valid integer?')
                interfacer.change_len(intlen)
                await message.channel.send('Done! New settings now in place.')
                
                time.sleep(1)
                await client.change_presence(activity=discord.Game(name='with AI | READY'))
                return

            elif command.startswith("temp"):
                print("Changing temperature...")
                try:
                    intlen = float(command[5:])
                    await message.channel.send('Changing temperature to `' + command[5:] + '`!')
                except:
                    print("Invalid float")
                    await message.channel.send('Hmm, was `' + command[5:] + '` a valid float?')
                interfacer.change_temp(intlen)
                await message.channel.send('Done! New settings now in place.')

                time.sleep(1)
                await client.change_presence(activity=discord.Game(name='with AI | READY'))
                return

            else:
                await client.change_presence(activity=discord.Game(name='with AI | READY'))
                # OUTPUT_MESSAGE = "Error! Invalid command!\nPlease check your spelling and try again!"
                return

        # Reply to a message
        else:
            # if(random.randint(1, 25) != 1:
            #     print("Ignoring... (randomiser: compulsory decline)")
            #     return
            # else:
            #     print("Replying! (randomiser: selected)")

            # if(str(message.guild) in presets.IGNORED_GUILDS and str(message.channel)[1:]=="bots"):
            #     await message.channel.send("Hey " + str(message.author) + ",\nTo avoid backlog, please use the Technoware server:\nhttps://discord.gg/QDc9KYy\nThanks for your understanding")
            #     await client.change_presence(activity=discord.Game(name='with AI | READY'))
            #     return

            try:
                await message.channel.send(presets.PRESET_RESPONSES[str(message.content)])
                await client.change_presence(activity=discord.Game(name='with AI | READY'))
                return
            except KeyError:
                pass
                

            if str(presets.BOT_ID) in message.content:
                await message.channel.send("Hey there, the bot is currently in **non finetuned raw mode**. This means the bot should be more generic.\n\nPlease use the command `.raw` before your message to feed it into the bot")
                await client.change_presence(activity=discord.Game(name='with AI | READY'))
                return
            
            if message.content[:9] == ".complete" or message.content[:9] == ".continue":
                in_text = message.content[10:]

                await client.change_presence(activity=discord.Game(name='with AI | Thinking...'))
                OUTPUT_MESSAGE = await processor.complete(in_text, message)

            else:
                await client.change_presence(activity=discord.Game(name='with AI | READY'))
                return

        if OUTPUT_MESSAGE == "NO_OUTPUT":
            await client.change_presence(activity=discord.Game(name='with AI | READY'))
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
        await client.change_presence(activity=discord.Game(name='with AI | READY'))

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
