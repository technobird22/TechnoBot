'''Takes inputs and parses and queues them to interface with the API'''
import asyncio
import re
import requests
import aiohttp
import random
import math
import time
import datetime
import discord

import interfacer
import presets

history = []
prompt = presets.ADVENTURE_PROMPT

def get_urls(in_text):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    urls = [x[0] for x in re.findall(regex, in_text)]
    return [out[:(len(out) if out.find('?')==-1 else out.find('?'))] for out in urls]

async def is_url_img(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            print("HEADER:", response.headers["content-type"])
            return response.headers["content-type"].startswith('image/')

async def adventure(message):
    global history, prompt
    bot_start = '[story]'
    human_start = '[action]'

    if message.content.startswith(">"):
        print("IGNORING: MANUAL IGNORE")
        return "NO_OUTPUT"

    if message.content.startswith(".prompt "):
        prompt = str(message.content)[9:]
        return "Successfully set prompt!"

    if message.content == ".getprompt":
        return prompt

    history.append("[action] " + message.content + "\n")
    result = await complete(prompt + '\n' + ''.join(history), message, length=64, temp=0.8, top_p=0.9, output_type="raw")

    if result == "API_BUSY":
        return "NO_OUTPUT"

    try:
        start_index = result.find(bot_start)+len(bot_start)+1
        print("start_index:", start_index)
        parsed_output = result[start_index:]
        parsed_output = parsed_output[:parsed_output.find(human_start)]
        print("Parsed output:", parsed_output)
        print("Truncated:", result[:result.find(bot_start)])
    except:
        return "huh."

    history.append("[story] " + parsed_output + "\n")
    return parsed_output


async def complete(in_text, message, length, temp, top_p, output_type="embed"):
    if in_text == '':
        return "Bot can't take empty prompts!"

    # Manual typing as this part can last quite long
    async with message.channel.typing():
        START_TIME = time.time()
        loading_emote = random.choice(presets.LOADING_EMOTES)
        await message.add_reaction(loading_emote)
        raw_output_message = await interfacer.complete(in_text, length=length, temp=temp, top_p=top_p)
        # raw_output_message = raw_output_message.replace('\n', '\n> ')
        await message.clear_reaction(loading_emote)

        if raw_output_message.find("<|endoftext|>") != -1:
            raw_output_message = raw_output_message[:raw_output_message.find("<|endoftext|>")]

        if raw_output_message == "BUSY":
            print("API Rate limit")
            busy_emote = random.choice(presets.BUSY_EMOTES)
            await message.add_reaction(busy_emote)
            reply = await message.reply('._.   Sorry, the API is currently busy. Please try again in a minute.')
            await asyncio.sleep(30)
            await message.clear_reaction(busy_emote)
            await message.add_reaction('🔁')
            await reply.delete()

            if output_type == "raw":
                return "API_BUSY"
            return "NO_OUTPUT"

        await message.add_reaction('✅')


        LEN_CAP = max(1, 1900 - len(in_text))
        print("LC:", LEN_CAP)
        part_num = 1
        parts_cnt = math.ceil((len(raw_output_message)+1-(1900-len(in_text)))/1900) + 1

        if output_type == "raw":
            return raw_output_message

        embedVar = discord.Embed(title="Generation Result", description="`Model: GPT-J-6B, length="+str(length)+", temp="+str(temp)+", top_p="+str(top_p)+". Elapsed: " + str(round(time.time()-START_TIME, 1)) + "s.`", color=0x00ff00, timestamp=datetime.datetime.utcnow())
        embedVar.description += '\n***' + in_text + '*** ' + raw_output_message[:LEN_CAP] + '...'
        embedVar.set_footer(text="Part " + str(part_num) + " of " + str(parts_cnt) + ". Requested by " + str(message.author))
        print("SENDING:", raw_output_message[:LEN_CAP])
        await message.reply(embed=embedVar,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        if len(raw_output_message) >= LEN_CAP:
            raw_output_message = raw_output_message[LEN_CAP:]
        else:
            raw_output_message = ''

        LEN_CAP = 1900
        while len(raw_output_message) > 0:
            part_num += 1

            embedVar = discord.Embed(title="Generation Result (continued)", description='', color=0x00ff00, timestamp=datetime.datetime.utcnow())
            embedVar.description += '...' + raw_output_message[:LEN_CAP] + '...'
            embedVar.set_footer(text="Part " + str(part_num) + " of " + str(parts_cnt) + ". Requested by " + str(message.author))
            print("SENDING:", raw_output_message[:LEN_CAP])
            await message.reply(embed=embedVar,
                    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

            if len(raw_output_message) >= LEN_CAP:
                raw_output_message = raw_output_message[LEN_CAP:]
            else:
                break

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
    LPROP_limit = 0.31
    MPROP_limit = 0.5
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
