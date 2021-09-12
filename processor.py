'''Takes inputs and parses and queues them to interface with the API'''
import re
import requests
import aiohttp
import random
import time
import discord

import interfacer
import presets

def get_urls(in_text):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    urls = [x[0] for x in re.findall(regex, in_text)]
    return [out[:(len(out) if out.find('?')==-1 else out.find('?'))] for out in urls]

async def is_url_img(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            print("HEADER:", response.headers["content-type"])
            return response.headers["content-type"].startswith('image/')

async def complete(in_text, message):
    if in_text == '':
        return "Bot can't take empty prompts!"

    # Manual typing as this part can last quite long
    async with message.channel.typing():
        START_TIME = time.time()
        loading_emote = random.choice(presets.LOADING_EMOTES)
        await message.add_reaction(loading_emote)
        raw_output_message = await interfacer.complete(in_text)
        # raw_output_message = raw_output_message.replace('\n', '\n> ')
        await message.clear_reaction(loading_emote)

        if raw_output_message.find("<|endoftext|>") != -1:
            raw_output_message = raw_output_message[:raw_output_message.find("<|endoftext|>")]

        if raw_output_message == "BUSY":
            print("API Rate limit")
            await message.add_reaction(random.choice(presets.BUSY_EMOTES))
            await message.reply('._.   Sorry, the API is currently busy. Please try again in a minute.')
            return "NO_OUTPUT"

        await message.add_reaction('✅')
        embedVar = discord.Embed(title="Generation Result:", description="Generated with `GPT-J-6B`, at temperature `0.8` and top_p `0.9`.\n*Elapsed:* `" + str(round(time.time()-START_TIME, 1)) + "` *seconds.*\nRequested by `" + str(message.author) + "`  at  <t:" + str(round(time.time())) + ":T>", color=0x00ff00)
        embedVar.add_field(name="Result:", value='[📝]' + in_text + '... [🤖] ...' + str(raw_output_message), inline=False)
        await message.reply(embed=embedVar)
        return "NO_OUTPUT"
        # return "       __**Generation result:**__\n***" + in_text + "*** " + str(raw_output_message)

async def react_image(message, attachment):
    global client

    print("Connecting to API...")
    
    result = await interfacer.react_image(attachment)

    print("Prediction result:", result)

    print("Reacting...")

    # Reactions are added if they pass a threshold for being a large enough proportion (PROP) of the last reaction (L), or main reaction (M)
    # Absolute Prop refers to the absolute percentage match
    LPROP_limit = 0.3
    MPROP_limit = 0.1
    APROP_limit = 0.02

    past_acc = 0.01
    orig_acc = result[0][2]
    for cur_reaction in result:
        if (cur_reaction[2]/100)<APROP_limit or (cur_reaction[2]/past_acc) < LPROP_limit or (cur_reaction[2]/orig_acc) < MPROP_limit:
            print("---\nThresholds not met, so NOT reacting with: ", end='')
            print(cur_reaction[0], "->  lprop:", round(cur_reaction[2]/past_acc, 2), ".        mprop:", round(cur_reaction[2]/orig_acc, 2))
            if cur_reaction[2] == orig_acc:
                await message.add_reaction('❓')
                # await message.add_reaction('❔')
            break
        else:
            print(cur_reaction[0], "->  lprop:", round(cur_reaction[2]/past_acc, 2), ".        mprop:", round(cur_reaction[2]/orig_acc, 2))
            past_acc = cur_reaction[2]
            await message.add_reaction(cur_reaction[1])
    print("Done.")
    return


if __name__ == '__main__':
    import main
    main.start_all()
    # print("This is a module and is not supposed to be run directly.\nPlease try running main.py instead")
