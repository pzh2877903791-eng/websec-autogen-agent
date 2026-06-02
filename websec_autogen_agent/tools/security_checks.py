from urllib.parse import urlparse

import requests

def normalize_url(raw_url:str) -> dict:
    """
    清洗和校验用户输入的url

    返回格式：
    {
        "ok": True 或 False,
        "url": "标准化后的url",
        "error": "错误原因"
    }
    """

    cleaned_url = raw_url.strip()
    cleaned_url = cleaned_url.rstrip("。。，,，")

    if not cleaned_url:
        return {
            "ok": False,
            "url": "",
            "error": "URL 不能为空"
        }

    parsed = urlparse(cleaned_url)

    if parsed.scheme and parsed.scheme not in ["http", "https"]:
        return {
            "ok": False,
            "url": "",
            "error": f"不支持的协议：{parsed.scheme}"
        }

    if not parsed.scheme:
        cleaned_url = "https://" + cleaned_url
        parsed = urlparse(cleaned_url)

    if not parsed.netloc:
        return {
            "ok": False,
            "url": "",
            "error": "URL 格式不正确，缺少域名"
        }

    return {
        "ok": True,
        "url": cleaned_url,
        "error": "none"
    }

def fetch_homepage(url:str, timeout:int = 10) -> dict:
    """
    请求网站首页，获取状态码、响应头和页面内容。

    返回格式：
    {
        "ok": True 或 False,
        "status_code":200,
        "headers":{...},
        "text":"网页 HTML 内容",
        "error": None 或 "错误原因"
    }
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent":"WebsecAutoGenAgent"
            }
        )

        return {
            "ok": True,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "text":"",
            "error":"请求超时"
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "text":"",
            "error":f"请求失败：{error}"
        }

def check_url_accessibility(homepage:dict) -> dict:
    """
    检查目标网站首页是否可以访问。
    """
    if not homepage["ok"]:
        return {
            "name":"URL 可访问性检查",
            "status":"异常",
            "risk":"高危",
            "detail":homepage["error"],
            "suggestion":"请确认域名是否正确、网络是否正常，或者目标网站是否允许访问。"
        }

    status_code = homepage["status_code"]

    if 200 <= status_code < 400:
        return {
            "name":"URL 可访问性检查",
            "status":"通过",
            "risk":"低危",
            "detail":f"首页请求成功，HTTP 状态码为{status_code}。",
            "suggestion":"网站首页可以正常访问。"
        }

    if status_code in [401, 403]:
        return {
            "name": "URL 可访问性检查",
            "status": "需关注",
            "risk": "低危",
            "detail": f"首页返回 HTTP 状态码{status_code}，表示访问受限或需要认证。",
            "suggestion": "如果这桑后台、管理页或受保护页面，属于正常情况；如果是公开首页，需要检查访问控制配置。"
        }

    return{
        "name":"URL 可访问性检查",
            "status":"需关注",
            "risk":"中危",
            "detail":f"首页返回 HTTP 状态码{status_code}。",
            "suggestion":"请确认该状态码是否符合预期，必要时检查服务器配置。"
    }

def check_https(url:str) -> dict:
    """
    检查目标 URL 是否使用HTTPS。
    """
    if url.lower().startswith("https://"):
        return {
            "name": "HTTPS 检查",
            "status": "通过",
            "risk": "低危",
            "detail": "目标 URL 使用 HTTPS 协议。",
            "suggestion": "继续保持 HTTPS 访问，并建议配合 HSTS 响应头增强安全性。"
        }

    if url.lower().startswith("http://"):
        return {
            "name": "HTTPS 检查",
            "status": "需关注",
            "risk": "中危",
            "detail": "目标 URL 使用 HTTP 协议，传输过程可能被窃听或篡改。",
            "suggestion": "建议启用 HTTPS，并将 HTTP 请求自动重定向到 HTTPS。"
        }

    return{
        "name": "HTTPS 检查",
        "status": "异常",
        "risk": "高危",
        "detail": "URL 协议无法识别。",
        "suggestion": "请使用 http:// 或 https:// 开头的 URL。"
    }