'''Main file'''

import discord
from discord.ext import tasks
import asyncio

import os
import time
import random
from dotenv import load_dotenv

import presets
import interfaces
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

        if not status_loop.is_running():
            status_loop.start()
        bot_start_msg = f'Initialised in **{elapsed_time}** seconds. Current Time: `{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())} UTC`\nConnected to: ```diff\n{joined_servers}```'

        print("[OK] Initialised!")

    @client.event
    async def on_message(message):
        global clean_start

        START_TIME = time.time()

        if message.author == client.user:
            return

        if len(message.content) > 50:
            print('-'*75)

        print('{0: <22}'.format(f'{message.guild} '), end='')
        print('{0: <22}'.format(f'> #{message.channel} '), end='')
        print('{0: <22}'.format(f'> {message.author} '), end='')

        if len(message.content) > 50:
            print(f":  ⤵\n  > '{message.content}'.\n{'-'*75}")
        else:
            print(f"> '{message.content}'.")


        if str(message.channel).startswith('Direct Message with ') and presets.IGNORE_DMS and not str(message.channel) == f'Direct Message with {presets.OWNER_TAG}':
            print("^^^ Ignoring Direct message. ^^^")
            return

        if message.channel.is_nsfw() and presets.IGNORE_NSFW:
            print("--> Ignoring NSFW Channel.")
            return

        urls = [attachment.url for attachment in message.attachments] + utils.get_urls(message.content)
        for embed in message.embeds:
            if embed.image.url is not discord.Embed.Empty:
                urls.append(embed.image.url)
        if urls != []:
            print('URLs and Attachments:')
            for n, url in enumerate(urls):
                print(f'   #{n}: {url}')

            for n, url in enumerate(urls):
                print(f'Checking link {n}: ', end='')
                
                if '://tenor.com/' in url:
                    print(f'Link {n} is a tenor gif')
                    url = await utils.get_tenor_gif(url)
                elif await utils.is_url_img(url):
                    print(f'Link {n} is an image!')
                else:
                    print(f'Link {n} is not an image!')
                    continue

                # await utils.react_image(message, url)
                # await custom_commands.receive_image(message, url)

                # Do in another new thread
                asyncio.get_event_loop().create_task(utils.react_image(message, url))
                asyncio.get_event_loop().create_task(custom_commands.receive_image(message, url))
            print('='*50)

        if len(message.content) == 0: # Attachment only / channel status message
            return

        if str(message.channel) in presets.BLOCKED_CHANNELS:
            print(f'[x] REJECTING MESSAGE FROM CHANNEL: #{message.channel} (BLOCKED)')
            return


        out_message = f'You shouldn\'t be seeing this... Please contact "{presets.OWNER_TAG}" on Discord to report this.\nThanks :)'

        # User commands
        if message.content[:9] == ".complete" or message.content[:9] == ".continue":
            in_text = message.content[10:]

            async with message.channel.typing():
                out_message = await utils.complete(in_text, message, length=128, temp=0.8, top_p=0.9)

        # Commands that require power ('!')
        elif str(message.author.id) == presets.OWNER_ID and clean_start:
            global bot_start_msg
            clean_start = 0
            if "bot_start_msg" not in globals():
                await message.author.send('Hold on... I\'m still starting up...')
                await asyncio.sleep(5)

            await utils.send_init_message(message, bot_start_msg)
            return

        elif str(message.author.id) in presets.POWERFUL and message.content[0] == '!':
            command = message.content[1:]

            if command.startswith("status"):
                print("Updating status...")
                await message.channel.send(f'Updating status...\n`{command[7:]}`')
                await utils.update_status(client, command[7:])

            if(command == "stop"):
                print("Stopping bot")
                await message.reply("Okay, I'm shutting down now")
                await message.channel.send("Have a nice day everyone and see you soon!")

                await asyncio.sleep(5)
                raise KeyboardInterrupt

            else:
                # out_message = "Error! Invalid command!\nPlease check your spelling and try again!"
                return

                
        elif str(message.channel) in presets.ADVENTURE_CHANNELS:
            print("In a text adventure channel")
            out_message = await utils.adventure(message)

        # Info
        elif message.content == ".help" or message.content == ".about" or message.content == ".info":
            print("\nPrinting about... ")
            out_message = presets.about_message
            await asyncio.sleep(1)

        # Reply to a message
        else:
            if await custom_commands.receive_message(message) is None:
                out_message = "NO_OUTPUT"
            else:
                try:
                    out_message = presets.PRESET_RESPONSES[message.content]
                except KeyError:
                    out_message = "NO_OUTPUT"

        if out_message == "NO_OUTPUT":
            return

        elapsed_time = str(round(time.time() - START_TIME, 2))
        print(f"BOT Response: '{out_message}'. Responded in {elapsed_time} seconds.")

        # Wait for typing indicator
        # await asyncio.sleep(0.01)

        LEN_CAP = 1950
        while len(out_message) >= LEN_CAP:
            await message.reply(out_message[:LEN_CAP], allowed_mentions=presets.ALLOWED_MENTIONS)
            out_message = out_message[LEN_CAP:]

        await message.reply(out_message, allowed_mentions=presets.ALLOWED_MENTIONS)
        print('='*50)


    @tasks.loop(seconds=1800)
    async def status_loop():
        status = random.choice(presets.STATUS_MESSAGES)
        print("Updating status to:", status)
        await utils.update_status(client, status)


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
    interfaces.check_apis()
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
