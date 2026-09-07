import requests
import time

def call_api(url):
    start = time.time() #time.time() —— 返回当前时间戳（秒，带小数）。前后各取一次相减，就是耗时。乘 1000 转毫秒，round() 去掉小数。
    try:
        r = requests.get(url, timeout=10)
        elapsed = round((time.time() - start) * 1000)   # 毫秒
        return {
            "ok": r.status_code < 400, #r.status_code < 400 —— 这个表达式直接产出 True/False，不用写 if。2xx/3xx 算成功，4xx/5xx 算失败。
            "status_code": r.status_code,
            "elapsed_ms": elapsed,
            "error": None if r.status_code < 400 else f"HTTP {r.status_code}"
        }
    except Exception as e:
        return {
            "ok": False,
            "status_code": None,
            "elapsed_ms": round((time.time() - start) * 1000),
            "error": str(e)
        }