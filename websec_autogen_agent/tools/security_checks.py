from urllib.parse import urlparse, urljoin

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
        "suggestion": f"建议根据业务情况逐步补充缺失的安全响应头：{', '.join(missing_headers)}。"
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
        "suggestion": "建议先确认这些 Cookie 的业务用途；如果承载会话、身份标识或敏感业务状态，应配置 Secure、HttpOnly 和 SameSite 属性。"
    }

def is_soft_404_page(text: str) -> bool:
    """
    判断一个返回 200 的页面是否其实是“页面不存在”。
    """
    soft_404_keywords = [
        "页面不存在",
        "未找到页面",
        "请确认网址是否正确",
        "返回首页",
        "not found",
        "page not found",
        "404"
    ]

    lower_text = text.lower()

    for keyword in soft_404_keywords:
        if keyword.lower() in lower_text:
            return True

    return False

def check_sensitive_paths(url: str, homepage: dict | None = None, timeout: int = 5) -> dict:
    """
    检查常见公开文件和敏感路径是否可以直接访问。
    """
    if homepage is not None and not homepage["ok"]:
        return {
            "name": "敏感路径检查",
            "status": "跳过",
            "risk": "低危",
            "detail": "首页请求失败，无法可靠检查敏感路径。",
            "suggestion": "请先确认目标网站可以正常访问，再进行敏感路径检查。"
        }

    public_info_paths = {
        "/robots.txt": "公开爬虫规则文件，通常可以存在。",
        "/.well-known/security.txt": "安全联系方式文件，通常可以存在。"
    }

    sensitive_file_paths = {
        "/.env": "环境变量文件，若可访问可能泄露密钥。",
        "/.git/config": "Git 配置文件，若可访问可能泄露仓库信息。",
        "/backup.zip": "备份压缩包，若可访问可能泄露源码或数据。"
    }

    attention_paths = {
        "/admin": "后台路径，若返回 200，需要确认是否有认证保护。"
    }

    exposed_paths = []
    review_paths = []
    skipped_paths = []

    all_paths = {}
    all_paths.update(public_info_paths)
    all_paths.update(sensitive_file_paths)
    all_paths.update(attention_paths)

    for path, description in all_paths.items():
        target_url = urljoin(url, path)

        try:
            response = requests.get(
                target_url,
                timeout=timeout,
                allow_redirects=False,
                headers={
                    "User-Agent": "WebSecAutoGenAgent-Learning/0.1"
                }
            )
        except requests.exceptions.RequestException as error:
            skipped_paths.append(f"{path}：请求失败，{error}")
            continue

        status_code = response.status_code

        if status_code == 200:
            if is_soft_404_page(response.text):
                continue

            if path in sensitive_file_paths:
                exposed_paths.append(
                    f"{path}：返回 200，{description}"
                )
            else:
                review_paths.append(
                    f"{path}：返回 200，{description}"
                )

        elif status_code in [401, 403]:
            review_paths.append(
                f"{path}：返回 {status_code}，路径存在但访问受限。"
            )

    if exposed_paths:
        detail_parts = [
            "发现可能暴露的敏感文件：" + "；".join(exposed_paths)
        ]

        if review_paths:
            detail_parts.append(
                "其他需要人工确认的路径：" + "；".join(review_paths)
            )

        if skipped_paths:
            detail_parts.append(
                "部分路径请求失败：" + "；".join(skipped_paths)
            )

        return {
            "name": "敏感路径检查",
            "status": "需关注",
            "risk": "高危",
            "detail": " ".join(detail_parts),
            "suggestion": "请优先确认 .env、.git、备份包等敏感文件是否被公开访问，并在服务器层面禁止访问这些路径。"
        }

    if review_paths:
        detail_parts = [
            "发现需要人工确认的公开路径：" + "；".join(review_paths)
        ]

        if skipped_paths:
            detail_parts.append(
                "部分路径请求失败：" + "；".join(skipped_paths)
            )

        return {
            "name": "敏感路径检查",
            "status": "需关注",
            "risk": "低危",
            "detail": " ".join(detail_parts),
            "suggestion": "请确认这些公开文件或路径是否符合预期。对于 /admin 等后台路径，应确保存在认证、权限控制和必要的访问限制。"
        }

    if skipped_paths:
        return {
            "name": "敏感路径检查",
            "status": "需关注",
            "risk": "低危",
            "detail": "未发现敏感文件直接暴露，但部分路径请求失败：" + "；".join(skipped_paths),
            "suggestion": "建议在网络稳定或具备授权环境下重新检查这些路径。"
        }

    return {
        "name": "敏感路径检查",
        "status": "通过",
        "risk": "低危",
        "detail": "未发现常见敏感文件可直接访问。",
        "suggestion": "继续保持敏感文件不可公开访问，并避免将 .env、.git、备份包等文件放在 Web 根目录。"
    }



