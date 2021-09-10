import json
import time
import requests

last_qry = time.time() - 30 # Last query was over 30 seconds ago (hopefully)

url = 'https://api.eleuther.ai/completion'
headers = {"Accept": "application/json","Content-Type": "application/json","User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36"}
errors = ["RATE_LIMITED", "API_ERROR", "NO_PROMPT"]

# Adding empty header as parameters are being sent in payload
def run_prompt(query_input, top_p=0.9, temp=0.8, length=128):
    global last_qry

    if query_input is None or query_input == '':
        print("Error: No input received!")
        return "NO_INPUT"
    
    # print(query_input, top_p, temp, length)
    query = {"context":str(query_input),"top-p":str(top_p),"temp":str(temp),"response-length":str(length),"remove-input":"1"}
    # print(query)

    print("Querying server...")
    start_time = time.time()
    response = requests.post(url, data=json.dumps(query), headers=headers)

    if response.status_code == 200:
        print("Completion received! Elapsed:", round(time.time()-start_time,2), "seconds.")
        print(response.json()[0]['generated_text'])
        last_qry = time.time()
        return response.json()[0]['generated_text']
    elif response.status_code == 503:
        print("You are being rate limited by the API! :/")
        last_qry = time.time() # wait another 30 seconds
        return "RATE_LIMITED"
    else:
        print("Error accessing API!")
        print(response.status_code)
        print(response.content)
        return "API_ERROR"

async def query(qry):
    global last_qry

    rate_limit = (time.time() - last_qry) < 30 # bool whether it's currently rate limited
    if rate_limit:
        print("Warning; Predicted rate limit.")
        return "BUSY"
    result = run_prompt(qry)
    if result not in errors:
        print(result)
        return result
    elif result == "RATE_LIMITED":
        print("Warning! Reached API Rate limit!")
        last_qry = time.time() # wait another 30 seconds
    else:
        print("ERROR: ", result)

if __name__ == "__main__":
    for i in range(10):
        q = input("Enter a prompt> ")
        result = "NO_PROMPT"

        while result in errors:
            result = run_prompt(q)
            if result not in errors:
                print(result)
                print("Waiting for rate limit to pass...")
                time.sleep(30)
            else:
                print("ERROR: ", result)
                if result == "RATE_LIMITED":
                    time.sleep(30)
                else:
                    time.sleep(1)
                    break
                print("Retrying...")

