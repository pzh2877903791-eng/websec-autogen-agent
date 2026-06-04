import json
import time
from pathlib import Path

import requests

from websec_autogen_agent.core.config import settings
from websec_autogen_agent.integrations.feishu import build_feishu_audit_post

_token_cache = {
    "tenant_access_token": None,
    "expire_at": 0,
}


def get_tenant_access_token() -> str | None:
    """
    获取飞书自建应用 tenant_access_token，并做简单内存缓存。
    """
    if not settings.has_feishu_app_credentials:
        print("未配置 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
        return None

    now = int(time.time())

    cached_token = _token_cache["tenant_access_token"]
    expire_at = _token_cache["expire_at"]

    if cached_token and now < expire_at - 60:
        return cached_token

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    payload = {
        "app_id": settings.feishu_app_id,
        "app_secret": settings.feishu_app_secret,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("code") != 0:
            print(f"获取 tenant_access_token 失败：{data}")
            return None

        token = data.get("tenant_access_token")
        expire = data.get("expire", 7200)

        _token_cache["tenant_access_token"] = token
        _token_cache["expire_at"] = now + int(expire)

        return token

    except requests.exceptions.RequestException as error:
        print(f"获取 tenant_access_token 异常：{error}")
        return None


def reply_feishu_text_message(message_id: str, text: str) -> dict:
    """
    回复飞书消息。
    """
    token = get_tenant_access_token()

    if not token:
        return {
            "ok": False,
            "error": "无法获取 tenant_access_token",
        }

    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "msg_type": "text",
        "content": json.dumps(
            {
                "text": text,
            },
            ensure_ascii=False,
        ),
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10,
        )

        if not response.ok:
            return {
                "ok": False,
                "error": f"回复飞书消息失败，状态码：{response.status_code}，返回内容：{response.text}",
            }

        data = response.json()

        if data.get("code") != 0:
            return {
                "ok": False,
                "error": f"回复飞书消息失败：{data}",
            }

        return {
            "ok": True,
            "error": None,
            "response": data,
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "error": f"回复飞书消息异常：{error}",
        }

def reply_feishu_audit_post_message(
    message_id: str,
    audit_result: dict,
    report_path: str | None = None,
) -> dict:
    """
    以飞书富文本 post 消息的形式回复审计摘要。
    """
    token = get_tenant_access_token()

    if not token:
        return {
            "ok": False,
            "error": "无法获取 tenant_access_token",
        }

    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    post_content = build_feishu_audit_post(audit_result, report_path)

    payload = {
        "msg_type": "post",
        "content": json.dumps(
            post_content,
            ensure_ascii=False,
        ),
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10,
        )

        if not response.ok:
            return {
                "ok": False,
                "error": f"回复飞书富文本消息失败，状态码：{response.status_code}，返回内容：{response.text}",
            }

        data = response.json()

        if data.get("code") != 0:
            return {
                "ok": False,
                "error": f"回复飞书富文本消息失败：{data}",
            }

        return {
            "ok": True,
            "error": None,
            "response": data,
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "error": f"回复飞书富文本消息异常：{error}",
        }

def upload_feishu_file(file_path: str) -> dict:
    """
    上传本地文件到飞书，返回 file_key。
    """
    token = get_tenant_access_token()

    if not token:
        return {
            "ok": False,
            "error": "无法获取 tenant_access_token",
            "file_key": None,
        }

    path = Path(file_path)

    if not path.is_file():
        return {
            "ok": False,
            "error": f"文件不存在：{file_path}",
            "file_key": None,
        }

    url = "https://open.feishu.cn/open-apis/im/v1/files"

    headers = {
        "Authorization": f"Bearer {token}",
    }

    data = {
        "file_type": "stream",
        "file_name": path.name,
    }

    try:
        with path.open("rb") as file_obj:
            files = {
                "file": (
                    path.name,
                    file_obj,
                    "text/markdown",
                )
            }

            response = requests.post(
                url,
                headers=headers,
                data=data,
                files=files,
                timeout=30,
            )

        if not response.ok:
            return {
                "ok": False,
                "error": f"上传飞书文件失败，状态码：{response.status_code}，返回内容：{response.text}",
                "file_key": None,
            }

        result = response.json()

        if result.get("code") != 0:
            return {
                "ok": False,
                "error": f"上传飞书文件失败：{result}",
                "file_key": None,
            }

        file_key = result.get("data", {}).get("file_key")

        if not file_key:
            return {
                "ok": False,
                "error": f"上传飞书文件成功但未返回 file_key：{result}",
                "file_key": None,
            }

        return {
            "ok": True,
            "error": None,
            "file_key": file_key,
            "response": result,
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "error": f"上传飞书文件异常：{error}",
            "file_key": None,
        }


def reply_feishu_file_message(message_id: str, file_key: str) -> dict:
    """
    以文件消息形式回复飞书消息。
    """
    token = get_tenant_access_token()

    if not token:
        return {
            "ok": False,
            "error": "无法获取 tenant_access_token",
        }

    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "msg_type": "file",
        "content": json.dumps(
            {
                "file_key": file_key,
            },
            ensure_ascii=False,
        ),
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10,
        )

        if not response.ok:
            return {
                "ok": False,
                "error": f"回复飞书文件消息失败，状态码：{response.status_code}，返回内容：{response.text}",
            }

        result = response.json()

        if result.get("code") != 0:
            return {
                "ok": False,
                "error": f"回复飞书文件消息失败：{result}",
            }

        return {
            "ok": True,
            "error": None,
            "response": result,
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "error": f"回复飞书文件消息异常：{error}",
        }