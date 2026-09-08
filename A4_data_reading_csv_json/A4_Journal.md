# A4 学习笔记 —— 从读 CSV 到 CI 流水线

记录做这个项目时每一步在干什么、为什么这么做、踩了什么坑。

---

## 目录

1. [整体脉络](#1-整体脉络)
2. [读 CSV](#2-读-csv)
3. [写 CSV](#3-写-csv)
4. [结构化返回值](#4-结构化返回值)
5. [写 JSON](#5-写-json)
6. [配置外置](#6-配置外置)
7. [多环境](#7-多环境)
8. [命令行传参与退出码](#8-命令行传参与退出码)
9. [Git 工程实践](#9-git-工程实践)
10. [CI / GitHub Actions](#10-ci--github-actions)
11. [认证:SSH、PAT、SSL/TLS](#11-认证ssh-pat-ssltls)
12. [面试准备](#12-面试准备)

---

## 1. 整体脉络

这个项目的骨架是一个通用模板:

```
读配置 → 循环 → 调用 → 收集 → 输出结构化结果
```

从一个只会 print 的脚本,一步步变成一个能被机器调用的工具。每一步只解决一个问题:

| 步骤 | 解决了什么 |
|---|---|
| 读 CSV | 检查项不再写死在代码里 |
| 写 CSV | 结果不再只存在于屏幕上 |
| 结构化返回值 | 记录状态码和耗时,不只是"成功/失败" |
| 写 JSON | 能表达层级,汇总和明细分开 |
| 配置外置 | 域名不写死在代码里 |
| 多环境 | 一份代码打多个环境 |
| 命令行传参 | 换环境不用改文件 |
| 退出码 | 机器能判断这一步成功没有 |
| CI | 不用人手动跑 |

**每一步的共同方向:把"写死的东西"往外挪。**

代码里剩下的应该只有逻辑,不该有数据、不该有配置、不该有环境。

---

## 2. 读 CSV

### csv.DictReader

把 CSV 每一行变成字典,**用表头当 key**。

```python
with open("endpoints.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["url"])
```

`endpoints.csv`:

```
name,path
get,/get
status_404,/status/404
```

循环第一圈 `row` 是 `{"name": "get", "path": "/get"}`,第二圈换成下一行。

### with open 的意义

`with` 是上下文管理器。离开这个代码块时**自动关闭文件**,即使中间抛异常也一样。

不用 `with` 就得手动 `f.close()`,而且异常时会漏关。文件句柄是有限资源,漏多了会耗尽。

### encoding="utf-8"

不写的话,不同操作系统会用不同的默认编码,中文直接乱码。

**规则:凡是 open 文件,都显式写编码。** 不要依赖系统默认值 —— 你的电脑上能跑,别人的电脑上就不一定。

### row 和 r(后来改名 check)的区别

这是当时卡住的地方,值得记牢:

```
row    ← 从 endpoints.csv 读进来的      「这次要检查什么」
check  ← call_api() 返回的               「检查结果如何」
```

- `row` 里只有 CSV 里写了的列(name、path),**不知道请求结果**
- `check` 里只有请求结果,**不知道这个 URL 叫什么名字** —— 因为传给 `call_api` 的只有一个 url

所以 `results.append({...})` 在干的事是:**把两个字典拼成一条完整记录。**

```
row   = {"name": "get", "path": "/get"}
check = {"ok": True, "status_code": 200, "elapsed_ms": 397, "error": None}
                    ↓ 合并 ↓
{"name": "get", "url": "...", "ok": True, "status_code": 200, ...}
```

单看 `check` 不知道是哪个接口挂了,单看 `row` 不知道它是好是坏。**报告需要两边都有。**

---

## 3. 写 CSV

### DictWriter 三步

```python
writer = csv.DictWriter(f, fieldnames=["name", "url", "ok"])
writer.writeheader()          # 写表头
writer.writerows(results)     # 写所有数据行
```

`fieldnames` 必须和字典的 key **完全对上**。多了少了都报错:

```
ValueError: dict contains fields not in fieldnames: 'env', 'base_url'
```

**这个报错是好事。** 它逼你保持数据结构一致。如果它默默忽略多余字段,你会在三个月后才发现某一列一直是空的。

> 严格的接口在写的时候烦,在查问题的时候救命。RAML 校验 payload 是同一个道理。

### newline=""

写 CSV 时必须加,否则 Windows 上每行之间会多一个空行。Python 的老坑,照抄。

### 文件名带时间戳

```python
stamp = datetime.now().strftime('%Y-%m-%d_%H%M')
filename = f"results_{env}_{stamp}.csv"
```

每次跑生成新文件,不覆盖上次的结果。**能对比历史,才叫监控;只有当前状态,只能叫检查。**

文件名里带 `env` 是因为**不同环境的结果绝不能混在一起** —— 这是查问题时的基本卫生。

### 踩过的坑

**datetime 拼成了 datatime。** PyCharm 不认识这个模块名,就以为是没装的第三方包,弹出 Install 按钮;pip 去 PyPI 找一个不存在的包,当然失败。

> `datetime` 是**标准库**,永远不需要 pip install。
> 记法:date + time,中间是 e 不是 a。

**教训**:看到"找不到这个包"时,先问一句 —— 这个包真的存在吗?名字拼对了吗?

---

## 4. 结构化返回值

最初 `call_api` 返回一个元组 `(ok, data)`。后来改成字典:

```python
def call_api(url, timeout=10):
    start = time.time()
    try:
        r = requests.get(url, timeout=timeout)
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
```

### 为什么从元组改成字典

**元组的位置是契约,字典的名字是契约。**

元组 `(ok, data)` 想加一个字段,所有调用方都得改(因为 `ok, data = ...` 的解包个数变了)。字典加一个 key,谁都不受影响。

> 接口的形状要能演进。定义 RAML 响应体时是同一个考虑。

### elapsed 是什么

**elapsed = 经过的、流逝的**。`elapsed_ms` = 耗时多少毫秒。

```python
start = time.time()             # 开始时刻
...
elapsed = time.time() - start   # 结束时刻 - 开始时刻 = 时长
```

`start` 是**时刻**,`elapsed` 是**时长**。英文分得清,中文都叫"时间",容易混。

### 变量名带单位

```python
elapsed = 1.5        # 1.5 什么?秒?分钟?
elapsed_ms = 1500    # 一眼就知道
timeout_s = 10
size_kb = 240
```

**凡是有单位的数字,把单位写进变量名。** NASA 1999 年丢过一个火星探测器,就是因为一个团队用英制、另一个用公制。

### 相关词汇

| 词 | 意思 |
|---|---|
| elapsed | 已耗时 |
| latency | 延迟(通常指网络往返) |
| timeout | 超时上限,超过就放弃 |
| duration | 时长(更通用) |
| throughput | 吞吐量,单位时间处理多少 |

### 默认参数

```python
def call_api(url, timeout=10):
```

不传就用 10,传了就用传的。**加参数时给默认值,老代码不用改也能跑** —— 这是向后兼容的基本手段。

---

## 5. 写 JSON

### 四个函数,别搞混

| 函数 | 方向 | 记法 |
|---|---|---|
| `json.dump(obj, f)` | 对象 → 文件 | |
| `json.dumps(obj)` | 对象 → 字符串 | 多个 s = string |
| `json.load(f)` | 文件 → 对象 | |
| `json.loads(s)` | 字符串 → 对象 | |

### 两个必加参数

```python
json.dump(report, f, ensure_ascii=False, indent=2)
```

- `ensure_ascii=False` —— 不加的话中文变成 `\u6210\u529f`
- `indent=2` —— 带缩进,人能读。不加就是一整行

### JSON ↔ Python 类型对应

| JSON | Python |
|---|---|
| object `{}` | dict |
| array `[]` | list |
| string | str |
| number | int / float |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

所以报告里写的是 `"ok": true`、`"error": null`,不是 Python 的写法 —— 已经转换过去了。

### 为什么 JSON 能做 CSV 做不到的事:嵌套

```json
{
  "env": "uat",
  "run_at": "...",
  "total": 5,
  "results": [ {...}, {...} ]
}
```

**外层是本次运行的元数据,内层 `results` 是明细。**

CSV 是平的一张表,想记"这次运行的整体信息"只能每一行重复一遍:

```
❌ name,url,env,base_url,ok
   get,...,uat,https://httpbin.org,true
   404,...,uat,https://httpbin.org,false     ← 重复
   500,...,uat,https://httpbin.org,false     ← 重复
```

冗余,而且改一个地方要改所有行。

**你调的每个 API 返回的响应体都是这个结构** —— 外层 `total`/`page`/`timestamp`,内层 `data` 数组放明细。同一个设计思路。

### isoformat

```python
datetime.now().isoformat()   # 2026-09-07T10:32:36.585486
```

ISO 8601 国际标准格式,任何系统都能解析。

**别自己发明时间格式。** `07/09/2026` 到底是 9 月 7 日还是 7 月 9 日?法国人和美国人的答案不一样。这是集成项目里的经典坑。

### 生成器表达式计数

```python
"success": sum(1 for r in results if r["ok"])
```

读作:对每个满足条件的元素产出 1,然后加起来 —— 即计数。

比手动 `+= 1` 紧凑,是 Python 里的惯用写法。

---

## 6. 配置外置

### 演进的三步

```python
# 第一步:全写死在 CSV 里
# endpoints.csv:  get,https://httpbin.org/get
#                 404,https://httpbin.org/status/404
#                     └─ 域名重复三遍,换域名要改三处

# 第二步:抽成变量
base_url = "https://httpbin.org"
full_url = base_url + row["path"]
#          └─ 换域名只改一处,但还在代码里

# 第三步:挪进配置文件
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)
base_url = config["base_url"]
#          └─ 换域名不用打开 .py 文件
```

### 为什么这一步重要

**不懂 Python 的人也能改配置了。**

运维、测试、同事,都能用这个脚本,不需要碰代码。

> 工具和脚本的区别就在这里。脚本是给自己用的,工具是给别人用的。

### 拆分的原则

```
https://httpbin.org  /get
└──── 环境相关 ────┘ └─ 环境无关 ─┘
      放 config          放 CSV
```

**域名随环境变,路径不变。** 按"什么会变"来切,不是按"什么看起来像一组"来切。

---

## 7. 多环境

### 套一层

```json
{
  "uat":  { "base_url": "https://httpbin.org" },
  "prod": { "base_url": "https://postman-echo.com" }
}
```

取值多一个方括号:

```python
config                        # {"uat": {...}, "prod": {...}}
config["uat"]                 # {"base_url": "..."}
config["uat"]["base_url"]     # "https://httpbin.org"
```

**每加一个 `[...]` 就往里钻一层。** 和 DataWeave 里写 `payload.customer.address.city` 是同一回事,只是符号不同。

写成 `config[env]` 而不是 `config["uat"]` —— 因为 `env` 是变量,改一个字符串就换环境,后面的代码一行不动。

### 多环境对比的价值

同一批检查打两个后端,结果:

```
              httpbin    postman-echo
get             401ms       170ms
404             374ms       144ms
500             416ms       143ms
```

状态码完全一致,耗时差两倍多。

> **状态码相同但耗时差几倍 → 不是功能问题,是资源、网络或配置问题。**

这就是配置漂移检测的雏形。集成项目里最阴的 bug 就是"UAT 好好的,PROD 挂了",查三天发现是某个配置没同步。

---

## 8. 命令行传参与退出码

### sys.argv

```python
import sys
env = sys.argv[1] if len(sys.argv) > 1 else "uat"
```

终端敲:

```bash
python read_csv.py prod
```

Python 拆成列表:

```python
sys.argv = ["read_csv.py", "prod"]
             ↑              ↑
          argv[0]        argv[1]
```

**`argv[0]` 永远是脚本自己的名字**,你传的第一个参数是 `argv[1]`。

不传参数时列表长度只有 1,直接取 `argv[1]` 会 IndexError。所以要有默认值。

> **默认值永远指向最安全的环境。** 手滑忘了参数,跑的是 UAT 不是 PROD。

### 退出码

```python
if env not in config:
    print(f"未知环境: {env},可选: {list(config.keys())}")
    sys.exit(1)
```

每个程序结束时都会给操作系统留下一个数字:

```
0     = 成功
非 0  = 失败
```

**它是程序之间唯一通用的"成功/失败"信号。** 不管是 Python、Java 还是 shell,含义都一样。

程序的 print 输出是给人看的,格式随便;退出码是给**机器**看的,只有一个数字,没有歧义。

验证:

```bash
python read_csv.py prod
echo $?          # 打印上一条命令的退出码 → 0

python read_csv.py xxx
echo $?          # → 1
```

### 串联

退出码的价值在于让命令能组成流水线:

```bash
命令A && 命令B      # A 成功(返回0)才执行 B
命令A || 命令B      # A 失败(非0)才执行 B

python read_csv.py prod && echo "巡检通过,可以发布"
```

**这就是"自动判断要不要继续"的最原始形态。CI 做的事本质上就是这个,只是加了界面和调度。**

### 注意

- 脚本里用 `sys.exit()`,不要用 `exit()` 或 `quit()`(那两个是交互式解释器用的)
- PyCharm 底部那句 `Process finished with exit code 0` 就是这个数字

---

## 9. Git 工程实践

### 三个区

```
工作区(你编辑的文件)
   ↓ git add
暂存区(准备提交的)
   ↓ git commit
本地仓库(已记录的历史)
   ↓ git push
远程仓库(GitHub)
```

`git status` 的三栏对应前三个区:

| 栏目 | 含义 |
|---|---|
| Changes to be committed | 已 add,下次 commit 会带上 |
| Changes not staged | 改过了,还没 add |
| Untracked files | 全新文件,git 从没见过 |

**为什么要多一层暂存区:** 可以只提交一部分改动。同时改了三个文件但只有两个属于同一件事,就只 add 那两个,分两次 commit。

> 一次 commit 只做一件事 —— 以后出问题时能精确回滚到某一个改动,而不是一坨。

### .gitignore 该挡什么

```
.venv/
__pycache__/
results_*
config.json
```

**判断标准:能从源码重新生成的,都不进版本控制。**

| | 说明 |
|---|---|
| `.venv/` | 虚拟环境。几百 MB,里面是别人的代码,含绝对路径(换电脑就废),可用 requirements.txt 重建 |
| `__pycache__/` | Python 字节码缓存。自动生成,和 Python 版本绑定,改一次源码变一次 |
| `results_*` | 脚本的输出产物。跑十次就多十个文件,git 历史全是噪音 |
| `config.json` | 可能含敏感信息(见下) |

对照:MuleSoft 项目里 `target/` 也从来不进版本控制。同一个道理。

### config.json vs config.example.json

**问题:** 配置文件会逐渐塞进敏感信息 —— 内部域名、API key、token。这些绝对不能进 git。

**标准做法:** 提交模板,忽略真实配置。

```
config.example.json   → 进 git,告诉别人配置长什么样
config.json           → 被 ignore,你本地的真实值
```

别人 clone 下来 `cp config.example.json config.json`,改成自己的值就能跑。

这是行业通用约定,在很多开源项目里见到的 `.env.example` 是同一个思路。

**副作用:** CI 环境里没有 `config.json`(被 ignore 了,GitHub 上不存在),所以流水线里要先 `cp` 一份。

### requirements.txt

```
requests>=2.31.0
```

**只列直接 import 的包。** 传递依赖(certifi、idna、urllib3 这些是 requests 自己的依赖)交给 pip 自己算。列出来反而有害 —— 哪天 requests 换了依赖,写死的版本会打架。

`pip freeze > requirements.txt` 是自动生成的偷懒办法,但会把所有包都列出来,分不清哪些是真正需要的。小项目手写更干净。

`>` 是 shell 的**重定向**,把本该打印到屏幕的内容写进文件。`>` 覆盖,`>>` 追加。

版本符号:

- `==` 锁死 → 应用/生产环境,保证可复现
- `>=` 宽松 → 小工具/库,留升级空间

**这个文件的意义:不传包本身,只传一张清单。** 任何人(包括 CI 的机器)`pip install -r requirements.txt` 就能重建环境。相当于 MuleSoft 的 `pom.xml`。

### 文件命名的坑

踩过两次:

- `config.js` ← 少了 `on`,变成 JavaScript 文件,Python 找不到
- `config example.json` ← 中间是空格不是点

**建文件时看一眼图标和后缀。**

### PyCharm 文件树的颜色

| 颜色 | 含义 |
|---|---|
| 🔴 红 | 新文件,git 还不知道(untracked) |
| 🟢 绿 | 已 add,等待 commit |
| 🔵 蓝 | 已跟踪,有改动 |
| 🟤 橄榄褐 | 被 .gitignore 挡掉 |
| ⚪️ 白/灰 | 已跟踪,无改动 |

### .gitignore 只对未跟踪的文件生效

如果文件已经被 `git add` 过,加规则也没用。要先让 git 忘掉它:

```bash
git rm --cached 文件名
```

`--cached` = 只从 git 索引里删,**本地文件留着**。不加这个参数会把磁盘上的文件也删了。

---

## 10. CI / GitHub Actions

### CI 是什么

**CI = Continuous Integration,持续集成。**

```
以前:  开发者改代码 → 攒两周 → 合并 → 💥 冲突、报错、没人知道哪坏了
CI:    每次提交代码 → 立刻自动跑一遍检查 → 坏了立刻告诉你
```

核心思想一句话:**尽早发现问题,因为越晚发现越贵。**

**CD = Continuous Delivery/Deployment**,是 CI 的下一段:检查过了就自动部署。

### 同类工具

原理完全一样,只是配置语法和界面不同:

- **GitHub Actions** —— GitHub 自带,配置在 `.github/workflows/*.yml`
- **GitLab CI** —— 配置在 `.gitlab-ci.yml`,目前最主流
- **Jenkins** —— 2011 年的老牌工具,Java 写的,很多大企业还在用
- **Azure DevOps** —— 微软系企业常见

### 为什么文件必须放在 .github/workflows/

GitHub 只认这一个位置。放错了**不会报错,只是永远不会运行**。

```
.github/workflows/       ✅
.githubs/workflows/      ❌
.github/workflow/        ❌  少了 s
github/workflows/        ❌  少了点
```

以点开头的文件夹在 Finder 和 `ls` 里默认隐藏,要用 `ls -la` 才看得到(`-a` = all)。

### 为什么是 YAML

YAML 是配置文件的通用格式,用缩进表示层级,比 JSON 适合人手写(能写注释、不用引号和逗号)。

**对缩进极其敏感,必须用空格不能用 Tab,层级错一格就解析失败。**

### workflow 文件逐段

```yaml
name: API Health Check          # 显示在 Actions 页面的名字

on:                             # 什么时候跑
  workflow_dispatch:            #   页面上出现手动运行按钮
  schedule:
    - cron: '0 8 * * *'         #   每天 UTC 08:00

jobs:
  check:                        # 任务名,可自定义
    runs-on: ubuntu-latest      # 用什么机器
    defaults:
      run:
        working-directory: A4_data_reading_csv_json

    steps:
      - uses: actions/checkout@v4      # 把代码拉下来
      - uses: actions/setup-python@v5  # 装 Python
        with:
          python-version: '3.12'

      - name: 安装依赖
        run: pip install -r requirements.txt
        working-directory: .           # 这个文件在根目录,临时切回去

      - name: 准备配置
        run: cp config.example.json config.json

      - name: 巡检 UAT
        run: python read_csv.py uat

      - name: 上传报告
        if: always()                   # 失败时也要执行
        uses: actions/upload-artifact@v4
        with:
          name: health-report
          path: A4_data_reading_csv_json/results_*
```

**关键点:**

| 配置 | 为什么 |
|---|---|
| `checkout@v4` | 不写这一步,机器上什么都没有 |
| `setup-python` | 新机器上要装指定版本的 Python |
| `pip install` | 新机器上没有任何第三方包 |
| `cp config.example.json config.json` | 真实配置被 ignore 了,CI 上不存在 |
| `working-directory` | 脚本用相对路径读 CSV,必须先进那个文件夹 |
| `if: always()` | 默认前一步失败后面就不跑了,但**报告恰恰在失败时最需要看** |

### cron 表达式

```
0 8 * * *
│ │ │ │ │
│ │ │ │ └─ 星期几 (0-6, 0=周日)
│ │ │ └─── 月份 (1-12)
│ │ └───── 几号 (1-31)
│ └─────── 小时 (0-23)
└───────── 分钟 (0-59)

* = 每个
```

| 表达式 | 含义 |
|---|---|
| `0 8 * * *` | 每天 8:00 |
| `0 */2 * * *` | 每两小时 |
| `30 9 * * 1-5` | 周一到周五 9:30 |
| `0 0 1 * *` | 每月 1 号午夜 |

**GitHub 用 UTC。** 巴黎夏令时 = UTC+2,所以 `0 8` 实际是本地上午 10 点。

**两个注意:**

- GitHub 对定时任务不保证准时,可能延迟几分钟到几十分钟。要求精确的场景别用。
- 仓库连续 60 天没有提交活动,定时任务会自动停用,GitHub 会发邮件通知。

### 一次运行发生了什么

```
1. 分配一台全新的 Ubuntu 虚拟机(几秒开出来)
2. checkout        → 拉代码
3. setup-python    → 装 Python 3.12
4. pip install     → 装 requests
5. cp config       → 准备配置
6. python read_csv.py uat  → 真的调了 httpbin.org 三次
7. upload-artifact → 存报告
8. 销毁这台机器
```

**那台机器已经不存在了。下次运行会开一台全新的。**

这是 CI 的关键特性:**每次都从零开始。** 所以它能杜绝"在我电脑上是好的" —— 如果漏写了一个依赖,本地跑得好好的,CI 上必定崩。

### CI 怎么判断成功

**它只看退出码。** 不读你 print 了什么。

```
退出码 0    → ✅ 绿色,继续下一步
退出码 非0  → ❌ 红色,流水线停下,发告警
```

**所以 `sys.exit(1)` 就是脚本和 CI 系统之间的接口。**

如果脚本发现 3 个接口挂了却返回 0,CI 会认为一切正常继续部署 —— 然后线上炸了。

想让"有接口失败就变红":

```python
if report["failed"] > 0:
    sys.exit(1)
```

(当前测试数据里有故意的 404/500,加了会一直红,换成真实接口时再打开)

### CI 的四种实际用法

**a) 部署后自动验证**

```yaml
on:
  workflow_run:
    workflows: ["Deploy to UAT"]
    types: [completed]
```

部署流水线跑完 → 自动触发巡检,人不用守着。

**b) 定时监控** —— 每小时跑一次,挂了立刻告警,比等客户投诉早几小时。

**c) 合并前的门禁**

```yaml
on:
  pull_request:
```

有人提 PR → 自动跑测试 → **不过就不让合并**。团队协作里最有价值的一条。

**d) 定期报告** —— 每周一早上跑全量检查,结果发到 Slack。

### 费用

公开仓库免费无限跑。私有仓库每月 2000 分钟免费额度。

---

## 11. 认证:SSH、PAT、SSL/TLS

> ⚠️ **先澄清一个混淆:SSH 和 SSL 是两个不同的东西。**
>
> - **SSH** (Secure Shell) —— 一套远程登录/传输协议。你用它连 GitHub、连服务器。
> - **SSL/TLS** —— 一套加密传输层协议。HTTPS 就是 HTTP 跑在 TLS 上。SSL 是旧名字,现在实际用的都是 TLS。
>
> **共同点:两者都用了非对称加密(公钥/私钥)。** 这是它们容易被混淆的原因。
> **区别:用途和场景完全不同。** SSH 主要用于登录和 git;TLS 用于保护网页和 API 的传输。

### 为什么突然不让 push 了

报错:

```
refusing to allow a Personal Access Token to create or update workflow
`.github/workflows/health-check.yml` without `workflow` scope
```

不是突然。是这次 push 里**多了一个特殊文件** —— workflow 文件会让 GitHub 在自己的服务器上执行代码。

如果一个泄漏的 token 能随便往这里塞文件,攻击者就能在你的仓库里跑任意命令、偷 secrets、篡改发布产物。

所以 GitHub 把它单列成一个权限:**能推普通代码 ≠ 能推流水线。**

> **规律:改"规则"的权限,永远比改"内容"的权限更敏感。**
>
> 对照:在 Anypoint 里,能部署应用 ≠ 能改 API policy。能改 policy 的人可以把所有鉴权关掉。

### PAT (Personal Access Token)

一串随机字符串,代替密码用。

为什么不直接用密码:

- 密码泄漏 = 整个账号全丢(包括改邮箱、删仓库)
- token 可以**限定权限**、**单独撤销**、**设过期时间**

**核心概念:scope(权限范围)。** 创建时勾选它能做什么:

```
☑ repo          读写仓库代码
☐ workflow      读写 .github/workflows/    ← 缺的就是这个
☐ delete_repo   删除仓库
```

没勾的事就做不了。这叫**最小权限原则** —— 给刚好够用的权限,不多给。

这就是 OAuth scope。调 Google API、配 Salesforce connected app 时勾的那些框,一模一样的机制。

### 非对称加密:两种玩法

```
玩法一:加密
   别人用【公钥】加密  →  只有【私钥】能解开
   用途:「我要给你发悄悄话」

玩法二:签名
   我用【私钥】签名    →  任何人用【公钥】验证
   用途:「证明这东西确实是我发的,没被改过」
```

**方向是反的。** 加密是"多人 → 一人",签名是"一人 → 多人"。

SSH 登录用的是玩法二。

### SSH key

```bash
ssh-keygen -t ed25519 -C "邮箱"
```

生成一对:

```
~/.ssh/id_ed25519       私钥   留在电脑上,永不外传
~/.ssh/id_ed25519.pub   公钥   贴到 GitHub,公开无所谓
```

**单向性:** 私钥能算出公钥,公钥算不出私钥。从公钥反推私钥需要解椭圆曲线离散对数问题,用现有计算机的时间尺度是宇宙年龄级别的。

**登录时发生了什么:**

```
1. 你:      我是 yxf99,我要连接
2. GitHub:  (从你的公钥出一道题)解这个
3. 你的电脑: (用私钥算出答案)给
4. GitHub:  (用公钥验证)对上了,是你
```

**私钥从来没有离开过电脑。** 网络上传的只是答案,每次的题都不一样,截获了也没用。

### 公钥可以公开吗

**必须公开。这是设计,不是意外。**

你的公钥现在就能被任何人拿到:`https://github.com/yxf99.keys` —— GitHub 主动公开的。

类比:公钥是你的**签名样本**(银行留底),私钥是你的**手**。别人看到签名样本复制不出你的签名习惯。银行拿样本**验证**,不是拿它**伪造**。

**怎么分辨:**

```
公钥:  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...  邮箱

私钥:  -----BEGIN OPENSSH PRIVATE KEY-----
       b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9u...
       -----END OPENSSH PRIVATE KEY-----
```

**看到 `PRIVATE KEY` 就是绝对不能外传的。** 这是唯一需要记住的判断标准。

**私钥的四条规矩:**

1. 不进 git(GitHub 会自动扫描并撤销被提交的私钥)
2. 不发给任何人 —— 没有任何正当理由需要你交出私钥
3. 不粘贴到网页
4. 权限必须是 600 (`chmod 600 ~/.ssh/id_ed25519`)

可选加固:给私钥设 passphrase

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
ssh-add --apple-use-keychain ~/.ssh/id_ed25519   # 配合钥匙串免输
```

### SSH vs PAT

| | PAT | SSH key |
|---|---|---|
| 本质 | 一串共享的字符串 | 一对公私钥 |
| 认证的是 | 「持有这串字符的人被允许做这些事」 | 「这个人是谁」 |
| 秘密是否上网 | 是,每次请求都发送 | 否,私钥永不离开本机 |
| 会过期吗 | 会 | 不会 |
| 权限粒度 | 细,可精确控制 | 粗,等同账号权限 |
| 适合 | 自动化脚本、CI、只读场景 | 日常开发机 |

**换 SSH 就通了的原因:SSH 没有 scope 的概念。** 它认的是身份,不是权限清单。GitHub 确认你是 yxf99 之后,你能干的事等于账号本身的权限 —— 你是仓库所有者,当然能改 workflow。

**核心差别:粒度 vs 便利。**

- PAT 适合"给出去"的场景 —— 给 CI 或第三方工具一个**只能做那件事**的 token,万一泄漏损失可控
- SSH 适合"自己用"的场景 —— 自己的电脑,不需要限制自己

### 同一套东西的四种应用

**1. HTTPS 证书(TLS)**

问题:输入 `github.com`,怎么确认回应你的是真 GitHub 而不是咖啡厅 WiFi 里的冒充者?

GitHub 把公钥交给一个大家都信任的第三方(CA,如 DigiCert),换回一张**证书**:

```
证书内容:
  域名:   github.com
  公钥:   (GitHub 的公钥)
  签发者: DigiCert
  签名:   xxxxx     ← DigiCert 用它的私钥签的
```

流程:

```
1. GitHub 把证书发给浏览器
2. 浏览器检查 DigiCert 的签名(浏览器出厂内置了 CA 公钥)
3. 对 → 这把公钥确实属于 github.com
4. 浏览器用这把公钥加密一个随机数发过去
5. 只有握着私钥的真 GitHub 能解开;冒充者解不开
```

**证书 = 公钥 + 身份信息 + 第三方的背书签名。** 地址栏那把小锁就是这个过程通过了。

**2. mTLS(双向 TLS)**

普通 HTTPS 是单向的:服务器证明自己是谁,客户端不用证明(你逛网站不需要出示身份)。

mTLS 是**双向**:客户端也要出示证书。

用在企业系统之间调用。比如 MuleSoft 调 SAP,SAP 需要确认"来的确实是那台授权过的服务器"。光靠用户名密码不够,因为密码可能被偷。

**配 TLS Context 时填的两个东西:**

```
Keystore   = 放我自己的私钥和证书      「我是谁」
Truststore = 放我信任的对方的证书      「我信谁」
```

**3. JWT 的 RS256 签名**

JWT 长这样(三段,点分隔):

```
eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjMiLCJyb2xlIjoiYWRtaW4ifQ.SflKxwRJ...
└─── 头部 ───┘└──────── 内容 ────────┘└─── 签名 ───┘
```

中间那段是 base64,**谁都能解开看**:

```json
{"sub": "123", "role": "admin", "exp": 1730000000}
```

⚠️ **JWT 的内容不是加密的,是公开可读的。别往里面放密码。**

安全性在**第三段签名**上:

```
授权服务器:  用【私钥】对前两段签名  →  第三段
你的 API:    用【公钥】验证签名是否匹配
```

有人把 `"role": "user"` 改成 `"admin"`,签名立刻对不上。**因为他没有私钥,签不出新的有效签名。**

**RS256 vs HS256:**

| | HS256 | RS256 |
|---|---|---|
| 用什么签 | 一个共享密钥 | 私钥 |
| 用什么验 | **同一个**共享密钥 | 公钥 |
| 问题 | 每个验证方都要知道密钥,知道了就能伪造 | 验证方只有公钥,伪造不了 |

**所以 RS256 才能用于分布式系统。** 20 个微服务要验 token,用 HS256 得把密钥发给 20 个服务,任何一个泄漏全盘皆输;用 RS256,20 个服务只拿公钥。

**jwks.json:** 授权服务器在固定地址公开发布自己的公钥:

```
https://auth.example.com/.well-known/jwks.json
```

API 启动时拉一次存下来,以后验签不用再联网问授权服务器。

**这是"公钥必须公开才有用"的最直接例子。**

**4. SAP / 银行接口的证书交换**

就是 mTLS 在实际项目里的流程:

```
你 → 银行:  我的客户端证书(里面是我的公钥)
银行 → 你:  银行服务器的证书(里面是银行的公钥)
```

**交换的永远只有公钥部分。私钥各自留在自己家里。**

如果对方要你发私钥 —— 那是钓鱼,或者对方不懂。

实际操作:

```
1. 生成密钥对,做一个 CSR(证书签名请求)
2. 把 CSR 发给 CA 或客户,拿回签好的证书
3. 证书 + 私钥 装进 Keystore
4. 对方给的证书装进 Truststore
5. 在 TLS Context 里配上这两个
6. 联调
```

通常要走两三周的邮件和审批。

### 串起来

| 场景 | 谁有私钥 | 谁用公钥 | 证明什么 |
|---|---|---|---|
| SSH | 你的电脑 | GitHub | 我是 yxf99 |
| HTTPS | 网站服务器 | 你的浏览器 | 我真是 github.com |
| mTLS | 双方各有 | 双方各有 | 我们互相是对方认可的 |
| JWT RS256 | 授权服务器 | 各个 API | 这个 token 是我签发的,没被改 |

**一句话:私钥用来"证明我是我",公钥用来"验证他是他"。公钥必须散出去,否则没人能验。**

### 认证机制的光谱

| 机制 | 特点 |
|---|---|
| 密码 | 最原始,尽量别用 |
| API Key | 简单,但一串字符走天下,风险高 |
| PAT / OAuth token | 有 scope、有过期,主流 |
| SSH key / mTLS 证书 | 非对称加密,最安全 |
| JWT + OAuth2 | MuleSoft 里配的 Client ID/Secret 就是这个 |

A3 练过的 Bearer token 和 PAT 是同一类:**一串放在 header 里的凭证字符串**。
SSH key / 客户端证书是另一类:**不传凭证本身,只证明持有它**。

---

## 12. 面试准备

### 简历条目

> **API Health Check Automation** — Python, GitHub Actions
>
> Built a configuration-driven health check tool that validates API endpoints across multiple environments. Externalized environment config (JSON) from test definitions (CSV) so new endpoints require no code changes. Outputs timestamped CSV/JSON reports with per-endpoint status codes and latency. Integrated into a CI pipeline running on schedule, with artifact archiving and non-zero exit codes gating downstream steps.

**为什么这样写:**

- 说的是**能力**,不是**学习行为**(别写 "Learned Python and GitHub Actions" —— 信息量为零)
- 每个词对应 JD 关键词:configuration-driven、multiple environments、CI pipeline、artifact
- 提到了**设计决策**(配置分离),这是初级和中级的分水岭
- 有 GitHub 链接可验证

### 口头版本

> "At my current project we validate APIs manually with Postman after each deployment — it's slow and inconsistent, and there's no record of what was checked. So I built a Python tool that reads endpoint definitions from a CSV and environment config from a JSON file, runs the checks, and outputs a timestamped report with status codes and response times.
>
> I put it on a CI pipeline so it runs automatically on a schedule and archives the reports. The key design choice was separating the config from the test definitions — that way anyone on the team can add an endpoint or point it at a new environment without touching Python."

**三个动作:**

1. 说出**痛点**(手工、不一致、无记录)
2. 说出**做法**(具体技术,但不堆术语)
3. 说出**为什么这么设计**(配置分离,让非开发者也能用)

**第三点最值钱。** 能写代码的人很多,能解释"为什么这样设计"的人少。那是 Consultant 和 Senior/Architect 的分界线。

### 对应 JD 的能力

| JD 里的说法 | 对应做的事 |
|---|---|
| CI/CD pipelines (Jenkins, GitLab CI, Azure DevOps) | GitHub Actions,同一套 |
| Automated testing / test automation | 自动化巡检 |
| Configuration management | config.json + example 模板 |
| Monitoring and alerting | 定时巡检 + 报告归档 |
| Scripting (Python/Bash) | 这个脚本 |
| Git / version control best practices | gitignore、SSH、语义化 commit |
| DevOps mindset | 把手工流程自动化 |

### 要能讲清楚的八条

1. 为什么配置要和代码分离
2. CSV 和 JSON 各自的适用场景(平 vs 嵌套)
3. 退出码是什么,CI 怎么用它
4. CI 为什么每次都用全新的机器
5. `.gitignore` 该挡什么(产物、依赖、密钥)
6. `requirements.txt` 存在的意义
7. SSH key 和 PAT 的区别
8. 公钥为什么可以公开

**其中一半不是 Python 知识,是工程习惯。** 而工程习惯恰恰是面试官用来区分"会写代码"和"能进团队干活"的东西。

### 分寸

**别写 "CI/CD expert"。** 这是一个小项目,离真实企业流水线还有距离 —— 那里有多环境审批、密钥管理、回滚策略、并行任务编排。

**可以说:** "I've set up a scheduled CI pipeline on GitHub Actions for a personal automation project."

诚实、具体、可验证。比虚张声势强,而且对方一听就知道你真的动过手。

**README 里也别写"学习项目""练习""新手"。** 不是撒谎,是不要主动贬低。让代码自己说话。

---

## 下一步可以做的

| 方向 | 内容 |
|---|---|
| 失败告警 | 挂了发 Slack / 邮件,而不是等人去看 |
| 环境对比 | 同时打 UAT 和 PROD,输出差异表 —— 直接用于配置漂移检测 |
| 重试 | 网络抖动导致的偶发失败自动重试,减少误报 |
| 认证 | 支持带 Bearer token 的接口(接上 A3 学的东西) |
| 响应校验 | 不只看状态码,还校验返回体的关键字段 |
| 历史趋势 | 把每次的 JSON 汇总,画出耗时随时间的变化 |

---

## 一句话总结

这个项目真正学到的不是 Python 语法,是**把手工流程变成工具**的思路:

```
写死 → 抽成变量 → 挪进配置 → 支持多环境 → 命令行传参 → 交给机器定时跑
```

每一步都在做同一件事:**让"会变的东西"离开代码。**