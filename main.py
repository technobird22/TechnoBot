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

import custom_commands

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
            print(f'ERROR! Channel \'{cur_channel}\' not found!')
            continue
        await client.get_channel(cur_channel).send(msg)

async def reset_status():
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

        joined_servers = "\n".join((f'+ Connected to server: \'{guild.name}\' (ID: {guild.id}).') for guild in client.guilds)
        print(joined_servers)
        elapsed_time = str(round(time.time() - START_TIME, 1))

        await asyncio.sleep(1)

        await reset_status()
        await discord_announce('**Bot is** `READY`!')
        bot_start_msg = f'Initialised in **{elapsed_time}** seconds. Current Time: `{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())} UTC`\nConnected to: ```diff\n{joined_servers}```'

        print("[OK] Initialised!")

    @client.event
    async def on_message(message):
        global history, clean_start

        START_TIME = time.time()

        if message.author == client.user:
            return

        # print(f'Message from: "{message.author}" saying "{message.content}".')
        
        if len(str(message.content)) > 50:
            print('-'*75)
        print('{0: <22}'.format(f'{message.guild} '), end='')
        print('{0: <22}'.format(f'> #{message.channel} '), end='')
        print('{0: <22}'.format(f'> {message.author} '), end='')
        if len(str(message.content)) > 50:
            print(f":  ⤵\n  > '{message.content}'.\n{'-'*75}")
        else:
            print(f"> '{message.content}'.")

        if str(message.channel).startswith('Direct Message with ') and presets.IGNORE_DIRECT_MESSAGES and not str(message.channel) == f'Direct Message with {presets.OWNER_TAG}':
            print("^^^ Ignoring Direct message. ^^^")
            return

        urls = [attachment.url for attachment in message.attachments] + processor.get_urls(message.content)
        if urls != []:
            print('URLs and Attachments:')
            for n, url in enumerate(urls):
                print(f'   #{n}: {url}')

            for n, url in enumerate(urls):
                print(f'Checking link {n}: ', end='')
                if await processor.is_url_img(url):
                    print(f'Link {n} is an image!')
                    await processor.react_image(message, url)
            print('='*50)

        if len(message.content) == 0: # Attachment only / status message
            return

        # if str(message.channel) not in presets.ALLOWED_CHANNELS:
        #     print(f'[x] REJECTING MESSAGE FROM CHANNEL: {message.channel}...')


        OUTPUT_MESSAGE = f'You shouldn\'t be seeing this... Please contact "{presets.OWNER_TAG}" on Discord to report this.\nThanks :)'

        # User commands
        if message.content[:9] == ".complete" or message.content[:9] == ".continue":
            in_text = message.content[10:]

            await client.change_presence(activity=discord.Game(name='with AI | Thinking...'))
            OUTPUT_MESSAGE = await processor.complete(in_text, message, length=128, temp=0.8, top_p=0.9)

        # Commands that require power ('!')
        elif str(message.author.id) == presets.OWNER_ID and clean_start:
            global bot_start_msg
            clean_start = 0
            if "bot_start_msg" not in globals():
                await message.author.send('Hold on... I\'m still starting up...')
                await asyncio.sleep(5)

            await processor.send_init_message(message, bot_start_msg)
            return

        elif str(message.author) in presets.POWERFUL and message.content[0] == '!':
            command = message.content[1:]
            if(command == "clearhist"):
                await start_typing(message)
                print("Clearing history...")
                await message.channel.send("> Clearing chat history...")
                print(f"{'='*25} DUMP OF CURRENT HISTORY: {'='*25}\n{history}")
                history = ""
                OUTPUT_MESSAGE = "> Cleared history!"

            elif(command == "stop"):
                print("Stopping bot")
                await discord_announce('**Bot is** `STOPPING`!')
                await client.change_presence(activity=discord.Game(name='with AI | STOPPING'))
                print(f"{'='*25} DUMP OF CURRENT HISTORY: {'='*25}\n{history}")
                
                await discord_announce('**Bot is** `STOPPING`!')
                await message.channel.send('**Bot is** `STOPPING`!')
                await client.change_presence(activity=discord.Game(name='with AI | STOPPING'))
                await asyncio.sleep(2)
                raise KeyboardInterrupt

            else:
                await reset_status()
                # OUTPUT_MESSAGE = "Error! Invalid command!\nPlease check your spelling and try again!"
                return

                
        elif str(message.channel) in presets.ADVENTURE_CHANNELS:
            print("In a text adventure channel")
            OUTPUT_MESSAGE = await processor.adventure(message)

        # Info
        elif message.content == ".help" or message.content == ".about" or message.content == ".info":
            # await start_typing(message)
            print("\nPrinting about... ")
            OUTPUT_MESSAGE = presets.about_message
            await asyncio.sleep(1)

        # Reply to a message
        else:
            if await custom_commands.receive_message(message) is not None:
                try:
                    await message.channel.send(presets.PRESET_RESPONSES[str(message.content)])
                    await reset_status()
                    return
                except KeyError:
                    pass

            await reset_status()
            return

        if OUTPUT_MESSAGE == "NO_OUTPUT":
            await reset_status()
            return

        LEN_CAP = 1950
        while len(OUTPUT_MESSAGE) >= LEN_CAP:
            elapsed_time = str(round(time.time() - START_TIME, 2))
            await message.reply(OUTPUT_MESSAGE[:LEN_CAP], allowed_mentions=presets.ALLOWED_MENTIONS)
            print(f"BOT Response: '{OUTPUT_MESSAGE}'. Responded in {elapsed_time} seconds.")
            if len(OUTPUT_MESSAGE) >= LEN_CAP:
                OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]

        elapsed_time = str(round(time.time() - START_TIME, 2))
        await message.reply(OUTPUT_MESSAGE[:LEN_CAP], allowed_mentions=presets.ALLOWED_MENTIONS)
        print(f"BOT Response: '{OUTPUT_MESSAGE}'. Responded in {elapsed_time} seconds.")
        print('='*50)

        await reset_status()

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

    print("[OK] The Discord bot is running!... ⤵\n       ↪ Catch it before it gets away!\n", flush=True)
    client.run(token)

if __name__ == "__main__":
    start_all()
