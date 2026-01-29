# Issue #44: Export Reports (PDF/Excel)

## 📋 Description
Implement report export functionality for learner progress reports (PDF) and admin analytics (Excel).

## 🎯 Requirements
- **REQ-ADMIN-13**: View statistics & reports with export capability
- **REQ-LEARNER-14**: Receive weekly/monthly performance reports
- Generate PDF reports with charts and statistics
- Generate Excel exports for data analysis

## 📌 Acceptance Criteria
- [ ] `GET /learner/reports/weekly/export?format=pdf` generates PDF
- [ ] `GET /learner/reports/monthly/export?format=pdf` generates PDF
- [ ] `GET /admin/analytics/export?format=excel` exports to Excel
- [ ] `GET /admin/transactions/export?format=excel` exports transactions
- [ ] Support date range parameters
- [ ] Reports include charts/graphs for visual analytics

## 🔧 Technical Details
```python
# Learner Report Export
GET /learner/reports/weekly/export?format=pdf

# Response
{
    "download_url": "/static/reports/weekly_2026_05.pdf",
    "expires_in": 3600
}

# Admin Excel Export
GET /admin/analytics/export?format=excel&start_date=2026-01-01&end_date=2026-01-31

# Response
{
    "download_url": "/static/exports/analytics_202601.xlsx",
    "expires_in": 3600
}
```

## 📦 Dependencies
- `reportlab` or `weasyprint` for PDF generation
- `openpyxl` or `xlsxwriter` for Excel export
- `matplotlib` for charts in reports

## 🧪 Tests
Tests are prepared in: `tests/unit/test_issue_44_export_reports.py`

## 📊 Priority
🔴 **Critical** - Required for documentation/reporting features

## 🏷️ Labels
`enhancement`, `backend`, `reports`, `priority-high`
