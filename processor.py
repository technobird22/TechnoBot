'''Takes inputs and parses and queues them to interface with the API'''
import interfacer

async def complete(in_text, message):
    if in_text == '':
        return "Bot can't take empty prompts!"

    # Manual typing as this part can last quite long
    async with message.channel.typing():
        raw_output_message = await interfacer.complete(in_text)
        # raw_output_message = raw_output_message.replace('\n', '\n> ')

        if raw_output_message.find("<|endoftext|>") != -1:
            raw_output_message = raw_output_message[:raw_output_message.find("<|endoftext|>")]

        if raw_output_message == "BUSY":
            print("API Rate limit")
            await message.add_reaction('🟥')
            # await message.add_reaction('<:dino_dark:790119668815364097>')
            await message.reply('._.   Sorry, the API is currently busy. Please try again in a minute.')
            return "NO_OUTPUT"

        return "       __**Generation result:**__\n***" + in_text + "*** " + str(raw_output_message)

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
    print("This is a module and is not supposed to be run directly.\nPlease try running main.py instead")
