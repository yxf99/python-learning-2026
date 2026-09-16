import requests
import time

def call_api(url, timeout=10, token=None): #token=None —— 默认不传就是不带认证。老的调用方式一行都不用改,这是向后兼容。
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}" #然后条件添加 —— 不需要认证时传一个空字典,requests 接受空 headers。别写成 headers=None if not token else {...},那样更难读。

    start = time.time()
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        elapsed = round((time.time() - start) * 1000)
        return {
            "ok": r.status_code < 400,
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