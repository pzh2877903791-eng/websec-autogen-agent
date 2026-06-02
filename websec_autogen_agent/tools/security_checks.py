from urllib.parse import urlparse


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