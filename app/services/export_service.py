"""
Export Service
==============
Provides export functionality for reports (PDF/Excel).

Features:
- PDF reports for learner progress (weekly/monthly)
- Excel exports for admin analytics
"""
import logging
import io
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from app.core.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Export directory
EXPORT_DIR = getattr(settings, 'EXPORT_DIR', 'static/exports')


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    filename: str
    filepath: str
    download_url: str
    format: str
    size_bytes: int = 0
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "filename": self.filename,
            "download_url": self.download_url,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


# =============================================================================
# SERVICE CLASS
# =============================================================================

class ExportService:
    """
    Export service for generating PDF/Excel reports.
    
    Uses reportlab for PDF and openpyxl for Excel.
    Falls back to simple text/CSV if dependencies not available.
    """
    
    def __init__(self):
        """Initialize export service and check dependencies."""
        self.has_reportlab = self._check_reportlab()
        self.has_openpyxl = self._check_openpyxl()
        self._ensure_export_dir()
    
    def _check_reportlab(self) -> bool:
        """Check if reportlab is available."""
        try:
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate
            logger.info("✅ reportlab available for PDF export")
            return True
        except ImportError:
            logger.warning("⚠️ reportlab not installed, PDF export will use fallback")
            return False
    
    def _check_openpyxl(self) -> bool:
        """Check if openpyxl is available."""
        try:
            import openpyxl
            logger.info("✅ openpyxl available for Excel export")
            return True
        except ImportError:
            logger.warning("⚠️ openpyxl not installed, Excel export will use CSV fallback")
            return False
    
    def _ensure_export_dir(self):
        """Ensure export directory exists."""
        os.makedirs(EXPORT_DIR, exist_ok=True)
    
    def _generate_filename(self, prefix: str, ext: str) -> str:
        """Generate unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{ext}"
    
    # =========================================================================
    # PDF EXPORT
    # =========================================================================
    
    async def export_learner_report_pdf(
        self,
        user_id: int,
        report_type: str,
        data: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ExportResult:
        """
        Export learner progress report as PDF.
        
        Args:
            user_id: Learner's user ID
            report_type: weekly or monthly
            data: Report data dictionary
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            ExportResult with download URL
        """
        filename = self._generate_filename(f"learner_{user_id}_{report_type}", "pdf")
        filepath = os.path.join(EXPORT_DIR, filename)
        
        if self.has_reportlab:
            await self._create_pdf_reportlab(filepath, data, report_type, user_id)
        else:
            await self._create_pdf_fallback(filepath, data, report_type, user_id)
        
        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        expires = datetime.now() + timedelta(hours=24)
        
        return ExportResult(
            success=True,
            filename=filename,
            filepath=filepath,
            download_url=f"/static/exports/{filename}",
            format="pdf",
            size_bytes=size,
            expires_at=expires
        )
    
    async def _create_pdf_reportlab(
        self,
        filepath: str,
        data: Dict[str, Any],
        report_type: str,
        user_id: int
    ):
        """Create PDF using reportlab."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            elements.append(Paragraph(f"{report_type.title()} Progress Report", title_style))
            elements.append(Spacer(1, 12))
            
            # Summary section
            elements.append(Paragraph("Summary", styles['Heading2']))
            summary_data = [
                ["Metric", "Value"],
                ["Total Sessions", str(data.get("total_sessions", 0))],
                ["Speaking Time", f"{data.get('total_speaking_time', 0)} minutes"],
                ["Average Score", f"{data.get('average_score', 0)}%"],
                ["Streak Days", str(data.get("streak_days", 0))],
            ]
            
            table = Table(summary_data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 24))
            
            # Skills breakdown
            if "skills" in data:
                elements.append(Paragraph("Skills Breakdown", styles['Heading2']))
                skills_data = [["Skill", "Score"]]
                for skill, score in data["skills"].items():
                    skills_data.append([skill, f"{score}%"])
                
                skills_table = Table(skills_data, colWidths=[3*inch, 2*inch])
                skills_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(skills_table)
            
            doc.build(elements)
            logger.info(f"PDF created: {filepath}")
            
        except Exception as e:
            logger.error(f"Error creating PDF with reportlab: {e}")
            await self._create_pdf_fallback(filepath, data, report_type, user_id)
    
    async def _create_pdf_fallback(
        self,
        filepath: str,
        data: Dict[str, Any],
        report_type: str,
        user_id: int
    ):
        """Create simple text file as PDF fallback."""
        # Change extension to .txt for fallback
        txt_path = filepath.replace('.pdf', '.txt')
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"{'='*50}\n")
            f.write(f"{report_type.upper()} PROGRESS REPORT\n")
            f.write(f"User ID: {user_id}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"{'='*50}\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Sessions: {data.get('total_sessions', 0)}\n")
            f.write(f"Speaking Time: {data.get('total_speaking_time', 0)} minutes\n")
            f.write(f"Average Score: {data.get('average_score', 0)}%\n")
            f.write(f"Streak Days: {data.get('streak_days', 0)}\n")
            
        logger.info(f"Fallback text report created: {txt_path}")
    
    # =========================================================================
    # EXCEL EXPORT
    # =========================================================================
    
    async def export_analytics_excel(
        self,
        data: Dict[str, Any],
        export_type: str = "analytics",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ExportResult:
        """
        Export analytics data as Excel.
        
        Args:
            data: Analytics data dictionary
            export_type: Type of export (analytics, users, transactions)
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            ExportResult with download URL
        """
        ext = "xlsx" if self.has_openpyxl else "csv"
        filename = self._generate_filename(f"admin_{export_type}", ext)
        filepath = os.path.join(EXPORT_DIR, filename)
        
        if self.has_openpyxl:
            await self._create_excel_openpyxl(filepath, data, export_type)
        else:
            await self._create_csv_fallback(filepath, data, export_type)
        
        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        expires = datetime.now() + timedelta(hours=24)
        
        return ExportResult(
            success=True,
            filename=filename,
            filepath=filepath,
            download_url=f"/static/exports/{filename}",
            format=ext,
            size_bytes=size,
            expires_at=expires
        )
    
    async def _create_excel_openpyxl(
        self,
        filepath: str,
        data: Dict[str, Any],
        export_type: str
    ):
        """Create Excel file using openpyxl."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
            
            wb = Workbook()
            ws = wb.active
            ws.title = export_type.title()
            
            # Header style
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            
            # Write headers
            if "headers" in data:
                headers = data["headers"]
            else:
                headers = list(data.get("rows", [{}])[0].keys()) if data.get("rows") else ["Data"]
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            # Write data rows
            rows = data.get("rows", [])
            for row_idx, row_data in enumerate(rows, 2):
                if isinstance(row_data, dict):
                    for col_idx, header in enumerate(headers, 1):
                        ws.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
                elif isinstance(row_data, (list, tuple)):
                    for col_idx, value in enumerate(row_data, 1):
                        ws.cell(row=row_idx, column=col_idx, value=value)
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 50)
            
            wb.save(filepath)
            logger.info(f"Excel created: {filepath}")
            
        except Exception as e:
            logger.error(f"Error creating Excel with openpyxl: {e}")
            await self._create_csv_fallback(filepath.replace('.xlsx', '.csv'), data, export_type)
    
    async def _create_csv_fallback(
        self,
        filepath: str,
        data: Dict[str, Any],
        export_type: str
    ):
        """Create CSV file as Excel fallback."""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers
            if "headers" in data:
                headers = data["headers"]
            else:
                headers = list(data.get("rows", [{}])[0].keys()) if data.get("rows") else ["Data"]
            writer.writerow(headers)
            
            # Write rows
            rows = data.get("rows", [])
            for row_data in rows:
                if isinstance(row_data, dict):
                    writer.writerow([row_data.get(h, "") for h in headers])
                elif isinstance(row_data, (list, tuple)):
                    writer.writerow(row_data)
        
        logger.info(f"CSV fallback created: {filepath}")
    
    async def export_transactions_excel(
        self,
        transactions: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ExportResult:
        """Export transactions to Excel."""
        data = {
            "headers": ["ID", "User", "Package", "Amount", "Status", "Date"],
            "rows": transactions
        }
        return await self.export_analytics_excel(data, "transactions", start_date, end_date)
    
    async def export_users_excel(
        self,
        users: List[Dict[str, Any]]
    ) -> ExportResult:
        """Export users list to Excel."""
        data = {
            "headers": ["ID", "Email", "Name", "Role", "Status", "Created"],
            "rows": users
        }
        return await self.export_analytics_excel(data, "users")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

export_service = ExportService()
