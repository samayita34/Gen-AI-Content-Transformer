import io
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)

from pptx import Presentation as PptxPresentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from app.services.generation.models import (
    OutputType,
    TransformationResult,
    ExecutiveSummaryContent,
    AdvisoryContent,
    PresentationContent,
    VideoScriptContent,
)
from app.services.verification.models import VerificationReport
from app.services.retrieval.models import SourceReference

logger = logging.getLogger("transformai.export.service")


class ExportService:
    """
    Pure Python document export generator for Multi-Format Generative Content.
    Generates publication-quality PDFs (via ReportLab) and PowerPoint Decks (via python-pptx).
    """

    def __init__(self):
        self._styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """Initializes refined ReportLab paragraph styles."""
        self.style_doc_title = ParagraphStyle(
            "DocTitle",
            parent=self._styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
        self.style_section_heading = ParagraphStyle(
            "SectionHeading",
            parent=self._styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        )
        self.style_subsection_heading = ParagraphStyle(
            "SubSectionHeading",
            parent=self._styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
        self.style_body = ParagraphStyle(
            "CustomBody",
            parent=self._styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        self.style_bullet = ParagraphStyle(
            "CustomBullet",
            parent=self._styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            leftIndent=15,
            spaceAfter=4,
        )
        self.style_meta_label = ParagraphStyle(
            "MetaLabel",
            parent=self._styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#475569"),
        )
        self.style_meta_val = ParagraphStyle(
            "MetaVal",
            parent=self._styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )
        self.style_badge_unverified = ParagraphStyle(
            "BadgeUnverified",
            parent=self._styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#92400e"),
        )
        self.style_badge_verified = ParagraphStyle(
            "BadgeVerified",
            parent=self._styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e3a8a"),
        )
        self.style_speaker_notes = ParagraphStyle(
            "SpeakerNotes",
            parent=self._styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475569"),
        )

    def generate_export(
        self,
        result: TransformationResult,
        export_format: str,
        verification_report: Optional[VerificationReport] = None,
        include_provenance: bool = True,
        include_verification: bool = True,
    ) -> bytes:
        """
        Dispatches export generation based on format and output_type.
        """
        fmt = export_format.lower()
        if fmt == "pptx":
            if result.output_type != OutputType.PRESENTATION:
                raise ValueError("PPTX export format is only supported for Presentation outputs.")
            return self.generate_presentation_pptx(result, verification_report, include_verification)
        elif fmt == "pdf":
            return self.generate_pdf_export(
                result=result,
                verification_report=verification_report,
                include_provenance=include_provenance,
                include_verification=include_verification,
            )
        else:
            raise ValueError(f"Unsupported export format: {export_format}. Use 'pdf' or 'pptx'.")

    # =========================================================================
    # PDF GENERATION (ReportLab)
    # =========================================================================

    def generate_pdf_export(
        self,
        result: TransformationResult,
        verification_report: Optional[VerificationReport] = None,
        include_provenance: bool = True,
        include_verification: bool = True,
    ) -> bytes:
        """Generates a structured PDF document for any supported output type."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45,
        )

        story = []

        # 1. Header Banner & Title
        story.append(self._build_header_banner(result, verification_report, include_verification))
        story.append(Spacer(1, 10))

        # 2. Metadata Box
        story.append(self._build_metadata_box(result))
        story.append(Spacer(1, 14))

        # 3. Format Specific Content
        if result.output_type == OutputType.EXECUTIVE_SUMMARY:
            self._render_executive_summary(story, result.content)
        elif result.output_type == OutputType.ADVISORY:
            self._render_advisory(story, result.content)
        elif result.output_type == OutputType.PRESENTATION:
            self._render_presentation_pdf(story, result.content)
        elif result.output_type == OutputType.VIDEO_SCRIPT:
            self._render_video_script(story, result.content)
        else:
            story.append(Paragraph(str(result.content), self.style_body))

        # 4. Verification Summary Section (if verified and requested)
        if include_verification and verification_report:
            story.append(Spacer(1, 14))
            self._render_verification_section(story, verification_report)

        # 5. Provenance & Source References Table (if requested)
        if include_provenance and result.source_references:
            story.append(Spacer(1, 14))
            self._render_provenance_section(story, result.source_references)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header_banner(
        self,
        result: TransformationResult,
        verification_report: Optional[VerificationReport],
        include_verification: bool,
    ) -> Table:
        """Builds top brand banner with project name and verification badge."""
        brand_p = Paragraph(
            "<b>TransformAI</b> <font size='8' color='#64748b'>| Source-Grounded Multi-Format Content Transformation</font>",
            self.style_body,
        )

        if include_verification and verification_report:
            rep = verification_report
            badge_text = (
                f"<b>CLAIM VERIFICATION COMPLETE</b><br/>"
                f"<font size='7.5'>{rep.supported_claims} Supported &bull; {rep.contradicted_claims} Contradicted &bull; "
                f"{rep.partially_supported_claims} Partial &bull; {rep.insufficient_evidence_claims} Insufficient Evidence</font>"
            )
            badge_p = Paragraph(badge_text, self.style_badge_verified)
            badge_bg = colors.HexColor("#eff6ff")
            badge_border = colors.HexColor("#bfdbfe")
        else:
            badge_text = "<b>SOURCE GROUNDED &mdash; UNVERIFIED</b>"
            badge_p = Paragraph(badge_text, self.style_badge_unverified)
            badge_bg = colors.HexColor("#fefce8")
            badge_border = colors.HexColor("#fef08a")

        header_table = Table(
            [[brand_p, badge_p]],
            colWidths=[3.2 * inch, 4.0 * inch],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BACKGROUND", (1, 0), (1, 0), badge_bg),
                ("BOX", (1, 0), (1, 0), 1, badge_border),
                ("TOPPADDING", (1, 0), (1, 0), 4),
                ("BOTTOMPADDING", (1, 0), (1, 0), 4),
                ("LEFTPADDING", (1, 0), (1, 0), 8),
                ("RIGHTPADDING", (1, 0), (1, 0), 8),
            ])
        )
        return header_table

    def _build_metadata_box(self, result: TransformationResult) -> Table:
        """Builds key-value metadata table."""
        cfg = result.configuration or {}
        created_str = (
            result.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if isinstance(result.created_at, datetime)
            else str(result.created_at)
        )

        rows = [
            [
                Paragraph("<b>Output Format:</b>", self.style_meta_label),
                Paragraph(result.output_type.value.replace("_", " ").title(), self.style_meta_val),
                Paragraph("<b>Generated At:</b>", self.style_meta_label),
                Paragraph(created_str, self.style_meta_val),
            ],
            [
                Paragraph("<b>Audience / Tone:</b>", self.style_meta_label),
                Paragraph(f"{cfg.get('audience', 'Executive')} / {cfg.get('tone', 'Professional')}", self.style_meta_val),
                Paragraph("<b>Model / Provider:</b>", self.style_meta_label),
                Paragraph(f"{result.provider} ({result.model})", self.style_meta_val),
            ],
            [
                Paragraph("<b>Document ID:</b>", self.style_meta_label),
                Paragraph(str(result.document_id)[:16] + "...", self.style_meta_val),
                Paragraph("<b>Transformation ID:</b>", self.style_meta_label),
                Paragraph(str(result.transformation_id)[:16] + "...", self.style_meta_val),
            ],
        ]

        t = Table(rows, colWidths=[1.3 * inch, 2.3 * inch, 1.3 * inch, 2.3 * inch])
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        return t

    def _render_executive_summary(self, story: list, content: Any):
        """Renders Executive Summary content."""
        if hasattr(content, "__dict__"):
            title = getattr(content, "title", "Executive Summary")
            overview = getattr(content, "overview", "")
            key_points = getattr(content, "key_points", [])
            important_facts = getattr(content, "important_facts", [])
            implications = getattr(content, "implications", [])
            conclusion = getattr(content, "conclusion", "")
        elif isinstance(content, dict):
            title = content.get("title", "Executive Summary")
            overview = content.get("overview", "")
            key_points = content.get("key_points", [])
            important_facts = content.get("important_facts", [])
            implications = content.get("implications", [])
            conclusion = content.get("conclusion", "")
        else:
            story.append(Paragraph(str(content), self.style_body))
            return

        story.append(Paragraph(title, self.style_doc_title))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        # Strategic Overview
        if overview:
            story.append(Paragraph("Strategic Overview", self.style_section_heading))
            story.append(Paragraph(overview, self.style_body))

        # Core Findings
        if key_points:
            story.append(Paragraph("Core Findings & Key Points", self.style_section_heading))
            for pt in key_points:
                story.append(Paragraph(f"&bull; {pt}", self.style_bullet))

        # Grounded Facts
        if important_facts:
            story.append(Paragraph("Grounded Factual Assertions", self.style_section_heading))
            for fact in important_facts:
                story.append(Paragraph(f"&bull; {fact}", self.style_bullet))

        # Implications
        if implications:
            story.append(Paragraph("Strategic & Operational Implications", self.style_section_heading))
            for imp in implications:
                story.append(Paragraph(f"&bull; {imp}", self.style_bullet))

        # Conclusion
        if conclusion:
            story.append(Paragraph("Conclusion", self.style_section_heading))
            story.append(Paragraph(conclusion, self.style_body))

    def _render_advisory(self, story: list, content: Any):
        """Renders Advisory content."""
        if hasattr(content, "__dict__"):
            title = getattr(content, "title", "Advisory Briefing")
            situation = getattr(content, "situation", "")
            key_info = getattr(content, "key_information", [])
            risks = getattr(content, "risks_or_considerations", [])
            actions = getattr(content, "recommended_actions", [])
            conclusion = getattr(content, "conclusion", "")
        elif isinstance(content, dict):
            title = content.get("title", "Advisory Briefing")
            situation = content.get("situation", "")
            key_info = content.get("key_information", [])
            risks = content.get("risks_or_considerations", [])
            actions = content.get("recommended_actions", [])
            conclusion = content.get("conclusion", "")
        else:
            story.append(Paragraph(str(content), self.style_body))
            return

        story.append(Paragraph(title, self.style_doc_title))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        if situation:
            story.append(Paragraph("Current Situation & Context", self.style_section_heading))
            story.append(Paragraph(situation, self.style_body))

        if key_info:
            story.append(Paragraph("Key Information", self.style_section_heading))
            for info in key_info:
                story.append(Paragraph(f"&bull; {info}", self.style_bullet))

        if risks:
            story.append(Paragraph("Risks & Considerations", self.style_section_heading))
            for r in risks:
                story.append(Paragraph(f"&bull; {r}", self.style_bullet))

        if actions:
            story.append(Paragraph("Grounded Recommended Actions", self.style_section_heading))
            for act in actions:
                story.append(Paragraph(f"&bull; {act}", self.style_bullet))

        if conclusion:
            story.append(Paragraph("Advisory Conclusion", self.style_section_heading))
            story.append(Paragraph(conclusion, self.style_body))

    def _render_presentation_pdf(self, story: list, content: Any):
        """Renders Presentation deck slide summaries in PDF format."""
        if hasattr(content, "__dict__"):
            title = getattr(content, "presentation_title", "Presentation Deck")
            slides = getattr(content, "slides", [])
        elif isinstance(content, dict):
            title = content.get("presentation_title", "Presentation Deck")
            slides = content.get("slides", [])
        else:
            story.append(Paragraph(str(content), self.style_body))
            return

        story.append(Paragraph(title, self.style_doc_title))
        story.append(Paragraph(f"Slide Deck Summary ({len(slides)} Slides)", self.style_meta_label))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        for slide in slides:
            s_num = getattr(slide, "slide_number", None) or (slide.get("slide_number") if isinstance(slide, dict) else "")
            s_title = getattr(slide, "title", None) or (slide.get("title") if isinstance(slide, dict) else "")
            s_bullets = getattr(slide, "bullets", []) or (slide.get("bullets", []) if isinstance(slide, dict) else [])
            s_notes = getattr(slide, "speaker_notes", None) or (slide.get("speaker_notes") if isinstance(slide, dict) else "")

            slide_elements = []
            slide_elements.append(Paragraph(f"Slide {s_num}: {s_title}", self.style_subsection_heading))
            for b in s_bullets:
                slide_elements.append(Paragraph(f"&bull; {b}", self.style_bullet))

            if s_notes:
                slide_elements.append(Spacer(1, 3))
                slide_elements.append(Paragraph(f"<b>Presenter Notes:</b> <i>&ldquo;{s_notes}&rdquo;</i>", self.style_speaker_notes))

            slide_elements.append(Spacer(1, 8))
            story.append(KeepTogether(slide_elements))

    def _render_video_script(self, story: list, content: Any):
        """Renders Video Script & Storyboard in PDF format."""
        if hasattr(content, "__dict__"):
            title = getattr(content, "title", "Video Storyboard Script")
            target_dur = getattr(content, "target_duration", "")
            scenes = getattr(content, "scenes", [])
        elif isinstance(content, dict):
            title = content.get("title", "Video Storyboard Script")
            target_dur = content.get("target_duration", "")
            scenes = content.get("scenes", [])
        else:
            story.append(Paragraph(str(content), self.style_body))
            return

        story.append(Paragraph(title, self.style_doc_title))
        if target_dur:
            story.append(Paragraph(f"<b>Target Duration:</b> {target_dur}", self.style_meta_val))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        story.append(Paragraph("Storyboard Scenes", self.style_section_heading))

        table_rows = [
            [
                Paragraph("<b>Scene #</b>", self.style_meta_label),
                Paragraph("<b>Visual Description & On-Screen Text</b>", self.style_meta_label),
                Paragraph("<b>Voiceover Narration</b>", self.style_meta_label),
            ]
        ]

        for sc in scenes:
            num = getattr(sc, "scene_number", "") or (sc.get("scene_number", "") if isinstance(sc, dict) else "")
            visual = getattr(sc, "visual_description", "") or (sc.get("visual_description", "") if isinstance(sc, dict) else "")
            narration = getattr(sc, "narration", "") or (sc.get("narration", "") if isinstance(sc, dict) else "")
            on_screen = getattr(sc, "on_screen_text", "") or (sc.get("on_screen_text", "") if isinstance(sc, dict) else "")

            visual_text = visual
            if on_screen:
                visual_text += f"<br/><br/><b>On-Screen:</b> {on_screen}"

            table_rows.append([
                Paragraph(f"<b>#{num}</b>", self.style_meta_val),
                Paragraph(visual_text, self.style_body),
                Paragraph(f"<i>&ldquo;{narration}&rdquo;</i>", self.style_body),
            ])

        table = Table(table_rows, colWidths=[0.8 * inch, 3.2 * inch, 3.2 * inch])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(table)

    def _render_verification_section(self, story: list, report: VerificationReport):
        """Renders M6 verification claim-level summary in PDF."""
        story.append(Paragraph("Claim Verification Summary (M6 Engine)", self.style_section_heading))
        summary_text = (
            f"<b>Total Claims Analyzed:</b> {report.total_claims} | "
            f"<b>Supported:</b> {report.supported_claims} | "
            f"<b>Contradicted:</b> {report.contradicted_claims} | "
            f"<b>Partially Supported:</b> {report.partially_supported_claims} | "
            f"<b>Insufficient Evidence:</b> {report.insufficient_evidence_claims}"
        )
        story.append(Paragraph(summary_text, self.style_body))

        # Sample table of verified claims
        if report.claim_results:
            table_rows = [
                [
                    Paragraph("<b>Claim Statement</b>", self.style_meta_label),
                    Paragraph("<b>Verdict</b>", self.style_meta_label),
                    Paragraph("<b>Explanation</b>", self.style_meta_label),
                ]
            ]
            for cr in report.claim_results[:10]:  # Up to top 10 claims for concise PDF
                stmt = cr.claim.statement if hasattr(cr.claim, "statement") else str(cr.claim)
                verdict_str = cr.verdict.value.upper() if hasattr(cr.verdict, "value") else str(cr.verdict).upper()
                table_rows.append([
                    Paragraph(stmt, self.style_bullet),
                    Paragraph(f"<b>{verdict_str}</b>", self.style_meta_val),
                    Paragraph(cr.explanation or "", self.style_meta_val),
                ])

            tbl = Table(table_rows, colWidths=[3.2 * inch, 1.4 * inch, 2.6 * inch])
            tbl.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )
            story.append(tbl)

    def _render_provenance_section(self, story: list, source_refs: List[SourceReference]):
        """Renders Provenance & Source References Table."""
        story.append(Paragraph("Provenance & Source References", self.style_section_heading))
        story.append(
            Paragraph(
                "The following discrete source chunks from the indexed repository were retrieved to ground this generated artifact.",
                self.style_body,
            )
        )

        table_rows = [
            [
                Paragraph("<b>Ref #</b>", self.style_meta_label),
                Paragraph("<b>Source File</b>", self.style_meta_label),
                Paragraph("<b>Section Heading</b>", self.style_meta_label),
                Paragraph("<b>Page / Chunk</b>", self.style_meta_label),
            ]
        ]

        for idx, ref in enumerate(source_refs, 1):
            fname = ref.source_filename or "source_document"
            sec = ref.section_title or "Overview"
            page = f"Page {ref.page_number}" if ref.page_number else "—"
            chunk_info = f"{page} (Chunk {ref.chunk_index})" if ref.chunk_index is not None else page

            table_rows.append([
                Paragraph(f"[{idx}]", self.style_meta_val),
                Paragraph(fname, self.style_meta_val),
                Paragraph(sec, self.style_meta_val),
                Paragraph(chunk_info, self.style_meta_val),
            ])

        tbl = Table(table_rows, colWidths=[0.6 * inch, 2.8 * inch, 2.4 * inch, 1.4 * inch])
        tbl.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        story.append(tbl)

    # =========================================================================
    # PPTX GENERATION (python-pptx)
    # =========================================================================

    def generate_presentation_pptx(
        self,
        result: TransformationResult,
        verification_report: Optional[VerificationReport] = None,
        include_verification: bool = True,
    ) -> bytes:
        """
        Generates a native 16:9 PowerPoint Deck using python-pptx.
        Preserves slide titles, bullet hierarchy, speaker notes, and verification provenance.
        """
        prs = PptxPresentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        content = result.content
        if hasattr(content, "__dict__"):
            pres_title = getattr(content, "presentation_title", "TransformAI Presentation")
            slides = getattr(content, "slides", [])
        elif isinstance(content, dict):
            pres_title = content.get("presentation_title", "TransformAI Presentation")
            slides = content.get("slides", [])
        else:
            pres_title = "TransformAI Presentation"
            slides = []

        # Color palette
        c_dark = RGBColor(15, 23, 42)     # slate-950
        c_indigo = RGBColor(79, 70, 229)  # indigo-600
        c_text = RGBColor(30, 41, 59)     # slate-800
        c_sub = RGBColor(100, 116, 139)   # slate-500

        # 1. Title Slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title_shape = slide.shapes.title
        subtitle_shape = slide.placeholders[1]

        title_shape.text = pres_title
        if title_shape.text_frame.paragraphs:
            p = title_shape.text_frame.paragraphs[0]
            p.font.size = Pt(36)
            p.font.bold = True
            p.font.color.rgb = c_dark

        # Verification subtitle text
        verif_status = "Source Grounded — Unverified"
        if include_verification and verification_report:
            vr = verification_report
            verif_status = f"Claim Verification Complete ({vr.supported_claims} Supported, {vr.contradicted_claims} Contradicted)"

        subtitle_shape.text = (
            f"TransformAI: Source-Grounded Generative Transformation\n"
            f"Status: {verif_status} | Model: {result.provider} / {result.model}"
        )
        if subtitle_shape.text_frame.paragraphs:
            p = subtitle_shape.text_frame.paragraphs[0]
            p.font.size = Pt(16)
            p.font.color.rgb = c_sub

        # Title slide notes
        slide.notes_slide.notes_text_frame.text = (
            f"Presentation: {pres_title}\n"
            f"Generated via TransformAI on {result.created_at}.\n"
            f"Transformation ID: {result.transformation_id}"
        )

        # 2. Content Slides
        bullet_slide_layout = prs.slide_layouts[1]
        for s in slides:
            s_num = getattr(s, "slide_number", None) or (s.get("slide_number") if isinstance(s, dict) else "")
            s_title = getattr(s, "title", None) or (s.get("title") if isinstance(s, dict) else "Slide")
            s_bullets = getattr(s, "bullets", []) or (s.get("bullets", []) if isinstance(s, dict) else [])
            s_notes = getattr(s, "speaker_notes", None) or (s.get("speaker_notes") if isinstance(s, dict) else "")

            c_slide = prs.slides.add_slide(bullet_slide_layout)
            c_title = c_slide.shapes.title
            c_title.text = f"{s_title}"
            if c_title.text_frame.paragraphs:
                p = c_title.text_frame.paragraphs[0]
                p.font.size = Pt(28)
                p.font.bold = True
                p.font.color.rgb = c_dark

            body_shape = c_slide.placeholders[1]
            tf = body_shape.text_frame
            tf.clear()

            for idx, bullet in enumerate(s_bullets):
                bp = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
                bp.text = bullet
                bp.level = 0
                bp.font.size = Pt(18)
                bp.font.color.rgb = c_text
                bp.space_after = Pt(12)

            # Speaker Notes
            if s_notes:
                c_slide.notes_slide.notes_text_frame.text = s_notes

        buffer = io.BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


default_export_service = ExportService()
