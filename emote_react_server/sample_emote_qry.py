import json
import time
import requests

url = 'http://192.168.1.63:9995/engines/react_emote/?'
errors = ["RATE_LIMITED", "API_ERROR", "NO_PROMPT"]

# Adding empty header as parameters are being sent in payload
def run_prompt(query_input, top_p=0.9, temp=0.8, length=128):
    if query_input is None or query_input == '':
        print("Error: No input received!")
        return "NO_INPUT"
    
    # print(query_input, top_p, temp, length)
    params = "url=" + str(query_input)
    # print(query)

    print("Querying server...")
    start_time = time.time()
    response = requests.get(url, params=params)

    if response.status_code == 200:
        print("Query received! Elapsed:", round(time.time()-start_time,2), "seconds.")
        print("Response:", response.json()[0])
        return response.json()[1]
    else:
        print("Error accessing API!")
        print(response.status_code)
        print(response.content)
        return "API_ERROR"

if __name__ == "__main__":
    # q = "https://nzbird.com/bird.jpg"
    q = "https://nzbird.com/botfox.png"
    result = run_prompt(q)
    if result not in errors:
        print(result)

