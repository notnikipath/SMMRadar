from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import StringIO
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field

from shared.smmradar_common import ReportFormat, ReportRequest, Settings

settings = Settings(service_name="report-service", service_port=8506)
app = FastAPI(title="SMM Radar Report Service", version="1.0.0")

reports: list[dict] = []


class DashboardBuildRequest(BaseModel):
    brand: str
    summary: dict = Field(default_factory=dict)
    mention_dynamics: list[dict] = Field(default_factory=list)
    top_authors: list[dict] = Field(default_factory=list)
    geo_distribution: list[dict] = Field(default_factory=list)
    word_cloud: list[dict] = Field(default_factory=list)
    competitors: list[dict] = Field(default_factory=list)
    alerts: list[dict] = Field(default_factory=list)


class ExportRequest(BaseModel):
    report_id: str
    report_format: ReportFormat


DashboardBuildRequest.model_rebuild()
ExportRequest.model_rebuild()
ReportRequest.model_rebuild()


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(lines: list[str]) -> bytes:
    text_ops = ["BT", "/F1 12 Tf", "50 780 Td"]
    for index, line in enumerate(lines[:32]):
        safe = _pdf_escape(line)
        if index == 0:
            text_ops.append(f"({safe}) Tj")
        else:
            text_ops.append(f"0 -18 Td ({safe}) Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", errors="ignore")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def _rows_to_csv(rows: list[dict]) -> bytes:
    if not rows:
        return b"empty\n"
    keys = sorted({key for row in rows for key in row})
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=keys)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/reports/dashboard/build")
async def build_dashboard(request: DashboardBuildRequest) -> dict:
    report_id = f"rpt-{uuid4().hex[:10]}"
    payload = {
        "report_id": report_id,
        "brand": request.brand,
        "created_at": datetime.now(UTC).isoformat(),
        **request.model_dump(mode="json"),
    }
    reports.append(payload)
    return {
        "report_id": report_id,
        "brand": request.brand,
        "widgets": [
            "mention_dynamics",
            "top_authors",
            "geo_distribution",
            "word_cloud",
            "sentiment_mix",
            "competitor_sov",
            "alerts_timeline",
        ],
        "status": "ready",
    }


@app.get("/reports/history")
async def history(limit: int = 20) -> dict:
    items = reports[-max(1, min(limit, 200)) :]
    return {"count": len(items), "items": items}


@app.post("/reports/export")
async def export(request: ExportRequest) -> Response:
    report = next((item for item in reversed(reports) if item["report_id"] == request.report_id), None)
    if report is None:
        return Response(content="Report not found", status_code=404)

    if request.report_format == ReportFormat.JSON:
        import json

        content = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
        headers = {"Content-Disposition": f"attachment; filename={request.report_id}.json"}
        return Response(content=content, media_type="application/json", headers=headers)

    if request.report_format == ReportFormat.EXCEL:
        rows = report.get("top_authors") or report.get("word_cloud") or []
        content = _rows_to_csv(rows)
        headers = {"Content-Disposition": f"attachment; filename={request.report_id}.csv"}
        return Response(content=content, media_type="text/csv", headers=headers)

    lines = [
        f"SMM Radar Report: {report['brand']}",
        f"Generated at: {report['created_at']}",
        f"Total mentions: {report.get('summary', {}).get('total_mentions', 0)}",
        f"Crisis probability: {report.get('summary', {}).get('crisis_probability', 0)}",
        f"Alerts: {len(report.get('alerts', []))}",
    ]
    content = _build_pdf(lines)
    headers = {"Content-Disposition": f"attachment; filename={request.report_id}.pdf"}
    return Response(content=content, media_type="application/pdf", headers=headers)
