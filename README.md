# WebSec AutoGen Agent

一个学习型 Web 安全配置审计 Agent。

当前项目已经实现：输入目标网站后，系统可以自动完成基础 Web 安全配置检查，生成审计摘要、修复建议、Markdown 报告，并支持通过飞书群机器人进行交互式审计。

> 当前版本重点是实现 Agent 的基础闭环：工具拿事实，审计执行器编排流程，规则层生成建议，LLM 层基于结构化结果增强解释，飞书机器人作为交互入口。

---

## 1. 项目简介

WebSec AutoGen Agent 是一个面向学习和防御性安全审计的 Web 安全配置检查工具。

用户可以通过 CLI、FastAPI 接口或飞书群机器人提交目标 URL，系统会对目标站点进行基础安全配置检查，并返回结构化审计结果。

本项目不进行攻击性测试，不进行漏洞利用，不进行密码爆破，不进行高并发扫描，仅用于授权环境下的基础安全配置审计和 Agent 架构学习。

---

## 2. 当前已实现功能

### 2.1 基础安全检查

- URL 标准化
- 首页可访问性检查
- HTTPS 使用检查
- 常见安全响应头检查
- Cookie 安全属性检查
- 常见公开路径 / 敏感文件路径检查
- 软 404 页面简单过滤
- 首页不可访问时自动提前停止后续检查

### 2.2 审计摘要

系统会根据检查结果生成：

- 整体状态
- 整体风险等级
- 安全评分
- 检查项数量
- 高危 / 中危 / 需关注数量统计

### 2.3 综合建议

系统支持两类建议：

- 本地规则建议
- DeepSeek 综合建议

DeepSeek 只基于结构化 JSON 审计结果生成说明，不直接猜测目标网站是否存在漏洞。

### 2.4 报告导出

支持自动生成 Markdown 审计报告，保存到：

```text
reports/
```

报告内容包括：

- 检测目标
- 审计摘要
- 检查结果
- 综合建议
- DeepSeek 综合建议
- 安全边界说明

### 2.5 FastAPI 接口

已提供：

```text
GET /health
POST /audit
POST /feishu/events
```

其中 `/audit` 支持：

- 是否导出 Markdown 报告
- 是否启用 DeepSeek
- 是否推送飞书自定义 webhook 通知

### 2.6 飞书机器人

当前支持两类飞书能力：

#### 自定义 webhook 通知

系统可以主动把审计摘要推送到飞书群。

#### 飞书应用机器人交互

支持在飞书群中 @机器人 触发审计：

```text
@WebSecBot 审计 https://doubao.com
```

机器人会自动完成：

```text
接收群消息
提取目标 URL
执行 Web 安全配置审计
生成审计摘要
以富文本消息回复到群聊
```

---

## 3. 技术栈

- Python 3.11
- requests
- python-dotenv
- FastAPI
- Uvicorn
- DeepSeek Chat API
- Feishu Open Platform
- cpolar
- Markdown 报告

后续计划接入：

- AutoGen 多角色编排
- PDF 报告导出
- 单元测试
- 部署上线

---

## 4. 项目结构

```text
websec-autogen-agent/
├── README.md
├── requirements.txt
├── .env.example
├── reports/
└── websec_autogen_agent/
    ├── __init__.py
    ├── api.py
    ├── cli_demo.py
    ├── core/
    │   ├── __init__.py
    │   ├── agents.py
    │   ├── config.py
    │   └── llm.py
    ├── tools/
    │   ├── __init__.py
    │   ├── security_checks.py
    │   ├── report.py
    │   ├── export.py
    │   └── brief.py
    └── integrations/
        ├── __init__.py
        ├── feishu.py
        ├── feishu_client.py
        └── feishu_events.py
```

---

## 5. 快速开始

### 5.1 克隆项目

```bash
git clone <your-repo-url>
cd websec-autogen-agent
```

### 5.2 创建 Python 环境

使用 conda：

```bash
conda create -n websecagent python=3.11
conda activate websecagent
```

或者使用已有 Python 3.11 环境。

### 5.3 安装依赖

```bash
pip install -r requirements.txt
```

### 5.4 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

`.env.example` 示例：

```env
ENABLE_LLM=false
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
LLM_TIMEOUT=30
LLM_RETRIES=2

AUDIT_ENABLE_AUTOGEN=false

FEISHU_WEBHOOK_URL=your_feishu_custom_bot_webhook_url_here

FEISHU_APP_ID=your_feishu_app_id_here
FEISHU_APP_SECRET=your_feishu_app_secret_here
```

注意：

```text
不要提交 .env
不要把真实 API Key、Webhook、App Secret 提交到 GitHub
```

---

## 6. CLI 使用方式

检测一个网站：

```bash
python -m websec_autogen_agent.cli_demo https://example.com
```

也可以输入不带协议的域名：

```bash
python -m websec_autogen_agent.cli_demo example.com
```

系统会自动标准化为：

```text
https://example.com
```

---

## 7. FastAPI 使用方式

启动服务：

```bash
uvicorn websec_autogen_agent.api:app --reload --port 8000
```

访问接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

调用审计接口：

```bash
curl -s -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://doubao.com","export_report":true,"enable_llm":false}' \
  | python -m json.tool
```

请求参数说明：

| 参数 | 类型 | 说明 |
|---|---|---|
| url | string | 需要审计的网站 URL |
| export_report | bool | 是否导出 Markdown 报告 |
| enable_llm | bool | 本次请求是否启用 DeepSeek |
| notify_feishu | bool | 是否通过自定义 webhook 主动推送飞书摘要 |

---

## 8. 飞书应用机器人使用方式

### 8.1 本地启动 FastAPI

```bash
uvicorn websec_autogen_agent.api:app --reload --port 8000
```

### 8.2 使用 cpolar 暴露本地服务

```bash
cpolar http 8000
```

得到公网地址，例如：

```text
https://xxxx.cpolar.top
```

### 8.3 配置飞书事件订阅

在飞书开放平台中，将事件订阅地址配置为：

```text
https://xxxx.cpolar.top/feishu/events
```

需要订阅接收消息事件。

### 8.4 群聊中触发审计

在飞书群中发送：

```text
@WebSecBot 审计 https://doubao.com
```

机器人会自动回复 Web 安全配置审计摘要。

---

## 9. 飞书机器人演示效果

用户发送：

```text
@WebSecBot 审计 https://doubao.com
```

机器人回复内容包括：

```text
Web 安全配置审计摘要

目标：https://doubao.com
整体状态：需关注
整体风险：中危
安全评分：70/100

重点问题：
1. 安全响应头检查
2. Cookie 安全属性检查

综合建议：
1. 优先处理安全响应头配置
2. 确认 Cookie 用途并补充安全属性
```

---

## 10. Agent 架构说明

本项目不是让大模型直接判断网站是否安全。

核心设计是：

```text
工具层：获取真实事实
审计执行器：组织工具调用
规则层：生成基础建议
LLM 层：基于事实解释结果
报告层：输出可读报告
交互层：CLI / FastAPI / 飞书机器人
```

也就是：

```text
Agent = 目标输入 + 工具调用 + 流程编排 + 结果解释 + 多端输出
```

当前项目已经形成了初级 Agent 闭环：

```text
用户输入 URL
↓
URL 标准化
↓
首页请求
↓
安全工具检查
↓
审计摘要
↓
规则建议 / DeepSeek 建议
↓
Markdown 报告 / FastAPI JSON / 飞书富文本回复
```

---

## 11. AutoGen 规划

项目名称中的 AutoGen 表示后续计划接入 AutoGen 多角色编排。

当前版本已经完成基础 Agent 审计闭环，但尚未正式启用 AutoGen 多智能体协作。

后续 AutoGen 设计计划：

```text
ScannerAgent：调用现有安全检查工具，获取结构化事实
RiskAnalystAgent：分析风险优先级和修复顺序
ReportAgent：生成面向用户的审计总结
CoordinatorAgent：负责任务分配和结果整合
```

设计原则：

```text
AutoGen 不替代工具检查
AutoGen 只基于工具结果进行多角色分析和表达
```

---

## 12. 安全边界

本项目仅进行基础 Web 安全配置检查。

不会执行：

- 密码爆破
- 漏洞利用
- 绕过认证
- 高并发扫描
- 攻击 payload 注入
- 未授权测试

请仅对自己拥有或已经获得明确授权的网站使用本工具。

---

## 13. Roadmap

- [√] CLI 输入 URL
- [√] URL 标准化
- [√] 首页请求
- [√] HTTPS 检查
- [√] 安全响应头检查
- [√] Cookie 安全属性检查
- [√] 敏感路径检查
- [√] 软 404 简单过滤
- [√] 审计摘要与安全评分
- [√] 本地规则建议
- [√] Markdown 报告导出
- [√] DeepSeek 综合建议
- [√] FastAPI 接口
- [√] 飞书自定义 Webhook 通知
- [√] 飞书应用机器人事件回调
- [√] 飞书群聊 @机器人触发审计
- [√] 飞书富文本审计摘要回复
- [ ] AutoGen 多角色编排
- [ ] PDF 报告导出
- [ ] 单元测试
- [ ] 部署上线

---

## 14. 答辩演示建议

推荐演示路径：

```text
1. 启动 FastAPI
2. 启动 cpolar
3. 在飞书群中 @WebSecBot 审计 https://doubao.com
4. 展示机器人自动回复审计摘要
5. 展示 FastAPI /docs
6. 展示生成的 Markdown 报告
```

答辩时可以强调：

```text
本项目不是单纯扫描脚本，而是一个具备工具调用、流程编排、结果解释和飞书交互能力的 Web 安全配置审计 Agent。
```

---

## 15. 免责声明

本工具仅用于学习和授权环境下的防御性安全配置审计。

使用者应确保对目标站点拥有所有权或明确授权。因未授权测试、误用或滥用造成的后果由使用者自行承担。