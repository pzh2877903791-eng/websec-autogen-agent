import asyncio
import json


from websec_autogen_agent.core.config import settings


def build_autogen_review_task(audit_result: dict) -> str:
    """
    把审计结果转换成 AutoGen 多角色复核任务。
    """
    audit_json = json.dumps(
        {
            "target": audit_result.get("target"),
            "normalized_url": audit_result.get("normalized_url"),
            "summary": audit_result.get("summary"),
            "checks": audit_result.get("checks"),
            "advice": audit_result.get("advice"),
            "llm_advice": audit_result.get("llm_advice"),
            "stopped_reason": audit_result.get("stopped_reason"),
        },
        ensure_ascii=False,
        indent=2,
    )

    return (
        "请基于下面的 Web 安全配置审计 JSON，完成一次多角色审计复核。\n\n"

        "统一边界：\n"
        "1. 只能基于 JSON 中已有事实分析，不得新增检测项、系统组件、安全设备、攻击类型或安全结论。\n"
        "2. 每个风险点必须对应 checks 中真实存在的检查项。\n"
        "3. 风险等级必须与检查项 risk 字段一致，不能自行升降级。\n"
        "4. status 为“通过”的检查项只能作为保持项，不能列为修复项。\n"
        "5. status 为“需关注”或“异常”的检查项必须保持审慎语气，不能表述为已确认问题。\n"
        "6. 修复建议必须基于对应检查项 suggestion 字段，可以润色，但不能扩展到 JSON 外内容。\n"
        "7. 不要承诺修复后一定降低评分或风险等级，只能说有助于降低风险，需重新审计确认。\n"
        "8. 输出需包含：复核结论、风险优先级、修复顺序、人工确认项。\n\n"

        f"审计 JSON：\n{audit_json}"
    )


async def run_autogen_audit_review_async(audit_result: dict) -> str | None:
    """
    使用 AutoGen 多角色对审计结果进行复核。
    """
    if not settings.enable_autogen:
        return None

    if not settings.has_deepseek:
        return None

    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.conditions import MaxMessageTermination
        from autogen_agentchat.teams import RoundRobinGroupChat
        from autogen_ext.models.openai import OpenAIChatCompletionClient
    except ImportError as error:
        return f"AutoGen 未安装或导入失败：{error}"

    model_client = OpenAIChatCompletionClient(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=settings.llm_timeout,
        max_retries=settings.llm_retries,
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
        include_name_in_message=False,
        add_name_prefixes=True,
    )

    scanner_agent = AssistantAgent(
        name="ScannerAgent",
        model_client=model_client,
        system_message=(
            "你是 ScannerAgent。"
            "你的职责是复核 checks 中的检测事实，区分通过项、需关注项和异常项。"
            "不要分析 JSON 中不存在的检查项。"
        ),
    )

    risk_analyst_agent = AssistantAgent(
        name="RiskAnalystAgent",
        model_client=model_client,
        system_message=(
            "你是 RiskAnalystAgent。"
            "你的职责是根据 checks 中的 status 和 risk 排列风险优先级。"
            "只有 status 为“需关注”或“异常”的检查项可以进入修复优先级。"
            "status 为“通过”的检查项只能作为保持项。"
        ),
    )

    report_agent = AssistantAgent(
        name="ReportAgent",
        model_client=model_client,
        system_message=(
            "你是 ReportAgent。"
            "你的职责是整合前面 Agent 的意见，输出最终中文 Markdown 复核报告。"
            "最终回答必须以“## AutoGen 多角色审计复核”作为标题。"
            "必须包含：复核结论、风险优先级、修复顺序、人工确认项。"
        ),
    )

    team = RoundRobinGroupChat(
        participants=[
            scanner_agent,
            risk_analyst_agent,
            report_agent,
        ],
        termination_condition=MaxMessageTermination(max_messages=5),
    )

    task = build_autogen_review_task(audit_result)

    try:
        result = await team.run(task=task)

        messages = getattr(result, "messages", [])

        for message in reversed(messages):
            content = getattr(message, "content", None)
            source = getattr(message, "source", "")

            print("AutoGen message source:", source)

            if content and source == "ReportAgent":
                return str(content).strip()

        if messages:
            last_content = getattr(messages[-1], "content", "")
            return str(last_content).strip()

        return "AutoGen 复核完成，但没有生成有效内容。"

    except Exception as error:
        return f"AutoGen 复核失败：{error}"

    finally:
        await model_client.close()


def run_autogen_audit_review(audit_result: dict) -> str | None:
    """
    同步封装：在普通 Python 函数里调用异步 AutoGen 工作流。
    """
    return asyncio.run(run_autogen_audit_review_async(audit_result))