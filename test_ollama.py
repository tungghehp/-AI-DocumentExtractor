import requests

url = "http://192.168.1.83:11434/api/generate"

data = {
    "model": "qwen3-vl:4b",
    "prompt": "Viết đoạn văn 300 từ về qwen 3.5",
    "stream": False
}

response = requests.post(url, json=data)

print(response.json())