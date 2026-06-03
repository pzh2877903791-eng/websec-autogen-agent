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

        checks = []

        return{
            "ok": False,
            "target": raw_url,
            "normalized_url": "",
            "homepage":None,
            "checks":checks,
            "summary":calculate_audit_summary(checks),
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
            "summary": calculate_audit_summary(checks),
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
        "summary": calculate_audit_summary(checks),
        "error": None,
        "stopped_reason": None,
    }

def calculate_audit_summary(checks: list[dict]) -> dict:
    """
    根据所有检查项计算整体风险、整体状态和安全评分。
    """
    if not checks:
        return {
            "overall_status": "未完成",
            "overall_risk": "高危",
            "security_score": 0,
            "total_checks": 0,
            "high_count": 0,
            "medium_count": 0,
            "attention_count": 0
        }

    risk_order = {
        "低危": 1,
        "中危": 2,
        "高危": 3
    }

    overall_risk = "低危"
    high_count = 0
    medium_count = 0
    attention_count = 0
    security_score = 100

    for check in checks:
        risk = check["risk"]
        status = check["status"]

        if risk_order.get(risk, 0) > risk_order[overall_risk]:
            overall_risk = risk

        if risk == "高危":
            high_count += 1
            security_score -= 30

        elif risk == "中危":
            medium_count += 1
            security_score -= 15

        if status in ["需关注", "异常"]:
            attention_count += 1

            if risk == "低危":
                security_score -= 5

    security_score = max(0, security_score)

    if high_count > 0:
        overall_status = "异常"
    elif medium_count > 0 or attention_count > 0:
        overall_status = "需关注"
    else:
        overall_status = "通过"

    return {
        "overall_status": overall_status,
        "overall_risk": overall_risk,
        "security_score": security_score,
        "total_checks": len(checks),
        "high_count": high_count,
        "medium_count": medium_count,
        "attention_count": attention_count
    }