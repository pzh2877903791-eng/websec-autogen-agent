def format_brief_message(audit_result: dict, report_path: str | None = None) -> str:
    """
    把审计结果格式化成适合飞书机器人发送的简短文本。
    """
    summary = audit_result["summary"]
    checks = audit_result["checks"]
    advice = audit_result["advice"]

    lines = []

    lines.append("## Web 安全配置审计摘要")
    lines.append("")
    lines.append(f"目标：{audit_result['normalized_url'] or audit_result['target']}")
    lines.append(f"整体状态：{summary['overall_status']}")
    lines.append(f"整体风险：{summary['overall_risk']}")
    lines.append(f"安全评分：{summary['security_score']}/100")
    lines.append(
        f"检查项：{summary['total_checks']} 项，"
        f"高危 {summary['high_count']} 项，"
        f"中危 {summary['medium_count']} 项，"
        f"需关注/异常 {summary['attention_count']} 项"
    )
    lines.append("")

    problem_checks = [
        check
        for check in checks
        if check["status"] in ["需关注", "异常"]
    ]

    lines.append("### 重点问题")

    if not problem_checks:
        lines.append("未发现需要重点关注的配置问题。")
    else:
        for index, check in enumerate(problem_checks[:3], start=1):
            lines.append(
                f"{index}. {check['name']}（{check['risk']}）：{check['detail']}"
            )

    lines.append("")
    lines.append("### 综合建议")

    if not advice:
        lines.append("暂无综合建议。")
    else:
        for index, item in enumerate(advice[:3], start=1):
            lines.append(f"{index}. {item}")

    if audit_result.get("llm_advice"):
        lines.append("")
        lines.append("DeepSeek 综合建议已生成，建议查看完整报告。")

    if report_path:
        lines.append("")
        lines.append(f"报告路径：{report_path}")

    if audit_result["stopped_reason"]:
        lines.append("")
        lines.append(f"停止原因：{audit_result['stopped_reason']}")

    return "\n".join(lines)