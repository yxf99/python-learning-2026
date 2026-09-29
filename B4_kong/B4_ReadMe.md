# B.4 — 用 Docker 跑一个 API Gateway (Kong)

> 目标:把 API Gateway 的三个核心概念 —— **认证、路由、限流** —— 从"知道"变成"亲手配过并验证过"。
>
> 成果:本地 8000 端口跑着一个网关,所有请求必须持有效 API key,且每个调用方每分钟限 5 次,通过后转发给上游服务。

---

## 0. 这一节要解决的问题

### 没有 Gateway 的世界

```
        ┌──▶ 订单服务   (自己做认证、限流、日志)
调用方 ──┼──▶ 商品服务   (自己做认证、限流、日志)
        └──▶ 客户服务   (自己做认证、限流、日志)
```

| 问题 | 说明 |
|---|---|
| **重复** | 每个服务实现一遍认证、限流、日志。写 20 遍,错 20 次 |
| **不一致** | A 服务每分钟 100,B 服务每秒 10,没人说得清 |
| **改不动** | 换认证方式 → 20 个服务全部重新部署 |
| **看不见** | 想知道"谁调了什么、多少次" → 要去 20 个地方拼日志 |
| **暴露内部** | 调用方要知道每个服务的地址,后端一重构就全崩 |

### 加上 Gateway

```
                ┌─────────────┐
调用方 ─────────▶│   Gateway   │  认证 / 限流 / 日志 / 路由
                └──────┬──────┘
                       ├──▶ 订单服务  (只写业务逻辑)
                       ├──▶ 商品服务  (只写业务逻辑)
                       └──▶ 客户服务  (只写业务逻辑)
```

> **Gateway = 所有 API 流量的单一入口,把"每个服务都要做的事"抽出来做一次。**
>
> 这些事叫**横切关注点(cross-cutting concerns)** —— 每个服务都需要,但都和业务逻辑无关。
>
> 理论依据:REST 六大约束里的 **Layered System** —— 调用方不需要知道后面有几层。

### ⚠️ 一个重要前提

Gateway 的价值 = **策略 + 它是唯一的路**。

只配了策略、但后端还能被绕过 = 等于没有。真实项目里后端跑在内网,防火墙只开放 Gateway 的端口,这样"想访问后端只能走 Gateway"才成立。

本练习中 httpbin.org 是公网服务,任何人都能直接访问 —— 它只是**扮演**内网服务的角色,方便验证 Kong 的行为。

---

## 1. 为什么用 Docker

### Docker 是什么

> **容器 = 一个打包好的、能立刻跑起来的完整环境。**

```
镜像 (image)     = 打包好的模板,只读     ≈ 类
容器 (container) = 用镜像跑起来的实例      ≈ 实例
```

### 传统装 Kong vs Docker 装 Kong

| | 传统方式 | Docker |
|---|---|---|
| 步骤 | 装 PostgreSQL、装 OpenResty、改配置、调端口 | 一条 `docker run` |
| 耗时 | 约两小时,还可能失败 | 一分钟 |
| 卸载 | 残留文件到处都是 | `docker rm -f kong`,痕迹全无 |

### 概念澄清

- **Docker 里本来什么都没有。** Kong 镜像是 `docker run` 时从 Docker Hub 自动下载的
- **Docker 是"怎么跑",Kong 是"跑什么"** —— Kong 也可以不用 Docker,直接装服务器、跑 K8s、用云托管版

```bash
docker images     # 看本地有哪些镜像
```

---

## 2. 环境准备

### 2.1 装 Docker Desktop

1. `docker.com/products/docker-desktop` → 下载 **Apple Silicon** 版
2. 拖进 Applications,打开,同意条款
3. 等菜单栏鲸鱼图标不再动画,Docker Desktop 左下角显示 **Engine running**

### 2.2 验证

```bash
docker --version
```

**目的:** 确认 CLI 工具进了 PATH。

> ⚠️ **踩坑记录:** 装完 Docker 后,已经打开的终端仍然报 `command not found`。
> **原因:** 终端是在装 Docker **之前**打开的,环境变量是旧的。
> **解法:** 关掉终端重开一个。

---

## 3. 写配置文件

### 3.1 建目录

```bash
cd ~/Desktop/python/python-learning-2026
mkdir B4_kong
cd B4_kong
```

### 3.2 写 kong.yaml

```bash
cat > kong.yaml << 'EOF'
_format_version: "3.0"

services:
  - name: httpbin-service
    url: https://httpbin.org
    routes:
      - name: api-route
        paths:
          - /api
        strip_path: true
    plugins:
      - name: key-auth
      - name: rate-limiting
        config:
          minute: 5
          policy: local

consumers:
  - username: eva
    keyauth_credentials:
      - key: my-secret-key-123
EOF
```

> `cat > 文件 << 'EOF'` 叫 **heredoc** —— 把中间的内容原样写进文件,直到遇到单独一行 `EOF`。
> 适合一次性写入多行文本,不用开编辑器。

### 3.3 逐块解释

#### Service —— 后端是谁

```yaml
services:
  - name: httpbin-service
    url: https://httpbin.org
```

**目的:** 声明一个上游服务。Gateway 要转发的目标。

#### Route —— 什么请求走这个 service

```yaml
routes:
  - name: api-route
    paths:
      - /api
    strip_path: true
```

**目的:** 定义路由规则。路径以 `/api` 开头的请求,转给上面的 service。

`strip_path: true` 表示转发时**剥掉 `/api` 前缀**:

```
调用方请求:  localhost:8000/api/get
Kong 转发:   https://httpbin.org/get      ← /api 没了
```

> **这是 Gateway 的解耦能力:对外 URL 结构和后端真实结构可以完全不同。**
> 后端换地址、换路径,调用方无感。

#### Plugins —— 挂在这个 service 上的策略

```yaml
plugins:
  - name: key-auth
  - name: rate-limiting
    config:
      minute: 5
      policy: local
```

**目的:** 把横切关注点挂上去。

| plugin | 作用 |
|---|---|
| `key-auth` | 没有有效 API key 的请求直接拒绝(401) |
| `rate-limiting` | 每个调用方每分钟最多 5 次,超了拒绝(429) |

`policy: local` = 计数存在本机内存(单节点够用;多节点要用 redis)。

> **httpbin 完全不知道有认证和限流这回事。** 这就是"抽出来做一次"。

#### Consumer —— 谁能调

```yaml
consumers:
  - username: eva
    keyauth_credentials:
      - key: my-secret-key-123
```

**目的:** 定义一个调用方身份和它的凭证。

> **限流是按 consumer 算的** —— 每个调用方各有每分钟 5 次的额度,不是所有人共享一个池子。
> 这是"按 client_id 分级限流"的基础(免费版 10 次/分,企业版 1000 次/分)。

---

## 4. 启动容器

```bash
docker run -d --name kong \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong/kong.yaml" \
  -e "KONG_PROXY_LISTEN=0.0.0.0:8000" \
  -v "$(pwd)/kong.yaml:/kong/kong.yaml:ro" \
  -p 8000:8000 \
  kong:3.6
```

### 参数逐个解释

| 参数 | 含义 | 目的 |
|---|---|---|
| `-d` | detached | 后台运行,不占住终端 |
| `--name kong` | 容器命名 | 之后可以用名字操作,不用记 ID |
| `-e KONG_DATABASE=off` | 环境变量 | **DB-less 模式**,不需要 PostgreSQL |
| `-e KONG_DECLARATIVE_CONFIG=...` | 环境变量 | 告诉 Kong 去哪读配置 |
| `-e KONG_PROXY_LISTEN=0.0.0.0:8000` | 环境变量 | 代理端口监听所有网卡 |
| `-v 本地:容器内:ro` | **挂载(volume)** | 把本机的 kong.yaml 映射进容器。`ro` = 只读 |
| `-p 8000:8000` | **端口映射** | 本机 8000 → 容器 8000 |
| `kong:3.6` | 镜像:版本 | 用哪个镜像 |

### 两个关键概念

**挂载(`-v`)**

容器有自己独立的文件系统。不挂载的话,容器里根本看不到你写的 kong.yaml。

好处:**改本机文件就等于改容器里的配置**,不用重建镜像。

**端口映射(`-p`)**

```
-p 8000:8000
   ↑     ↑
  本机   容器内
```

容器有自己的网络。这行是在墙上打个洞 —— **没有它,curl 根本够不着 Kong。**

> `$(pwd)` 是 **命令替换** —— 执行 `pwd` 取当前目录绝对路径,嵌进字符串。
> `\` 是**续行符**,告诉 shell 这条命令还没完。

### 验证启动

```bash
docker ps
```

**目的:** 看容器状态。STATUS 应该是 `Up ...`。

```bash
docker logs kong
```

**目的:** 看启动日志。关键的一行:

```
[kong] init.lua:589 declarative config loaded from /kong/kong.yaml
```

**这行出现 = 配置读进去了。** 前面那些 `[warn]` `[notice]` 都是正常启动信息。

---

## 5. 验证三个场景

**配置写了不等于生效了。** 三条 curl 分别验证三个 plugin/规则。

### curl 参数说明

| 参数 | 含义 |
|---|---|
| `-i` | 显示响应头(排查时几乎总要加) |
| `-H "头名: 值"` | 添加请求头 |
| `-s` | silent,关掉进度条(脚本里必加) |
| `-o /dev/null` | 响应体丢进系统垃圾桶,只看状态码 |
| `-w "%{http_code} "` | 自定义输出,`%{...}` 是 curl 变量 |

常用 `-w` 变量:`%{http_code}` 状态码、`%{time_total}` 总耗时、`%{size_download}` 字节数。

---

### 测试 ① 不带 key → 期望 401

```bash
curl -i http://localhost:8000/api/get
```

**目的:** 验证 key-auth plugin 生效。

**实际结果:**

```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Key realm="kong"
X-Kong-Response-Latency: 17
Server: kong/3.6.1
X-Kong-Request-Id: 4c62fe14e6ba3b33aeabb22c00a52464

{
  "message":"No API key found in request",
  "request_id":"4c62fe14e6ba3b33aeabb22c00a52464"
}
```

**观察点:**

| 头 | 说明 |
|---|---|
| `Server: kong/3.6.1` | **是 Kong 回的,请求根本没到 httpbin** |
| `WWW-Authenticate: Key realm="kong"` | HTTP 标准头,告诉调用方"要用 Key 认证" |
| `X-Kong-Request-Id` | **correlation ID**,响应体里也带同一个 |

> **correlation ID 的价值:** 调用方报问题时甩这个 ID,你在日志里 `grep 4c62fe14` 就能定位整条请求。
> 不暴露任何内部信息,又能查问题 —— 这正是 RFC 7807 里建议的做法。Kong 自动做了。

---

### 测试 ② 带 key → 期望 200

```bash
curl -i -H "apikey: my-secret-key-123" http://localhost:8000/api/get
```

**目的:** 验证认证通过后,路由和路径剥离正确。

**实际结果(节选):**

```
HTTP/1.1 200 OK
RateLimit-Limit: 5
RateLimit-Remaining: 4
RateLimit-Reset: 17
X-RateLimit-Limit-Minute: 5
X-RateLimit-Remaining-Minute: 4
Server: gunicorn/19.9.0
Via: kong/3.6.1
X-Kong-Upstream-Latency: 478
X-Kong-Proxy-Latency: 155

{
  "headers": {
    "Apikey": "my-secret-key-123",
    "Host": "httpbin.org",
    "X-Consumer-Id": "bb4480be-54ca-509c-b986-f36cc7293b25",
    "X-Consumer-Username": "eva",
    "X-Credential-Identifier": "47d7dd2b-...",
    "X-Forwarded-Path": "/api/get",
    "X-Forwarded-Prefix": "/api",
    "X-Kong-Request-Id": "f91fe95049b35259c527da36b8a63231"
  },
  "url": "https://localhost/get"
}
```

#### 观察点 A:限流头自动出现

```
RateLimit-Limit: 5          上限
RateLimit-Remaining: 4      还剩
RateLimit-Reset: 17         多少秒后重置
```

**一行代码没写。** 两套格式并存是为兼容:`RateLimit-*` 是 IETF 新草案,`X-RateLimit-*-Minute` 是 Kong 传统格式。

> **好的限流要告诉调用方三件事:上限多少、还剩多少、什么时候恢复。**
> 有了这些,客户端可以主动减速而不是一头撞上 429:
> ```python
> if int(r.headers["RateLimit-Remaining"]) < 2:
>     time.sleep(5)
> ```

#### 观察点 B:两个延迟指标 ⭐

```
X-Kong-Proxy-Latency: 155       Kong 自己处理花的时间
X-Kong-Upstream-Latency: 478    等后端响应花的时间
```

**这个拆分极其有用。** 排查慢请求的第一个问题永远是"是网关慢还是后端慢":

```
Proxy 高    → 网关问题(policy 太多、插件慢)
Upstream 高 → 后端问题
```

#### 观察点 C:Kong 注入的身份信息 ⭐⭐

```
X-Consumer-Id: bb4480be-...
X-Consumer-Username: eva
X-Credential-Identifier: 47d7dd2b-...
```

**这是 Gateway 最核心的价值之一:**

```
Kong 完成认证 → 把"这是谁"通过 header 告诉后端
后端不用再验一遍 token,直接读 header
```

后端因此可以:按调用方记日志和用量、做业务层权限判断、**完全不实现任何认证逻辑**。

> **这是 B.3 说的"按 client 统计用量"的实现基础。**
> 没有它就不知道谁在用哪个版本,也就不敢下线任何 API。

#### 观察点 D:路由改写痕迹

```
X-Forwarded-Path: /api/get      调用方原本请求的
X-Forwarded-Prefix: /api        被剥掉的部分
Host: httpbin.org               实际转发目标
```

httpbin 收到的路径是 `/get`,但 Kong 告诉它原始请求是什么。

#### 观察点 E:`Server` 头换人了

```
测试①  Server: kong/3.6.1        Kong 自己回的
测试②  Server: gunicorn/19.9.0   httpbin 回的(它用 Python gunicorn)
        Via: kong/3.6.1          但经过了 Kong
```

**一眼看出请求有没有真的到达后端。**

#### ⚠️ 发现的安全问题

```
"Apikey": "my-secret-key-123"
```

**API key 被原样转给了后端。** 生产环境不该这样 —— Kong 已经验证过了,后端读 `X-Consumer-Username` 就够了,不需要看到原始凭证。

**修法:**

```yaml
- name: key-auth
  config:
    hide_credentials: true
```

> 面试题:*"How do you prevent credential leakage through a gateway?"* —— 答案就是这个。

---

### 测试 ③ 连打 7 次 → 期望触发限流

```bash
for i in {1..7}; do
  curl -s -o /dev/null -w "%{http_code} " -H "apikey: my-secret-key-123" http://localhost:8000/api/get
done
echo
```

**目的:** 验证 rate-limiting 精确计数。

**实际结果:**

```
200 200 200 200 200 429 429
└────── 5 次 ──────┘└─ 超了 ─┘
```

**第 6、7 次被 Kong 直接拒绝,httpbin 完全不知道有这两个请求存在。**

> 最后那个 `echo` 是打个换行,否则提示符会贴在数字后面。
> 这条命令用到了 A.5 学的:`for` 循环、`-s`、`-o /dev/null`、`-w`。

---

## 6. 改配置并重启

试试把限流改成每分钟 10 次:

```bash
# 编辑 kong.yaml,把 minute: 5 改成 minute: 10
docker restart kong
```

等几秒再跑循环。

> **重点:你改的是一个 YAML 文件,不是任何服务的代码。** httpbin 完全不知情。
>
> **这就是"配置即代码"** —— 这个文件可以进 git、可以 code review、可以回滚、可以在 CI 里自动部署。
>
> 对比在网关界面上点几下:没有历史记录,没人知道谁什么时候改的,出问题也回不去。
>
> 清单里的 **F.4 Terraform** 和 **GitOps** 就是把这个思想推到整个基础设施。

---

## 7. 清理

```bash
docker stop kong        # 停掉,还在,可以重启
docker start kong       # 再启动
docker rm -f kong       # 删掉容器
docker rmi kong:3.6     # 连镜像一起删
```

删完本机**一点痕迹都没有** —— 没有残留配置、没有装在 /usr/local 里的东西。

---

## 8. 概念对照表

### Kong ↔ MuleSoft ↔ Azure

| Kong | MuleSoft | Azure APIM |
|---|---|---|
| Service | API 的后端地址 | Backend |
| Route | API 路径 | Operation |
| **Plugin** | **Policy** | **Policy** |
| Consumer | Client Application | Subscription |
| declarative config (YAML) | API Manager 界面配置 | ARM / Bicep 模板 |

**"Plugin = Policy" 是关键一行。** Anypoint 里 "Add Policy" 看到的那个列表(Rate Limiting、Client ID Enforcement、JWT Validation、CORS)就是 Kong 的 plugin 列表。

### ⚠️ Kong ≠ MuleSoft

```
Anypoint Platform
├── API Manager        ← 网关,加 policy     ≈ Kong
└── Mule Runtime       ← 集成引擎,写 flow   ← Kong 没有
    (Studio、DataWeave、connectors)
```

| 能力 | MuleSoft | Kong |
|---|---|---|
| 认证、限流、日志、路由 | ✅ | ✅ |
| 数据转换(DataWeave) | ✅ | ❌ |
| 编排多个系统 | ✅ | ❌ |
| 连接 SAP / Salesforce | ✅ connector | ❌ |
| 批处理、错误处理流程 | ✅ | ❌ |

> **类比:** Kong = 大楼的门禁 + 保安;MuleSoft = 门禁 + 保安 + 整栋楼里干活的人。
>
> **什么时候该用哪个:**
> 只需要给几个后端加认证和限流 → Kong / APIM(MuleSoft 是杀鸡用牛刀)
> 要连企业系统、做复杂转换和编排 → MuleSoft
>
> **能说清"什么时候该用什么"是架构师的判断力。** 只推荐自己熟的那个,是顾问的常见毛病。

---

## 9. 面试可用的话

> "I've run Kong locally in Docker with a declarative config — a service, a route with path stripping, key-auth and rate-limiting plugins, and a consumer with its own quota. It made the gateway concepts concrete: the upstream never sees the auth or throttling logic, and the gateway automatically returns rate-limit headers and injects consumer identity into the upstream request.
>
> The mapping to MuleSoft is direct — Kong plugins are API Manager policies, same concepts, different vendor. And a gateway is the prerequisite for API governance in general: you can't manage versions, retire endpoints, or enforce SLAs without per-client usage metrics, and the gateway is where you get them."

---

## 10. 这一节实际用到的旧知识

| 来自 | 用在哪 |
|---|---|
| B.1 状态码 | 401 认证失败 / 429 限流 / 200 成功 |
| B.1 REST 约束 | Layered System 是 Gateway 的理论依据 |
| B.1 RFC 7807 | correlation ID(`X-Kong-Request-Id`) |
| B.3 版本治理 | 按 consumer 统计用量是下线 API 的前提 |
| A.5 bash | `for` 循环、`$(pwd)`、heredoc、`/dev/null` |
| A.5 curl | `-i` `-H` `-s` `-o` `-w` |

---

## 待办

```
⬜ 加 hide_credentials: true,验证 key 不再透传给后端
⬜ 了解 Azure APIM 界面和核心概念(B.4 最后一条)
⬜ 看懂一份 Dockerfile(F.3)
```