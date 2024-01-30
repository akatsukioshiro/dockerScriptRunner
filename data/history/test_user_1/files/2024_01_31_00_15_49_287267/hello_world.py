import requests, json

req = requests.get("https://jsonplaceholder.typicode.com/todos/1").text
print(json.dumps(json.loads(req), indent=2))