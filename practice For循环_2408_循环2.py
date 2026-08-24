from tkinter.messagebox import YESNO

logs = ["200", "404", "200", "500", "200"]
count_200 = 0

for log in logs:
    if log == "200":
        count_200 += 1

print(f'成功率是{count_200/len(logs) * 100}%')
#-----------
numbers = [12, 5, 88, 3, 47]
big_numbers = []
for num in numbers:
    if num > 10:
        big_numbers.append(num)

print(big_numbers)

#-----------
text = "hello world"
count_char = {}
for char in text:
    if char in count_char:
        count_char[char] += 1
    else:
        count_char[char] = 1
print(count_char)

#-----------
words = ["apple", "banana", "avocado", "blueberry", "cherry"]
groups = {}

for word in words:
    key = word[0]
    if key in groups:
        groups[key].append(word)
    else:
        groups[key] = [word]

print(groups)

#-------------
items = ["apple", "banana", "cherry"]
target = "banana"
found = None

for fruit in items:
    if fruit == target:
        found = items
        break
if found:
    print(found)
else:
    print("not found")

#--------
scores = [78, 92, 65, 88, 95, 71]
# 找出最高分和最低分
# 预期输出:
# 最高分: 95
# 最低分: 65
highst_score = scores[0]
lowst_score = scores[0]
#改正 并列if 递增数据里,每个数都刷新了最高分,于是永远走不到 else,最低分从头到尾没被检查过,还是初始的 100。
for score in scores:
    if score > highst_score:
        highst_score = score
    if score < lowst_score:
        lowst_score = score

print(highst_score, lowst_score)

#--------
prices = [12.5, 8.0, 23.9, 15.5]
# 算总价和平均价,平均价保留两位小数
# 预期输出:
# 总价: 59.9
# 平均价: 14.98
price_total = 0
for price in prices:
    price_total += price

price_average = price_total / len(prices)
print(price_total, round(price_average, 2))

#----------
apis = ["order-api", "customer-service", "payment-api", "auth-service", "stock-api"]
# 挑出所有以 -api 结尾的
# 预期: ['order-api', 'payment-api', 'stock-api']
list_apis = []
for api in apis:
    key = api.split("-")
    if key[-1] == "api":
        list_apis.append(api)

print(list_apis)

#-----------
names = ["alice smith", "bob jones", "carol white"]
# 每个名字首字母大写
# 预期: ['Alice Smith', 'Bob Jones', 'Carol White']
list_name = []
for name in names:
    list_name.append(name.title())
print(list_name)

#------------
methods = ["GET", "POST", "GET", "PUT", "GET", "POST", "DELETE"]
# 统计每种方法出现几次
# 预期: {'GET': 3, 'POST': 2, 'PUT': 1, 'DELETE': 1}
times = {}
for method in methods:
    if method in times:
        times[method] += 1
    else:
        times[method] = 1
print(times)

#--------------
apis = ["prod-order", "dev-order", "prod-payment", "test-auth", "dev-stock"]
# 按环境分组
# 预期: {'prod': ['prod-order', 'prod-payment'], 'dev': ['dev-order', 'dev-stock'], 'test': ['test-auth']}
env_api = {}
for api in apis:
    key = api.split("-")[0]
    if key in env_api:
        env_api[key].append(api)
    else:
        env_api[key] = [api]

print(env_api)

#----------------
logs = ["200 OK", "301 Moved", "200 OK", "500 Internal Error", "200 OK"]
have_500 = False
# 两件事:
# (a) 有没有 5xx 错误?
# (b) 找到第一个 5xx,把它打印出来
#
# 预期输出:
# 有5xx错误: True
# 第一个5xx: 500 Internal Error

for log in logs:
    if log[0] == "5":
        have_500 = True
        break

print(log, have_500)

#改正 循环结束后不要用循环变量。 要什么,循环里就存到独立变量里。
logs = ["200 OK", "301 Moved", "200 OK", "500 Internal Error", "200 OK"]
has_5xx = False
first_5xx = None

for log in logs:
    if log.startswith("5"):
        has_5xx = True
        first_5xx = log      # 存起来
        break

print(f"有5xx错误: {has_5xx}")
print(f"第一个5xx: {first_5xx}")

#-------------------
logs = ["200", "404", "200", "500", "200", "404", "403", "502"]
count_status = {}
count_200 = 0
count_4xx = 0
# 一个循环里同时完成:
# - 各状态码计数(计数字典)
# - 成功数,即 2xx 的个数(累加器)
# - 4xx 错误数(累加器)
#
# 预期输出:
# 各状态码: {'200': 3, '404': 2, '500': 1, '403': 1, '502': 1}
# 成功数: 3
# 4xx数: 3
# 成功率: 37.5%

for log in logs:
    if log in count_status:
        count_status[log] += 1
    else:
        count_status[log] = 1
    if log == "200":
        count_200 += 1
    elif log[0] == "4":
        count_4xx += 1

success_rate = count_200 / len(logs) * 100
print(count_status, count_200, count_4xx, f'{success_rate}%')