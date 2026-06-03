def format_markdown_report(audit_result: dict) -> str:
    """
    把审计结果格式化成 Markdown 报告文本。
    """
    summary = audit_result["summary"]

    lines = []

    lines.append("# Web 安全配置审计报告")
    lines.append("")
    lines.append("## 1. 检测目标")
    lines.append("")
    lines.append(f"- 原始输入：{audit_result['target']}")
    lines.append(f"- 标准化 URL：{audit_result['normalized_url'] or '无'}")
    lines.append("")

    lines.append("## 2. 审计摘要")
    lines.append("")
    lines.append(f"- 整体状态：{summary['overall_status']}")
    lines.append(f"- 整体风险：{summary['overall_risk']}")
    lines.append(f"- 安全评分：{summary['security_score']}/100")
    lines.append(f"- 检查项数量：{summary['total_checks']}")
    lines.append(f"- 高危数量：{summary['high_count']}")
    lines.append(f"- 中危数量：{summary['medium_count']}")
    lines.append(f"- 需关注或异常数量：{summary['attention_count']}")
    lines.append("")

    lines.append("## 3. 检查结果")
    lines.append("")

    if not audit_result["checks"]:
        lines.append("本次审计未执行具体检查项。")
        lines.append("")
    else:
        for index, check in enumerate(audit_result["checks"], start=1):
            lines.append(f"### 3.{index} {check['name']}")
            lines.append("")
            lines.append(f"- 状态：{check['status']}")
            lines.append(f"- 风险：{check['risk']}")
            lines.append(f"- 细节：{check['detail']}")
            lines.append(f"- 建议：{check['suggestion']}")
            lines.append("")

    lines.append("## 4. 综合建议")
    lines.append("")

    if not audit_result["advice"]:
        lines.append("暂无综合建议。")
        lines.append("")
    else:
        for index, item in enumerate(audit_result["advice"], start=1):
            lines.append(f"{index}. {item}")

        lines.append("")

    if audit_result["stopped_reason"]:
        lines.append("## 5. 提前停止原因")
        lines.append("")
        lines.append(audit_result["stopped_reason"])
        lines.append("")
        lines.append("## 6. 安全边界")
    else:
        lines.append("## 5. 安全边界")
    lines.append("")
    lines.append("本工具仅进行基础 Web 安全配置检查，不进行密码爆破、漏洞利用、高并发扫描或攻击性测试。")
    lines.append("请仅对自己拥有或已获得明确授权的网站使用本工具。")
    lines.append("")

    return "\n".join(lines)