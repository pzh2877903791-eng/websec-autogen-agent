import argparse

from websec_autogen_agent.core.agents import run_security_audit
from websec_autogen_agent.tools.export import save_markdown_report
from websec_autogen_agent.tools.report import format_markdown_report

def print_check_result(check:dict) -> None:
    print(f"\n{check['name']}")
    print(f"状态：{check['status']}")
    print(f"风险：{check['risk']}")
    print(f"细节：{check['detail']}")
    print(f"建议：{check['suggestion']}")

def main():
    parser = argparse.ArgumentParser(
        description = "WebSec Autogen Agent CLI"
    )

    # 声明需要一个叫url的参数
    parser.add_argument(
        "url",
        help = "需要检测的网站 URL，例如 https://example.com"
    )

    # 读取命令行传的参数
    args = parser.parse_args()

    print("收到检测目标：")
    print(args.url)

    audit_result = run_security_audit(args.url)

    if not audit_result["normalized_url"]:
        print("\nURL 校验失败：")
        print(audit_result["error"])
        return

    print("\n标准化后的URL:")
    print(audit_result["normalized_url"])

    homepage = audit_result["homepage"]

    print("\n首页请求结果：")

    if not homepage["ok"]:
        print(homepage["error"])
    else:
        print(f"状态码：{homepage['status_code']}")
        print(f"响应头数量：{len(homepage['headers'])}")
        print(f"页面内容长度：{len(homepage['text'])}")

    summary = audit_result["summary"]

    print("\n审计摘要：")
    print(f"整体状态：{summary['overall_status']}")
    print(f"整体风险：{summary['overall_risk']}")
    print(f"安全评分：{summary['security_score']}/100")
    print(f"检查项数量：{summary['total_checks']}")
    print(
        f"高危：{summary['high_count']}，"
        f"中危：{summary['medium_count']}，"
        f"需关注/异常：{summary['attention_count']}"
    )

    print("\n基础安全检查结果：")

    for check in audit_result["checks"]:
        print_check_result(check)

    if audit_result["stopped_reason"]:
        print(f"\n{audit_result['stopped_reason']}")

    print("\n综合建议：")

    for index, item in enumerate(audit_result["advice"], start=1):
        print(f"{index}. {item}")

    report = format_markdown_report(audit_result)

    report_target = audit_result["normalized_url"] or audit_result["target"]
    report_path = save_markdown_report(report, report_target)

    print(f"\nMarkdown 报告已保存：{report_path}")

if __name__ == "__main__":
    main()
