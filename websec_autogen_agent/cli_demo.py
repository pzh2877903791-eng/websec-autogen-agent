import argparse

from websec_autogen_agent.tools.security_checks import (
    normalize_url,
    fetch_homepage,
    check_url_accessibility,
    check_https,
    check_security_headers,
    check_cookie_security,
)


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

    result = normalize_url(args.url)

    if not result["ok"]:
        print("\nURL 校验失败：")
        print(result["error"])
        return

    print("\n标准化后的URL:")
    print(result["url"])

    homepage = fetch_homepage(result["url"])

    print("\n首页请求结果：")

    if not homepage["ok"]:
        print(homepage["error"])
    else:
        print(f"状态码：{homepage['status_code']}")
        print(f"响应头数量：{len(homepage['headers'])}")
        print(f"页面内容长度：{len(homepage['text'])}")

    checks = [
        check_url_accessibility(homepage),
        check_https(result["url"]),
        check_security_headers(homepage),
        check_cookie_security(homepage),
    ]

    print("\n基础安全检查结果：")

    for check in checks:
        print(f"\n{check['name']}")
        print(f"状态：{check['status']}")
        print(f"风险：{check['risk']}")
        print(f"细节：{check['detail']}")
        print(f"建议：{check['suggestion']}")

if __name__ == "__main__":
    main()
