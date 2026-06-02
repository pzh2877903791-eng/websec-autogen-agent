import argparse

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

if __name__ == "__main__":
    main()
