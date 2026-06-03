from fastapi import FastAPI
from pydantic import BaseModel, Field

from websec_autogen_agent.core.agents import run_security_audit
from websec_autogen_agent.tools.export import save_markdown_report
from websec_autogen_agent.tools.report import format_markdown_report


app = FastAPI(
    title="WebSec AutoGen Agent API",
    description="A learning-oriented Web security audit agent API.",
    version="0.1.0",
)


class AuditRequest(BaseModel):
    url: str = Field(..., min_length=1, description="需要审计的网站 URL")
    export_report: bool = Field(True, description="是否导出 Markdown 报告")
    enable_llm: bool = Field(True, description="本次审计是否尝试调用 DeepSeek 生成综合建议")


def build_public_audit_response(audit_result: dict, report_path: str | None = None) -> dict:
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
        "stopped_reason": audit_result["stopped_reason"],
        "report_path": report_path,
    }


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "websec-autogen-agent",
    }


@app.post("/audit")
def audit_site(request: AuditRequest) -> dict:
    audit_result = run_security_audit(
        request.url,
        enable_llm = request.enable_llm,
    )

    report_path = None

    if request.export_report:
        report = format_markdown_report(audit_result)
        report_target = audit_result["normalized_url"] or audit_result["target"]
        report_path = save_markdown_report(report, report_target)

    return build_public_audit_response(audit_result, report_path)