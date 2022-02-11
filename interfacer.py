'''Interact with the model'''

#!python

import time
import aiohttp
import json

import presets

async def react_image(url_in):
    '''Respond to a given image'''  
    params = {"url": url_in}
    # print(query)

    print("Querying server...")
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(presets.EMOTE_SERVER, params=params) as response:
            if response.status == 200:
                print("Query received! Elapsed:", round(time.time()-start_time,2), "seconds.")
                return await response.json()
            else:
                print("Error accessing API!")
                print(f'Error {response.status}: {response.reason}')
                return "API_ERROR"

async def complete(txt_in, length, temp, top_p):
    '''Respond to a given prompt'''  
    params = {"query_text": txt_in, "length": length, "temp": str(temp), "top_p": str(top_p)}
    # print(query)

    print("Querying server...")
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(presets.COMPLETION_SERVER, params=params) as response:
            if response.status == 200:
                print("Query received! Elapsed:", round(time.time()-start_time,2), "seconds.")
                return await response.json()
            else:
                print("Error accessing API!")
                print(response.status)
                print(response.content)
                return "INTERNAL_API_CONNECTION_ERROR"

def exit_things():
    '''Save queue, logs, etc.'''
    return

def check_apis():
    print("  Checking APIs...")
    # Todo

    print("  Skipped... Not implemented")

if __name__ == '__main__':
    print("This is a module and is not supposed to be run directly.\nPlease try running main.py instead")
