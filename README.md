# !BS GDB Solution
Solution to !BS GDB CTF
https://websec.co.il/nobs

# Compression Side-Channel Attack Writeup

## Overview

A user creates a new note via the **POST** endpoint.  
After that, the user calls the **report** endpoint.

The server generates a string that contains the titles and IDs, where `title,id` are separated by a comma and each entry ends with `\n`.  
This result is then passed into the `deflateRaw` function, which performs compression.
The compressed data is subsequently encrypted using AES, encoded in base64, and returned to the client.

---

## Compression Mechanism

The compression mechanism works by detecting patterns and shortening them.  
For example, compressing the string `"AAAAA"` will produce a binary representation meaning **"A appears 5 times"**.

In the context of this challenge, it is possible to create a note whose title itself contains a comma.  
Because compression is applied, this creates a potential **side-channel attack**.

---

## Legitimate Server State

In a legitimate state, the data on the server (returned by the `notesToCSV` function, with IDs represented as hex) looks like this:

```flag,A2F4CFF1F1\nmynote,B1F2AFF2F2```

When a request is sent to the **report** endpoint, the data is first compressed, then encrypted using **AES**, and returned as **base64**.

---

## Side-Channel Attack

Theoretically, if I create a note whose title contains the name of a note that I know already exists (for example, `mynote`) and then append the character `B`, which I know is the beginning of the ID, the compression process will shorten the repeated patterns.

- If compression occurs → the output size is **smaller**
- If compression does not occur → the output size is **larger** (at least for the ID portion)

After compression, the data is encrypted with AES and encoded with base64.  
By observing the **Content-Length**, it is possible to determine when compression occurred and when it did not.

---

## Practical Considerations

To verify that this theory works, I considered three things:

1. I use the **PUT** endpoint, which allows changing the title of an existing note.  
   This avoids creating a new note each time and allows iterative guesses such as `"flag,A"` or `"flag,0"`.
2. AES encryption works on a block size of **16 bytes**.  
   For example, encrypting `'AAAAA'` gives 16 bytes, while encrypting 17 `'A'`s gives 32 bytes. The extra bytes come from padding to fill AES’s 16-byte blocks.
   In this challenge, the same idea applies but on a base of **4**, meaning the compression output must land on the correct padding boundary before encryption.  
   If compression produces 4 bytes or less, it aligns differently than if it produces 5 bytes, in which case AES padding adds 3 bytes.  
4. When guessing the ID, I only use hexadecimal characters: `0–9` and `A–F`.

---

## Exploitation

I created two notes: one for testing and one acting as a test flag.  
The test flag note is named `"getme"` and its ID is `"550C0AC005"`.

When I edited my test note’s title to `"getme,5"` and requested the report, the response size was smaller compared to using `"getme,1"`, `"getme,A"`, etc.  
This indicated a successful guess.

However, sometimes all hexadecimal guesses produced the same response size.  
This happens because of the **4-byte padding** that AES uses in this challenge.

To overcome this, I prepended characters to the title:

- `"title,?"`
- `"Atitle,?"`
- `"AAtitle,?"`

Eventually, this aligned with the correct AES padding and revealed the correct character of the `"getme"` ID.

---

## Result

<img width="348" height="238" alt="image" src="https://github.com/user-attachments/assets/b09eb765-fdeb-497d-baf2-ff1323112047" />

I wrote a script that automates this process and targets a note named `"flag"` (the code explicitly assumes such a note exists).  
The script successfully recovered the ID of that note, allowing me to read its contents and obtain the flag:

**BS{c0mpr3ss10n_15_fun!}**


```
import requests
URL = "" # replace with ctf uri
MY_NOTE_ID = "AAAAAAAAAA" # replace with a note ID that you will need to create at the endpoint "POST /note"
found_id = "" 

for i in range(10): # Guessing a 10-char hex ID
    best_char = None
    for p in range(1337):
        results = []
        for char in "0123456789ABCDEF":
            # Using 'flag,' prefix to target the actual secret
            payload = {"title": ("Z"*p) + (f"flag,{found_id}{char}"), "content": "a"}
            requests.put(f"{URL}/note/{MY_NOTE_ID}", json=payload)
            size = len(requests.get(f"{URL}/report").json()['encrypted'])
            results.append((size, char))
        results.sort()
        if results[0][0] < results[-1][0]:
            best_char = results[0][1]
            break
    found_id += (best_char if best_char else "?")
    print(f"Pos {i} | Current Flag ID: {found_id}")
```
