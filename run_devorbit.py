#!/usr/bin/env python3
"""Example script to run Devorbit programmatically."""

from devorbit import Devorbit


# Initialize with Gemini
client = Devorbit(provider="gemini", api_key="AIzaSyC7-immDgKVyNRl167P1x0xfRrBKDufmrA")

# Your prompt here
prompt = input("Enter your prompt: ")

print("\n=== Devorbit Response ===\n")

# Send message and get response
message = client.messages.create(
    model="gemini-2.0-flash", max_tokens=4096, messages=[{"role": "user", "content": prompt}]
)

# Print the response
print(message.content[0].text)
print(message.content[0].text)
