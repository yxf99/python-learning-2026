def greeting(name):
    return f"Hello, {name}!"

message = greeting("Alice")
print(message)
print(greeting("Bob"))

# 写一个函数 double,输入一个数,返回它的两倍
# 测试:
# print(double(5))    → 10
# print(double(12))   → 24
def double(num):
    return num * 2
print(double(5))
print(double(12))

# 写一个函数 rectangle_area,输入长和宽,返回面积
# print(rectangle_area(3, 4))    → 12
def rectangle_area(long,width):
    return long * width
print(rectangle_area(3,4))

# 写一个函数 sum_list,输入一个列表,返回总和
# print(sum_list([1, 2, 3, 4]))      → 10
# print(sum_list([10, 20, 30]))      → 60
def sum_list(lst):
    somme = 0
    for num in lst:
        somme += num
    return somme
print(sum_list([1,2,3,4]))

# 写一个函数 count_multiples,输入一个数字 n,
# 返回 1 到 100 里有几个 n 的倍数
# print(count_multiples(7))     → 14
# print(count_multiples(10))    → 10

def count_multiples(n):
    count = 0
    for num in range(1,100):
        if num % n == 0:
            count += 1
    return count

print(count_multiples(7))

# 写一个函数 greet(name, greeting="你好")
# print(greet("Alice"))          → 你好, Alice!
# print(greet("Bob", "Hi"))      → Hi, Bob!
def greet(name, greeting = "Hello"):
    return f"{greeting} {name}"
print(greet("Alice", "Hi"))

# 写一个函数 min_max,输入列表,同时返回最小值和最大值
# low, high = min_max([78, 92, 65, 88])
# print(low, high)    → 65 92
def min_max(lst):
    return min(lst), max(lst)
print(min_max([1,2,3,4,5,6]))

# 把你之前写的"统计状态码次数"改成函数
# def count_status(logs): ...
#
# result = count_status(["200", "404", "200"])
# print(result)    → {'200': 2, '404': 1}
def count_status(log):
    code = {}
    for num in log:
        if num not in code:
            code[num] = 1
        else:
            code[num] += 1
    return code
print(count_status(["200", "404", "200"]))

scores = [85, 92, 78, 95, 88]

# 写两个函数:
# - average(scores) 返回平均分
# - grade(score) 输入一个分数返回等级(90+ A, 80+ B, 70+ C, 其他 D)
#
# 然后组合:
# avg = average(scores)
# print(f"平均分 {avg:.1f},等级 {grade(avg)}")
# → 平均分 87.6,等级 B
def average(scores):
    return sum(scores) / len(scores)
def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    else :
        return "D"
avg = average([85, 92, 78, 95, 88])
print(f'平均分 {avg:.1f}, 等级 {grade(avg)}')