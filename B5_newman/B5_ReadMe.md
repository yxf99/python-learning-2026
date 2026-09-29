# B.5 — 用 Newman 把 API 测试搬进 CI

> 目标:把 API 测试从"人点着看"变成"机器自动判断",并接进 GitHub Actions 流水线。
>
> 成果:一份带断言的 Postman collection + 一条每次 push 自动运行的测试流水线,断言失败时流水线变红。

---

## 0. 这一节解决的问题

### 现在的做法

打开 Postman,点 Send,**用眼睛看**:

```
状态码是 200 吗?       眼睛看
返回里有 sku 字段吗?    眼睛看
qty 是数字吗?          眼睛看
```

三个毛病:

| 问题 | 说明 |
|---|---|
| **慢** | 20 个接口每次点 15 分钟 |
| **会漏** | 点到第 15 个时基本只瞄一眼绿色的 200,不看返回体了 |
| **机器不会做** | 结果只存在于人的眼睛里,CI 拿不到 |

### 要达到的效果

```
push 代码
   ↓
CI 自动跑所有断言
   ↓
有失败 → 退出码非 0 → 流水线红灯 → 部署被拦住
```

---

## 1. 三个概念先理清

### 断言(Assertion)

> **把"用眼睛判断"写成代码,让机器自己判断。**

```javascript
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});
```

翻译成人话:**"我声明:状态码应该是 200。不是的话就算失败。"**

英文 assertion = 断定、声明。所有测试框架的核心都是断言 —— Python 的 `assert`、JUnit、JavaScript 的 `expect`,全是这一套。

### Newman

**Postman 的命令行版。** 同一个 collection 文件,Postman 里点 Run 能跑,Newman 在终端里也能跑。

```
Postman (图形界面)  ←→  Newman (命令行)
        同一个 collection.json
```

**为什么需要它:** CI 服务器没有图形界面,没有鼠标,没人点按钮。测试必须能用**一条命令**触发。

> 名字来历:Postman = 邮差,Newman 是《宋飞正传》里那个邮差角色。Postman 官方的冷笑话。

### Node / npm / Newman 的关系

```
Node.js          运行 JavaScript 的引擎     ← 地基
  └─ npm         装 JS 包的工具              ← 包管理器
       └─ newman 一个具体的包                ← 要用的工具
```

完全对应 Python 生态:

| | JavaScript | Python |
|---|---|---|
| 运行时 | Node.js | Python 解释器 |
| 包管理器 | **npm** | pip |
| 装包 | `npm install x` | `pip install x` |
| 全局装 | `npm install -g x` | `pip install x` |
| 依赖清单 | `package.json` | `requirements.txt` |
| 仓库 | npmjs.com | PyPI |

**Newman 是用 JavaScript 写的,所以要先装 Node。** 就像别人跑你的 `read_csv.py` 必须先装 Python。

---

## 2. 环境准备

### 2.1 装 Node.js

原计划 `brew install node`,但 Homebrew 之前装失败了(Xcode 工具下载不下来)。

**绕过 Homebrew,直接下官方安装包:**

1. `https://nodejs.org` → LTS 版本
2. macOS Installer (.pkg),Apple Silicon
3. 双击安装

**关掉终端重开**(刷新环境变量),然后:

```bash
node --version    # v24.21.0
npm --version     # 11.19.0
```

### 2.2 踩坑:npm 全局安装权限

```bash
npm install -g newman
```

报错:

```
npm error code EACCES
npm error Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules/newman'
```

**原因:** `/usr/local/lib` 是系统目录,普通用户没有写权限。

**⚠️ 不要用 `sudo npm install`** —— 那会把 root 拥有的文件散布到系统里,以后权限问题越来越多。npm 官方明确不推荐。

**正确解法:把全局安装目录改到家目录**

```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile
npm install -g newman
newman --version    # 6.2.2
```

| 命令 | 作用 |
|---|---|
| `mkdir -p ~/.npm-global` | 在家目录建放全局包的文件夹(家目录你有完全权限) |
| `npm config set prefix` | 告诉 npm:`-g` 装的东西放这儿,别放 `/usr/local` |
| `echo ... >> ~/.zprofile` | 把新目录加进 `PATH`,否则装了也找不到命令 |
| `source ~/.zprofile` | 让配置立刻生效,不用重开终端 |

> **`PATH` 是什么:** 一串目录列表,shell 按顺序去这些目录里找你敲的命令。
> **`>>` 是追加,`>` 是覆盖** —— 写错成 `>` 会把 `.zprofile` 原有内容清空。

> **这和 Python 的 `pip install --user` 是同一个思路:装进自己的地盘,不碰系统目录。**

### 2.3 Postman 打不开怎么办

本次 Postman 客户端报 `Version mismatch detected` 打不开。

**不影响这一节** —— Postman collection 本质上就是一个 JSON 文件,手写一个照样能用 Newman 跑。

> **手写反而更有价值:** 平时在界面上点按钮,看不到背后生成了什么结构。

---

## 3. 手写 collection.json

```bash
cd ~/Desktop/python/python-learning-2026
mkdir B5_newman
cd B5_newman
```

```bash
cat > collection.json << 'EOF'
{
  "info": {
    "name": "API Health Tests",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get httpbin",
      "request": { "method": "GET", "url": "{{base_url}}/get" },
      "event": [{
        "listen": "test",
        "script": {
          "type": "text/javascript",
          "exec": [
            "pm.test('Status is 200', function () {",
            "    pm.response.to.have.status(200);",
            "});",
            "",
            "pm.test('Response under 2000ms', function () {",
            "    pm.expect(pm.response.responseTime).to.be.below(2000);",
            "});",
            "",
            "pm.test('Has url field', function () {",
            "    pm.expect(pm.response.json()).to.have.property('url');",
            "});"
          ]
        }
      }]
    },
    {
      "name": "Get 404",
      "request": { "method": "GET", "url": "{{base_url}}/status/404" },
      "event": [{
        "listen": "test",
        "script": {
          "type": "text/javascript",
          "exec": [
            "pm.test('Status is 404', function () {",
            "    pm.response.to.have.status(404);",
            "});"
          ]
        }
      }]
    },
    {
      "name": "Bearer with token",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/bearer",
        "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
      },
      "event": [{
        "listen": "test",
        "script": {
          "type": "text/javascript",
          "exec": [
            "pm.test('Status is 200', function () {",
            "    pm.response.to.have.status(200);",
            "});",
            "",
            "pm.test('Authenticated is true', function () {",
            "    pm.expect(pm.response.json().authenticated).to.eql(true);",
            "});"
          ]
        }
      }]
    }
  ]
}
EOF
```

### heredoc 说明

```bash
cat > 文件 << 'EOF'
...内容...
EOF
```

| 部分 | 作用 |
|---|---|
| `cat` | 把输入原样输出 |
| `> collection.json` | **输出重定向** —— 写进文件,不打印到屏幕 |
| `<< 'EOF'` | **输入重定向** —— 接下来的内容都是输入,直到单独一行 `EOF` |

**`EOF` 不是关键字**,只是约定俗成的结束标记,写 `END` 也行,只要首尾一致。

**单引号很重要:**

```bash
<< EOF      # 不加引号:$变量 和 `命令` 会被 shell 替换
<< 'EOF'    # 加引号:原样写入,什么都不解释
```

写配置文件时永远加引号。

> ⚠️ **踩坑:** 最后那行单独的 `EOF` 一定要贴进去。漏了的话终端会一直等结束标记(提示符变成 `>`),文件写不成。本次就因此漏建了环境文件。

---

## 4. collection.json 的结构

### 顶层两块

```json
{
  "info": { ... },     // 叫什么、什么格式
  "item": [ ... ]      // 请求列表
}
```

**`info.schema` 必须有** —— 声明"我是 collection v2.1 格式",Newman 靠它判断怎么解析。那个 URL 只是标识符,不会真的被访问。

**`item` 数组的每个元素 = Postman 里的一个请求。**

### 一个 item 的内部

```json
{
  "name": "Get httpbin",     // 输出里显示的名字
  "request": { ... },        // 请求本身
  "event": [ ... ]           // 附加脚本
}
```

#### request

```json
"request": {
  "method": "GET",
  "url": "{{base_url}}/get",
  "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
}
```

就是 Postman 界面上那三样:方法下拉框、URL 框、Headers 标签。

**`{{base_url}}` 是变量占位符**,运行时从环境文件取值替换。

> 这和 `config.json` 里的 `base_url` 作用一样 —— **换环境只改变量,不改用例。**

#### event —— 断言脚本在这

```json
"event": [{
  "listen": "test",
  "script": { "type": "text/javascript", "exec": [ ...一行一个... ] }
}]
```

| 字段 | 含义 |
|---|---|
| `listen: "test"` | **响应之后执行**(Postman 界面的 Scripts → Post-response) |
| `listen: "prerequest"` | 请求之前执行(生成时间戳、算签名) |
| `exec` | JavaScript 代码,**数组,一行一个元素** |

**为什么 `exec` 是数组:** JSON 不支持多行字符串。Postman 拆成数组,每元素一行,Newman 读时用换行拼起来。空字符串 `""` 就是空行,纯为可读性。

### 断言语法(来自 Chai 库)

| 写法 | 作用 |
|---|---|
| `pm.response.to.have.status(200)` | 断言状态码 |
| `pm.response.responseTime` | 响应耗时(毫秒) |
| `pm.response.json()` | 响应体解析成对象 |
| `pm.expect(x).to.be.below(2000)` | x 小于 2000 |
| `pm.expect(x).to.have.property('url')` | x 有这个字段 |
| `pm.expect(x).to.eql(true)` | x 等于 true |

**写得像英语是故意的:** `expect(x).to.be.below(2000)` 读作"期望 x 小于 2000"。

### 三个请求分别在测什么

| 请求 | 断言 | 验证的概念 |
|---|---|---|
| Get httpbin | 200 / <2000ms / 有 url 字段 | 可用性 + 性能 + 结构 |
| Get 404 | 状态码是 404 | **预期失败也要测** |
| Bearer with token | 200 + `authenticated` 为 true | **认证 + 响应体内容** ⭐ |

> **第二个:** 测试不只测成功路径。"错误情况返回正确的错误码"同样是契约的一部分。
>
> **第三个是超出巡检工具的地方:** `pm.expect(pm.response.json().authenticated).to.eql(true)` 检查的是**响应体内容**,不只是状态码。
> **一个接口可能返回 200 但内容是错的 —— "活着"和"对"是两回事。**

---

## 5. 环境文件

```bash
cat > uat.postman_environment.json << 'EOF'
{
  "name": "UAT",
  "values": [
    { "key": "base_url", "value": "https://httpbin.org", "enabled": true },
    { "key": "token", "value": "test-token-abc123", "enabled": true }
  ]
}
EOF
```

**用例和配置分离** —— 同一个 collection 可以打 UAT、PROD、本地,只换环境文件。

### ⚠️ 凭证泄漏风险

导出的环境文件里,**你填的 token、API key、密码会原样写进去**:

```json
{ "key": "api_token", "value": "eyJhbGciOiJIUzI1..." }   ← 进 git 就泄漏了
```

**三种正确做法:**

```bash
# ① 环境文件里留占位符
{ "key": "api_token", "value": "{{$processEnv API_TOKEN}}" }

# ② 命令行覆盖
newman run collection.json -e uat.json --env-var "api_token=$API_TOKEN"

# ③ 真实值存在 CI 的 Secrets 里
#    GitHub 仓库 → Settings → Secrets and variables → Actions
```

```yaml
      - name: Run tests
        env:
          API_TOKEN: ${{ secrets.API_TOKEN }}
        run: newman run collection.json --env-var "api_token=$API_TOKEN"
```

> **和 `config.json` + `config.example.json` 是同一个模式:模板进 git,真实值在别处。**
>
> 本项目用的是 httpbin 的假 token,无所谓;但习惯要从一开始就对。

---

## 6. 运行

```bash
newman run collection.json -e uat.postman_environment.json
```

**输出:**

```
API Health Tests

→ Get httpbin
  GET https://httpbin.org/get [200 OK, 637B, 420ms]
  ✓  Status is 200
  ✓  Response under 2000ms
  ✓  Has url field

→ Get 404
  GET https://httpbin.org/status/404 [404 NOT FOUND, 243B, 93ms]
  ✓  Status is 404

→ Bearer with token
  GET https://httpbin.org/bearer [200 OK, 290B, 96ms]
  ✓  Status is 200
  ✓  Authenticated is true

┌─────────────────────────┬──────────┬────────┐
│              iterations │        1 │      0 │
│                requests │        3 │      0 │
│            test-scripts │        3 │      0 │
│              assertions │        6 │      0 │
└─────────────────────────┴──────────┴────────┘
```

> **关于 DeprecationWarning:** Newman 6.2.2 内部用了 Node 24 已弃用的 `fs.F_OK`。只是警告,不影响运行。

### 常用参数

| 参数 | 作用 |
|---|---|
| `-e environment.json` | 加载环境变量 |
| `-d data.csv` | **数据驱动** —— 用 CSV 每行跑一遍 |
| `-n 5` | 重复跑 5 轮 |
| `--bail` | 第一个失败就停 |
| `--folder "Smoke"` | 只跑 collection 里某个文件夹 |
| `--timeout-request 5000` | 单请求超时(毫秒) |
| `--insecure` | 忽略 SSL 证书错误(自签证书的测试环境) |

**`-d` 数据驱动** —— 同一个请求用 CSV 每行的数据跑一遍:

```csv
sku,expected_status
SKU123,200
SKU999,404
```

> 这就是 `endpoints.csv` 做的事。**我用 Python 手写了一遍数据驱动测试的机制。**

**`--folder` 很实用** —— 同一份 collection,不同场景跑不同子集:

```
Collection
├── Smoke          ← 部署后立刻跑,1 分钟
├── Regression     ← 发版前跑,20 分钟
└── Edge Cases
```

---

## 7. ⭐ 核心实验:验证退出码

**这是整节最重要的一步。**

### 故意制造失败

```bash
sed -i '' 's/Status is 404/Status is 200/; s/have.status(404)/have.status(200)/' collection.json
```

把"期望 404"改成"期望 200",但那个接口就是返回 404 的 —— **断言必然失败。**

> `sed -i '' 's/旧/新/' 文件` 是命令行查找替换。
> **Mac 的 `sed` 要求 `-i` 后面跟一个空字符串**(Linux 不用),这是经典的跨平台坑。

### 结果

```
→ Get 404
  GET https://httpbin.org/status/404 [404 NOT FOUND]
  1. Status is 200                    ← 不是 ✓ 了,变成编号

assertions:  6 executed,  1 failed

  #  failure          detail
 1.  AssertionError   Status is 200
                      expected response to have status code 200 but got 404
                      at assertion:0 in test-script
                      inside "Get 404"
```

**失败详情告诉你三件事:** 期望什么、实际什么、在哪个请求里。不用回头翻日志。

### 退出码

```bash
echo $?
→ 1
```

### 为什么这个实验必须做

```
测试全绿时退出码 0   → 谁都知道
测试红了退出码是几?  ← 这才是关键
```

**如果失败了退出码还是 0,CI 就以为一切正常,继续部署。**

```
newman 退出码 0    → ✅ 绿灯,继续
newman 退出码 1    → ❌ 红灯,流水线停下
```

> ### 一句话
>
> **Postman 里点 Run → 结果在你眼睛里 → 机器不知道**
> **newman run → 结果在退出码里 → CI 能判断**
>
> **这一个数字,就是"手工测试"和"自动化测试"的分界线。**

验证完记得把断言改回 404。

---

## 8. 挂进 GitHub Actions

`.github/workflows/api-tests.yml`

```yaml
name: API Tests

on:
  workflow_dispatch:
  push:
    paths:
      - 'B5_newman/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Newman
        run: npm install -g newman

      - name: Run API tests
        working-directory: B5_newman
        run: |
          newman run collection.json \
            -e uat.postman_environment.json \
            --reporters cli,junit \
            --reporter-junit-export results.xml

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: newman-results
          path: B5_newman/results.xml
```

### 结构和 health-check.yml 一模一样

```
checkout → 装运行时 → 装依赖 → 跑命令 → 归档产物 + if: always()
```

### 新东西:路径过滤

```yaml
on:
  push:
    paths:
      - 'B5_newman/**'
```

**只有这个目录下的文件变了才触发。** 改 README 不会白跑一次流水线。

### Reporter

```bash
--reporters cli,junit --reporter-junit-export results.xml
```

| reporter | 用途 |
|---|---|
| `cli` | 终端输出(默认) |
| `json` | 机器可读,自己做分析 |
| **`junit`** | **标准 XML,CI 平台能渲染成测试报告页面** |
| `htmlextra` | 漂亮的 HTML 报告(需另装插件) |

**JUnit XML 是 Java 测试框架定下的格式,后来变成事实标准** —— 所有语言的测试工具都支持输出它,GitLab / Jenkins 会渲染成带通过/失败列表的页面。

```xml
<testsuites name="API Health Tests" tests="6" failures="0">
  <testsuite name="Get httpbin" tests="3" failures="0">
    <testcase name="Status is 200" .../>
```

### `if: always()`

**默认前一步失败后面就不跑了。但测试报告恰恰在失败时最需要看**,所以强制执行。

### 别忘了 gitignore

```
results.xml
```

它是产物,不是代码。

---

## 9. 运行结果

```
Triggered via push              ← 没手动点,path 过滤器生效了
Status: Success
Total duration: 16s
Artifacts: newman-results (529 Bytes)
```

### 两条 Annotation

```
⚠️ Node.js 20 is deprecated. The following actions target Node.js 20
   but are being forced to run on Node.js 24:
   actions/checkout@v4, actions/setup-node@v4, actions/upload-artifact@v4
```

**说的不是 `node-version: '20'`**,而是那三个 action **自身的运行时**。GitHub 正在淘汰 Node 20 运行时。

处理:把 action 版本号升到当前主版本(去各自 repo 的 Releases 页面确认最新版本号)。

```
ℹ️ ubuntu-latest will migrate to Ubuntu 26 beginning October 19, 2026
```

只是预告,不用管。

> **习惯:CI 配置里的版本号会过期,定期扫一眼 warning 就能发现。**

---

## 10. 两条流水线的分工 ⭐

```
health-check.yml   Python 巡检工具    "活着吗"      smoke test
api-tests.yml      Newman 断言        "对不对"      integration test
```

| | 巡检工具 | Newman |
|---|---|---|
| 检查 | status_code + elapsed_ms | 响应体任何字段和内容 |
| 问的问题 | **活着吗** | **对不对** |
| 类型 | smoke test | integration test |
| 耗时 | 1 分钟 | 5-20 分钟 |
| 时机 | 部署后立刻 | 冒烟通过后 |

**不是替代关系,是流水线上的两道关卡:**

```
部署 UAT
   ↓
巡检工具   ← 全挂了?立刻回滚,别浪费后面 20 分钟
   ↓ 通过
Newman     ← 活着但返回的东西不对?也拦住
   ↓ 通过
人工验收
   ↓
部署 PROD
   ↓
再跑一次冒烟   ← UAT 通过不代表 PROD 没问题(配置/网络/数据都不同)
```

---

## 11. 完整流水线里各种测试的位置

```
提交代码
   ↓
单元测试           秒级,每次提交
   ↓
契约测试(Pact)    秒级,每次提交       ← 防 breaking change
   ↓
构建 & 部署 UAT
   ↓
冒烟测试           1 分钟               ← 巡检工具
   ↓
Newman 集成测试    5 分钟               ← 验证真实行为
   ↓
人工审批 ✋         ← 有这步 = Continuous Delivery,没有 = Continuous Deployment
   ↓
部署 PROD
   ↓
再跑冒烟
```

**越快越稳的越靠前,越慢越真实的越靠后。** 问题尽早被发现,反馈循环最短。

---

## 12. 契约测试 vs 集成测试(概念部分)

### 集成测试在微服务下的痛点

```
要测订单服务 → 必须启动库存服务
库存服务又依赖 → 商品服务、价格服务
商品服务又依赖 → 数据库、缓存
```

- 跑一次要启动十几个服务
- 别人的服务挂了,你的 build 变红,**但跟你的改动无关**
- 慢:几十分钟

### 契约测试的思路

> **不测"能不能调通",测"双方对消息格式的理解是否一致"。**

```
消费者侧:  用 mock 代替真实提供者跑测试 → 产出契约文件
提供者侧:  拿契约当测试用例,验证自己符合
```

**关键:两边不用同时在线。**

| | 集成测试 | 契约测试 |
|---|---|---|
| 需要对方在线 | ✅ 必须 | ❌ 不用 |
| 速度 | 分钟级 | 秒级 |
| 稳定性 | 差(别人挂你也红) | 好(完全隔离) |
| 能发现 | 网络、配置、真实数据问题 | 格式不兼容、breaking change |

**两者不是二选一:** 契约测试每次提交都跑(快、稳),集成测试部署后跑(慢、真实)。

### Pact —— 消费者驱动契约

```
1. 消费者写测试 → Pact 启动 mock server → 产出 pact 文件(JSON)
2. pact 文件上传到 Pact Broker
3. 提供者 CI 里:拉下所有消费者的 pact,对真实服务重放验证
```

**"消费者驱动"= 契约由使用者定义,只约束真正被用到的字段。**

```
库存服务返回 20 个字段,订单服务只用 3 个
→ 契约只写那 3 个
```

| 库存服务的改动 | Pact 结果 |
|---|---|
| 删掉 `supplier`(没人用) | ✅ 通过 |
| 新增 `location` | ✅ 通过 |
| **`qty` 改名成 `quantity`**(有人用) | ❌ 失败 |
| **`qty` 从数字改成字符串** | ❌ 失败 |

> **Pact 不改变 API 返回什么。它让提供者在改动之前,自动知道"这个改动会不会伤到真实的使用方"。**

**为什么"只约束用到的"重要:减少 false positive(假警报)。**

```
用 OpenAPI 全量校验:删掉没人用的 supplier → 也报警 ❌ 假警报
```

> **一个经常误报的测试,等于没有测试。**
> 测试天天红 → 大家习惯了 → 真出问题时也被忽略。这叫 **alert fatigue(告警疲劳)**。

**多个消费者时才是 Pact 真正发力的地方:**

```
订单服务用:  sku, qty
报表服务用:  sku, qty, warehouse
移动端用:    sku, qty, price

改 price → 只有移动端那份失败 → 精确知道去找谁沟通
```

Pact Broker 还提供 `can-i-deploy` 命令,直接在 CI 里当门禁:**"我要部署 v2,会不会搞挂谁?"**

### Pact vs OpenAPI

⚠️ 是 **OpenAPI**(API 规范),不是 OpenAI(ChatGPT 那家公司)。

| | OpenAPI | Pact |
|---|---|---|
| 谁写的 | **提供者**("我长这样") | **消费者**("我需要这些") |
| 是什么 | 一份规范文件 | 一套测试流程 |
| 约束范围 | 整个接口的完整形状 | 只约束真正被用到的字段 |
| 会自动验证吗 | ❌ 不会 | ✅ 在 CI 里跑 |

**类比:**

```
OpenAPI = 餐厅的菜单          "我们提供这 50 道菜,配料是这些"
Pact    = 常客的订单记录 + 厨房检查
          "张三每周点宫保鸡丁,不要花生"
          → 改配方前自动检查:还符合张三的要求吗?
```

菜单改第 47 道菜,张三不受影响;宫保鸡丁加了花生,**立刻报警**。

**不冲突,各管一段:**

```
OpenAPI → 设计时的契约(contract-first)
Pact    → 运行时的验证(防 breaking change)
```

**Pact 的代价:** 消费者要写测试、要维护 Broker、CI 两边都要改。**适合多团队、多消费者、服务边界清晰的场景**,小团队直接沟通更快。

---

## 13. 术语表

| 中文 | 英文 |
|---|---|
| 契约测试 | **Contract testing** |
| 消费者驱动契约测试 | **Consumer-Driven Contract (CDC) testing** |
| 集成测试 | **Integration testing** |
| 单元测试 | Unit testing |
| 端到端测试 | End-to-end (E2E) testing |
| 冒烟测试 | **Smoke testing** |
| 回归测试 | Regression testing |
| 测试金字塔 | Test pyramid |
| 断言 | **Assertion** |
| 桩 / 模拟 | Stub / Mock |
| 不稳定的测试 | **Flaky test** |
| 假警报 | False positive |
| 告警疲劳 | Alert fatigue |

**契约测试语境里固定用 consumer / provider,不用 client / server。**

### 冒烟测试的来历

来自硬件工程:电路板造好后第一件事是通电,**冒烟了就停,别测了**。不冒烟才开始真正的测试。

```
冒烟测试问  "能用吗?"
集成测试问  "对不对?"
回归测试问  "有没有把别的搞坏?"
```

**没有冒烟测试的后果:** 服务根本没起来,但 200 个集成测试还是全跑一遍全部超时,40 分钟后你才知道"服务压根没启动"。

---

## 14. 面试可用的话

> "Postman collections with assertions are great, but they only run when someone clicks. Newman is the CLI runner — same collection file, executed from a command. It exits non-zero when any assertion fails, so it gates the pipeline directly.
>
> I export the collection and environment into the repo, run it in CI after deployment with the JUnit reporter so results render as a test report, and keep credentials out of the environment file — placeholders in git, real values injected from CI secrets at runtime.
>
> One practical detail: I split the collection into folders — a small Smoke folder that runs right after deploy, and the full regression suite before release. Same file, different `--folder` flag."

> "Contract testing and integration testing solve different problems. Integration testing verifies services actually talk to each other, but it requires every dependency running — which gets fragile fast: someone else's service goes down and your build turns red for reasons unrelated to your change.
>
> Contract testing verifies both sides agree on the message format, and each side can be tested independently. Pact uses consumer-driven contracts: the consumer declares what it actually needs, the provider replays those expectations in its own pipeline. The provider only has to honor fields someone is really using, so it keeps maximum freedom to evolve."

---

## 15. 用到的旧知识

| 来自 | 用在哪 |
|---|---|
| A.5 bash | heredoc、`>` 重定向、`echo $?`、`sed` |
| A.3 HTTP | Bearer token、状态码 |
| B.1 状态码 | 200 / 404 断言,预期失败也要测 |
| B.2 契约优先 | OpenAPI vs Pact 的定位 |
| B.3 breaking change | 契约测试要拦住的就是它 |
| F.2 CI | 退出码、`if: always()`、artifact 归档 |
| 巡检工具 | 环境变量与用例分离、数据驱动 |

---

## 待办

```
⬜ 把 action 版本号升到当前主版本(消除 deprecation warning)
⬜ 修好 Postman 客户端(下最新版覆盖安装)
⬜ 试 --folder 拆分 Smoke / Regression
⬜ 试 -d 数据驱动(用 CSV 跑多组数据)
```