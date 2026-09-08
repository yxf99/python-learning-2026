# python-learning-2026

Python 学习记录与实践项目。

---

## 🔧 API Health Check

[![API Health Check](https://github.com/yxf99/python-learning-2026/actions/workflows/health-check.yml/badge.svg)](https://github.com/yxf99/python-learning-2026/actions/workflows/health-check.yml)

配置驱动的 API 巡检工具。支持多环境切换,输出带时间戳的 CSV / JSON 报告,已接入 GitHub Actions 定时运行。

📁 [`A4_data_reading_csv_json/`](A4_data_reading_csv_json)

### 解决的问题

集成项目里,每次部署后都要手工用 Postman 逐个验证接口。这件事有三个毛病:

- **慢** —— 十几个接口,每次十几分钟
- **不可靠** —— 人会跳过"上次是好的"那些,会在第 15 个时不看返回体
- **没有记录** —— 三天后问"周二那次部署后 stock API 正常吗",答不上来

这个工具把它变成一条命令,并留下可归档、可对比的报告。

### 用法

```bash
pip install -r requirements.txt

cd A4_data_reading_csv_json
cp config.example.json config.json     # 填入自己的环境地址
python read_csv.py uat                 # 或 prod;不传参数默认 uat
```

### 项目结构

| 文件 | 职责 |
|---|---|
| `config.json` | 环境配置(域名、超时)。本地文件,不进版本控制 |
| `config.example.json` | 配置模板,说明配置该长什么样 |
| `endpoints.csv` | 检查项清单(名称、路径) |
| `read_csv.py` | 编排:读配置 → 遍历检查项 → 调用 → 汇总 → 输出 |
| `api_call.py` | 单次请求。返回状态码、耗时、错误信息 |

### 设计决策

**一、配置与检查项分离**

环境相关的部分(域名)放 `config.json`,环境无关的部分(路径)放 `endpoints.csv`。

结果:

- 新增一个接口 → 只改 CSV
- 切换一个环境 → 只改 JSON 或命令行传参
- 两种情况都**不需要修改 Python 代码**

不写代码的团队成员也能维护这个工具。

**二、双格式输出**

同一批数据出两份:

- **CSV 给人看** —— Excel 直接打开,一行一个接口
- **JSON 给机器看** —— 带层级。外层是本次运行的元数据,内层是明细

CSV 是平的,装不下"这次运行的整体信息";JSON 可以。

**三、报告自解释**

`env`、`base_url`、`run_at` 都写进报告本身,而不是只依赖文件名。三个月后打开一个报告文件,不需要任何外部上下文就能知道它是什么。

### 输出示例

```json
{
  "env": "uat",
  "base_url": "https://httpbin.org",
  "run_at": "2026-09-07T10:32:36.585486",
  "total": 3,
  "success": 1,
  "failed": 2,
  "results": [
    {
      "name": "get",
      "url": "https://httpbin.org/get",
      "ok": true,
      "status_code": 200,
      "elapsed_ms": 170,
      "error": null
    }
  ]
}
```

`elapsed_ms` 用于识别性能问题:状态码相同但耗时差几倍,说明问题不在功能,在资源、网络或配置。

### CI

`.github/workflows/health-check.yml`

- 每天 UTC 08:00 自动运行,也可在 Actions 页面手动触发
- 每次运行都在一台全新的 Ubuntu 虚拟机上执行,杜绝环境依赖
- 报告作为 artifact 归档,可从运行记录页面下载
- 脚本以非零退出码表示失败,可用于阻断下游步骤

---

## 学习记录

| 阶段 | 内容 |
|---|---|
| A1 | 循环、range 的三种形式、函数 |
| A3 | requests、GET / POST、Bearer token、请求头 |
| A4 | CSV / JSON 读写、配置外置、Git 工程实践、CI/CD |

A4 的详细笔记(含每一步的动机与踩过的坑)见 [`A4_data_reading_csv_json/NOTES.md`](A4_data_reading_csv_json/NOTES.md)。