
import requests

response = requests.get("https://httpbin.org/get")

print(response.status_code)
print(response.text)

#从text到json .json() 把返回的字符串变成 Python 字典。 变成字典之后,就是你已经会的东西了——用方括号按 key 取值。
data = response.json()      # 字符串 → 字典

print(f'type = {type(data)}')           # <class 'dict'>
print(f'url = {data["url"]}')
print(f'header = {data["headers"]}')
print(f'origin = {data["origin"]}')

# 故意要一个 404
bad = requests.get("https://httpbin.org/status/404")
print(f'code_error = {bad.status_code}')


print("----一个真实的 API--这是 GitHub 的公开 API,查的是你自己的账号。-----")

response = requests.get("https://api.github.com/users/yxf99")
data = response.json()

if response.status_code == 200:
    print(data["login"])
    print(data["public_repos"])
    print(data["created_at"])

elif str(response.status_code).startswith("4"):
    print("请求有问题,检查参数或认证")
elif str(response.status_code).startswith("5"):
    print("服务器故障,稍后重试")

# 状态码抓不到
#状态码 404/500  →  连上了,对方给了个不好的答复  →  用 if 判断
#连接失败/超时    →  压根没连上,没有状态码       →  用 try/except
# timeout=5 —— 五秒没回应就放弃。不加这个,程序可能永远卡住。 生产环境的脚本必须加。

try:
    response = requests.get("https://httpbin.org/get", timeout=5)
    if response.status_code == 200:
        print(response.json()["origin"])
    else:
        print(f"失败: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"连不上: {e}")

