from websec_autogen_agent.tools.security_checks import (
    normalize_url,
    fetch_homepage,
    check_url_accessibility,
    check_https,
    check_security_headers,
    check_cookie_security,
    check_sensitive_paths,
)


def run_security_audit(raw_url:str) -> dict:
    normalize_result = normalize_url(raw_url)

    if not normalize_result["ok"]:
        return{
            "ok": False,
            "target": raw_url,
            "normalized_url": "",
            "homepage":None,
            "checks":[],
            "error":normalize_result["error"],
            "stopped_reason":"URL 校验失败，无法继续审计。"
        }

    normalized_url = normalize_result["url"]
    homepage = fetch_homepage(normalized_url)

    checks = [
        check_url_accessibility(homepage),
    ]

    if not homepage["ok"]:
        return{
            "ok": False,
            "target": raw_url,
            "normalized_url": normalized_url,
            "homepage":homepage,
            "checks":checks,
            "error":normalize_result["error"],
            "stopped_reason":"首页无法访问，已停止后续检查。"
        }

    checks.extend([
        check_https(normalized_url),
        check_security_headers(homepage),
        check_cookie_security(homepage),
        check_sensitive_paths(normalized_url, homepage),
    ])

    return {
        "ok": True,
        "target": raw_url,
        "normalized_url": normalized_url,
        "homepage": homepage,
        "checks": checks,
        "error": None,
        "stopped_reason": None,
    }

