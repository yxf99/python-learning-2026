"""
A.3 练习 —— header 与 POST
日期:2026-08-26

规则:
- 一题一题做,做完立刻运行
- 卡住 15 分钟就跳过,在题号后面标个 TODO
- 允许翻之前的代码
"""
import os

import requests


# ============================================================
# 题 1 · 带 header 发 GET
# ============================================================
# 目标:
#   给 https://httpbin.org/get 发一个 GET
#   带上 header {"X-My-Name": "Xufang"}
#   从返回里找到这个 header 并打印出来
#
# 预期输出:
#   Xufang
#
# 提示:
#   headers 是个字典,直接传 headers=你的字典
#   返回的 JSON 里,data["headers"] 是一个字典

print("=" * 50)
print("题1 · 带 header 的 GET")
print("=" * 50)

# 你的代码写这里

url  = "https://httpbin.org/get"

headers = {
    "Authorization": f"Bearer {os.getenv('token')}",
    "X-My-Name" : "Xufang"
}

try:
    response = requests.get(url, headers=headers)
    print(headers["X-My-Name"])
except requests.exceptions.RequestException as e:
    print(e)

# ============================================================
# 题 2 · 发一个 POST
# ============================================================
# 目标:
#   给 https://httpbin.org/post 发一个 POST
#   body 里放三个字段:order_id、amount、status
#   打印返回里的 json 字段,确认三个都在
#
# 预期输出类似:
#   {'amount': 99.9, 'order_id': 'ORD-001', 'status': 'pending'}
#
# 提示:
#   requests.post(url, json=你的字典)
#   返回的 JSON 里,data["json"] 就是你发过去的 body

print()
print("=" * 50)
print("题2 · POST 请求")
print("=" * 50)

# 你的代码写这里

url = "https://httpbin.org/post"

headers = {
    "Authorization": f"Bearer {os.getenv('token')}"
}

payload = {
    "order_id":"ORD-001",
    "amount":"100",
    "status":"pending"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data_body = response.json()
        print(data_body["json"])
    else:
        print(response.status_code)
except requests.exceptions.RequestException as e:
    print(e)

# ============================================================
# 题 3 · 升级 fetch 函数(有点难)
# ============================================================
# 目标:
#   写一个通用函数,GET 和 POST 都能发
#   返回 (成功与否, 数据或错误信息)
#
# 骨架:
#
#   def call_api(url, method="GET", headers=None, payload=None):
#       try:
#           if method == "GET":
#               response = requests.get(url, headers=headers, timeout=5)
#           else:
#               response = requests.post(url, headers=headers, json=payload, timeout=5)
#
#           if response.status_code == 200:
#               return ___, ___
#           else:
#               return ___, ___
#       except requests.exceptions.RequestException as e:
#           return ___, ___
#
# 测试用例(三条路径都要走到):
#   call_api("https://httpbin.org/get")
#   call_api("https://httpbin.org/post", method="POST", payload={"a": 1})
#   call_api("https://httpbin.org/status/500")
#   call_api("https://httpbon.org/get")          ← 故意拼错,走 except

print()
print("=" * 50)
print("题3 · 通用 call_api 函数")
print("=" * 50)

# 你的代码写这里
def call_api(url, method="GET", headers = None, payload = None):
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        else :
            response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            return True, response.json() #要返回两个值 这样第一个值一下就知道是不是成功了
        else:
            return False, response.status_code
    except requests.exceptions.RequestException as e:
        return False, str(e)

ok, data = call_api("https://httpbin.org/get")

if ok:
    print("成功",data)
else:
    print("失败",data)

# ============================================================
# 题 4 · 综合(选做)
# ============================================================
# 目标:
#   用你的 call_api,批量检查下面这批地址
#   打印每个的结果
#
# 这就是"接口批量巡检脚本"的雏形

endpoints = [
    "https://httpbin.org/get",
    "https://httpbin.org/status/404",
    "https://httpbin.org/status/500",
    "https://api.github.com/users/yxf99",
    "https://httpbon.org/get",
]

# 预期输出类似:
#   ✅ https://httpbin.org/get
#   ⚠️  https://httpbin.org/status/404 — HTTP 404
#   ⚠️  https://httpbin.org/status/500 — HTTP 500
#   ✅ https://api.github.com/users/yxf99
#   ❌ https://httpbon.org/get — 连不上

print()
print("=" * 50)
print("题4 · 批量巡检")
print("=" * 50)

# 你的代码写这里


results = {"成功": 0, "失败": 0}

for endpoint in endpoints:
    ok, data = call_api(endpoint)
    if ok:
        print("✅", endpoint)
        results["成功"] += 1
    else:
        print("❌", endpoint, "—", data)
        results["失败"] += 1

print()

print(f"共 {len(endpoints)} 个,成功 {results['成功']},失败 {results['失败']}")