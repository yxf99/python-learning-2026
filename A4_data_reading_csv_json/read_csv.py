import csv
import json
import sys
from datetime import datetime
from api_call import call_api


def run_check(env, config):
    """巡检一个环境,返回 report 字典"""
    settings = config[env]
    base_url = settings["base_url"]
    timeout = settings.get("timeout", 10)

    results = []
    with open("endpoints.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_url = base_url + row["path"]
            token = settings.get("token") if row.get("auth") == "yes" else None
            check = call_api(full_url, timeout, token=token)
            results.append({
                "name": row["name"],
                "url": full_url,
                "ok": check["ok"],
                "status_code": check["status_code"],
                "elapsed_ms": check["elapsed_ms"],
                "error": check["error"]
            })

    return {
        "env": env,
        "base_url": base_url,
        "run_at": datetime.now().isoformat(),
        "total": len(results),
        "success": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "results": results
    }


def main():
    env = sys.argv[1] if len(sys.argv) > 1 else "uat"

    with open("config.json", encoding="utf-8") as f:
        config = json.load(f)

    if env not in config:
        print(f"未知环境: {env},可选: {list(config.keys())}")
        sys.exit(1)

    report = run_check(env, config)
    stamp = datetime.now().strftime('%Y-%m-%d_%H%M')

    with open(f"results_{env}_{stamp}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "ok", "status_code", "elapsed_ms", "error"])
        writer.writeheader()
        writer.writerows(report["results"])

    with open(f"results_{env}_{stamp}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[{env}] 共 {report['total']} 个,成功 {report['success']},失败 {report['failed']}")


if __name__ == "__main__":
    main()