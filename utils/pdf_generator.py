import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from datetime import datetime

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print the total page count
    along with running header rules and page numbers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        # Save state for second pass
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))  # Slate color
        
        # Header
        self.drawString(54, 755, "FitPulse Diagnostic Health & Anomaly Report")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.drawRightString(558, 755, f"Report Generated: {current_time}")
        
        # Header Line divider
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.75)
        self.line(54, 747, 558, 747)
        
        # Footer Line divider
        self.line(54, 45, 558, 45)
        
        # Footer details
        self.drawString(54, 32, "CONFIDENTIAL // FOR DIAGNOSTIC HEALTH SUMMARY & CLINICAL ALGORITHMS USE ONLY")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def generate_pdf_report(user_id, user_details, kpis, ai_insights, anomalies):
    """
    Generates a professional, clinical-looking PDF report using ReportLab.
    Returns the path to the generated temporary PDF file.
    """
    temp_dir = tempfile.gettempdir()
    pdf_filename = f"fitpulse_report_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf_path = os.path.join(temp_dir, pdf_filename)
    
    # Establish document layout (Margins: 0.75 inch)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Styles System
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#718096"),
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748")
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#718096")
    )
    
    # --- 1. TITLE & SUBTITLE ---
    story.append(Paragraph("FITPULSE CLINICAL DIAGNOSTIC REPORT", title_style))
    story.append(Paragraph(f"Patient profile: <b>{user_id}</b> | Assessment period metrics & statistical anomaly timeline summary", subtitle_style))
    
    # --- 2. USER BIO INFORMATION TABLE ---
    bio_data = [
        [
            Paragraph(f"<b>Person ID / Code:</b> {user_details.get('person_id', 'N/A')}", body_style),
            Paragraph(f"<b>Avg Blood Pressure:</b> {user_details.get('bp', 'N/A')} mmHg", body_style),
            Paragraph(f"<b>Weight Category:</b> {user_details.get('weight', 'N/A')}", body_style)
        ],
        [
            Paragraph(f"<b>Age / Demographic:</b> {user_details.get('age', 'N/A')} Years", body_style),
            Paragraph(f"<b>Avg Stress level:</b> {user_details.get('stress', 'N/A')}/10", body_style),
            Paragraph(f"<b>Subjective Sleep Quality:</b> {user_details.get('sleep_quality', 'N/A')}/10", body_style)
        ]
    ]
    
    bio_table = Table(bio_data, colWidths=[168, 168, 168])
    bio_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(bio_table)
    story.append(Spacer(1, 12))
    
    # --- 3. HEALTH SCORE CALLOUT PANEL ---
    score = ai_insights.get("score", 100)
    status = ai_insights.get("overall_status", "Normal")
    summary_text = ai_insights.get("summary", "")
    
    status_color_val = ai_insights.get("status_color", "green")
    status_colors = {
        "green": colors.HexColor("#E6FFFA"),   # soft teal
        "orange": colors.HexColor("#FFFAF0"),  # soft orange
        "red": colors.HexColor("#FFF5F5")     # soft pink/red
    }
    status_border_colors = {
        "green": colors.HexColor("#319795"),
        "orange": colors.HexColor("#DD6B20"),
        "red": colors.HexColor("#E53E3E")
    }
    
    bg_color = status_colors.get(status_color_val, colors.HexColor("#E6FFFA"))
    border_color = status_border_colors.get(status_color_val, colors.HexColor("#319795"))
    
    score_text_style = ParagraphStyle(
        'ScoreText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=25,
        alignment=1,
        textColor=border_color
    )
    
    score_lbl_style = ParagraphStyle(
        'ScoreLbl',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        alignment=1,
        textColor=colors.HexColor("#718096")
    )
    
    status_text_style = ParagraphStyle(
        'StatusText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=border_color
    )

    score_html = f"<b>{score}</b><font size=9 color='#718096'>/100</font>"
    status_html = f"<b>{status.upper()}</b>"
    
    score_cell = [
        Spacer(1, 2),
        Paragraph(score_html, score_text_style),
        Spacer(1, 2),
        Paragraph("HEALTH SCORE", score_lbl_style),
        Spacer(1, 4),
        Paragraph(status_html, status_text_style),
        Spacer(1, 2)
    ]
    
    summary_cell = [
        Paragraph("<b>CLINICAL EVALUATION SUMMARY:</b>", ParagraphStyle('EvalHeader', parent=body_style, fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor("#2D3748"))),
        Spacer(1, 3),
        Paragraph(summary_text, body_style)
    ]
    
    score_table = Table([[score_cell, summary_cell]], colWidths=[100, 404])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('BOX', (0,0), (-1,-1), 1.25, border_color),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 12))
    
    # --- 4. KEY INDICATOR PERFORMANCES (KPIs) ---
    kpis_data = [
        [
            Paragraph("<b>AVG HEART RATE</b>", ParagraphStyle('KPITitle', parent=body_style, fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.HexColor("#718096"))),
            Paragraph("<b>AVG SLEEP</b>", ParagraphStyle('KPITitle', parent=body_style, fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.HexColor("#718096"))),
            Paragraph("<b>TOTAL STEPS</b>", ParagraphStyle('KPITitle', parent=body_style, fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.HexColor("#718096"))),
            Paragraph("<b>ANOMALY FLAGS</b>", ParagraphStyle('KPITitle', parent=body_style, fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.HexColor("#718096")))
        ],
        [
            Paragraph(f"<font size=13><b>{kpis.get('avg_hr', 0)}</b></font> <font size=8>bpm</font>", body_style),
            Paragraph(f"<font size=13><b>{kpis.get('avg_sleep', 0)}</b></font> <font size=8>hrs</font>", body_style),
            Paragraph(f"<font size=13><b>{kpis.get('total_steps', 0):,}</b></font> <font size=8>steps</font>", body_style),
            Paragraph(f"<font size=13 color='#E53E3E'><b>{kpis.get('total_anoms', 0)}</b></font> <font size=8 color='#718096'>flags</font>", body_style)
        ]
    ]
    kpis_table = Table(kpis_data, colWidths=[126, 126, 126, 126])
    kpis_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpis_table)
    story.append(Spacer(1, 14))
    
    # --- 5. SUGGESTIONS & RECOMMENDATIONS ACTIONS ---
    recommendations_list = []
    recs = ai_insights.get("recommendations", [])
    if recs:
        for rec in recs:
            status = rec.get("status", "Info")
            metric = rec.get("metric", "")
            text = rec.get("text", "")
            
            # Left color bar based on priority
            bar_color = colors.HexColor("#A0AEC0")
            if status == "Critical":
                bar_color = colors.HexColor("#E53E3E")
            elif status == "Warning":
                bar_color = colors.HexColor("#DD6B20")
            elif status == "Good":
                bar_color = colors.HexColor("#38A169")
            elif status == "Info":
                bar_color = colors.HexColor("#3182CE")
            
            rec_para = Paragraph(f"<b>{metric}:</b> {text}", body_style)
            rec_table = Table([["", rec_para]], colWidths=[4, 500])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0), bar_color),
                ('BACKGROUND', (1,0), (1,0), colors.HexColor("#F8FAFC")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (1,0), (1,0), 8),
                ('RIGHTPADDING', (1,0), (1,0), 8),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            recommendations_list.append(rec_table)
            recommendations_list.append(Spacer(1, 4))
    else:
        recommendations_list.append(Paragraph("All active vitals and activity counts map to health standards. No deviations found.", body_style))
        
    story.append(KeepTogether([
        Paragraph("🩺 SUGGESTED CLINICAL RECOMMENDATIONS & ACTIONS", section_title_style),
        *recommendations_list
    ]))
    
    story.append(Spacer(1, 10))
    
    # --- 6. FLAGGED ANOMALIES TIMELINE TABLE ---
    anom_story_elements = []
    if anomalies:
        anom_header = [
            Paragraph("<b>Timestamp</b>", bold_body_style),
            Paragraph("<b>Anomaly Type</b>", bold_body_style),
            Paragraph("<b>Heart Rate</b>", bold_body_style),
            Paragraph("<b>Sleep</b>", bold_body_style),
            Paragraph("<b>Daily Steps</b>", bold_body_style)
        ]
        anom_table_rows = [anom_header]
        for anom in anomalies:
            anom_table_rows.append([
                Paragraph(anom.get("timestamp", "N/A"), body_style),
                Paragraph(f"<font color='#E53E3E'><b>{anom.get('type', 'N/A')}</b></font>", body_style),
                Paragraph(f"{anom.get('hr', 'N/A')} bpm", body_style),
                Paragraph(f"{anom.get('sleep', 'N/A')} hrs", body_style),
                Paragraph(f"{anom.get('steps', 0):,}" if isinstance(anom.get('steps'), (int, float)) else str(anom.get('steps')), body_style)
            ])
            
        anom_table = Table(anom_table_rows, colWidths=[120, 114, 90, 90, 90])
        anom_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        anom_story_elements.append(anom_table)
    else:
        no_anom_table = Table([[
            Paragraph("<b>Biometrics Stability Verified:</b> No statistical outlier trends or anomalous residuals detected in current sensor feeds.", body_style)
        ]], colWidths=[504])
        no_anom_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FFF4")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#C6F6D5")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        anom_story_elements.append(no_anom_table)
        
    story.append(KeepTogether([
        Paragraph("🚨 DETECTED ANOMALOUS BIO-EVENT LOG TIMELINE", section_title_style),
        *anom_story_elements
    ]))
    
    story.append(Spacer(1, 14))
    
    # --- 7. CLINICAL DISCLAIMER ---
    disclaimer_elements = [
        Paragraph("<b>CLINICAL EVALUATION DISCLAIMER:</b>", ParagraphStyle('DisclaimerHeader', parent=body_style, fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#718096"))),
        Spacer(1, 2),
        Paragraph(ai_insights.get("clinical_note", "This report is generated automatically by mathematical models (Prophet and DBSCAN). It represents a statistical diagnostic assessment and does not constitute primary medical advice. Please consult your physician for clinical diagnoses."), disclaimer_style)
    ]
    
    story.append(KeepTogether(disclaimer_elements))
    
    # Draw Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return pdf_path
