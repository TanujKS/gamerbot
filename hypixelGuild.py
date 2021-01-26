import requests
data = requests.get(f"https://api.hypixel.net/guild?key=dba11918-7be7-49af-871f-0a0e56f2b41a&name=rebound").json()
print(data)
