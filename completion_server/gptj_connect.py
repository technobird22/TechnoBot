import json
import time
import aiohttp

RATE_LIMIT_TIME = 20

last_qry = time.time() - RATE_LIMIT_TIME # Last query was over RATE_LIMIT_TIME seconds ago (hopefully)

url = 'https://api.eleuther.ai/completion'
headers = {"Accept": "application/json","Content-Type": "application/json","User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36"}
errors = ["RATE_LIMITED", "API_ERROR", "NO_PROMPT"]

# Adding empty header as parameters are being sent in payload
async def run_prompt(query_input, length=128, temp=0.8, top_p=0.9):
    global last_qry

    if query_input is None or query_input == '':
        print("Error: No input received!")
        return "NO_INPUT"
    
    # print(query_input, top_p, temp, length)
    query = {"context":str(query_input),"topP":str(top_p),"temp":str(temp),"response_length":str(length),"remove-input":"true"}
    # print(query)

    print("Querying server...")
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json.dumps(query), headers=headers) as response:
            if response.status == 200:
                print("Result received! Elapsed:", round(time.time()-start_time,2), "seconds.")
                # print(response.json()[0]['generated_text'])
                last_qry = time.time()
                return (await response.json())[0]['generated_text']
            elif response.status == 503:
                print("You are being rate limited by the API! :/")
                last_qry = time.time() # wait another RATE_LIMIT_TIME seconds
                return "RATE_LIMITED"
            else:
                print("Error accessing API!")
                print(response.status)
                print(response.content)
                return "API_ERROR"

async def query(qry, length, temp, top_p):
    global last_qry

    rate_limit = (time.time() - last_qry) < RATE_LIMIT_TIME # bool whether it's currently rate limited
    if rate_limit:
        print("Warning; Predicted rate limit.")
        return "BUSY"

    result = await run_prompt(qry, length=length, temp=temp, top_p=top_p)
    if result not in errors:
        print("RESULT:", result)
        return result

    elif result == "RATE_LIMITED":
        print("Warning! Reached API Rate limit!")
        last_qry = time.time() # wait another RATE_LIMIT_TIME seconds
        return "BUSY"
    else:
        print("ERROR: ", result)
        return "WARNING: GENERAL ERROR"

if __name__ == "__main__":
    for i in range(10):
        q = input("Enter a prompt> ")
        result = "NO_PROMPT"

        while result in errors:
            result = run_prompt(q, 128, 0.8, 0.9)
            if result not in errors:
                print(result)
                print("Waiting for rate limit to pass...")
                time.sleep(RATE_LIMIT_TIME)
            else:
                print("ERROR: ", result)
                if result == "RATE_LIMITED":
                    time.sleep(RATE_LIMIT_TIME)
                else:
                    time.sleep(1)
                    break
                print("Retrying...")

