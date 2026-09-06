#这两个是集成场景里天天用的 你 MuleSoft 里配的 Authorization、Content-Type,就是 header;往 SAP 推数据,就是 POST。

import requests

url = "https://httpbin.org/post"

headers = {
    "Authorization": "Bearer fake-token-123",
    "Content-Type": "application/json"
}

payload = {
    "order_id": "ORD-001",
    "amount": 99.9
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("发出去的 headers:", data["headers"]["Authorization"])
        print("发出去的 body:", data["json"])
    else:
        print(f"失败: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"连不上: {e}")

