# 1. 用 try/except + 状态码判断,写一个完整的请求
#    测三种情况:
#    - https://httpbin.org/get              → 200
#    - https://httpbin.org/status/500       → 走 else
#    - https://httpbon.org/get              → 走 except(故意拼错)

import requests

urls = ["https://httpbin.org/status/200","https://httpbin.org/status/500","https://httpbon.org/get" ]

for url in urls:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"{url} 成功: {response.status_code}")
        else:
            print(f"{url}失败: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{url}无法加载: {e}")


# 2. 用 https://httpbin.org/delay/10 加 timeout=3
#    看看超时是什么样

url = "https://httpbin.org/delay/10"
try:
    response = requests.get(url, timeout=3)
    print(response.status_code)
except requests.exceptions.RequestException as e:
    print(f"{e}")

# 3. 写成函数
#    def fetch(url):
#        返回 (成功与否, 数据或错误信息)
#    这样以后调 API 都能复用

def fetch(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f'成功: {response.status_code}'
        else:
            return f'失败: {response.status_code}'
    except requests.exceptions.RequestException as e:
        return f"{e}"

fetch("https://httpbin.org/get")
fetch("https://httpbin.org/status/404")

# 用 fetch 查这三个 GitHub 用户,打印每人的仓库数
users = ["yxf99", "torvalds", "thisuserdoesnotexist12345"]
# 第三个会 404,应该走失败分支

def fetch_user(user):
    try:
        response = requests.get(f"https://api.github.com/users/{user}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            #它之前在 if 外面,意味着 404 时也会执行。GitHub 的 404 恰好也返回 JSON,所以没炸——但换个 API 就会炸,因为很多服务器出错时返回的是 HTML,.json() 直接抛异常
            return True, data["public_repos"]
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, str(e)

for user in users:
    ok, result = fetch_user(user)#这是拆包 —— 函数返回了两个值,你用两个变量同时接住。
    if ok:
        print(f"{user}: {result} 个仓库")
    else:
        print(f"{user}: 查询失败 ({result})")