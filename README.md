# WebSec AutoGen Agent

A learning-oriented Web security audit agent built from scratch with Python, DeepSeek, FastAPI and AutoGen.

> 当前版本重点是学习 Agent 的基础结构：工具层负责获取事实，审计执行器负责编排流程，DeepSeek 只基于结构化结果生成防御性建议。

## 1. 项目简介

WebSec AutoGen Agent 是一个学习型 Web 安全配置审计工具。

它可以对授权网站执行基础配置检查，包括：

- URL 可访问性检查
- HTTPS 使用检查
- 常见安全响应头检查
- Cookie 安全属性检查
- 常见公开路径 / 敏感路径检查
- 审计摘要与安全评分
- 本地规则综合建议
- DeepSeek 综合建议
- Markdown 报告导出

本项目仅用于防御性安全配置审计和 Agent 学习，不进行密码爆破、漏洞利用、高并发扫描、绕过认证测试或攻击性测试。

## 2. 当前功能

### 基础检查

- 检查目标 URL 是否可访问
- 检查目标是否使用 HTTPS
- 检查是否缺少常见安全响应头
- 检查 Cookie 是否缺少 Secure、HttpOnly、SameSite 等属性
- 检查 robots.txt、security.txt、.env、.git/config、backup.zip、admin 等路径的访问情况
- 对软 404 页面进行简单过滤，减少误报

### 审计结果

- 生成整体状态
- 生成整体风险等级
- 计算安全评分
- 统计高危、中危、需关注 / 异常数量
- 生成本地规则建议
- 可选调用 DeepSeek 生成综合建议

### 报告导出

- 自动生成 Markdown 报告
- 报告保存到 `reports/` 目录

## 3. 技术栈

- Python 3.11
- requests
- python-dotenv
- DeepSeek Chat API
- Markdown 报告

后续计划接入：

- FastAPI
- AutoGen
- 飞书机器人
- PDF 报告导出

## 4. 项目结构

```text
websec-autogen-agent/
├── README.md
├── requirements.txt
├── .env.example
├── reports/
└── websec_autogen_agent/
    ├── __init__.py
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
    │   └── export.py
    └── integrations/
        └── __init__.py
```

## 5. 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/pzh2877903791-eng/websec-autogen-agent
cd websec-autogen-agent
```

### 2. 创建 Python 环境

使用 conda：

```bash
conda create -n websecagent python=3.11
conda activate websecagent
```

或者使用你自己的 Python 3.11 环境。

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制配置模板：

```bash
cp .env.example .env
```

如果不使用 DeepSeek，可以保持：

```env
ENABLE_LLM=false
```

如果使用 DeepSeek，需要在 `.env` 中配置：

```env
ENABLE_LLM=true
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
LLM_TIMEOUT=30
LLM_RETRIES=2
AUDIT_ENABLE_AUTOGEN=false
```

注意：不要提交 `.env` 文件。

## 6. 运行方式

检测一个网站：

```bash
python -m websec_autogen_agent.cli_demo https://example.com
```

也可以输入不带协议的域名：

```bash
python -m websec_autogen_agent.cli_demo example.com
```

程序会自动标准化为：

```text
https://example.com
```

## 7. 输出结果示例

```text
收到检测目标：
https://example.com

标准化后的URL:
https://example.com

首页请求结果：
状态码：200
响应头数量：11
页面内容长度：528

审计摘要：
整体状态：需关注
整体风险：中危
安全评分：70/100
检查项数量：5
高危：0，中危：2，需关注/异常：3

基础安全检查结果：
...

综合建议：
...

DeepSeek 综合建议：
...

Markdown 报告已保存：reports/example.com_20260603_175901.md
```

## 8. 报告说明

程序会在 `reports/` 目录下生成 Markdown 报告。

报告内容包括：

- 检测目标
- 审计摘要
- 具体检查结果
- 本地规则综合建议
- DeepSeek 综合建议
- 安全边界说明

`reports/*.md` 默认不会提交到 GitHub，只保留 `reports/.gitkeep`。

## 9. 安全边界

本项目只进行基础 Web 安全配置检查。

不会执行：

- 密码爆破
- 漏洞利用
- 绕过认证
- 高并发扫描
- 攻击 payload 注入
- 未授权测试

请仅对自己拥有或已经获得明确授权的网站使用本工具。

## 10. Agent 学习目标

本项目的核心学习目标不是“写一个扫描脚本”，而是理解 Agent 的基本结构：

```text
工具层：获取真实事实
审计执行器：组织工具调用
规则层：生成基础建议
LLM 层：基于事实解释结果
报告层：输出可读报告
```

也就是：

```text
Agent = 目标输入 + 工具调用 + 流程编排 + 结果解释 + 输出报告
```

当前项目已经形成了一个初级 Agent 架构：

```text
CLI 入口
↓
审计执行器
↓
工具函数
↓
规则建议
↓
DeepSeek 综合建议
↓
Markdown 报告
```

## 11. 设计原则

### 工具拿事实

安全检查结果必须来自工具函数，例如：

- `check_https()`
- `check_security_headers()`
- `check_cookie_security()`
- `check_sensitive_paths()`

### LLM 只解释事实

DeepSeek 只基于结构化 JSON 结果生成建议，不应该编造工具没有检测到的风险。

### 先本地，后增强

没有 DeepSeek API Key 时，项目仍然可以使用本地规则建议正常运行。

启用 DeepSeek 后，DeepSeek 只作为建议增强层，不影响基础审计流程。

## 12. Roadmap

- [√] CLI 输入 URL
- [√] URL 标准化
- [√] 首页请求
- [√] HTTPS 检查
- [√] 安全响应头检查
- [√] Cookie 安全属性检查
- [√] 敏感路径检查
- [√] 审计摘要与安全评分
- [√] 本地规则建议
- [√] Markdown 报告导出
- [√] DeepSeek 综合建议
- [ ] FastAPI 接口
- [ ] AutoGen 多角色编排
- [ ] 飞书机器人接入
- [ ] PDF 报告导出
- [ ] 单元测试

## 13. Git 提交建议

当前阶段推荐提交：

```bash
git status
git add README.md
git commit -m "docs: add project README"
git status
```

如果你还没有提交 DeepSeek 相关代码，可以先提交功能代码，再提交 README：

```bash
git add websec_autogen_agent/core/llm.py websec_autogen_agent/core/agents.py websec_autogen_agent/cli_demo.py websec_autogen_agent/tools/report.py websec_autogen_agent/tools/security_checks.py
git commit -m "feat: add DeepSeek advisory generation"

git add README.md
git commit -m "docs: add project README"
```

## 14. 免责声明

本工具仅用于学习和授权环境下的防御性安全配置审计。

使用者应确保对目标站点拥有所有权或明确授权。因未授权测试、误用或滥用造成的后果由使用者自行承担。