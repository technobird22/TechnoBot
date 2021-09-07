'''Interact with the model'''

#!python

import os
import sys
import time
import requests

import json
import numpy as np

import presets
import processor

def change_len(new_len):
    global length
    length = new_len
    print("Successfully changed len")

def change_temp(new_temp):
    global temperature
    temperature = new_temp
    print("Successfully changed temp")

def init_params():
    global length, temperature, top_k, top_p
    length = 128
    temperature = 0.8
    top_k = 40
    top_p = 0.9

async def react_image(url_in):
    '''Respond to a given image'''  
    params = "url=" + str(url_in)
    # print(query)

    print("Querying server...")
    start_time = time.time()
    response = requests.get(presets.EMOTE_SERVER, params=params)

    if response.status_code == 200:
        print("Query received! Elapsed:", round(time.time()-start_time,2), "seconds.")
        return response.json()
    else:
        print("Error accessing API!")
        print(response.status_code)
        print(response.content)
        return "API_ERROR"

async def complete(txt_in):
    '''Respond to a given prompt'''  
    params = "query_text=" + str(txt_in)
    # print(query)

    print("Querying server...")
    start_time = time.time()
    response = requests.get(presets.COMPLETION_SERVER, params=params)

    if response.status_code == 200:
        print("Query received! Elapsed:", round(time.time()-start_time,2), "seconds.")
        return response.json()
    else:
        print("Error accessing API!")
        print(response.status_code)
        print(response.content)
        return "API_ERROR"

def exit_things():
    '''Save queue, logs, etc.'''
    return

def respond_raw_inp(cur_inp):
    '''Take raw input and return unformatted output for the given number of iterations'''
    print("Generating...")

    start_time = time.time()

    output_msg = respond(cur_inp)

    elapsed = time.time() - start_time

    print("=" * 30 + " Generated Response: " + "=" * 30)
    print("Elapsed", round(elapsed, 1), "seconds. Generated:\n", output_msg)
    print("=" * 80)
    return output_msg

def initialise():
    print("Initialising interfaces...")
    init_params()

if __name__ == '__main__':
    init_params()

    # raw_inp(5)
    print("This is a module and is not supposed to be run directly.\nPlease use main.py instead")
