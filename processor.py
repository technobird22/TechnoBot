'''Takes inputs and parses and queues them to interface with the API'''
import asyncio
import json
import re
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
bot_temp = 0.9

async def list_saves(message):
    data = json.load(open('adventure_presets.json'))

    embedVar = discord.Embed(title="Saves/Presets", description='To load a save, run `.load [NAME OF SAVE]`\nTo create a save of the current message history, run `.save [SAVE_NAME]`!', color=0x00ff00, timestamp=datetime.datetime.utcnow())
    preset_names = str(''.join([('- "'+cur+'"\n') for cur in data['presets'].keys()]))
    save_names = str(''.join([('- "'+cur+'"\n') for cur in data['saves'].keys()]))
    legacy_names = str(''.join([('- "'+cur+'"\n') for cur in data['legacy_saves'].keys()]))
    print(preset_names)
    print(save_names)
    embedVar.add_field(name="Presets", value=preset_names, inline=False)
    if len(save_names) != 0:
        embedVar.add_field(name="User saves", value=save_names, inline=False)
    if len(legacy_names) != 0:
        embedVar.add_field(name="Legacy saves", value=legacy_names, inline=False)
    await message.reply(embed=embedVar)

def load(preset_name):
    data = json.load(open('adventure_presets.json'))

    print("Loading preset:", preset_name)

    try:
        result = data['presets'][preset_name]
        return result
    except KeyError:
        print("Not a preset...")

    try:
        result = data['saves'][preset_name]
        return result
    except KeyError:
        print("Not a save..")

    try:
        result = data['legacy_saves'][preset_name]
        return result
    except KeyError:
        print("Not a legacy save...")
        return "NOT_FOUND"

def save(savename):
    data = json.load(open('adventure_presets.json'))
    print("Saving as:", savename)

    if savename in data["presets"] or savename in data["saves"]:
        print("Already taken!")
        return "TAKEN"
    else:
        print("Adding to dict...")
        data["saves"][savename] = prompt + ''.join(history)
        print("Writing to savefile...")
        json.dump(data, open('adventure_presets.json', 'w'))
        print("Done")
        return "OK"

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
    global history, prompt, bot_temp
    # bot_start = ''
    human_start = '>'

    if message.content.startswith(".clearhistory"):
        history = []
        return "Successfully cleared history!"

    if message.content.startswith(".continue"):
        return "btw, continue commands don't work here. Try using another channel that isn't in adventure mode"

    if message.content == ".save":
        return "To create a save, please give a name under which the save will be created\nEg. `.save this is the name of the save`"

    if message.content.startswith(".setprompt"):
        prompt = str(message.content)[11:] + '\n'
        history = []
        return "Successfully set prompt!"

    if message.content.startswith(".load"):
        data = load(str(message.content)[6:])
        if data == "NOT_FOUND":
            return "Save not found! :/\nTo view available saves, use `.listsaves` to view available saves"
        prompt = data
        history = []
        return "Successfully loaded the prompt!\nYou can check it with `.getprompt` :)"

    if message.content == ".listsaves" or message.content == ".saves":
        await list_saves(message)
        return "NO_OUTPUT"

    if message.content.startswith(".save "):
        savename = str(message.content)[6:]

        result = save(savename)
        if result == "TAKEN":
            return "The name '"+savename+"' has been used already!\nPlease try saving it under a different name."
        return "Successfully saved current context under '"+savename+"'!\nBtw, you can continue using the current context; nothing in history has been modified :)"

    if message.content.startswith(".temp"):
        print("Changing temperature...")
        try:
            await message.channel.send('Changing temperature to `' + message.content[6:] + '`!')
            bot_temp = float(message.content[6:])
            await message.channel.send('Done! New settings now in place.')
        except:
            print("Invalid float")
            await message.channel.send('Hmm, was `' + message.content[6:] + '` a valid float?')
        return

    if message.content == ".help":
        return presets.ADVENTURE_HELP

    if message.content == ".getprompt":
        await raw_long_output(message, prompt)
        return "NO_OUTPUT"

    if message.content == ".geteverything":
        await long_output(message, prompt + '------------------------------\n' + ''.join(history), "idk")
        return "NO_OUTPUT"

    if message.content == ".getdata" or message.content == ".getsave":
        await raw_long_output(message, '.setprompt ' + prompt + ''.join(history))
        return "NO_OUTPUT"

    if not message.content.startswith(">"):
        print("IGNORING: IGNORE NON PROMPT")
        return "NO_OUTPUT"

    if message.content[1] != ' ':
        return "btw, if you're doing an action for adventure mode, you'll have to have a `SPACE` (' ') between the `>` and the start of your action!"

    print("ADDING:" + human_start + ' ' + message.content[2:] + "\n")
    for attempt in range(3):
        result = await complete(prompt + ''.join(history) + human_start + ' ' + message.content[2:] + "\n", message, length=128, temp=bot_temp, top_p=0.9, output_type="raw")
        result = result.strip()
        if len(result) > 1 and result[0] != human_start:
            break
        await message.reply("Hmm... The model's responses aren't being parsed correctly...\nHold on, I'll give it another try")
        await asyncio.sleep(20)
        bot_temp += 0.1
    else:
        return "Warning: The model's responses aren't being parsed correctly\nDoes the prompt follow the correct format for adventure mode?"

    if result == "API_BUSY":
        return "NO_OUTPUT"
    
    if result == "WARNING: GENERAL ERROR":
        return "Strange... Something went wrong... Maybe the prompt is too long? Try `.clearhistory`?"

    # Save to history
    history.append(human_start + ' ' + message.content[2:] + "\n")

    try:
        start_index = 0
        print('-'*30)
        print("Raw Output:", result)
        print("start_index:", start_index)
        print('-'*30)
        print("Truncated (start):", result[:start_index])
        parsed_output = result[start_index:]

        print('-'*30)
        print("Truncated (end):", result[parsed_output.find(human_start)-1:])
        parsed_output = parsed_output[:parsed_output.find(human_start)-1]
        # parsed_output = parsed_output.replace(bot_start + ' ', '')
        print('-'*30)
        print("Parsed output:", parsed_output)
        print('-'*30)
    except:
        return "huh. model output didn't contain tokens I'm looking for (`>`)...\nMaybe the API glitched? Try again? Otherwise it could be the prompt or something... Try changing that..."

    history.append(' ' + parsed_output + "\n")
    return parsed_output

async def long_output(message, OUTPUT_MESSAGE, parts_cnt):
    LEN_CAP = max(1, 1900)
    print("LC:", LEN_CAP)
    part_num = 1

    embedVar = discord.Embed(title="Generation Result", description=OUTPUT_MESSAGE[:LEN_CAP]+'...', color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embedVar.set_footer(text="Part " + str(part_num) + " of " + str(parts_cnt) + ". Requested by " + str(message.author))
    print("SENDING:", OUTPUT_MESSAGE[:LEN_CAP])
    await message.reply(embed=embedVar,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    if len(OUTPUT_MESSAGE) >= LEN_CAP:
        OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]
    else:
        OUTPUT_MESSAGE = ''

    LEN_CAP = 1900
    while len(OUTPUT_MESSAGE) > 0:
        part_num += 1

        embedVar = discord.Embed(title="Generation Result (continued)", description='...'+OUTPUT_MESSAGE[:LEN_CAP]+'...', color=0x00ff00, timestamp=datetime.datetime.utcnow())
        embedVar.set_footer(text="Part " + str(part_num) + " of " + str(parts_cnt) + ". Requested by " + str(message.author))
        print("SENDING:", OUTPUT_MESSAGE[:LEN_CAP])
        await message.reply(embed=embedVar,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        if len(OUTPUT_MESSAGE) >= LEN_CAP:
            OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]
        else:
            break

async def raw_long_output(message, OUTPUT_MESSAGE):
    LEN_CAP = max(1, 1900)
    print("LC:", LEN_CAP)
    part_num = 1

    embedVar = discord.Embed(title="Savefile", description='```md\n'+OUTPUT_MESSAGE[:LEN_CAP]+'```', color=0xff0000, timestamp=datetime.datetime.utcnow(), )
    print("SENDING:", OUTPUT_MESSAGE[:LEN_CAP])
    await message.reply(embed=embedVar,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    if len(OUTPUT_MESSAGE) >= LEN_CAP:
        OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]
    else:
        OUTPUT_MESSAGE = ''

    LEN_CAP = 1900
    while len(OUTPUT_MESSAGE) > 0:
        part_num += 1

        embedVar = discord.Embed(title="Savefile (continued)", description='```'+OUTPUT_MESSAGE[:LEN_CAP]+'```', color=0xff0000, timestamp=datetime.datetime.utcnow())
        print("SENDING:", OUTPUT_MESSAGE[:LEN_CAP])
        await message.reply(embed=embedVar,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        if len(OUTPUT_MESSAGE) >= LEN_CAP:
            OUTPUT_MESSAGE = OUTPUT_MESSAGE[LEN_CAP:]
        else:
            break


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
            await asyncio.sleep(20)
            await message.clear_reaction(busy_emote)
            await message.add_reaction('🔁')
            await reply.delete()

            if output_type == "raw":
                return "API_BUSY"
            return "NO_OUTPUT"

        await message.add_reaction('✅')

        if output_type == "raw":
            return raw_output_message

        model_info = "`Model: GPT-J-6B, length="+str(length)+", temp="+str(temp)+", top_p="+str(top_p)+". Elapsed: " + str(round(time.time()-START_TIME, 1)) + "s.`"
        output = '\n***' + in_text + '*** ' + raw_output_message
        parts_cnt = math.ceil((len(raw_output_message)+1-(1900-len(in_text)))/1900) + 1
        await long_output(message, model_info+output, parts_cnt)

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
