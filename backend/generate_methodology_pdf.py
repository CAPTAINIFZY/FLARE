"""
Generate the FLARE Methodology PDF.
Run: python.exe generate_methodology_pdf.py
Output: ../frontend/public/flare_methodology.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Output path ──────────────────────────────────────────────────────────────
OUTPUT = os.path.join("..", "frontend", "public", "flare_methodology.pdf")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# ── Color palette ─────────────────────────────────────────────────────────────
PRIMARY      = HexColor("#7c3aed")   # violet-700
LIGHT_BG     = HexColor("#f5f3ff")   # violet-50
DARK_BG      = HexColor("#1e1b4b")   # indigo-950
BORDER_COLOR = HexColor("#ddd6fe")   # violet-200
MUTED        = HexColor("#6b7280")   # gray-500
AMBER        = HexColor("#92400e")   # amber-800
AMBER_BG     = HexColor("#fffbeb")   # amber-50
TEXT         = HexColor("#111827")   # gray-900

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    rightMargin=20*mm,
    leftMargin=20*mm,
    topMargin=22*mm,
    bottomMargin=22*mm,
    title="FLARE Airfare Price Index — Methodology",
    author="FLARE Platform",
    subject="Technical Methodology Documentation",
)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    "FLARETitle",
    parent=styles["Heading1"],
    fontSize=28,
    textColor=PRIMARY,
    spaceAfter=4,
    spaceBefore=0,
    fontName="Helvetica-Bold",
    alignment=TA_LEFT,
)
subtitle_style = ParagraphStyle(
    "FLARESubtitle",
    parent=styles["Normal"],
    fontSize=11,
    textColor=MUTED,
    spaceAfter=8,
    fontName="Helvetica",
)
section_title_style = ParagraphStyle(
    "SectionTitle",
    parent=styles["Heading2"],
    fontSize=14,
    textColor=PRIMARY,
    spaceBefore=14,
    spaceAfter=6,
    fontName="Helvetica-Bold",
    borderPad=4,
)
subsection_style = ParagraphStyle(
    "SubSection",
    parent=styles["Heading3"],
    fontSize=11,
    textColor=TEXT,
    spaceBefore=8,
    spaceAfter=3,
    fontName="Helvetica-Bold",
)
body_style = ParagraphStyle(
    "FLAREBody",
    parent=styles["Normal"],
    fontSize=10,
    textColor=TEXT,
    leading=15,
    spaceAfter=6,
    fontName="Helvetica",
    alignment=TA_JUSTIFY,
)
disclaimer_style = ParagraphStyle(
    "Disclaimer",
    parent=styles["Normal"],
    fontSize=9.5,
    textColor=AMBER,
    leading=14,
    spaceBefore=6,
    spaceAfter=6,
    fontName="Helvetica",
    alignment=TA_JUSTIFY,
)
label_style = ParagraphStyle(
    "Label",
    parent=styles["Normal"],
    fontSize=8,
    textColor=PRIMARY,
    fontName="Helvetica-Bold",
    letterSpacing=1,
)

# ── Content data ──────────────────────────────────────────────────────────────
sections = [
    {
        "id": 1,
        "title": "Data Sources",
        "items": [
            ("OTA Booking Portals (via scrape.do)",
             "Fares are collected from MakeMyTrip, Cleartrip, Ixigo, Yatra, Goibibo, and EaseMyTrip "
             "using the scrape.do JavaScript-rendering API. Each observation records the source portal, "
             "timestamp, and raw HTML selector path for provenance."),
            ("Government Airline — Air India",
             "Air India is a Government of India (GoI) owned airline. Fares from airindia.com are tagged "
             "source_type='govt_airline_scrape' to distinguish them from private OTA data. This is "
             "significant for CPI analysis as it represents direct government pricing."),
            ("Direct Airline Portals",
             "IndiGo direct bookings are collected from goindigo.in via scrape.do. These are tagged "
             "source_type='airline_scrape' and have no OTA convenience charge markup."),
            ("Amadeus GDS",
             "The Amadeus Global Distribution System provides industry-standard fare data when API "
             "credentials are configured. Labelled source_type='gds'."),
            ("Google Flights (Apify)",
             "Google Flights data via the Apify actor provides meta-search aggregated fares. "
             "Requires APIFY_API_TOKEN."),
            ("Demo Data",
             "When live sources are unavailable, a DemoCollector generates statistically realistic "
             "synthetic fares. Always labelled data_status='DEMO' — never mixed with live data."),
        ],
    },
    {
        "id": 2,
        "title": "Collection Process",
        "items": [
            ("Trigger",
             "Collection is triggered on every user search. All sources run in parallel via asyncio.gather(). "
             "Failures in any individual source do not affect others."),
            ("scrape.do Configuration",
             "API: api.scrape.do · JS rendering enabled · geoCode=IN (India) · 5–6 second wait for React "
             "hydration · Retry on rate limits. Configured via SCRAPE_DO_TOKEN environment variable."),
            ("Provenance Fields",
             "Every observation records: source (e.g., 'makemytrip'), source_type, observation_timestamp, "
             "data_status (LIVE/DEMO/ERROR), quality_score."),
        ],
    },
    {
        "id": 3,
        "title": "Data Cleaning",
        "items": [
            ("Validation",
             "Fares must be between ₹800 and ₹1,50,000. Travel date must be valid. Route must match known "
             "airport IATA codes. Invalid records are rejected and logged."),
            ("Deduplication",
             "Observations with identical route, date, airline, and fare (rounded to nearest rupee) collected "
             "within the same 1-hour window are deduplicated. The original observation is kept; duplicates "
             "are discarded."),
            ("Outlier Detection",
             "Z-score outlier detection applied per batch. Observations with |Z| > 3.0 are flagged "
             "(outlier_flag=True) but NOT deleted. Reason stored in outlier_reason. Quality score reduced."),
        ],
    },
    {
        "id": 4,
        "title": "Fare Normalization",
        "items": [
            ("Raw vs Normalized",
             "Both raw_fare and normalized_fare are stored. Raw observations are never destroyed."),
            ("Convenience Charge Adjustment",
             "OTA portals add convenience charges (₹150–₹350 typically). Known per-OTA estimates are "
             "subtracted from total_fare to derive the normalized fare. Direct airline sources (Air India, "
             "IndiGo) have zero convenience charge."),
            ("Stop Equivalency",
             "Stop adjustments are recorded for reference but not applied to the index calculation — "
             "the index captures actual market prices including stop variations."),
        ],
    },
    {
        "id": 5,
        "title": "Route Selection",
        "items": [
            ("12-Route Basket",
             "The index is calculated over a basket of 12 major domestic routes: DEL-BOM, BOM-DEL, DEL-BLR, "
             "BOM-BLR, DEL-HYD, BOM-MAA, DEL-MAA, BLR-HYD, DEL-CCU, BOM-CCU, DEL-COK, BOM-GOI."),
            ("Extensibility",
             "The RouteBasket table is configurable. Additional routes can be added via the database "
             "with their respective weights."),
        ],
    },
    {
        "id": 6,
        "title": "Weighting",
        "items": [
            ("Weight Source",
             "Route weights are based on approximate passenger traffic volumes from DGCA Annual Reports. "
             "The DEL-BOM corridor receives the highest weight (18%) as India's busiest route."),
            ("Weight Storage",
             "Stored in route_basket table with fields: weight, weight_source, weight_methodology, "
             "effective_from, active."),
            ("Normalisation",
             "Weights are normalised to sum to 1.0 across all active routes."),
        ],
    },
    {
        "id": 7,
        "title": "Index Calculation",
        "items": [
            ("Method: Laspeyres Price Index",
             "Index = Σ (current_route_avg / base_route_avg × 100) × route_weight / Σ route_weight"),
            ("Advance Purchase Window",
             "Only fares for travel T+7 to T+30 days ahead are included in index calculation, "
             "standardising for advance-purchase effects."),
            ("Economy Direct/1-stop Only",
             "Only economy class, maximum 1-stop fares are included to ensure comparability."),
        ],
    },
    {
        "id": 8,
        "title": "Base Period",
        "items": [
            ("Default Base Period",
             "January 2025 = 100. This can be reconfigured in the system."),
            ("Base Fare",
             "The average fare for each route during the base period is stored and used as the denominator "
             "in the Laspeyres formula."),
        ],
    },
    {
        "id": 9,
        "title": "Inflation Calculation",
        "items": [
            ("Year-on-Year (YoY)",
             "YoY Inflation = ((Current Period Index − Same Month Prior Year Index) / "
             "Same Month Prior Year Index) × 100%"),
            ("Month-on-Month (MoM)",
             "MoM Inflation = ((Current Month Index − Previous Month Index) / Previous Month Index) × 100%"),
            ("Minimum Data Requirement",
             "YoY requires 13+ months of index data. MoM requires 2+ consecutive months. Values are not "
             "displayed until sufficient data exists."),
        ],
    },
    {
        "id": 10,
        "title": "CPI Comparison",
        "items": [
            ("Official CPI Source",
             "Official CPI data from MoSPI/NSO (Ministry of Statistics & Programme Implementation, "
             "Government of India). Combined CPI, Rural+Urban, Base 2012=100."),
            ("Clear Labelling",
             "The Computed Airfare Price Index and Official Government CPI are always displayed as separate "
             "series. They are never merged or presented as the same metric."),
            ("Inflation Gap",
             "Gap = Airfare YoY% − Official CPI YoY%. A positive gap means airfares are inflating faster "
             "than general prices."),
        ],
    },
    {
        "id": 11,
        "title": "Contribution Methodology",
        "items": [
            ("Mode A — Official Weight Available",
             "Estimated Contribution = Airfare Inflation (YoY%) × Official CPI Transport Weight (8.59%). "
             "Result expressed in percentage points (pp)."),
            ("Mode B — No Official Weight",
             "If no appropriate official weight is available, the system shows: 'Calculation unavailable "
             "— required official data/weight not available.' No contribution figure is fabricated."),
            ("Disclaimer",
             "The estimated contribution is an analytical estimate based on the documented methodology. "
             "It is NOT an official Government of India CPI contribution figure. The NSO CPI basket does "
             "not publish a separate national weight for domestic air transport specifically."),
        ],
    },
    {
        "id": 12,
        "title": "Limitations",
        "items": [
            ("OTA Website Structure Changes",
             "OTA websites frequently update their HTML structure. If scraping fails, the system falls back "
             "to DemoCollector and logs the failure — it does not crash."),
            ("scrape.do Rate Limits",
             "The scrape.do API has rate limits. High-frequency collection across all sources may result "
             "in some requests being rate-limited."),
            ("CPI Weight Granularity",
             "The NSO CPI basket does not provide a separate national weight for domestic air transport. "
             "The Transport & Communication weight (8.59%) is the most applicable official category available."),
            ("Base Period Sensitivity",
             "The index value is sensitive to the choice of base period. A high-fare base period will "
             "produce a lower index for the same current fares."),
            ("Advance Purchase Standardisation",
             "The T+7–T+30 window standardises for advance purchase but excludes last-minute and "
             "long-advance fares from the index."),
        ],
    },
]

# ── Build story ───────────────────────────────────────────────────────────────
story = []

# Cover header
story.append(Paragraph("TECHNICAL DOCUMENTATION", label_style))
story.append(Spacer(1, 4))
story.append(Paragraph("FLARE Airfare Price Index", title_style))
story.append(Paragraph("Methodology &amp; Technical Reference", subtitle_style))
story.append(Paragraph(
    "Complete explanation of how the FLARE Airfare Price Index is computed — "
    "from data collection through economic analysis. Every number displayed in "
    "the system is traceable to this methodology.",
    body_style
))
story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=8))

# Table of contents
toc_data = [["#", "Section"]]
for s in sections:
    toc_data.append([str(s["id"]), s["title"]])

toc = Table(
    toc_data,
    colWidths=[12*mm, 140*mm],
    style=TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  9),
        ("TOPPADDING",  (0, 0), (-1, 0),  5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 1), (0, -1),  PRIMARY),
        ("TEXTCOLOR",   (1, 1), (1, -1),  TEXT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING",  (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ])
)
story.append(toc)
story.append(Spacer(1, 10))

# Sections
for section in sections:
    block = []
    block.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceAfter=4))
    block.append(Paragraph(
        f'<font color="#7c3aed"><b>{section["id"]}.</b></font>  {section["title"]}',
        section_title_style
    ))
    for heading, body in section["items"]:
        block.append(Paragraph(heading, subsection_style))
        block.append(Paragraph(body, body_style))
    story.append(KeepTogether(block))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceAfter=8))

# Disclaimer box
disclaimer_text = (
    "<b>Important Disclaimer:</b> The FLARE system's Computed Airfare Price Index is an experimental, "
    "analytical tool produced from collected fare data. It is NOT an official Government of India statistic. "
    "Official CPI data is sourced from MoSPI/NSO and is always clearly labelled as such. The system maintains "
    "strict separation between live data, historical data, official government data, and synthetic demo data."
)
story.append(Paragraph(disclaimer_text, disclaimer_style))

# Footer info
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Generated by FLARE Platform  ·  SIH Presentation  ·  India Airfare Price Index",
    ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=MUTED,
                   alignment=TA_CENTER, fontName="Helvetica")
))

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc.build(story)
print(f"PDF generated: {os.path.abspath(OUTPUT)}")
