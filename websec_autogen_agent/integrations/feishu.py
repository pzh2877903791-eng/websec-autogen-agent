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