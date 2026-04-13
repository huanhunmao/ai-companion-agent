# 🚀 AI Companion Agent

> 一个从 0 到 1 构建的 AI Native 陪伴系统
> 支持多会话、上下文记忆雏形、Agent 架构扩展能力

---

## ✨ 项目简介

AI Companion Agent 是一个基于大模型（当前使用 Moonshot / Kimi）的 AI 陪伴系统。

项目目标：

* 构建一个具备 **长期演进能力的 AI Agent 系统**
* 从基础聊天逐步扩展到：

  * 🧠 Memory（记忆系统）
  * 🤖 Agent（自主执行）
  * 🧩 Tool（工具调用）
  * 🌐 Multi-Agent（多智能体世界）

---

## 🧠 核心能力（当前版本）

### ✅ 已实现

* 多轮对话（基于 messages 上下文）
* 多会话管理（Session）
* 本地持久化（localStorage）
* AI 人设（system prompt）
* 前后端完整工程结构

### 🚧 规划中（下一阶段）

* Memory（长期记忆 / 向量检索）
* Agent（规划 + 执行）
* Tool Calling（工具调用）
* 多角色 AI 社交系统

---

## 🏗️ 项目架构

```text
Frontend (Vue3)
   ↓
FastAPI Backend
   ↓
LLM (Moonshot / Kimi)
   ↓
Memory (规划中)
   ↓
Agent (规划中)
```

---

## 📁 项目结构

```text
ai-companion-agent/
├── server/                 # 后端（FastAPI）
│   ├── app.py
│   ├── requirements.txt
│   └── .env
│
├── web/                   # 前端（Vue3 + Vite）
│   ├── src/
│   │   ├── App.vue
│   │   └── utils/session.js
│   └── package.json
│
├── README.md
└── .gitignore
```

---

## 🛠️ 技术栈

### 前端

* Vue3
* Vite
* Axios

### 后端

* FastAPI
* Uvicorn
* Python

### AI / LLM

* Moonshot (Kimi API)
* OpenAI SDK 兼容调用

### 数据（当前）

* localStorage（会话存储）

### 后续规划

* Qdrant（向量数据库）
* Redis（缓存）
* PostgreSQL（结构化数据）

---

## ⚙️ 本地运行

### 1️⃣ 克隆项目

```bash
git clone git@github.com:huanhunmao/ai-companion-agent.git
cd ai-companion-agent
```

---

### 2️⃣ 启动后端

```bash
cd server

python3 -m venv venv
source venv/bin/activate

python -m pip install -r requirements.txt

python -m uvicorn app:app --reload --port 8000
```

访问：

```text
http://127.0.0.1:8000/health
```

---

### 3️⃣ 配置环境变量

创建 `.env`：

```env
MOONSHOT_API_KEY=你的API_KEY
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2-0905-preview
```

---

### 4️⃣ 启动前端

```bash
cd web

npm install
npm run dev
```

---

## 📱 移动端适配

当前版本已经支持响应式布局：

* 桌面端保持三栏结构：会话 / 聊天 / 记忆
* 平板和手机端自动切换为分区视图
* 顶部提供「对话 / 会话 / 记忆」切换按钮，避免横向溢出
* 输入框、消息操作区、参数面板都会在小屏下自动换行

---

## 🌍 上线部署

这个项目现在支持一种很实用的部署方式：

* 前端先执行 `vite build`
* 后端 FastAPI 直接托管 `web/dist`
* 用户访问同一个域名即可使用页面和 API

### 1️⃣ 构建前端

```bash
cd web
npm install
npm run build
```

构建完成后会生成：

```text
web/dist/
```

### 2️⃣ 启动生产后端

```bash
cd server
python -m pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

如果 `web/dist` 存在，FastAPI 会自动托管静态前端页面。

此时你可以直接访问：

```text
http://你的服务器IP:8000/
```

### 3️⃣ 推荐环境变量

```env
MOONSHOT_API_KEY=你的API_KEY
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2-0905-preview
DEFAULT_MODEL_NAME=moonshot/kimi-k2-0905-preview

# 如果你希望前端跨域访问后端，可配置：
CORS_ORIGINS=https://your-domain.com

# 如果你给应用增加访问保护，可配置：
APP_API_KEY=your-app-key
```

### 4️⃣ 反向代理建议

推荐使用 Nginx 或云平台的反向代理，把 80/443 转发到 `8000`：

* `https://your-domain.com` -> FastAPI
* FastAPI 同时返回前端页面和 `/api/*` 接口

这样部署最简单，也最适合先把产品发到线上给大家试用。

---

## 🧩 核心设计思路

### 1️⃣ 多轮对话

通过维护：

```js
messages = [
  { role: "system" },
  { role: "user" },
  { role: "assistant" }
]
```

实现上下文连续性。

---

### 2️⃣ 会话系统（Session）

每个会话包含：

```js
{
  id,
  title,
  messages,
  updatedAt
}
```

支持：

* 多会话切换
* 本地持久化
* 自动生成标题

---

### 3️⃣ AI 人设（Persona）

通过 system prompt 控制：

```text
你是一个温柔、聪明、会长期陪伴用户的AI伙伴
```

后续将扩展为：

* 情绪系统
* 性格系统
* 关系系统

---

## 🧠 下一步演进（重点）

### 🔹 Memory 系统

* 向量检索（Qdrant）
* 长期记忆
* 语义召回

---

### 🔹 Agent 系统

* Planner（规划）
* Tool Executor（工具执行）
* Reflection（反思）

---

### 🔹 Tool Calling

* 搜索
* 天气
* 日程
* 游戏

---

### 🔹 Multi-Agent

* AI角色互动
* 社交关系网络
* AI世界模拟

---

## 📸 项目预览

（后续补截图）

---

## 💡 亮点

这个项目可用于 AI Agent 展示：

* ✅ 完整 AI 产品架构（非 demo）
* ✅ 多会话系统设计
* ✅ Context Engineering 实践
* ✅ 可扩展 Agent 架构
* 🚀 可扩展 Memory / Tool / Multi-Agent

---

## 📌 Roadmap

* [x] Chat 基础能力
* [x] Session 会话系统
* [ ] Memory（向量记忆）
* [ ] Agent（规划执行）
* [ ] Tool Calling
* [ ] Multi-Agent World

---

## 🤝 贡献

欢迎提 Issue / PR，一起完善 AI Agent 工程体系 🚀

---

## ⭐ Star History

如果这个项目对你有帮助，欢迎点个 ⭐️
