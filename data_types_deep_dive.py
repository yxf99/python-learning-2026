#数据类型深入
from variables_practice import is_student

#1. int
age = 26
year = 2026
temprature = -5
print(f"Int examples: {age}, {year}, {temprature}")

#2. float 小数
height = 1.72
price = 99999
percentage = 99.9
print(f"Float examples: {age}, {height}, {price}, {percentage}")

#3. string
name = "Xufang"
city = "Beijing"
message = "I am learning"
print(f"string examples: {name}, {city}, {message}")

#4. Boolean
is_raining = True
is_student = False
print(f"bool examples: {is_raining}, {is_student}")

#5. 类型转换
age_as_string = str(age) + " years old"
price_as_int = int(price)
text_to_number = float("3.12")

print()
print("Type conversions:")
print(f"Age as string: '{age_as_string}' (type: {type(age_as_string)})")
print(f"Price as int: '{price_as_int}' (type: {type(price_as_int)})")
print(f"text as Float: '{text_to_number}' (type: {type(price_as_int)})")

#6. 字符串合并
greeting = "Hello"
name = "Beauty"
full_msg = greeting + " "+ name
print()
print(f"String concatenation: {full_msg}")

#7. 字符串转换方法
text = "grapes"
print(f'Orginal string: {text}')
print(f"Uppercase: {text.upper()}")
print(f"Lowercase: {text.lower()}")
print(f"Capitalized: {text.capitalize()}")
print(f"Title: {text.title()}")
print(f"Length: {len(text)}")

