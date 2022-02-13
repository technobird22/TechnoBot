'''Takes inputs and parses and queues them to interface with the API'''
import discord
import asyncio
import aiohttp

import math
import time
import datetime
import random
import json
import re

import interfaces
import presets

history = []
prompt = presets.ADVENTURE_PROMPT
bot_temp = 0.7

SHORT_SPACER = '-'*30
SPACER = '-'*60

async def update_status(client, status):
    if status.startswith('Listening to '):
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status[13:]))
    elif status.startswith('Playing '):
        await client.change_presence(activity=discord.Game(name=status[8:]))
    elif status.startswith('Watching '):
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status[9:]))
    else:
        await client.change_presence(activity=discord.Activity(name=status))

async def list_saves(message):
    data = json.load(open('adventure_presets.json'))

    embedVar = discord.Embed(title="Saves/Presets", description='To load a save, run `.load [NAME OF SAVE]`\nTo create a save of the current message history, run `.save [SAVE_NAME]`!', color=0x00ff00, timestamp=datetime.datetime.utcnow())
    preset_names = str(''.join([(f'- "{cur}"\n') for cur in data['presets'].keys()]))
    save_names = str(''.join([(f'- "{cur}"\n') for cur in data['saves'].keys()]))
    legacy_names = str(''.join([(f'- "{cur}"\n') for cur in data['legacy_saves'].keys()]))
    print(preset_names)
    print(save_names)
    embedVar.add_field(name="Presets", value=preset_names, inline=False)
    if len(save_names) != 0:
        embedVar.add_field(name="User saves", value=save_names, inline=False)
    # if len(legacy_names) != 0:
    #     embedVar.add_field(name="Legacy saves", value=legacy_names, inline=False)
    await message.reply(embed=embedVar)

def load(preset_name):
    data = json.load(open('adventure_presets.json'))

    print(f'Loading preset "{preset_name}"...')

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
    print(f'Saving as: "{savename}"')

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
            print(f'Header is "{response.headers["content-type"]}"')
            # return response.headers["content-type"].startswith('image/') or response.headers["content-type"].startswith('video/')
            return response.headers["content-type"].startswith('image/')

async def get_tenor_gif(url):
    # if 'c.tenor.com/' in url:
    #     print("Already a raw tenor gif!")
    #     return url

    print('Sending Tenor request... ', end='', flush=True)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            assert response.status == 200
            response_text = await response.text()
            print('Response received!', flush=True)
            try:
                gif_url = re.findall(r'<meta class="dynamic" property="og:url" content="(.*?)"', response_text)[0]
                print(f'Extracted gif url: "{gif_url}"')
            except UnicodeDecodeError:
                print('Unicode error!')
                gif_url = None
    return gif_url

async def adventure(message):
    global history, prompt, bot_temp

    if message.content.startswith(".clearhistory"):
        history = []
        return 'Successfully cleared history!'

    if message.content.startswith(".continue") or message.content.startswith(".complete"):
        return 'btw, continue commands don\'t work here. Try using another channel that isn\'t in adventure mode'

    # Helpful messages
    if message.content == ".save":
        return 'To create a save, please give a name under which the save will be created\nEg. `.save [NAME OF SAVE]`'

    if message.content == ".load":
        return 'To load a save, please give the name of the save\nEg. `.load [savename]`'

    if message.content == ".temp":
        return f'The current temperature for adventure mode is `{bot_temp}`\nYou can set a new temp with `.temp [NEW TEMP]`'

    # Utility commands
    if message.content == ".trim":
        print(SHORT_SPACER)
        print("Trimmed off:", history[:8])
        print(SPACER)
        print("Keeping:", history[8:])
        print(SHORT_SPACER)
        history = history[8:]
        return "Trimmed off the first `4` messages from history!"

    if message.content == ".undo":
        print(SHORT_SPACER)
        print("Deleting last messages from history:", history[-2:])
        print(SPACER)
        print("Keeping:", history[:-2])
        print(SPACER)
        history = history[:-2]
        return "Undid the last action!"

    if message.content.startswith(".setprompt"):
        prompt = str(message.content)[11:] + '\n\n'
        history = []
        return "Successfully set prompt!"

    if message.content.startswith(".load"):
        data = load(str(message.content)[6:])
        if data == "NOT_FOUND":
            return "Save not found! :/\nTo view available saves, use `.listsaves` to view available saves"
        prompt = data
        history = []
        return "Successfully loaded the prompt!\nYou can check it with `.getprompt` :)"

    if message.content.startswith(".peek"):
        data = load(str(message.content)[6:])
        if data == "NOT_FOUND":
            return "Save not found! :/\nTo view available saves, use `.listsaves` to view available saves"
        await raw_long_output(message, data)
        return 'NO_OUTPUT'

    if message.content == ".listsaves" or message.content == ".saves":
        await list_saves(message)
        return 'NO_OUTPUT'

    if message.content.startswith(".save "):
        savename = str(message.content)[6:]

        result = save(savename)
        if result == "TAKEN":
            return f'The name "{savename}" has been used already!\nPlease try saving it under a different name.'
        return f'Successfully saved current context under "{savename}"!'

    if message.content.startswith(".temp"):
        print("Changing temperature...")
        try:
            await message.channel.send(f'Changing temperature to `{message.content[6:]}`...')
            bot_temp = float(message.content[6:])
            await message.channel.send('Done! New settings now in place.')
        except:
            print("Invalid float")
            await message.channel.send(f'Hmm, was `{message.content[6:]}` a valid float?')
        return 'NO_OUTPUT'

    if message.content == ".help":
        return presets.ADVENTURE_HELP

    if message.content == ".getprompt":
        await raw_long_output(message, prompt)
        return 'NO_OUTPUT'

    if message.content == ".geteverything":
        await long_output(message, f'{prompt}==========< ***New (unsaved) history below*** >==========\n{"".join(history)}', "unknown")
        return 'NO_OUTPUT'

    if message.content == ".getsave":
        await raw_long_output(message, f'.setprompt {prompt} {"".join(history)}')
        return 'NO_OUTPUT'

    if message.content == "$":
        await message.channel.send('Continuing previous message...')
        return await adventure_action('', message)

    if message.content.startswith("$"):
        if message.content[1] != ' ':
            return 'Please add a **space** (\' \') between the `$` and the start of your adventure inject and try again.'

        history[-1] = f'{history[-1][:-1]} {message.content[2:]}\n'
        await message.channel.send('Injected action. Continuing from action...')
        return await adventure_action('', message)

    if not message.content.startswith(">"):
        print("IGNORING: Not a command")
        return 'NO_OUTPUT'

    if message.content[1] != ' ':
        return "btw, if you're doing an action for adventure mode, please add a `SPACE` (' ') between the `>` and the start of your action!"


    return await adventure_action(message.content, message)


async def adventure_action(action, message):
    global history, prompt, bot_temp
    
    # bot_start = ''
    human_start = '>'

    is_completion = action == ''
    if is_completion:
        print("Continuing previous messages...")
        history[-1] = history[-1].rstrip() # Cut off newline so model will complete last output
    else:
        print(f"Generating adventure step for prompt: {human_start} {action[2:]}\n")

    for attempt in range(1):
        if is_completion:
            result = await complete(prompt + ''.join(history), message, length=128, temp=bot_temp, top_p=0.98, output_type="raw")
        else:
            result = await complete(f'{prompt}{"".join(history)}{human_start} {action[2:]}\n', message, length=256, temp=bot_temp, top_p=0.98, output_type="raw")

        result = result.strip()
        if result == "WARNING: GENERAL ERROR":
            history = history[1:]
            continue
        if len(result) > 1 and result[0] != human_start:
            break
        # await message.reply("Hmm... The model's responses aren't being parsed correctly...\nHold on, I'll give it another try")
        # await asyncio.sleep(20)
        # bot_temp += 0.1
    else:
        if not result:
            return "The model already decided to end it's message, and refuses to elaborate further... Try an action instead ⚔"
        return f"Warning: The model's responses aren't being parsed correctly\nDoes the prompt follow the correct format for adventure mode?\n\nHere's what the model is returning:\n```{result}```. It should be returning something like this:\n```Foo\n> Bar\nBaz```"

    if result == "API_BUSY":
        return 'NO_OUTPUT'
    
    # if result == "WARNING: GENERAL ERROR":
    #     return "Strange... Something went wrong... Maybe the prompt is too long? Try `.clearhistory`?"

    # Save to history
    if not is_completion:
        history.append(f'{human_start} {action[2:]}\n')

    try:
        start_index = 0
        print(SHORT_SPACER)
        print("Raw Output:", result)
        print("start_index:", start_index)
        print(SHORT_SPACER)
        print("Truncated (start):", result[:start_index])
        parsed_output = result[start_index:]

        print(SHORT_SPACER)
        # print("Truncated (end):", result[parsed_output.find(human_start)-1:])
        if human_start in result:
            parsed_output = parsed_output[:parsed_output.find(human_start)-1]
        elif result[-1] != '.' and '.' in result:
            parsed_output = result[:result.rfind('.')+1]
        # parsed_output = parsed_output.replace(bot_start + ' ', '')
        print(SHORT_SPACER)
        print("Parsed output:", parsed_output)
        print(SHORT_SPACER)
    except:
        return "Huh. The model output didn't contain tokens I'm looking for (`>`)...\nMaybe the API glitched? Try again? Otherwise it could be the prompt or something... Try changing that..."

    if is_completion:
        history[-1] += f' {parsed_output}\n'
    else:
        history.append(f' {parsed_output}\n')

    return parsed_output


async def long_output(message, out_message, parts_cnt):
    LEN_CAP = max(1, 1900)
    print("LC:", LEN_CAP)
    part_num = 1

    embedVar = discord.Embed(title="Generation Result", description=out_message[:LEN_CAP]+'...', color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embedVar.set_footer(text=f'Part {part_num} of {parts_cnt}. Requested by {message.author}.')
    print("SENDING:", out_message[:LEN_CAP])
    await message.reply(embed=embedVar,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    if len(out_message) >= LEN_CAP:
        out_message = out_message[LEN_CAP:]
    else:
        out_message = ''

    LEN_CAP = 1900
    while len(out_message) > 0:
        part_num += 1

        embedVar = discord.Embed(title="Generation Result (continued)", description=f'...{out_message[:LEN_CAP]}...', color=0x00ff00, timestamp=datetime.datetime.utcnow())
        embedVar.set_footer(text=f'Part {part_num} of {parts_cnt}. Requested by {message.author}.')
        print("SENDING:", out_message[:LEN_CAP])
        await message.reply(embed=embedVar,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        if len(out_message) >= LEN_CAP:
            out_message = out_message[LEN_CAP:]
        else:
            break

async def raw_long_output(message, out_message):
    LEN_CAP = max(1, 1900)
    print("LC:", LEN_CAP)
    part_num = 1

    embedVar = discord.Embed(title="Output", description=f'```md\n{out_message[:LEN_CAP]}```', color=0xff0000, timestamp=datetime.datetime.utcnow())
    print("SENDING:", out_message[:LEN_CAP])
    await message.reply(embed=embedVar,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    if len(out_message) >= LEN_CAP:
        out_message = out_message[LEN_CAP:]
    else:
        out_message = ''

    LEN_CAP = 1900
    while len(out_message) > 0:
        part_num += 1

        embedVar = discord.Embed(title="Output (continued)", description=f'```{out_message[:LEN_CAP]}```', color=0xff0000, timestamp=datetime.datetime.utcnow())
        print("SENDING:", out_message[:LEN_CAP])
        await message.reply(embed=embedVar,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        if len(out_message) >= LEN_CAP:
            out_message = out_message[LEN_CAP:]
        else:
            break


async def complete(in_text, message, length, temp, top_p, output_type="embed"):
    if in_text == '':
        return "`complete` can't take empty prompts! What do you want me to autocomplete?"

    async with message.channel.typing():
        START_TIME = time.time()
        loading_emote = random.choice(presets.LOADING_EMOTES)
        await message.add_reaction(loading_emote)
        raw_output_message = await interfaces.complete(in_text, length=length, temp=temp, top_p=top_p)
        # raw_output_message = raw_output_message.replace('\n', '\n> ')
        await message.clear_reaction(loading_emote)

        if raw_output_message.find("<|endoftext|>") != -1:
            raw_output_message = raw_output_message[:raw_output_message.find("<|endoftext|>")]

        if raw_output_message == "BUSY":
            print("API Rate limit")
            busy_emote = random.choice(presets.SAD_EMOTES)
            await message.add_reaction(sad_emote)
            reply = await message.reply('._.   Sorry, the API is currently busy. Please try again in a minute.')
            await asyncio.sleep(20)
            await message.clear_reaction(busy_emote)
            await message.add_reaction('🔁')
            await reply.delete()

            if output_type == "raw":
                return "API_BUSY"
            return 'NO_OUTPUT'

        if raw_output_message == "WARNING: GENERAL ERROR":
            print("API Error (general)")
            busy_emote = random.choice(presets.SAD_EMOTES)
            await message.add_reaction(sad_emote)
            reply = await message.reply('._.  Something went wrong with the completion API. Please retry shortly.')
            await asyncio.sleep(20)
            await message.clear_reaction(busy_emote)
            await message.add_reaction('🔁')

            if output_type == "raw":
                return "API_ERROR"
            return 'NO_OUTPUT'

        await message.add_reaction('✅')

        if output_type == "raw":
            return raw_output_message

        model_info = f'`Model: GPT-J-6B, length={length}, temp={temp}, top_p={top_p}. Elapsed: {round(time.time()-START_TIME, 1)}s.`'
        output = f'\n***{in_text}*** {raw_output_message}'
        parts_cnt = math.ceil((len(raw_output_message)+1-(1900-len(in_text)))/1900) + 1
    await long_output(message, model_info + output, parts_cnt)

    return 'NO_OUTPUT'
    # return f'       __**Generation result:**__\n***{in_text}*** {raw_output_message}'

async def react_image(message, attachment):
    global client

    # print("Connecting to API...")
    
    result = await interfaces.react_image(attachment)
    if result == "API_ERROR":
        await message.reply('Image reaction API error. What content are you sending? Videos are currently not supported Please try again later.')
        # await message.add_reaction('')
        return

    # print("Prediction result:", result)

    print("Adding reactions...")

    # Reactions are added if they pass a threshold for being a large enough proportion (prop) of the last reaction (L), or main reaction (M)
    # Absolute Prop refers to the absolute percentage match
    LPROP_limit = 0.31
    MPROP_limit = 0.5
    APROP_limit = 0.02

    past_acc = 0.01
    orig_acc = result[0][2]
    for cur_reaction in result:
        if (cur_reaction[2]/100)<APROP_limit or (cur_reaction[2]/past_acc) < LPROP_limit or (cur_reaction[2]/orig_acc) < MPROP_limit:
            print("Thresholds not met, so NOT reacting with: ", end='')
            print(f'{"{:4.2f}".format(cur_reaction[2])}% => ', end='')
            print(f'[ {cur_reaction[1]} ]: {cur_reaction[0]} ->  lprop: {round(cur_reaction[2]/past_acc, 2)}.        mprop: {round(cur_reaction[2]/orig_acc, 2)}')
            if cur_reaction[2] == orig_acc:
                # await message.add_reaction('❔')
                pass
            break
        else:
            print(f'{"{:6.2f}".format(cur_reaction[2])}% => ', end='')
            print('{0: <7}'.format(f'[ {cur_reaction[1]} ]') + '{0: <35}'.format(f'{cur_reaction[0]} -> '), end='')
            print('{0: <20}'.format(f'lprop: {round(cur_reaction[2]/past_acc, 2)}.'), end='')
            print(f'mprop: {round(cur_reaction[2]/orig_acc, 2)}')
            past_acc = cur_reaction[2]
            try:
                await message.add_reaction(cur_reaction[1])
            except:
                print("Reaction failed:", cur_reaction[0])
    print("Done.")
    print(SHORT_SPACER)
    return

async def send_init_message(message, bot_start_msg):
    HORIZ_RULE = f'~~{" "*160}~~'
    SHORT_HORIZ_RULE = f'~~{" "*50}~~'
    vowels = ['a', 'e', 'i', 'o', 'u']
    positive_things = ['great', 'wonderful', 'awesome', 'well', 'okay', 'fantastic', 'amazing', 'excellent']
    quote = random.choice(presets.QUOTES)

    await message.author.send(f'{HORIZ_RULE}\n**{random.choice(presets.GREETINGS)} {presets.OWNER_NAME}!** :)\nJust finished starting up <t:{int(time.time())}:R> {random.choice(presets.START_EMOTES)} \nHope you\'re doing {random.choice(positive_things)}!')
    await message.author.send(f'{SHORT_HORIZ_RULE}\n{bot_start_msg}')
    await message.author.send(f'''{HORIZ_RULE}
    **__Error log:__**
        `Empty :)`

    **__Unfinished request queue:__** *(`0` pending)*
        `Nothing here! :)`
    ''')
    if quote[0] == '':
        quote[0] = 'Unknown'
    await message.author.send(f'{HORIZ_RULE}\n> ***"{quote[1]}"***\n            *- {quote[0]}*')

    positive_descriptor = random.choice(presets.GOOD_THINGS)
    if positive_descriptor[0].lower() in vowels:
        indefinite_article = "an"
    else:
        indefinite_article = "a"
    await message.author.send(f'{HORIZ_RULE}\nHave {indefinite_article} {positive_descriptor} day!')

    if str(message.channel) != f'Direct Message with {presets.OWNER_TAG}' and presets.STARTUP_REMINDER:
        msg_alert = await message.channel.send(f'<@!{presets.OWNER_ID}> Psst. Check your DMs {random.choice(presets.START_EMOTES)}')
        await asyncio.sleep(5)
        await msg_alert.delete()

if __name__ == '__main__':
    print("This is a module and is not supposed to be run directly.\nPlease try running main.py instead")
