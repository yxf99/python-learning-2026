import csv
from api_call import call_api
from datetime import datetime

rows_out = []

result = {"成功": 0, "失败": 0}
with open("endpoints.csv",encoding="utf-8") as f: #打开文件,用完自动关 encoding="utf-8" 防止中文乱码
    reader = csv.DictReader(f)#把每行读成字典

    for row in reader:
        ok, data = call_api(row["url"])
        rows_out.append({ #—— 转换模板。遍历一个列表,加工后放进新列表,只是这次加工出来的是字典。
            "name": row["name"],
            "url": row["url"],
            "status": "OK" if ok else "ERROR",
            "detail": "" if ok else str(data)
        })
        if ok:
            result["成功"] += 1
        else:
            result["失败"] += 1

filename = f"results_{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"  #—— 生成 2026-09-06_1430 这种时间戳,每次跑不覆盖上次的结果。

with open(filename, "w", encoding="utf-8", newline="") as f: #newline —— 写 CSV 必须加,否则 Windows 上每行之间多一个空行。照抄,别问为什么。
    writer = csv.DictWriter(f, fieldnames=["name", "url", "status", "detail"]) # 声明列名
    writer.writeheader()  # 写表头
    writer.writerows(rows_out) # 写数据

print(f"共 {result['成功'] + result['失败']} 个,成功 {result['成功']},失败 {result['失败']}")

