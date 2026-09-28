# B. API 设计与架构 — 学习笔记

> 配合《Mastering API Architecture》(James Gough)
> 进度:B.1 ✅ / B.2 ✅ / B.3–B.6 待学

---

# B.1 REST 设计基础

## 1. REST 六大约束

REST 不是协议,是 Roy Fielding 2000 年博士论文提出的**一套架构约束**。满足这些约束的 API 才叫 RESTful。

> ⚠️ 常见错误答法:"用 HTTP + JSON 的 API"。这只答了表面。

| 约束 | 含义 | 实际意义 |
|---|---|---|
| **Client-Server** | 前后端分离 | 两边独立演进 |
| **Stateless** ⭐ | 服务器不记住客户端上下文 | 每个请求自带 token → 可水平扩展 |
| **Cacheable** | 响应声明能不能缓存、多久 | 通过 `Cache-Control` 头 |
| **Uniform Interface** ⭐ | 资源=URL,动作=HTTP 方法 | URL 里不该有动词 |
| **Layered System** | 客户端不知道后面有几层 | API Gateway / API-led 三层的理论基础 |
| **Code on Demand** | 服务器可下发代码(唯一可选项) | 实际很少用 |

### Stateless 展开

```
❌ 有状态: 登录 → 服务器记住"这个连接是 Alice"
✅ 无状态: 登录 → 返回 token;之后每个请求都带 token
```

**好处:任何一台服务器都能处理任何请求** → 加机器就能扩容,负载均衡不用管"这个用户上次去了哪台"。

### Cacheable 展开

缓存 = 把结果存起来,下次直接用,不再问服务器。

**谁最清楚数据多久会变?服务器。** 所以由服务器在响应头声明:

```
Cache-Control: max-age=3600     可以存 1 小时
Cache-Control: no-store         绝对不要存(敏感数据)
Cache-Control: no-cache         可以存,但每次用前先问我还有没有效
Cache-Control: private          只能存用户自己浏览器,中间代理不能存
```

不同数据能缓存的时长差别极大:

| 数据 | 缓存时长 |
|---|---|
| 国家列表 | 几天 |
| 商品描述 | 几小时 |
| 商品价格 | 几分钟 |
| **库存数量** | 几秒或不缓存 |
| 银行余额 | 绝不缓存 |

> **设计时要问:"这个数据晚几分钟更新,业务能接受吗?"** 这是业务判断,不只是技术判断。
> MuleSoft 对应物:Cache Scope、Object Store、API Manager 的 HTTP Caching Policy。

### 面试答法

> "REST is a set of architectural constraints, not a protocol. The two most important in practice are **statelessness** and **uniform interface**. Statelessness is why every request carries its own token — it lets you scale horizontally, since any instance can handle any request. Uniform interface means resources are nouns in the URL and actions are HTTP verbs. And the **layered system** constraint is what makes API-led connectivity work: the Experience API doesn't need to know how many layers sit behind it."

---

## 2. 资源命名规范

### 六条规则

**① 名词,不用动词** — 动作由 HTTP 方法表达

```
❌ /getOrders   /createOrder   /deleteProduct/99
✅ GET /orders  POST /orders   DELETE /products/99
```

**② 复数** — 集合用复数,单个用 `/复数/{id}`

```
❌ /order/123        ✅ /orders/123
```

**③ 层级表达从属,但别太深**

```
✅ GET /customers/123/orders
❌ /countries/FR/stores/12/customers/123/orders/456/items/7
```

> 只在"没有父资源就不存在"时嵌套。有独立 ID 的资源直接 `/orders/456`。不超过两三层。

**④ 路径 vs 查询参数** ⭐

| | 路径参数 | 查询参数 |
|---|---|---|
| 回答 | "**哪一个**"(身份) | "**什么样的**"(条件) |
| 例子 | `/products/SKU123` | `/products?category=pasta` |
| 找不到时 | **404** | **200 + 空数组 []** |
| 必填? | 必填 | 通常可选 |
| 返回 | 一个对象 | 一个数组 |

SQL 类比:路径参数 = 主键查询,查询参数 = WHERE 条件。

**⑤ 格式统一** — `/order-items` 小写 + 连字符。选一种,全 API 统一。

**⑥ 新建时 URL 指向集合**

```
❌ POST /users/Tom
✅ POST /users + body {"name":"Tom"}
   → 201 Created
   → Location: /users/42
```

ID 由服务器分配。客户端决定 ID 时用 `PUT /products/SKU123`。

### 例外:非 CRUD 动作

```
POST /orders/123/cancel
POST /orders/123/refund
```

确实不是增删改查的操作,允许用动词,但用 POST + 挂在资源下面。Google、Stripe 都这么做。

---

## 3. 幂等性(Idempotency)

### 定义

> **同一个请求执行一次和执行多次,结果一样。**

电梯按钮(按十次也只来一次)= 幂等;售货机投币(投十次买十瓶)= 不幂等。

### 为什么重要:网络会骗你 ⭐

```
客户端 ──POST /orders──▶ 服务器  ✅ 订单建好了
客户端 ◀───── ✗ ────────  响应丢了 → 客户端超时
```

**关键:客户端无法区分这两种情况**

```
A. 请求在路上丢了     → 服务器什么都没做 → 应该重试
B. 请求成功,响应丢了 → 服务器已经做了   → 不该重试
```

看到的现象都是"超时"。**唯一出路:让重试变安全。**

> 面试金句:**"You can't distinguish a failed request from a lost response."**

### 各方法的幂等性

| 方法 | 幂等 | 安全(不改数据) | 说明 |
|---|---|---|---|
| GET | ✅ | ✅ | 只读 |
| PUT | ✅ | ❌ | "设成这样",设十次还是这样 |
| DELETE | ✅ | ❌ | 删了就没了。(第二次可能返回 404,但**服务器状态**相同) |
| PATCH | ⚠️ | ❌ | 设定值幂等,增量不幂等 |
| **POST** | ❌ | ❌ | 每次新建一个 |

```
安全 ⊂ 幂等
```

> **永远别用 GET 做修改操作。** 浏览器预加载、爬虫、缓存都默认 GET 安全,会随意发 GET 请求。

### PUT vs POST vs PATCH

原始数据:`{"id":42, "name":"Tom", "email":"tom@old.com", "city":"Paris"}`

```
PATCH /users/42  {"email":"new@x.com"}
→ 只改 email,name 和 city 保持不变        部分修改

PUT /users/42    {"email":"new@x.com"}
→ name 和 city 被清空!                    整体替换
```

| | PUT | PATCH |
|---|---|---|
| 含义 | 整体替换(换整张表格) | 部分修改(用修正液改一格) |
| 要发什么 | 完整对象 | 只发要改的字段 |
| 没发的字段 | **被清空** | 保持不变 |
| 幂等 | ✅ 永远 | ⚠️ 看写法 |

PATCH 幂等性:

```
{"balance": 100}   设成 100     → 执行十次还是 100   ✅ 幂等
{"add": 100}       加 100       → 执行十次加了 1000  ❌ 不幂等
```

> **集成陷阱:** 源系统只发变化字段(增量),下游若当成 PUT 处理 → 没发的字段被清空 → 数据丢失。
> "为什么同步之后客户地址不见了" —— 往往就是 PUT/PATCH 语义没对齐。

### Idempotency Key

POST 天生不幂等,但下单、支付必须用 POST。解法:

```
POST /orders
Idempotency-Key: 7f3a9c2e-1b4d-4e8a-9f6c-2d5e8a1b3c7f

服务器逻辑:
  这个 Key 见过吗?
    ├─ 没见过 → 正常处理,存下 Key 和结果
    └─ 见过   → 不处理,直接返回上次的结果
```

- Key 由**客户端生成**
- **重试时用同一个 Key**(每次换新 Key 就失去意义)
- Stripe / PayPal / Adyen 全都这么做。**支付接口没有幂等键 = 设计缺陷**

### MuleSoft 对应

| 组件 | 幂等性风险 |
|---|---|
| **Until Successful** | 包住不幂等调用 = 制造重复数据 |
| **Idempotent Message Validator** | 按 ID 判断消息处理过没有,就是 Idempotency Key 的实现 |
| **Anypoint MQ / Kafka** | at-least-once 投递 → 同一条消息可能来两次 → **消费端必须幂等** |

> **L'Oréal NPS 场景:** Qualtrics 推一条回复,超时后重推。
> 插入新记录 → 算了两次,NPS 分数偏了
> 按回复 ID upsert → 推多少次都只有一条
>
> **数据集成的重复数据问题,本质上都是幂等性问题。**

---

## 4. HTTP 状态码

### 大分类

```
2xx  成功         "好了"
3xx  重定向       "去别处找"
4xx  客户端错误    "你的问题" → 重试一百次还是错
5xx  服务端错误    "我的问题" → 过会儿重试可能就好
```

**4xx / 5xx 的区分决定了该不该重试。**

### 速查表

| 码 | 名称 | 一句话 |
|---|---|---|
| **200** | OK | 成功,有数据 |
| **201** | Created | 建好了,配 `Location` 头 |
| **204** | No Content | 成功,没数据(DELETE 常用) |
| **400** | Bad Request | 格式看不懂(JSON 坏了、类型错) |
| **401** | Unauthorized | **你是谁?** 没认证/token 无效 |
| **403** | Forbidden | **知道你是谁,但没权限** |
| **404** | Not Found | 没这个东西 |
| **409** | Conflict | 和当前状态冲突(重名、版本冲突) |
| **422** | Unprocessable | 看懂了,业务规则不允许 |
| **429** | Too Many Requests | 限流,配 `Retry-After` 头 |
| **500** | Internal Error | 我这出 bug 了 |
| 502/503/504 | Gateway 类 | 后端无效响应 / 暂时不可用 / 后端超时 |

### 三组易混

**401 vs 403**

```
401 "你是谁?"          → 查 token 配置、过期时间
403 "知道你是谁,不行"   → 查权限、角色、scope(换 token 没用)
```

> 名字起得很烂:401 叫 "Unauthorized",实际意思是"未认证"(unauthenticated)。历史遗留,面试爱考。

**400 vs 422**

```
400  "看不懂"       "quantity": "abc"   类型错
422  "看懂了,不行"  "quantity": -3      业务规则不过
```

**404 vs 403(安全考量)**

有些系统故意对"存在但无权访问"返回 404,避免泄露资源存在性。
返回 403 = 告诉攻击者"这东西存在,只是你看不了"。

### 判断顺序

```
URL 指向的东西存在吗?   不存在 → 404
请求格式/类型对吗?      不对   → 400
业务规则允许吗?         不允许 → 422
```

### ⭐ 错误映射(集成核心)

```
SAP 说"客户 123 不存在"  → 真实业务结果 → 对外 404  ✅
SAP 抛异常 / 超时        → 我这边的故障 → 对外 5xx  ✅
```

> **对外暴露的状态码,描述的是"调用方视角看到的问题",不是内部发生了什么。**
> **坏设计:所有错误都返回 500。** 调用方无法判断是谁的问题,也不知道该不该重试。
> MuleSoft error handling 的核心工作就是这个映射。

### 什么时候可以自动重试

**可以:**
- 5xx(尤其 502/503/504)
- **429**(按 `Retry-After` 等待)
- 网络超时 / 连接失败

**附加条件:**
- 只对**幂等操作**自动重试。POST 要有 Idempotency Key
- 要有**退避(backoff)**:1s → 2s → 4s,不要猛重试打垮正在恢复的服务
- 要有**上限**,超了就放弃 + 报警

**不该重试:** 4xx(除 429)

---

## 5. 分页三种方案

### ① Offset(偏移量)

```
GET /orders?offset=40&limit=20     跳过前 40 条,拿 20 条
SQL: LIMIT 20 OFFSET 40
```

**优点:** 简单,能直接跳到第 N 页
**缺点:**

**a. 越往后越慢** — 数据库必须读完前 100 万条再丢掉

**b. 数据漂移** ⭐ — Offset 记的是**位置**,位置会移动

```
翻页前:   A  B  C | D  E  F
插入 Z:   Z  A  B | C  D  E
                    ↑ 第 4 个位置现在是 C → C 被看两次

删除 A:   B  C  D | E  F  G
                    ↑ D 被跳过,永远看不到
```

### ② Cursor(游标)

```
GET /orders?limit=20
→ 20 条 + "next_cursor": "eyJpZCI6MTAyMH0"

GET /orders?limit=20&cursor=eyJpZCI6MTAyMH0
```

服务器给一个**不透明书签**。优点:快、不漂移。缺点:**不能跳页**。
(Stripe、GitHub、Slack 都用这个)

### ③ Keyset(键集)

```
GET /orders?limit=20&after_id=1020
SQL: WHERE id > 1020 ORDER BY id LIMIT 20
```

其实就是把游标内容摊开写。走索引,**翻到第几页都一样快**。

### 选型

| 场景 | 选 |
|---|---|
| 后台管理,要"跳到第 7 页" | Offset |
| 数据量小(几千条) | Offset |
| 无限滚动、App 列表 | Cursor |
| **批量同步、数据导出** ⭐ | **Keyset / Cursor** |

> **集成场景必须用 Keyset/Cursor:** 从 SAP 拉 50 万条跑 2 小时,期间数据一直在变。
> Offset 会导致**重复同步**和**静默漏数据** —— 后者最危险,没有报错,直到业务方问"为什么这个客户没过来"。

**一句话:Offset 记位置(会漂),Cursor 记内容(不漂)。**

---

## 6. 错误响应体(RFC 7807 / RFC 9457)

### 问题

每个 API 错误格式都不同,集成十个系统要写十套解析逻辑:

```json
{"error": "bad request"}
{"msg": "failed", "code": 1001}
{"success": false, "reason": "invalid"}
```

### 标准格式

```
Content-Type: application/problem+json
```

```json
{
  "type": "https://api.example.com/errors/insufficient-stock",
  "title": "库存不足",
  "status": 422,
  "detail": "SKU123 请求数量 10,当前库存 3",
  "instance": "/orders/456"
}
```

| 字段 | 含义 |
|---|---|
| **type** | 错误类型唯一标识(URI)。**给机器用** —— 代码可以 `if type == "..."` |
| **title** | 这**类**错误叫什么(固定不变) |
| **status** | HTTP 状态码(重复一遍,方便日志) |
| **detail** | 这**次**具体发生了什么(每次不同) |
| **instance** | 出错的具体资源 |

### 可扩展:校验错误列表

```json
{
  "type": ".../errors/validation",
  "title": "请求参数校验失败",
  "status": 400,
  "errors": [
    {"field": "email", "message": "格式不正确"},
    {"field": "quantity", "message": "必须大于 0"}
  ]
}
```

**一次告诉调用方所有问题**,而不是改一个再发一次。
常加 `trace_id` / `correlation_id`,方便报问题时在日志里 grep。

### ⚠️ 安全:绝不能暴露

- 堆栈信息(stack trace)
- 数据库报错原文
- 内部系统名、服务器路径、IP
- SAP 的原始错误消息

> 这些对攻击者是地图。**详细信息写日志,对外只给 trace_id。**

### 面试答法

> "Status codes tell the client the category of error; the body tells them what exactly went wrong. I standardize error bodies on RFC 7807 Problem Details — type, title, status, detail, instance — so consumers write one error handler for all our APIs. Internal details like stack traces go to logs with a correlation ID, never to the response."

---

# B.2 契约优先

## 1. Contract-first vs Code-first

**API 契约** = 描述 API 长什么样的机器可读文档(OpenAPI / RAML)。它就是提供方和调用方之间的合同。

```
Code-first:      写代码 → 从代码生成文档
Contract-first:  写契约 → 各方评审 → 按契约写代码
```

### Contract-first 的好处

**① 并行开发** ⭐ 最大价值

```
契约定好 → 后端实现真实逻辑
        → 前端对着 Mock 开发,不用等后端
```

> Sysco 三个供应商团队,没有先定契约的话,每个团队都会卡在等别人。

**② 早发现分歧** — 改文档成本≈0,代码写完再改成本高得多

**③ 契约即文档** — Mock、测试、文档都从同一份契约生成,不会对不上

**④ 设计质量更好** — 逼你站在调用方视角。Code-first 容易把内部数据库结构直接暴露

### Code-first 的好处

快;契约永远和实现一致;一个人全包时没有并行需求

### 选型

| 场景 | 选 |
|---|---|
| 多团队协作、对外 API | **Contract-first** |
| 调用方多、需要稳定 | **Contract-first** |
| **集成项目(多系统对接)** | **Contract-first** |
| 原型、内部小工具 | Code-first |

> MuleSoft 整个工作流就是 contract-first:
> Design Center 写 RAML → Mocking Service → 发布 Exchange → Studio scaffold 生成 flow 骨架

---

## 2. RAML vs OpenAPI

两者干同一件事:用 YAML 描述 API 契约。

| | RAML | OpenAPI |
|---|---|---|
| 出身 | MuleSoft 2013 | 前身 Swagger,现归 Linux 基金会 |
| 地位 | MuleSoft 生态 | **行业事实标准** |
| 路径 | **嵌套**(资源树) | **扁平**(每个路径单列) |
| 复用 | traits / resourceTypes / libraries | components + `$ref` |
| 工具 | 主要 Anypoint | 几乎所有工具 |
| 趋势 | 收缩 | 扩张 |

### RAML 的技术优势:traits

```yaml
traits:
  pageable:
    queryParameters:
      page: integer
      size: integer

/orders:
  get:
    is: [pageable]
/products:
  get:
    is: [pageable]
```

**"给一批接口贴行为标签"** —— OpenAPI 没有等价机制,只能靠 `$ref` 重复引用。

### 但 OpenAPI 赢了生态

- Azure APIM / AWS API Gateway / Kong / Apigee 全部原生支持
- Swagger UI、Redoc、Postman、代码生成器首选
- **MuleSoft 自己也妥协了** —— Design Center 现在支持直接写 OAS 3.0

> **两个都会 = 不被绑在一个厂商上。** JD 里的 "MuleSoft ou outils équivalents",等价工具全是 OpenAPI。

### 面试答法

> "Both describe API contracts in YAML. RAML has stronger reuse — traits let you apply behaviors like pagination across many endpoints. OpenAPI is more verbose but it's the industry standard: every gateway and tool supports it, and even MuleSoft now supports OAS natively. I've written RAML on MuleSoft projects; for anything outside that ecosystem — Azure APIM, Kong — I'd go with OpenAPI."

---

## 3. OpenAPI 3.0 结构

### 顶层只有六个 key

```yaml
openapi: 3.0.3        # 规范版本
info:                 # 名字、版本、描述
servers:              # 部署地址(Try it out 会用)
tags:                 # 端点分组
security:             # 全局认证要求
paths:                # ⭐ 所有端点
components:           # ⭐ 可复用定义
```

对照 RAML:
- `paths` ≈ RAML 的 `/资源:` 树
- `components.schemas` ≈ RAML 的 `types`
- `components.securitySchemes` ≈ RAML 的 `securitySchemes`

### 参数

```yaml
parameters:
  - name: petId
    in: path          # path / query / header / cookie
    required: true    # 路径参数永远必填
    schema:
      type: integer
      format: int64   # 给工具用:生成 long 而不是 int
```

> `schema` 直接定义了 400 和 404 的区分:
> `/pet/abc` → 类型不对 → **400**
> `/pet/99999` → 类型对但不存在 → **404**

### 响应

```yaml
responses:
  '200':                          # 引号!不加会变成数字
    description: successful
    content:
      application/json:           # 按 Content-Type 分开
        schema:
          $ref: '#/components/schemas/Pet'
      application/xml:            # 同一结构,两种格式
        schema:
          $ref: '#/components/schemas/Pet'
```

### `$ref` — 最重要的机制

```yaml
$ref: '#/components/schemas/Pet'
 #                当前文件
 /components/schemas   往下两层
 /Pet                  找这个定义
```

**定义一次,到处引用。加字段只改一处。**
= RAML 的 library。(Sysco 42 个 API 共用 Product 类型)

还能跨文件:

```yaml
$ref: './schemas/pet.yaml#/Pet'
$ref: 'https://example.com/common.yaml#/Error'
```

> 大型项目把公共类型抽成独立文件多 API 共享 —— 这就是 API 治理的一部分。

### Schema 要点

```yaml
Pet:
  required: [name, photoUrls]     # 单独列表,不写在字段里(和 RAML 不同)
  type: object
  properties:
    category:
      $ref: '#/components/schemas/Category'   # 可嵌套引用
    photoUrls:
      type: array
      items:                       # array 必须配 items
        type: string
    status:
      type: string
      enum: [available, pending, sold]        # 限定取值
    error:
      type: string
      nullable: true               # ⚠️ 可能为 null 必须声明
```

- **`enum`** 把"状态有哪几种"写进契约,调用方不用猜。集成里状态值对不齐是常见 bug 源
- **`example`** — Swagger UI 的 Try it out 和 Mock 服务会用它。**写好 example = 免费获得可用 mock**
- **`nullable: true`** 容易漏。不写的话 `"error": null` 违反契约,调用方代码会崩

### `allOf` — 组合

```yaml
Endpoint:
  allOf:
    - $ref: '#/components/schemas/EndpointInput'
    - type: object
      properties:
        created_at: {type: string, format: date-time}
```

读作 **"Endpoint = EndpointInput 的所有字段 + created_at"**。

> **输入模型和输出模型要分开:**
> `EndpointInput` — 客户端发过来的
> `Endpoint` — 服务器返回的(多了服务器生成的字段)
>
> 不分开的话,契约上看起来客户端可以自己设 `created_at`,语义是错的。

相关:`oneOf`(几选一)、`anyOf`(至少满足一个)

### 认证

```yaml
components:
  securitySchemes:      # 定义有哪些认证方式
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:               # 顶层:应用到所有端点
  - bearerAuth: []
```

某个端点免认证 → 该端点下写 `security: []` 覆盖。

---

## 4. 实践:自己写的 spec

**`B2_openapi/health-check-api.yaml`** — 7 个端点,3 个分组

```
environments   GET    /environments
endpoints      GET    /endpoints
               POST   /endpoints
               DELETE /endpoints/{name}
checks         POST   /checks
               GET    /checks
               GET    /checks/{check_id}
```

### 用上的知识点

| 设计 | 对应的概念 |
|---|---|
| `POST /endpoints` → 201 + `Location` 头 | 新建语义 |
| → 409 重名 / 422 业务规则 | 状态码区分 |
| `DELETE` → 204 / 404 | 无内容成功 |
| **`POST /checks` → 202 Accepted** | **异步模式** |
| `GET /checks?limit=&cursor=` | **Cursor 分页** |
| `error: nullable: true` | 契约与实现对齐 |
| `CheckReport` 含 `results: [CheckResult]` | 汇总 + 明细嵌套 |

### 202 Accepted ⭐

```
POST /checks  → 202 + {"check_id": "chk_xxx", "status": "queued"}
             （不等巡检跑完）
GET /checks/chk_xxx  → 过会儿来取结果
```

**202 = "我收到了,正在处理,还没做完"。**
异步 API 的标准模式 —— 批量导入、报表生成、数据同步都用这个。

---

## 5. Petstore 示例的设计问题

官方示例,但是 2011 年代的设计,违反了好几条规范:

```
❌ GET /pet/findByStatus?status=available
   问题1:URL 里有动词 findBy
   问题2:/pet 是单数

✅ GET /pets?status=available
```

> **能看出官方示例的问题,说明已经在用架构师的眼光审 API。** 这正是架构评审要做的事。

---

## 6. 工具

- **editor.swagger.io** — 免费、无需注册、无需登录。左边写 YAML,右边实时预览
- **SwaggerHub** — 付费团队版(30 天试用),个人学习用不上
- **AsyncAPI** — OpenAPI 在事件驱动世界的兄弟,描述 Kafka / MQ 这类**异步**接口,语法故意设计得很像。E 段会用到

### YAML 三大坑

| 坑 | 后果 |
|---|---|
| 用了 Tab | 解析失败(必须空格) |
| **缩进差一格** | 层级错位。`Endpoint:` 缩 3 格而不是 4 格 → `$ref` 找不到 |
| 版本号不加引号 | `'3.12'` 不加引号 → 3.12 浮点数 → 装成 Python 3.1 |

> **`-` 后面第一个字段的列,决定该元素所有字段的缩进列。**
> ```yaml
> - name: petId
>   in: path       ← 必须和 name 对齐
> ```
>
> Swagger Editor 的缩进竖线:**对齐的层级,竖线在同一列。** 养成扫一眼的习惯。

---

# 待学

```
⬜ B.3 版本与演进(三种版本方案 / breaking change / deprecation → sunset)
⬜ B.4 API Gateway(解决什么问题 / vs Service Mesh / 限流算法 / 熔断重试)⭐⭐⭐
⬜ B.5 API 测试(契约测试 vs 集成测试 / Newman / Pact)
⬜ B.6 API-led 三层架构(System / Process / Experience)
```

---

# 自测题(面试前回来做)

## B.1

1. 为什么每个 API 请求都要带 token,而不是登录一次就行?
2. `/getAllOrders` 违反了哪条约束?应该怎么改?
3. API-led 三层架构依赖哪条约束?
4. 为什么"网络超时"是幂等性问题的根源?
5. `PATCH {"balance": 100}` 和 `PATCH {"add": 100}`,哪个幂等?
6. MuleSoft 用 Until Successful 包住 POST,有什么风险?
7. 这些场景返回什么状态码:邮箱已注册 / 没带 Authorization / 创建成功 / 无权限删除 / `"quantity": "abc"` / `"quantity": -3` / 超过限流 / 删除成功 / SAP 抛出未处理异常
8. 哪些状态码可以自动重试?附加条件是什么?
9. 从 SAP 分页拉 50 万条,用哪种分页?为什么?
10. RFC 7807 的 `title` 和 `detail` 有什么区别?

## B.2

11. Contract-first 最大的好处是什么?举一个项目里的例子
12. RAML 最大的技术优势?为什么 OpenAPI 还是赢了?
13. 客户用 Azure APIM 做网关,契约用哪个?
14. `allOf` 用来做什么?为什么输入模型和输出模型要分开?
15. `nullable: true` 不写会有什么后果?

## 📐 API Contract

`B2_openapi/health-check-api.yaml` — 用 OpenAPI 3.0 为巡检工具设计的 API 契约。

7 个端点,涵盖环境配置、巡检项管理、异步巡检执行与历史查询。

设计要点:
- `POST /checks` 返回 202 Accepted + check_id,异步获取结果
- 历史查询使用 cursor 分页,避免 offset 在数据变动时的漂移
- 输入模型与输出模型分离(`EndpointInput` / `Endpoint`,用 `allOf` 组合)
- 全局 Bearer 认证声明