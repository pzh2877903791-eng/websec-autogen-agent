from fastapi import FastAPI
from pydantic import BaseModel, Field

from websec_autogen_agent.core.agents import run_security_audit
from websec_autogen_agent.tools.export import save_markdown_report
from websec_autogen_agent.tools.report import format_markdown_report
from websec_autogen_agent.tools.brief import format_brief_message
from websec_autogen_agent.integrations.feishu import send_feishu_audit_post_message
from websec_autogen_agent.integrations.feishu_events import parse_feishu_message_event
from fastapi import BackgroundTasks
from websec_autogen_agent.integrations.feishu_client import (
    reply_feishu_audit_post_message,
    reply_feishu_text_message,
    reply_feishu_file_message,
    upload_feishu_file,
)
app = FastAPI(
    title="WebSec AutoGen Agent API",
    description="A learning-oriented Web security audit agent API.",
    version="0.1.0",
)


class AuditRequest(BaseModel):
    url: str = Field(..., min_length=1, description="需要审计的网站 URL")
    export_report: bool = Field(True, description="是否导出 Markdown 报告")
    enable_llm: bool = Field(True, description="本次审计是否尝试调用 DeepSeek 生成综合建议")
    enable_autogen: bool | None = Field(None, description="本次审计是否启用 AutoGen 多角色复核；为空时使用环境变量配置")
    notify_feishu: bool = Field(False, description="是否将审计摘要推送到飞书群")


def build_public_audit_response(audit_result: dict, report_path: str | None = None, feishu_notification:dict | None = None) -> dict:
    homepage = audit_result.get("homepage")

    if homepage is None:
        homepage_summary = None
    else:
        homepage_summary = {
            "ok": homepage["ok"],
            "status_code": homepage["status_code"],
            "headers_count": len(homepage["headers"]),
            "text_length": len(homepage["text"]),
            "cookies_count": len(homepage.get("cookies", [])),
            "error": homepage["error"],
        }

    return {
        "ok": audit_result["ok"],
        "target": audit_result["target"],
        "normalized_url": audit_result["normalized_url"],
        "homepage": homepage_summary,
        "summary": audit_result["summary"],
        "checks": audit_result["checks"],
        "advice": audit_result["advice"],
        "llm_advice": audit_result.get("llm_advice"),
        "autogen_review": audit_result.get("autogen_review"),
        "brief_message": format_brief_message(audit_result, report_path),
        "stopped_reason": audit_result["stopped_reason"],
        "report_path": report_path,
        "feishu_notification": feishu_notification,
    }


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "websec-autogen-agent",
    }

@app.post("/feishu/events")
def handle_feishu_event(payload: dict, background_tasks: BackgroundTasks) -> dict:
    """
    接收飞书应用机器人的事件回调。

    当前阶段：
    1. 处理 URL 校验 challenge；
    2. 解析群消息文本；
    3. 提取消息中的 URL；
    4. 暂时只打印，不自动审计和回复。
    """
    if payload.get("type") == "url_verification" and "challenge" in payload:
        return {
            "challenge": payload["challenge"]
        }

    if "challenge" in payload:
        return {
            "challenge": payload["challenge"]
        }

    parsed_event = parse_feishu_message_event(payload)

    print("收到飞书事件：")
    print(parsed_event)

    if parsed_event.get("message_type") == "text":
        background_tasks.add_task(
            process_feishu_audit_message,
            parsed_event,
        )

    return {
        "ok": True,
        "message": "event received",
        "parsed_event": parsed_event,
    }

def process_feishu_audit_message(parsed_event: dict) -> None:
    """
    后台处理飞书审计消息：
    1. 检查是否提取到 URL；
    2. 判断快速模式 / 深度模式；
    3. 执行审计；
    4. 优先用富文本回复；
    5. 富文本失败时降级为普通文本回复。
    """
    message_id = parsed_event.get("message_id")
    url = parsed_event.get("url")
    text = parsed_event.get("text", "")

    is_deep_audit = (
            "深度审计" in text
            or "详细审计" in text
            or "autogen" in text.lower()
            or "deep" in text.lower()
    )

    print(f"开始处理飞书审计任务：{url}，深度模式：{is_deep_audit}")

    try:
        audit_result = run_security_audit(
            url,
            enable_llm=is_deep_audit,
            enable_autogen=is_deep_audit,
        )

        report_path = None

        if is_deep_audit:
            report = format_markdown_report(audit_result)
            report_target = audit_result["normalized_url"] or audit_result["target"]
            report_path = save_markdown_report(report, report_target)
            print(f"飞书深度审计 Markdown 报告已生成：{report_path}")

        post_reply_result = reply_feishu_audit_post_message(
            message_id,
            audit_result,
            report_path=report_path,
        )

        print(f"飞书富文本回复结果：{post_reply_result}")

        if is_deep_audit and report_path:
            upload_result = upload_feishu_file(report_path)
            print(f"飞书报告文件上传结果：{upload_result}")

            file_key = upload_result.get("file_key")

            if upload_result.get("ok") and file_key:
                file_reply_result = reply_feishu_file_message(
                    message_id,
                    file_key,
                )
                print(f"飞书报告文件回复结果：{file_reply_result}")
            else:
                fallback_result = reply_feishu_text_message(
                    message_id,
                    f"Markdown 报告已生成到本地：{report_path}\n但上传飞书文件失败：{upload_result.get('error')}",
                )
                print(f"飞书文件上传失败兜底回复结果：{fallback_result}")

        if not post_reply_result.get("ok"):
            brief_message = format_brief_message(
                audit_result,
                report_path=report_path,
            )

            text_reply_result = reply_feishu_text_message(
                message_id,
                brief_message,
            )

            print(f"飞书文本兜底回复结果：{text_reply_result}")

    except Exception as error:
        print(f"飞书审计任务执行异常：{error}")

        reply_result = reply_feishu_text_message(
            message_id,
            "审计任务执行失败，请查看后端日志。",
        )

        print(f"飞书异常兜底回复结果：{reply_result}")

@app.post("/audit")
def audit_site(request: AuditRequest) -> dict:
    audit_result = run_security_audit(
        request.url,
        enable_llm = request.enable_llm,
        enable_autogen=request.enable_autogen,
    )

    report_path = None

    if request.export_report:
        report = format_markdown_report(audit_result)
        report_target = audit_result["normalized_url"] or audit_result["target"]
        report_path = save_markdown_report(report, report_target)

    brief_message = format_brief_message(audit_result, report_path)

    feishu_notification = None

    if request.notify_feishu:
        feishu_notification = send_feishu_audit_post_message(audit_result, report_path)

    return build_public_audit_response(
        audit_result,
        report_path,
        feishu_notification,
    )