import requests

user = requests.get("http://127.0.0.1:5000/api/v1/wardrobe/1,2,3")
print(user.json())