import json
import re


URL_PATTERN = re.compile(
    r"https?://[^\s，。；、\]\)）]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s，。；、\]\)）]*"
)

def extract_feishu_message_text(payload: dict) -> str:
    """
    从飞书事件 payload 中提取文本消息内容。
    当前主要兼容飞书事件订阅 2.0 的消息结构。
    """
    event = payload.get("event", {})
    message = event.get("message", {})

    content = message.get("content", "")

    if not content:
        return ""

    try:
        content_data = json.loads(content)
    except json.JSONDecodeError:
        return content

    text = content_data.get("text", "")

    return text.strip()


def extract_first_url(text: str) -> str | None:
    """
    从文本中提取第一个 URL 或域名。
    """
    match = URL_PATTERN.search(text)

    if not match:
        return None

    return match.group(0).strip().rstrip(")]）")


def parse_feishu_message_event(payload: dict) -> dict:
    """
    解析飞书消息事件，返回后续审计需要的关键信息。
    """
    event = payload.get("event", {})
    message = event.get("message", {})

    message_id = message.get("message_id")
    chat_id = message.get("chat_id")
    message_type = message.get("message_type")

    text = extract_feishu_message_text(payload)
    url = extract_first_url(text)

    return {
        "message_id": message_id,
        "chat_id": chat_id,
        "message_type": message_type,
        "text": text,
        "url": url,
    }

