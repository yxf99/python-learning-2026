import json
import sys
from read_csv import run_check


def main():
    if len(sys.argv) < 3:
        print("用法: python compare.py <环境A> <环境B>")
        sys.exit(1)

    env_a, env_b = sys.argv[1], sys.argv[2]

    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)

    for env in (env_a, env_b):
        if env not in config:
            print(f"未知环境: {env},可选: {list(config.keys())}")
            sys.exit(1)

    print(f"巡检 {env_a} ...")
    report_a = run_check(env_a, config)
    print(f"巡检 {env_b} ...")
    report_b = run_check(env_b, config)

    # 把明细列表转成"按名字能查"的字典
    a = {r["name"]: r for r in report_a["results"]}
    b = {r["name"]: r for r in report_b["results"]}

    all_names = sorted(set(a) | set(b))

    print(f"\n{'接口':<16}{env_a:<12}{env_b:<12}")
    print("-" * 46)

    diff_count = 0
    for name in all_names:
        ra, rb = a.get(name), b.get(name)
        code_a = ra["status_code"] if ra else "缺失"
        code_b = rb["status_code"] if rb else "缺失"

        if code_a != code_b:
            diff_count += 1
            mark = "  <-- 差异"
        else:
            mark = ""

        print(f"{name:<16}{str(code_a):<12}{str(code_b):<12}{mark}")

    print("-" * 46)
    print(f"共 {len(all_names)} 个接口,{len(all_names) - diff_count} 个一致,{diff_count} 个存在差异")

    if diff_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()