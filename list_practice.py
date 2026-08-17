#切片+列表

#切片 sequence[start:end:step(每隔几个取一个)]

str1 = "hello world"

print(str1[::])      # hello world  → 全部（start/end/step都省略）
print(str1[:])       # hello world  → 全部
print(str1[1::])     # ello world   → 从索引1到最后
print(str1[2::2])    # low r        → 从索引2开始，每隔2个取一个
print(str1[1:9:1])   # ello wor     → 索引1到8（不含9）
print(str1[1:3])     # el           → 索引1到2（不含3）
print(str1[-10:-1])  # ello worl    → 倒数第10到倒数第2（不含-1）
print(str1[-10:])    # ello world   → 倒数第10到最后

#最实用！！！
str1 = "hello world"

str1[:5]      # 'hello'      前5个
str1[-5:]     # 'world'      后5个
str1[::-1]    # 'dlrow olleh' 反转！step=-1 最实用
str1[::2]     # 'hlowrd'     每隔一个取

#1. 创建列表
numbers = [10, 20, 30, 40, 50]
names = ["Alex", "Bob", "Carol", "Daniel"]
mix = [3, "hi", 3.45, True]

print("Lists")
print(f"numbers: {numbers}")
print(f"names: {names}")
print(f"mix: {mix}")

#2. 访问元素 （从0)

print()
print(f'First number: {numbers[0]}')
print(f'Last name: {names[-1]}')
print(f'Second name: {names[-2]}')

#3. List列表 [] 列表可以放任何东西 还可以嵌套列表
lst1 = [1, 2, 3, 4, "hello", [1, 2, 3]]
print(lst1)        # [1, 2, 3, 4, 'hello', [1, 2, 3]]
print(type(lst1))  # <class 'list'>

#列表也一样用切片
nums = [1, 2, 3, 4, 5, 6]

nums[1:4]     # [2, 3, 4]
nums[:3]      # [1, 2, 3]
nums[::-1]    # [6, 5, 4, 3, 2, 1]

#嵌套列表
a = [[1, 2],
     [2, 3]]
#取值要用两层索引
a[0]      # [1, 2]     第一行
a[0][1]   # 2          第一行的第二个元素
a[1][0]   # 2          第二行的第一个元素

