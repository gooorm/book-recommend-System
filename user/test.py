import requests

REST_API_KEY = "79647d5a8395e6b28b6e21d66f852344"

url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
params = {
    "x": 126.92831675617963,
    "y": 37.36157716799082
}
headers = {
    "Authorization": f"KakaoAK {REST_API_KEY}"
}

res = requests.get(url, params=params, headers=headers)

print(res.status_code)
print(res.text)