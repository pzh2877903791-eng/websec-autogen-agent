import argparse

from websec_autogen_agent.core.agents import run_security_audit

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

    print("\n基础安全检查结果：")

    for check in audit_result["checks"]:
        print_check_result(check)

    if audit_result["stopped_reason"]:
        print(f"\n{audit_result['stopped_reason']}")


if __name__ == "__main__":
    main()
