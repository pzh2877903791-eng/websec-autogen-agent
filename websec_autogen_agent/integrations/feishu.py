import requests

from websec_autogen_agent.core.config import settings


def send_feishu_text_message(text: str, webhook_url: str | None = None) -> dict:
    """
    通过飞书自定义机器人 webhook 发送文本消息。
    """
    target_webhook_url = webhook_url or settings.feishu_webhook_url

    if not target_webhook_url:
        return {
            "ok": False,
            "error": "未配置飞书机器人 Webhook URL",
        }

    payload = {
        "msg_type": "text",
        "content": {
            "text": text,
        },
    }

    try:
        response = requests.post(
            target_webhook_url,
            json=payload,
            timeout=10,
        )

        if not response.ok:
            return {
                "ok": False,
                "error": f"飞书消息发送失败，状态码：{response.status_code}，返回内容：{response.text}",
            }

        return {
            "ok": True,
            "error": None,
            "response": response.json(),
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "error": f"飞书消息发送异常：{error}",
        }

def build_feishu_audit_post(audit_result: dict, report_path: str | None = None) -> dict:
    """
    把审计结果构造成飞书富文本 post 消息内容。
    """
    summary = audit_result["summary"]
    checks = audit_result["checks"]
    advice = audit_result["advice"]

    target = audit_result["normalized_url"] or audit_result["target"]

    problem_checks = [
        check
        for check in checks
        if check["status"] in ["需关注", "异常"]
    ]

    content = []

    content.append([
        {
            "tag": "text",
            "text": (
                f"目标：{target}\n"
                f"整体状态：{summary['overall_status']}\n"
                f"整体风险：{summary['overall_risk']}\n"
                f"安全评分：{summary['security_score']}/100\n"
                f"检查项：{summary['total_checks']} 项，"
                f"高危 {summary['high_count']} 项，"
                f"中危 {summary['medium_count']} 项，"
                f"需关注/异常 {summary['attention_count']} 项"
            ),
        }
    ])

    content.append([
        {
            "tag": "text",
            "text": "\n重点问题：",
        }
    ])

    if not problem_checks:
        content.append([
            {
                "tag": "text",
                "text": "未发现需要重点关注的配置问题。",
            }
        ])
    else:
        for index, check in enumerate(problem_checks[:3], start=1):
            content.append([
                {
                    "tag": "text",
                    "text": f"{index}. {check['name']}（{check['risk']}）：{check['detail']}",
                }
            ])

    content.append([
        {
            "tag": "text",
            "text": "\n综合建议：",
        }
    ])

    if not advice:
        content.append([
            {
                "tag": "text",
                "text": "暂无综合建议。",
            }
        ])
    else:
        for index, item in enumerate(advice[:3], start=1):
            content.append([
                {
                    "tag": "text",
                    "text": f"{index}. {item}",
                }
            ])

    if audit_result.get("llm_advice"):
        content.append([
            {
                "tag": "text",
                "text": "\nDeepSeek 综合建议已生成，建议查看完整报告。",
            }
        ])

    if report_path:
        content.append([
            {
                "tag": "text",
                "text": f"\n报告路径：{report_path}",
            }
        ])

    if audit_result["stopped_reason"]:
        content.append([
            {
                "tag": "text",
                "text": f"\n停止原因：{audit_result['stopped_reason']}",
            }
        ])

    return {
        "zh_cn": {
            "title": "Web 安全配置审计摘要",
            "content": content,
        }
    }


def send_feishu_audit_post_message(
    audit_result: dict,
    report_path: str | None = None,
    webhook_url: str | None = None,
) -> dict:
    """
    通过飞书自定义机器人 webhook 发送富文本审计摘要。
    """
    target_webhook_url = webhook_url or settings.feishu_webhook_url

    if not target_webhook_url:
        return {
            "ok": False,
            "error": "未配置飞书机器人 Webhook URL",
        }

    payload = {
        "msg_type": "post",
        "content": {
            "post": build_feishu_audit_post(audit_result, report_path),
        },
    }

    try:
        response = requests.post(
            target_webhook_url,
            json=payload,
            timeout=10,
        )

        if not response.ok:
            return {
                "ok": False,
                "error": f"飞书富文本消息发送失败，状态码：{response.status_code}，返回内容：{response.text}",
            }

        return {
            "ok": True,
            "error": None,
            "response": response.json(),
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "error": f"飞书富文本消息发送异常：{error}",
        }