
"""
Project 1: 学生成绩分类系统

功能说明：
- 接收用户输入的学生分数
- 自动将分数转换为等级（A/B/C/D/F）
- 计算统计信息（平均、最高、最低）
- 支持输入多个学生的分数

使用方法：
1. 运行程序
2. 输入分数（0-100）
3. 程序显示等级
4. 输入'quit'退出
5. 查看统计结果

作者：[你的名字]
日期：2026年8月17日
"""
# 功能：接收分数，分类为等级，计算统计
# 时间：Week 1-2

print("="*50)
print("学生成绩分类系统")
print("="*50)

# 创建空列表存储所有分数
all_scores = []

while True:
    user_input = input("\请输入学生分数 或输入quit退出：")

    if user_input.lower() == "quit":
        print("\退出系统")
        break

    try:
        score = float(user_input)

        if 0 <= score <= 100:
            all_scores.append(score)

            if score >= 90:
                grade = "A"
            elif score >= 80:
                grade = "B"
            elif score >= 70:
                grade = "C"
            elif score >= 60:
                grade = "D"
            else :
                grade = "F"

            print(f"分数 {score} -> 等级 {grade}")
        else:
            print("✗ 请输入0-100之间的分数")

    except ValueError:
        print("please enter correct number")
if all_scores:
    print("\n" + "="*50)
    print("统计结果")
    print("=" * 50)
    print(f"总分数数量: {len(all_scores)}")
    print(f"平均分: {sum(all_scores) / len(all_scores):.2f}")
    print(f"最高分: {max(all_scores)}")
    print(f"最低分: {min(all_scores)}")
else:
    print("\n没有输入任何分数")
