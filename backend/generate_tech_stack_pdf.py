"""
Generate the FLARE Technology Stack Presentation PDF for Hackathon / Jury Review.
Output:
- c:/Users/ACER/SIH/FLARE_Technology_Stack_Presentation.pdf
- c:/Users/ACER/SIH/frontend/public/flare_tech_stack.pdf
"""
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_ROOT = os.path.join(ROOT_DIR, "FLARE_Technology_Stack_Presentation.pdf")
OUTPUT_PUBLIC = os.path.join(ROOT_DIR, "frontend", "public", "flare_tech_stack.pdf")

# Palette
PRIMARY       = HexColor("#1d4ed8")  # Royal Blue 700
ACCENT        = HexColor("#0284c7")  # Sky Blue 600
EMERALD       = HexColor("#059669")  # Emerald 600
DARK_HEADER   = HexColor("#0f172a")  # Slate 900
LIGHT_BG      = HexColor("#f8fafc")  # Slate 50
CARD_BG       = HexColor("#f1f5f9")  # Slate 100
BORDER_COLOR  = HexColor("#cbd5e1")  # Slate 300
MUTED         = HexColor("#64748b")  # Slate 500
TEXT          = HexColor("#1e293b")  # Slate 800
AMBER_BG      = HexColor("#fffbeb")  # Amber 50
AMBER_BORDER  = HexColor("#fde68a")  # Amber 200
AMBER_TEXT    = HexColor("#92400e")  # Amber 800

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TechTitle",
    parent=styles["Heading1"],
    fontSize=24,
    leading=28,
    textColor=PRIMARY,
    fontName="Helvetica-Bold",
    spaceAfter=4,
)

subtitle_style = ParagraphStyle(
    "TechSubtitle",
    parent=styles["Normal"],
    fontSize=11,
    leading=15,
    textColor=MUTED,
    fontName="Helvetica",
    spaceAfter=12,
)

h1_style = ParagraphStyle(
    "TechH1",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    textColor=DARK_HEADER,
    fontName="Helvetica-Bold",
    spaceBefore=14,
    spaceAfter=6,
)

body_style = ParagraphStyle(
    "TechBody",
    parent=styles["Normal"],
    fontSize=9,
    leading=13,
    textColor=TEXT,
    fontName="Helvetica",
)

bold_body = ParagraphStyle(
    "TechBoldBody",
    parent=body_style,
    fontName="Helvetica-Bold",
)

th_style = ParagraphStyle(
    "TechTH",
    parent=styles["Normal"],
    fontSize=9,
    leading=12,
    textColor=white,
    fontName="Helvetica-Bold",
)

td_title = ParagraphStyle(
    "TechTDTitle",
    parent=styles["Normal"],
    fontSize=8.5,
    leading=11,
    textColor=PRIMARY,
    fontName="Helvetica-Bold",
)

td_body = ParagraphStyle(
    "TechTDBody",
    parent=styles["Normal"],
    fontSize=8,
    leading=11,
    textColor=TEXT,
    fontName="Helvetica",
)

td_highlight = ParagraphStyle(
    "TechTDHighlight",
    parent=styles["Normal"],
    fontSize=8,
    leading=11,
    textColor=EMERALD,
    fontName="Helvetica-Bold",
)

pitch_style = ParagraphStyle(
    "PitchText",
    parent=styles["Normal"],
    fontSize=9.5,
    leading=14,
    textColor=AMBER_TEXT,
    fontName="Helvetica-Oblique",
)

def create_table(headers, rows, col_widths):
    data = [[Paragraph(h, th_style) for h in headers]]
    for row in rows:
        formatted_row = []
        for idx, cell in enumerate(row):
            if idx == 0:
                formatted_row.append(Paragraph(cell, td_title))
            elif idx == len(row) - 1 and len(row) == 3:
                formatted_row.append(Paragraph(cell, td_highlight))
            else:
                formatted_row.append(Paragraph(cell, td_body))
        data.append(formatted_row)
    
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
    ]))
    return t

def build_pdf(target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    doc = SimpleDocTemplate(
        target_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title="FLARE Technology Stack & Presentation Architecture",
        author="FLARE Engineering Team",
    )

    elements = []

    # Title & Metadata Header
    elements.append(Paragraph("FLARE : Technology Stack & Architecture", title_style))
    elements.append(Paragraph("Flight Airfare Real-Time Economic Index Platform • Smart India Hackathon (SIH) Technical Briefing", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=8))

    # 30-Second Elevator Pitch Callout Box
    pitch_data = [
        [
            Paragraph(
                "<b>Executive Presentation Pitch (30-Second Summary for Judges):</b><br/>"
                "<i>\"FLARE is built on a decoupled, high-performance architecture combining <b>Next.js 16</b> and <b>FastAPI</b>. "
                "It ingests live airfares across 8+ OTAs (MakeMyTrip, Goibibo, EaseMyTrip, IndiGo Direct) via <b>Firecrawl</b>, "
                "<b>Scrape.do</b>, and <b>Apify</b>. Data is sanitized using <b>Median Absolute Deviation (MAD)</b> outlier detection, "
                "split into itemized components (<b>Base Rate, Tax & GST, and Convenience Fee</b>), and modeled into a Laspeyres-weighted "
                "airfare index cross-verified with <b>MoSPI Government CPI</b> benchmarks—complete with interactive <b>Leaflet GIS route corridors</b> "
                "and real-time Recharts financial analytics.\"</i>",
                pitch_style
            )
        ]
    ]
    pitch_table = Table(pitch_data, colWidths=[180*mm])
    pitch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AMBER_BG),
        ("BOX", (0, 0), (-1, -1), 1, AMBER_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(pitch_table)
    elements.append(Spacer(1, 6))

    # ── SECTION 1: FRONTEND ──
    elements.append(Paragraph("1. Frontend & User Experience (UX / UI)", h1_style))
    fe_headers = ["Technology", "Role in Architecture", "Engineering Highlights"]
    fe_rows = [
        ["Next.js 16 (App Router)", "Core Web Framework & SSR", "Server Components, dynamic client routing (/search, /explorer, /economic), Turbopack compilation"],
        ["React 19 & TypeScript 5", "UI Rendering & Type Safety", "Strict contracts, Suspense boundary streaming, zero runtime type errors, interactive state hooks"],
        ["Tailwind CSS v4", "Design System & Theming", "Glassmorphic cards, dynamic light/dark modes, customized HSL color tokens, micro-animations"],
        ["Leaflet & React-Leaflet", "Interactive GIS Route Network", "Custom HTML divIcon pulsing nodes, great-circle flight corridor polylines, map-to-search redirection"],
        ["Recharts (v3)", "Financial Data Visualizations", "Stacked bar charts (Base vs. Tax vs. Fee), CPI area trends, carrier price distributions"],
        ["Date-fns", "Temporal Date Engine", "Advance booking days, ISO time serialization, flight duration calculation"],
        ["Cinematic Intro", "Brand & 3D Experience", "High-framerate video splash with smooth canvas transition into live dashboard"],
    ]
    elements.append(create_table(fe_headers, fe_rows, [45*mm, 60*mm, 75*mm]))
    elements.append(Spacer(1, 6))

    # ── SECTION 2: BACKEND ──
    elements.append(Paragraph("2. Backend Microservices & API Architecture", h1_style))
    be_headers = ["Technology", "Role in Architecture", "Engineering Highlights"]
    be_rows = [
        ["FastAPI", "Asynchronous REST Framework", "Async non-blocking I/O endpoints, BackgroundTasks for live scraping, auto OpenAPI/Swagger docs"],
        ["Python 3.12+ / 3.14", "Core Computing Language", "Async event loop (asyncio), robust math operations, vectorized statistical aggregations"],
        ["Uvicorn (ASGI)", "Application Server", "Lightning-fast ASGI production server handling high concurrent requests without thread locks"],
        ["SQLAlchemy 2.0 (ORM)", "Database Relational Mapping", "Declarative models, connection pooling, indexed multi-column filter queries"],
        ["Alembic", "Schema Migrations", "Version-controlled database migrations with repeatable upgrade/downgrade scripts"],
        ["SQLite / PostgreSQL", "Relational Database Engine", "Stores 1,000+ flight observations, airport metadata, and official MoSPI CPI historical series"],
        ["Pydantic v2", "Data Validation & Schemas", "Strict input/output contracts, ISO-8601 parsing, itemized fare breakdown validation"],
    ]
    elements.append(create_table(be_headers, be_rows, [45*mm, 60*mm, 75*mm]))

    # Page Break for clean 2-page executive format
    elements.append(PageBreak())

    # ── SECTION 3: DATA COLLECTION ──
    elements.append(Paragraph("3. Multi-Source Scraping & Data Ingestion Pipeline", h1_style))
    sc_headers = ["Service / Tool", "Target Platform", "Ingestion Capabilities"]
    sc_rows = [
        ["Firecrawl API", "Government Portals & Booking Engines", "AI-driven clean markdown conversion, DOM extraction of dynamic JS content"],
        ["Scrape.do API", "Indian OTAs & Direct Airlines", "Proxy rotation, anti-bot bypass, Indian residential IPs (geoCode=IN), full JS rendering"],
        ["Apify Google Flights Actor", "Google Flights Matrix", "Bulk airline flight card extraction, multi-segment route scraping"],
        ["Amadeus GDS API", "Official Aviation Schedules", "GDS flight timetable validation, schedule consistency checks"],
        ["BeautifulSoup4 (BS4)", "HTML Parsing Engine", "Fast DOM traversal, regex pattern extraction for INR fares, carrier codes, and flight timings"],
        ["HTTPX (Async)", "HTTP/2 Network Client", "Concurrent parallel collectors across 8+ OTAs (MMT, Goibibo, EaseMyTrip, Yatra, Ixigo, IndiGo, Air India)"],
    ]
    elements.append(create_table(sc_headers, sc_rows, [45*mm, 55*mm, 80*mm]))
    elements.append(Spacer(1, 6))

    # ── SECTION 4: STATISTICAL ENGINE ──
    elements.append(Paragraph("4. Economic & Statistical Airfare Index Modeling", h1_style))
    ec_headers = ["Model / Algorithm", "Economic Purpose", "Mathematical Implementation"]
    ec_rows = [
        ["Laspeyres & Jevons Index", "Weighted Inflation Metric", "Weighted arithmetic & geometric means measuring basket price changes against base periods"],
        ["Fare Component Breakdown", "Transparent Pricing Yields", "Strict decomposition: Total Fare = Base Rate + Tax & GST + Portal Convenience Fee"],
        ["MoSPI CPI Integration", "Govt Benchmark Calibration", "Incorporates official data.gov.in Transport weights (1.86% national airfare weighting)"],
        ["Median Absolute Deviation (MAD)", "Outlier Elimination", "Robust statistical filtering detecting promotional flash sales and extreme holiday spikes"],
        ["Haversine Geodesic Distance", "Route Yield Normalization", "Spherical distance calculation (lat/lng) to estimate per-passenger-km fare yields"],
        ["Availability Pressure Index", "Supply / Demand Indicator", "Ratio of sold-out vs. available booking classes across advance purchase windows"],
    ]
    elements.append(create_table(ec_headers, ec_rows, [50*mm, 55*mm, 75*mm]))
    elements.append(Spacer(1, 6))

    # ── SECTION 5: DEVOPS & REPORTING ──
    elements.append(Paragraph("5. DevOps, Reporting & Version Control", h1_style))
    do_headers = ["Technology", "Functionality", "Production Relevance"]
    do_rows = [
        ["ReportLab (Python)", "Automated PDF Generation", "Renders official methodology and technical presentation documentation programmatically"],
        ["Docker & Docker Compose", "Containerized Orchestration", "Multi-container setup (docker-compose.yml) encapsulating frontend, backend, and database"],
        ["Git & GitHub", "Version Control & Security", "Clean repository with GitHub Push Protection compliance and sanitized secrets"],
    ]
    elements.append(create_table(do_headers, do_rows, [45*mm, 60*mm, 75*mm]))

    # Footer note
    elements.append(Spacer(1, 10))
    footer_text = Paragraph(
        "<b>FLARE Architecture Document</b> • Generated for Smart India Hackathon Presentation • 100% Open Source & Production Ready",
        ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    )
    elements.append(footer_text)

    doc.build(elements)
    print(f"Successfully generated PDF: {target_path}")

if __name__ == "__main__":
    build_pdf(OUTPUT_ROOT)
    build_pdf(OUTPUT_PUBLIC)
