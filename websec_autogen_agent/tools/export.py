import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def build_report_filename(target_url: str) -> str:
    """
    根据目标 URL 生成安全的 Markdown 报告文件名。
    """
    parsed = urlparse(target_url)

    raw_name = parsed.netloc or parsed.path or "target"

    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw_name)
    safe_name = safe_name.strip("_") or "target"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{safe_name}_{timestamp}.md"


def save_markdown_report(report: str, target_url: str, output_dir: str = "reports") -> str:
    """
    保存 Markdown 报告，并返回文件路径。
    """
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    filename = build_report_filename(target_url)
    report_path = report_dir / filename

    report_path.write_text(report, encoding="utf-8")

    return str(report_path)