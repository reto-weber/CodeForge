#!/usr/bin/env python3
import requests
import json

# Test multi-file Eiffel compilation
url = "http://localhost:8000/compile"

# Simple Eiffel test case
payload = {
    "language": "eiffel",
    "files": [
        {
            "name": "hello_world.e",
            "content": """class
	HELLO_WORLD

create
	make

feature
	make
			-- Print hello world message
		do
			print ("Hello, World!%N")
		end

end
"""
        },
        {
            "name": "new_file.e", 
            "content": """class
	NEW_FILE

create
	make

feature
	make
			-- Print hello world message
		do
			print ("Hello, new file!%N")
		end

end
"""
        }
    ],
    "main_file": "hello_world.e"
}

headers = {
    "Content-Type": "application/json"
}

print("Testing multi-file Eiffel compilation...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
