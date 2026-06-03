import json
import time

import requests

from websec_autogen_agent.core.config import settings


def build_deepseek_prompt(audit_result:dict) -> str:
    """
    根据审计结果构造 DeepSeek 输入提示词
    """
    audit_json = json.dumps(audit_result, ensure_ascii = False, indent = 2)

    return (
        "你是防御视角的 Web 安全配置审计助手。"
        "你的任务是把结构化审计 JSON 转换为中文 Markdown 综合建议。\n\n"

        "核心原则：\n"
        "1. 只能依据 JSON 中的 target、normalized_url、checks、summary、rule_based_advice 字段生成内容。\n"
        "2. 不得新增 JSON 中没有出现的检测项、风险项、漏洞类型或安全结论。\n"
        "3. 每个风险点必须来自 checks 中的某一项，并且风险等级必须与该检查项的 risk 字段一致。\n"
        "4. 如果某项检查只是“需关注”或“低危”，不能升级描述为高危、漏洞或已经确认的安全事件。\n"
        "5. 如果 detail 只表达“需要人工确认”，输出也必须保持“需要确认”的语气。\n"
        "6. 修复建议必须基于对应检查项的 suggestion 字段，可以润色，但不能扩展到未检测内容。\n"
        "7. 不要提供攻击性测试、漏洞利用、绕过认证、密码爆破或高并发扫描建议。\n\n"

        "输出要求：\n"
        "1. 使用 Markdown。\n"
        "2. 包含：总体评价、重点风险、优先修复建议、后续加固方向。\n"
        "3. 不要写“好的”“以下是”等开场白。\n"
        "4. 不要写审计日期，除非 JSON 中提供了日期字段。\n"
        "5. 使用“风险项”“配置问题”“需关注项”等表述；不要使用“漏洞”一词，除非 JSON 明确出现漏洞检测结果。\n\n"
    f"审计 JSON：\n{json.dumps(audit_json, ensure_ascii=False, indent=2)}"
    )

def call_deepseek_chat(prompt:str) -> str | None:
    """
    调用 DeepSeek Chat API，返回模型生成的文本。
    """
    if not settings.enable_llm:
        return None
    if not settings.has_deepseek:
        return None

    api_url = settings.deepseek_base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model":settings.deepseek_model,
        "messages": [
            {
                "role":"system",
                "content":"你是防御视角的 Web 安全配置审计助手，只给防御性建议。"
            },
            {
                "role":"user",
                "content": prompt,
            },
        ],
        # 生成随机性，越低输出越稳定
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    last_error = None

    for attempt in range(settings.llm_retries + 1):
        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=settings.llm_timeout,
            )

            if not response.ok:
                return (
                    "DeepSeek 调用失败，已使用本地规则建议。"
                    f"状态码：{response.status_code}。"
                    f"返回内容：{response.text}"
                )

            data = response.json()

            return data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.RequestException as error:
            last_error = error

            if attempt < settings.llm_retries:
                time.sleep(1.5 * (attempt + 1))

        except KeyError as error:
            last_error = error
            break

    return f"DeepSeek 调用失败，已使用本地规则建议。错误信息：{last_error}"

def generate_deepseek_advice(audit_result:dict) -> str | None:
    """
    根据审计结果生成 DeepSeek 综合建议
    """
    prompt = build_deepseek_prompt(audit_result)

    return call_deepseek_chat(prompt)