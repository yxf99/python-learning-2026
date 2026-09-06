"""通用 API 调用工具"""

import requests


def call_api(url, method="GET", headers=None, payload=None, timeout=5):
    """
    调用一个 API。

    返回 (成功与否, 数据或错误信息)
    """
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, str(e)


if __name__ == "__main__":
    print(call_api("https://httpbin.org/get"))
    print(call_api("https://httpbin.org/status/500"))
    print(call_api("https://httpbon.org/get"))