'''Takes inputs and parses and queues them to interface with the API'''
import re
import requests
import random
import discord

import interfacer
import presets

def get_urls(in_text):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    urls = [x[0] for x in re.findall(regex, in_text)]
    return [out[:(len(out) if out.find('?')==-1 else out.find('?'))] for out in urls]

def is_url_img(url):
    r = requests.head(url)
    return r.headers["content-type"].startswith('image/')

async def complete(in_text, message):
    if in_text == '':
        return "Bot can't take empty prompts!"

    # Manual typing as this part can last quite long
    async with message.channel.typing():
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
        embedVar = discord.Embed(title="Completion result:", description="Generated using `GPT-J-6B`, temp=`0.8`, top-k=`0.9`", color=0x00ff00)
        embedVar.add_field(name="Input:", value=in_text, inline=False)
        embedVar.add_field(name="Output:", value=str(raw_output_message), inline=False)
        await message.channel.send(embed=embedVar)
        return "NO_OUTPUT"
        # return "       __**Generation result:**__\n***" + in_text + "*** " + str(raw_output_message)

async def react_image(message, attachment):
    global client

    print("Connecting to API...")
    
    result = await interfacer.react_image(attachment)

    print("Prediction result:", result)

    print("Reacting...")

    past_acc = 6.0
    orig_acc = result[0][2]
    for cur_reaction in result:
        print(cur_reaction[0], "->  lprop:", round(cur_reaction[2]/past_acc, 2), ".        mprop:", round(cur_reaction[2]/orig_acc, 2))
        if (cur_reaction[2]/past_acc) < 0.3 or (cur_reaction[2]/orig_acc) < 0.7:
            if cur_reaction[2] == orig_acc:
                await message.add_reaction('❓')
                # await message.add_reaction('❔')
            break
        else:
            past_acc = cur_reaction[2]
            await message.add_reaction(cur_reaction[1])
    print("Done.")
    return


if __name__ == '__main__':
    import main
    main.start_all()
    # print("This is a module and is not supposed to be run directly.\nPlease try running main.py instead")
