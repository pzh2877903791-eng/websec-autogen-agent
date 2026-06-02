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

        cookies = []

        for cookie in response.cookies:
            cookie_rest = getattr(cookie, "_rest",{})

            cookies.append({
                "name":cookie.name,
                # Secure 作用：这个 Cookie 只能通过 HTTPS 发送，不能通过 HTTP 明文发送。
                "secure":cookie.secure,
                # HttpOnly 作用：阻止 JavaScript 直接读取这个 Cookie。
                "httponly":"HttpOnly" in cookie.name,
                # SameSite 作用：限制跨站请求时 Cookie 是否会被自动携带，可以降低 CSRF 风险。
                "samesite":cookie_rest.get("SameSite") or cookie_rest.get("samesite")
            })

        return {
            "ok": True,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text,
            "cookies": cookies,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "text":"",
            "cookies":[],
            "error":"请求超时"
        }

    except requests.exceptions.RequestException as error:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "text":"",
            "cookies":[],
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
            "detail":f"首页请求成功，HTTP 状态码为 {status_code}。",
            "suggestion":"网站首页可以正常访问。"
        }

    if status_code in [401, 403]:
        return {
            "name": "URL 可访问性检查",
            "status": "需关注",
            "risk": "低危",
            "detail": f"首页返回 HTTP 状态码 {status_code}，表示访问受限或需要认证。",
            "suggestion": "如果这桑后台、管理页或受保护页面，属于正常情况；如果是公开首页，需要检查访问控制配置。"
        }

    return{
        "name":"URL 可访问性检查",
            "status":"需关注",
            "risk":"中危",
            "detail":f"首页返回 HTTP 状态码 {status_code}。",
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

def check_security_headers(homepage:dict) -> dict:
    """
    检查目标网站是否配置常见 HTTP 安全响应头
    """
    if not homepage["ok"]:
        return {
            "name": "安全响应头检查",
            "status": "跳过",
            "risk": "低危",
            "detail": "首页请求失败，无法检查响应头。",
            "suggestion": "请先确认目标网站可以正常访问。"
        }

    headers = homepage["headers"]

    lower_headers = {
        key.lower():value
        for key, value in headers.items()
    }

    required_headers = {
        "content-security-policy":"限制页面可以加载哪些脚本、样式和资源，降低 XSS 风险。",
        "strict-transport-security":"强制浏览器以后使用 HTTPS 访问网站。",
        "x-frame-options":"防止浏览器错误猜测文件类型。",
        "x-content-type-options":"防止浏览器错误猜测文件类型。",
        "referrer-policy":"控制浏览器跳转时携带多少来源信息",
        "permissions-policy":"限制摄像头、麦克风、定位等浏览器能力。"
    }

    missing_headers = []

    for header_name in required_headers:
        if header_name not in lower_headers:
            missing_headers.append(header_name)

    if not missing_headers:
        return {
            "name": "安全响应头检查",
            "status": "通过",
            "risk": "低危",
            "detail": "目标网站已配置常见安全响应头。",
            "suggestion": "继续保持安全响应头配置，并定期检查策略是否符合业务需求。"
        }

    return {
        "name": "安全响应头检查",
        "status": "需关注",
        "risk": "中危",
        "detail": f"缺少以下安全响应头：{', '.join(missing_headers)}。",
        "suggestion": "建议根据业务情况逐步补充安全响应头，优先关注 CSP、HSTS、X-Frame-Options 和 X-Content-Type-Options。"
    }

def check_cookie_security(homepage:dict) -> dict:
    """
    检查 Cookie 是否配置 Secure、HttpOnly、SameSite 等安全属性。
    """
    if not homepage["ok"]:
        return {
            "name": "Cookie 安全属性检查",
            "status": "跳过",
            "risk": "低危",
            "detail": "首页请求失败，无法检查 Cookie。",
            "suggestion": "请先确认目标网站可以正常访问。"
        }

    cookies = homepage["cookies"]
    if not cookies:
        return {
            "name": "Cookie 安全属性检查",
            "status": "通过",
            "risk": "低危",
            "detail": "目标响应中未发现 Set-Cookie。",
            "suggestion": "当前首页未设置 Cookie；如果登录态或会话 Cookie 在其他页面设置，仍建议继续检查。"
        }

    weak_cookie_details = []

    for cookie in cookies:
        problems = []

        if not cookie["secure"]:
            problems.append("缺少 Secure")

        if not cookie["httponly"]:
            problems.append("缺少 HttpOnly")

        if not cookie["samesite"]:
            problems.append("缺少 SameSite")

        if problems:
            weak_cookie_details.append(
                f"{cookie['name']}:{', '.join(problems)}"
            )

    if not weak_cookie_details:
        return {
            "name": "Cookie 安全属性检查",
            "status": "通过",
            "risk": "低危",
            "detail": "首页返回的 Cookie 已配置常见安全属性。",
            "suggestion": "继续保持 Cookie 安全属性配置，并关注登录态 Cookie 的保护。"
        }

    return {
        "name": "Cookie 安全属性检查",
        "status": "需关注",
        "risk": "中危",
        "detail": "发现 Cookie 安全属性不完整：" + "； ".join(weak_cookie_details),
        "suggestion": "建议为敏感 Cookie 配置 Secure、HttpOnly 和 SameSite 属性，降低会话泄露、XSS 窃取 Cookie 和 CSRF 风险。"
    }
