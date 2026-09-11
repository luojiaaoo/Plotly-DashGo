# OrcaRouter 接入文档

[OrcaRouter](https://www.orcarouter.ai) 是一个面向模型与 Agent 的 OpenAI 兼容 AI 网关：自适应路由、自动故障转移、零加价推理、可观测性、护栏以及 Agent 工具治理。它还在同一入口为 AI Agent 提供网关级零信任安全能力——对每一次 prompt/response 做审查，并以默认拒绝的方式治理每一次工具调用，应用代码无需改动。

DashGo 把 OrcaRouter 作为一等 provider 接入，位于**系统设置 → OrcaRouter接口**。

## 两种接入方式

两种方式最终都得到**同一种**普通 OrcaRouter API Key（`sk-orca-…`），由使用者自己的 OrcaRouter 账号计费、在其控制台中可见、并可随时撤销；两者共用同一套推理接口与模型目录。

| 方式 | ID | 适用场景 | 凭据来源 |
| --- | --- | --- | --- |
| OrcaRouter - API | `orcarouter` | 已有 API Key | 粘贴 `sk-orca-…` |
| OrcaRouter - Auth | `orcarouter-oauth` | 没有现成 Key | 浏览器授权（OAuth 2.0 + PKCE）获得 Key |

没有浏览器的环境仍然可以使用 API Key；没有现成 Key 的使用者可以走账号授权。

### 1. API Key

在「1. OrcaRouter - API」中粘贴 Key 后保存。Key 使用项目已有的密钥机制存储：写入数据库表 `sys_orcarouter_credential`，并以 `util_encrypt`（AES-CBC，密钥取自 `CommonConf.ENCRYPT_KEY`）加密；**不会**新增独立的密钥库。界面上只显示掩码（如 `sk-orca-…SZFS`），可以随时清除。

格式检查只用于拦截明显的输入错误；`sk-orca-` 前缀并不代表凭据有效。本集成不会为了「让表单变绿」而发送一次计费请求。

密钥管理/撤销入口：<https://www.orcarouter.ai/console/authorized-apps>

### 2. Connect with OrcaRouter（OAuth 2.0 + PKCE）

点击 **Connect with OrcaRouter** 发起授权。有两种授权方式：

* **粘贴授权码（Flow B，默认）**：授权页会显示一个授权码，复制后粘贴回来完成连接。DashGo 是自建部署软件，安装地址不固定，Flow B 无需回调地址，因此作为默认。
* **浏览器自动回调（Flow A）**：浏览器与 DashGo 同机时可用。回调监听 `127.0.0.1` 的随机端口，并用**恒定时间**比较 `state` 后才使用授权码。

两种方式都固定使用 `code_challenge_method=S256`：每次尝试都用系统 CSPRNG 新建 verifier 与 state，challenge 为无 padding 的 `base64url(sha256(verifier))`。verifier 不进入 URL、不写入日志，只在换取 Key 的请求体中出现。不需要 client secret，也不需要预注册 redirect URI。

换取到的 Key 是**持久 API Key，不是 refresh token**：重启后会继续复用直到被撤销，不会主动刷新，也不会每次启动重新授权（每用户每 24 小时最多签发 10 个 PKCE Key）。当推理接口返回 `401` 时，只有**发出该请求的那个凭据代数**会被标记为需要重新授权，旧的异步失败不会污染刚重登的新凭据；在重新登录成功前不会静默删除旧凭据。

## 模型目录与能力过滤

模型清单的唯一事实源是当前配置 origin 下的 `GET /v1/models`，使用使用者自己的 API Key 读取，因此得到的是该 workspace 真正可调用的模型。模型 ID 原样保留 `vendor/model` 命名空间，并且**不能自由填写**——模型控件是下拉选择器。

每一种入口按能力独立过滤，依据的是目录元数据而不是模型名：

| 入口 | 过滤规则 |
| --- | --- |
| 文本对话 | `?capability=chat`，且 `supported_endpoint_types` 包含 openai / anthropic / gemini / openai-response 之一 |
| 多模态理解 | 先满足文本对话，再要求 `architecture.input_modalities` **明确包含**实际上传的模态（image / audio / video / file） |
| 向量嵌入 | `?capability=embedding`，或严格匹配 `embeddings` endpoint |
| 图片生成 | `?capability=image`，或严格匹配 `image-generation` endpoint |
| 视频生成 | 严格匹配 `openai-video` endpoint |
| 重排序 | 严格匹配 `jina-rerank` endpoint |

未声明能力的模型一律 **fail closed**，不会混入下拉。切换能力、勾选/取消附件模态或更换凭据时都会重新计算下拉内容；已选模型如果不再兼容会被清空并提示重新选择。

API Key 不会出现在浏览器中：模型目录由后端持 Key 拉取，返回给前端的只有最小化的模型元数据（ID、名称、上下文长度、输入模态、reasoning 支持等）。

实时目录成功时以其为权威结果。拉取失败（超时、网络错误、非预期响应）时回退到一小份**已验证的备用目录**并在界面标注为「降级」，不会退回自由文本输入：

`openai/gpt-5.5`、`anthropic/claude-opus-4.8`、`google/gemini-3.5-flash`、`deepseek/deepseek-v4-pro`、`orcarouter/auto`

备用目录保留已验证的上下文长度、输入模态与 reasoning effort 档位（`openai/gpt-5.5` 为 low / medium / high / xhigh）。

## 配置

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ORCA_BASE_URL` | 无 | 自建部署的共享 origin，同时作为下面两个的回退 |
| `ORCA_AUTH_BASE_URL` | `https://www.orcarouter.ai` | 认证与换取 Key 的 origin，显式值优先 |
| `ORCA_API_BASE_URL` | `https://api.orcarouter.ai/v1` | 推理与模型目录的 origin，显式值优先 |

> 认证在 `www.orcarouter.ai`，其接口位于 `/api/v1/auth`；推理中转在 `api.orcarouter.ai` 的 `/v1`。
> `https://api.orcarouter.ai/v1/auth/keys` 是 404——认证与推理是两个不同的公开 origin，不能由其中一个推导出另一个。

非 loopback 的远程 origin 必须是 HTTPS；HTTP 仅允许用于 loopback 本地开发。

## 代码结构

```
src/common/orcarouter/
├─ __init__.py       provider ID / 展示名 / 控制台链接
├─ errors.py         终止性、可操作的错误类型
├─ origins.py        origin 解析与网络策略
├─ pkce.py           PKCE 原语与换取请求契约
├─ credentials.py    凭据 seam 与两个 adapter（API Key / PKCE）
├─ catalog.py        模型目录解析与能力过滤
├─ transport.py      Bearer 传输（推理与目录）
├─ loopback.py       Flow A 的回调监听
└─ runtime.py        面向页面与入口的统一门面
```

推理与模型目录不会感知凭据来自哪个 adapter；两种方式产出的都是同一个 `OrcaCredential`。

## 测试

```bash
python -m pytest tests/ -q                      # 单元与流程测试（不需要网络与真实 Key）
python -m pytest tests/ -q -m slow              # 含绑定 loopback 端口的 Flow A 测试
ORCA_E2E_BASE_URL=http://127.0.0.1:8090 python -m pytest tests/e2e -m e2e   # 真实浏览器截图证据
```

`tests/test_orcarouter_flow.py` 使用本地 fake auth server 完整跑通 authorize → callback/粘贴 → exchange → persist，不使用任何真实凭据。真实授权始终需要人工在浏览器中同意。
