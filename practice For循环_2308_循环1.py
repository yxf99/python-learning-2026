#1.
import code

greeting = "Hello World"
print(greeting)
print(greeting.upper())
print(greeting.lower())
print(len(greeting))
print(greeting[0])
print(greeting[-1])

#2.
price = 99.999
count = 5
name = "Python"

print(f"价格: {price:.2f}")
print(f"计数: {count:05d}")
print(f"名字: {name:^10}")

#3.
for i in range(1, 6):
    print(i)

#4.
for i in range(0, 10, 2):
    print(i)

#5.
fruits = ["apple", "banana", "cherry"]
for i in fruits:
    print(f"{i}")

#6. 7的倍数
for i in range(1,101):
    if i % 7 == 0:
        print(i)

#7. 找最大值
numbers = [2, 5, 1, 9, 0]
max_number = numbers[0]
for i in numbers:
    if i > max_number:
        max_number = i

    print(max_number)

# practice

numbers = [5, 10, 15, 20]
sum = 0

for i in numbers:
    if i % 2 == 0:
        sum += i
print(sum)

text = "hello world"
count_o = 0
for i in text:
    if i == "o":
        count_o += 1
print(count_o)

list = [85, 92, 78, 95, 88]
sum_list = 0
for i in list:
    sum_list += i

print(sum_list/len(list))

logs = ["200", "404", "200", "500", "200"]
count_200 = 0
for i in logs:
    if i == "200":
        count_200 += 1

print(f'成功: {count_200}')
print(f'成功率:{count_200/len(logs) * 100}%')

logs = ["200", "404", "200", "500", "403", "404"]
count_4 = 0
for log in logs:
    if log.startswith("4"):
        count_4 += 1

print(count_4)

# 1. 从 [12, 5, 88, 3, 47] 里挑出大于 10 的
# 预期: [12, 88, 47]
lst = [12,5,88,3,47]
lst_2 = []
for i in lst:
    if i > 10:
        lst_2.append(i)

print(lst_2)

# 2. 把 ["200", "404", "500"] 转成整数列表
# 预期: [200, 404, 500]
lst = ["200", "404", "500"]
lst_2 = []
for i in lst:
    lst_2.append(int(i))

print(lst_2)

# 字典
text = "hello world"
count_dic = {}
for i in text:
    if i in count_dic:
        count_dic[i] += 1
    else:
        count_dic[i] = 1

print(count_dic)

# 统计每个状态码出现几次
# 预期: {'200': 3, '404': 2, '500': 1}
logs = ["200", "404", "200", "500", "200", "404"]
count_dic = {}
for code in logs:
    if code in count_dic:
        count_dic[code] += 1
    else:
        count_dic[code] = 1

print(count_dic)
