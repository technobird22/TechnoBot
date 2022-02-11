'''Main file'''

import discord
import asyncio

import os
import time
import random
from dotenv import load_dotenv

import presets
import interfacer
import utils
import custom_commands


def init_discord_bot():
    global client, START_TIME, clean_start

    clean_start = presets.SEND_INIT_MESSAGE

    @client.event
    async def on_ready():
        global bot_start_msg

        joined_servers = "\n".join((f'+ Connected to server: \'{guild.name}\' (ID: {guild.id}).') for guild in client.guilds)
        print(joined_servers)
        elapsed_time = str(round(time.time() - START_TIME, 1))

        await asyncio.sleep(1)

        bot_start_msg = f'Initialised in **{elapsed_time}** seconds. Current Time: `{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())} UTC`\nConnected to: ```diff\n{joined_servers}```'

        print("[OK] Initialised!")

    @client.event
    async def on_message(message):
        global clean_start

        START_TIME = time.time()

        if message.author == client.user:
            return

        if len(str(message.content)) > 50:
            print('-'*75)
        print('{0: <22}'.format(f'{message.guild} '), end='')
        print('{0: <22}'.format(f'> #{message.channel} '), end='')
        print('{0: <22}'.format(f'> {message.author} '), end='')
        if len(str(message.content)) > 50:
            print(f":  ⤵\n  > '{message.content}'.\n{'-'*75}")
        else:
            print(f"> '{message.content}'.")


        if str(message.channel).startswith('Direct Message with ') and presets.IGNORE_DMS and not str(message.channel) == f'Direct Message with {presets.OWNER_TAG}':
            print("^^^ Ignoring Direct message. ^^^")
            return

        urls = [attachment.url for attachment in message.attachments] + utils.get_urls(message.content)
        if urls != []:
            print('URLs and Attachments:')
            for n, url in enumerate(urls):
                print(f'   #{n}: {url}')

            for n, url in enumerate(urls):
                print(f'Checking link {n}: ', end='')
                
                if '://tenor.com/' in url:
                    print(f'Link {n} is a tenor gif')
                    url = await utils.get_tenor_gif(url)
                    await utils.react_image(message, url)

                elif await utils.is_url_img(url):
                    print(f'Link {n} is an image!')
                    await utils.react_image(message, url)
            print('='*50)

        if len(message.content) == 0: # Attachment only / channel status message
            return

        if str(message.channel) in presets.BLOCKED_CHANNELS:
            print(f'[x] REJECTING MESSAGE FROM CHANNEL: #{message.channel} (BLOCKED)')
            return


        OUTPUT_MESSAGE = f'You shouldn\'t be seeing this... Please contact "{presets.OWNER_TAG}" on Discord to report this.\nThanks :)'

        # User commands
        if message.content[:9] == ".complete" or message.content[:9] == ".continue":
            in_text = message.content[10:]

            async with message.channel.typing():
                OUTPUT_MESSAGE = await utils.complete(in_text, message, length=128, temp=0.8, top_p=0.9)

        # Commands that require power ('!')
        elif str(message.author.id) == presets.OWNER_ID and clean_start:
            global bot_start_msg
            clean_start = 0
            if "bot_start_msg" not in globals():
                await message.author.send('Hold on... I\'m still starting up...')
                await asyncio.sleep(5)

            await utils.send_init_message(message, bot_start_msg)
            return

        elif str(message.author) in presets.POWERFUL and message.content[0] == '!':
            command = message.content[1:]

            if(command == "stop"):
                print("Stopping bot")
                await message.reply("Okay, I'm shutting down now")
                await message.channel.send("Have a nice day everyone and see you soon!")

                await asyncio.sleep(5)
                raise KeyboardInterrupt

            else:
                # OUTPUT_MESSAGE = "Error! Invalid command!\nPlease check your spelling and try again!"
                return

                
        elif str(message.channel) in presets.ADVENTURE_CHANNELS:
            print("In a text adventure channel")
            OUTPUT_MESSAGE = await utils.adventure(message)

        # Info
        elif message.content == ".help" or message.content == ".about" or message.content == ".info":
            print("\nPrinting about... ")
            OUTPUT_MESSAGE = presets.about_message
            await asyncio.sleep(1)

        # Reply to a message
        else:
            if await custom_commands.receive_message(message) is None:
                OUTPUT_MESSAGE = "NO_OUTPUT"
            else:
                try:
                    OUTPUT_MESSAGE = presets.PRESET_RESPONSES[str(message.content)]
                except KeyError:
                    OUTPUT_MESSAGE = "NO_OUTPUT"

        if OUTPUT_MESSAGE == "NO_OUTPUT":
            return

        elapsed_time = str(round(time.time() - START_TIME, 2))
        print(f"BOT Response: '{OUTPUT_MESSAGE}'. Responded in {elapsed_time} seconds.")

        # Wait for typing indicator
        # await asyncio.sleep(0.01)

        LEN_CAP = 1950
        while len(OUTPUT_MESSAGE) >= LEN_CAP:
            await message.reply(OUTPUT_MESSAGE[:LEN_CAP], allowed_mentions=presets.ALLOWED_MENTIONS)
            OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]

        await message.reply(OUTPUT_MESSAGE, allowed_mentions=presets.ALLOWED_MENTIONS)
        print('='*50)


def start_all():
    '''Start everything to run model'''
    global client, START_TIME

    START_TIME = time.time()

    print("[INFO] Starting script...", flush=True)

    # Initialize Discord dependancies
    print("[INFO] Initializing Discord dependancies...", flush=True)
    load_dotenv()
    client = discord.Client()
    print("[OK] Initialized Discord dependancies!", flush=True)

    # Check APIs
    print("[INFO] Initial API Check...", flush=True)
    interfacer.check_apis()
    print("[OK] Completed check!", flush=True)

    # Run Discord bot
    print("[INFO] Initializing Discord bot...", flush=True)
    init_discord_bot()
    print("[OK] Initialized Discord bot!", flush=True)

    # Get Discord token
    print("[INFO] Getting Discord token...", flush=True)
    token = os.getenv('DISCORD_TOKEN')
    print("[OK] Got Discord token!", flush=True)

    print("[OK] The Discord bot is running!... ⤵\n       ↪ Catch it before it gets away!\n", flush=True)
    client.run(token)

if __name__ == "__main__":
    start_all()
