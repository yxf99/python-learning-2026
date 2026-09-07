import csv
import json
from datetime import datetime
from api_call import call_api
import sys

# base_url = "https://postman-echo.com"

with open("config.json", encoding="utf-8") as f:
    config = json.load(f) # 文件  →  Python 字典

#env = "prod"
env = sys.argv[1] if len(sys.argv) > 1 else "uat"  # ← 替换掉 env = "uat", 列表长度大于 1（说明有传参）就用传的，否则用 "uat"。

if env not in config: # 防呆 如果你敲 python read_csv.py prd（打错了），现在会报一个看不懂的 KeyError: 'prd'
    print(f"未知环境: {env}，可选: {list(config.keys())}")
    sys.exit(1)

base_url = config[env]["base_url"]

results = []

with open("endpoints.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        full_url = base_url + row["path"]
        check = call_api(full_url)
        results.append({
            "name": row["name"],
            "url": full_url,
            "ok": check["ok"],
            "status_code": check["status_code"],
            "elapsed_ms": check["elapsed_ms"],
            "error": check["error"]
        })
        #row  ←  从 endpoints.csv 读进来的      「输入」
        #r    ←  call_api() 返回的             「输出」

stamp = datetime.now().strftime('%Y-%m-%d_%H%M')

# ---- CSV（给人看）----
with open(f"results_{env}_{stamp}.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "url", "ok", "status_code", "elapsed_ms", "error"])
    writer.writeheader()
    writer.writerows(results)

# ---- JSON（给机器看）----
report = {
    "env": env,
    "base_url": base_url,
    "run_at": datetime.now().isoformat(),   # datetime.now().isoformat() —— 产出 2026-09-06T16:30:45.123456，国际标准格式，任何系统都能解析。别自己发明时间格式，这是集成里的老坑。
    "total": len(results),
    "success": sum(1 for r in results if r["ok"]),  # sum(1 for r in results if r["ok"]) —— 生成器表达式。意思是"对每个满足条件的元素产出 1，然后加起来"，即计数。比你之前手动 += 1 更紧凑。这是 Python 里统计的惯用写法。
    "failed": sum(1 for r in results if not r["ok"]),
    "results": results
}

with open(f"results_{env}_{stamp}.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
    #json.dump(对象, 文件) —— 把 Python 对象写成 JSON
    #ensure_ascii=False —— 不加的话中文会变成 \u6210\u529f。加上才是可读的中文。
    #indent=2 —— 带缩进的漂亮格式。不加就是一整行，人看不了。


print(f"共 {report['total']} 个,成功 {report['success']},失败 {report['failed']}")