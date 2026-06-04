from websec_autogen_agent.tools.security_checks import (
    normalize_url,
    fetch_homepage,
    check_url_accessibility,
    check_https,
    check_security_headers,
    check_cookie_security,
    check_sensitive_paths,
)

from websec_autogen_agent.core.llm import generate_deepseek_advice
from websec_autogen_agent.core.autogen_workflow import run_autogen_audit_review

def run_security_audit(raw_url:str, enable_llm: bool = True) -> dict:
    normalize_result = normalize_url(raw_url)

    if not normalize_result["ok"]:
        checks = []
        summary = calculate_audit_summary(checks)
        advice = generate_rule_based_advice(checks, summary)

        return{
            "ok": False,
            "target": raw_url,
            "normalized_url": "",
            "homepage":None,
            "checks":checks,
            "summary": summary,
            "advice": advice,
            "llm_advice": None,
            "autogen_review": None,
            "error":normalize_result["error"],
            "stopped_reason":"URL 校验失败，无法继续审计。"
        }

    normalized_url = normalize_result["url"]
    homepage = fetch_homepage(normalized_url)

    checks = [
        check_url_accessibility(homepage),
    ]

    if not homepage["ok"]:
        summary = calculate_audit_summary(checks)
        advice = generate_rule_based_advice(checks, summary)

        return{
            "ok": False,
            "target": raw_url,
            "normalized_url": normalized_url,
            "homepage":homepage,
            "checks":checks,
            "summary": summary,
            "advice": advice,
            "llm_advice": None,
            "autogen_review": None,
            "error":normalize_result["error"],
            "stopped_reason":"首页无法访问，已停止后续检查。"
        }

    checks.extend([
        check_https(normalized_url),
        check_security_headers(homepage),
        check_cookie_security(homepage),
        check_sensitive_paths(normalized_url, homepage),
    ])

    summary = calculate_audit_summary(checks)
    advice = generate_rule_based_advice(checks, summary)

    llm_advice = None

    if enable_llm:
        llm_advice = generate_deepseek_advice({
            "target": raw_url,
            "normalized_url": normalized_url,
            "checks": checks,
            "summary": summary,
            "rule_based_advice": advice,
        })

    autogen_review = None

    autogen_input = {
        "target": raw_url,
        "normalized_url": normalized_url,
        "checks": checks,
        "summary": summary,
        "advice": advice,
        "llm_advice": llm_advice,
        "stopped_reason": None,
    }

    autogen_review = run_autogen_audit_review(autogen_input)

    return {
        "ok": True,
        "target": raw_url,
        "normalized_url": normalized_url,
        "homepage": homepage,
        "checks": checks,
        "summary": summary,
        "advice": advice,
        "llm_advice": llm_advice,
        "autogen_review": autogen_review,
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

def generate_rule_based_advice(checks: list[dict], summary: dict) -> list[str]:
    """
    根据检查结果和审计摘要生成规则化综合建议。
    """
    advice = []

    if summary["high_count"] > 0:
        advice.append("存在高危风险项，请优先处理可能导致敏感信息泄露或服务不可用的问题。")

    elif summary["medium_count"] > 0:
        advice.append("存在中危配置问题，建议优先处理安全响应头、Cookie 安全属性和 HTTPS 相关配置。")

    elif summary["attention_count"] > 0:
        advice.append("当前未发现明显高危问题，但存在需要人工确认的配置项。")

    else:
        advice.append("当前基础配置风险较低，建议保持定期审计和日志监控。")

    for check in checks:
        if check["status"] in ["需关注", "异常"]:
            advice.append(f"{check['name']}：{check['suggestion']}")

    unique_advice = []

    for item in advice:
        if item not in unique_advice:
            unique_advice.append(item)

    return unique_advice