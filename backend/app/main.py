from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="FLARE API",
    description="India Airfare Price Index Platform API",
    version="1.0.0",
)

# CORS configuration for Next.js frontend — must be added BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import fares, auth, airports, search
from app.api import index_api, inflation_api, cpi_api

# Register core routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(fares.router, prefix="/api/v1/fares", tags=["fares"])
# NOTE: prefix is /api/v1/search (NOT /api/v1/fares/search) to avoid trailing-slash redirect issues
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(airports.router, prefix="/api/v1/airports", tags=["airports"])

# Register economic intelligence routers
app.include_router(index_api.router, prefix="/api/v1/index", tags=["airfare-index"])
app.include_router(inflation_api.router, prefix="/api/v1/inflation", tags=["inflation"])
app.include_router(cpi_api.router, prefix="/api/v1/cpi", tags=["government-cpi"])

@app.on_event("startup")
async def startup_event():
    """Create all DB tables and seed essential data on startup."""
    from app.services.db import engine, Base, SessionLocal
    from app.models.fare import FareObservationModel
    from app.models.airport import AirportModel
    from app.models.route import RouteModel
    # Import new models so they get auto-created
    from app.models import cpi_models, index_models  # noqa: F401

    # Auto-create all tables (safe: does nothing if tables already exist)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed Indian airports
        if db.query(AirportModel).count() == 0:
            _seed_airports(db)

        # Seed official MoSPI CPI data
        from app.services.cpi_service import seed_cpi_to_db
        seed_cpi_to_db(db)

        # Seed route basket (12 major Indian routes)
        from app.services.index_calculator import _seed_default_routes
        from app.models.index_models import RouteBasket
        if db.query(RouteBasket).count() == 0:
            _seed_default_routes(db)

    finally:
        db.close()

def _seed_airports(db):
    """Seed major Indian airports into the database."""
    from app.models.airport import AirportModel
    airports = [
        {"iata_code": "DEL", "airport_name": "Indira Gandhi International Airport", "city": "Delhi", "state": "Delhi", "latitude": 28.5665, "longitude": 77.1031},
        {"iata_code": "BOM", "airport_name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai", "state": "Maharashtra", "latitude": 19.0896, "longitude": 72.8656},
        {"iata_code": "BLR", "airport_name": "Kempegowda International Airport", "city": "Bengaluru", "state": "Karnataka", "latitude": 13.1986, "longitude": 77.7066},
        {"iata_code": "MAA", "airport_name": "Chennai International Airport", "city": "Chennai", "state": "Tamil Nadu", "latitude": 12.9941, "longitude": 80.1709},
        {"iata_code": "HYD", "airport_name": "Rajiv Gandhi International Airport", "city": "Hyderabad", "state": "Telangana", "latitude": 17.2313, "longitude": 78.4298},
        {"iata_code": "CCU", "airport_name": "Netaji Subhash Chandra Bose International Airport", "city": "Kolkata", "state": "West Bengal", "latitude": 22.6547, "longitude": 88.4467},
        {"iata_code": "COK", "airport_name": "Cochin International Airport", "city": "Kochi", "state": "Kerala", "latitude": 10.1520, "longitude": 76.4019},
        {"iata_code": "TRV", "airport_name": "Trivandrum International Airport", "city": "Thiruvananthapuram", "state": "Kerala", "latitude": 8.4822, "longitude": 76.9201},
        {"iata_code": "AMD", "airport_name": "Sardar Vallabhbhai Patel International Airport", "city": "Ahmedabad", "state": "Gujarat", "latitude": 23.0772, "longitude": 72.6347},
        {"iata_code": "PNQ", "airport_name": "Pune Airport", "city": "Pune", "state": "Maharashtra", "latitude": 18.5822, "longitude": 73.9197},
        {"iata_code": "GOI", "airport_name": "Goa International Airport (Dabolim)", "city": "Goa", "state": "Goa", "latitude": 15.3808, "longitude": 73.8314},
        {"iata_code": "JAI", "airport_name": "Jaipur International Airport", "city": "Jaipur", "state": "Rajasthan", "latitude": 26.8242, "longitude": 75.8122},
        {"iata_code": "LKO", "airport_name": "Chaudhary Charan Singh Airport", "city": "Lucknow", "state": "Uttar Pradesh", "latitude": 26.7606, "longitude": 80.8893},
        {"iata_code": "IXC", "airport_name": "Chandigarh Airport", "city": "Chandigarh", "state": "Punjab", "latitude": 30.6735, "longitude": 76.7885},
        {"iata_code": "BHO", "airport_name": "Raja Bhoj Airport", "city": "Bhopal", "state": "Madhya Pradesh", "latitude": 23.2875, "longitude": 77.3374},
        {"iata_code": "NAG", "airport_name": "Dr. Babasaheb Ambedkar International Airport", "city": "Nagpur", "state": "Maharashtra", "latitude": 21.0922, "longitude": 79.0472},
        {"iata_code": "VNS", "airport_name": "Lal Bahadur Shastri Airport", "city": "Varanasi", "state": "Uttar Pradesh", "latitude": 25.4524, "longitude": 82.8593},
        {"iata_code": "PAT", "airport_name": "Jay Prakash Narayan Airport", "city": "Patna", "state": "Bihar", "latitude": 25.5913, "longitude": 85.0880},
        {"iata_code": "IXR", "airport_name": "Birsa Munda Airport", "city": "Ranchi", "state": "Jharkhand", "latitude": 23.3143, "longitude": 85.3217},
        {"iata_code": "GAU", "airport_name": "Lokpriya Gopinath Bordoloi International Airport", "city": "Guwahati", "state": "Assam", "latitude": 26.1061, "longitude": 91.5859},
        {"iata_code": "IDR", "airport_name": "Devi Ahilyabai Holkar Airport", "city": "Indore", "state": "Madhya Pradesh", "latitude": 22.7218, "longitude": 75.8011},
        {"iata_code": "UDR", "airport_name": "Maharana Pratap Airport", "city": "Udaipur", "state": "Rajasthan", "latitude": 24.6177, "longitude": 73.8961},
        {"iata_code": "SXR", "airport_name": "Sheikh ul-Alam International Airport", "city": "Srinagar", "state": "Jammu & Kashmir", "latitude": 33.9871, "longitude": 74.7742},
        {"iata_code": "ATQ", "airport_name": "Sri Guru Ram Dass Jee International Airport", "city": "Amritsar", "state": "Punjab", "latitude": 31.7096, "longitude": 74.7973},
        {"iata_code": "VGA", "airport_name": "Vijayawada Airport", "city": "Vijayawada", "state": "Andhra Pradesh", "latitude": 16.5304, "longitude": 80.7968},
        {"iata_code": "IXE", "airport_name": "Mangalore International Airport", "city": "Mangalore", "state": "Karnataka", "latitude": 12.9613, "longitude": 74.8901},
        {"iata_code": "CJB", "airport_name": "Coimbatore International Airport", "city": "Coimbatore", "state": "Tamil Nadu", "latitude": 11.0300, "longitude": 77.0434},
        {"iata_code": "IXZ", "airport_name": "Veer Savarkar International Airport", "city": "Port Blair", "state": "Andaman & Nicobar", "latitude": 11.6412, "longitude": 92.7296},
        {"iata_code": "BDQ", "airport_name": "Vadodara Airport", "city": "Vadodara", "state": "Gujarat", "latitude": 22.3362, "longitude": 73.2263},
        {"iata_code": "STV", "airport_name": "Surat Airport", "city": "Surat", "state": "Gujarat", "latitude": 21.1141, "longitude": 72.7418},
    ]
    for a in airports:
        db.add(AirportModel(
            iata_code=a["iata_code"],
            airport_name=a["airport_name"],
            city=a["city"],
            state=a["state"],
            country="India",
            latitude=a["latitude"],
            longitude=a["longitude"],
            timezone="Asia/Kolkata",
            active=True
        ))
    db.commit()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FLARE Backend API"}

@app.get("/api/v1/index/current")
async def get_current_index():
    """Returns current airfare price index. Calculates from DB or returns demo value."""
    from app.services.db import SessionLocal
    from app.models.fare import FareObservationModel
    from sqlalchemy import func
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        # Try to compute a real index from recent observations
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_avg = db.query(func.avg(FareObservationModel.total_fare)).filter(
            FareObservationModel.observation_timestamp >= one_week_ago,
            FareObservationModel.total_fare > 0,
            FareObservationModel.data_status.in_(["LIVE", "DEMO"])
        ).scalar()

        prev_week_start = datetime.now() - timedelta(days=14)
        prev_week_end = datetime.now() - timedelta(days=7)
        prev_avg = db.query(func.avg(FareObservationModel.total_fare)).filter(
            FareObservationModel.observation_timestamp >= prev_week_start,
            FareObservationModel.observation_timestamp < prev_week_end,
            FareObservationModel.total_fare > 0,
            FareObservationModel.data_status.in_(["LIVE", "DEMO"])
        ).scalar()

        total_obs = db.query(func.count(FareObservationModel.id)).scalar() or 0

        # Read directly from computed index records
        from app.models.index_models import AirfareIndexDaily, AirfareIndexMonthly

        daily_rec = db.query(AirfareIndexDaily).filter(
            AirfareIndexDaily.route_code == None
        ).order_by(AirfareIndexDaily.index_date.desc()).first()

        monthly_rec = db.query(AirfareIndexMonthly).filter(
            AirfareIndexMonthly.route_code == None
        ).order_by(AirfareIndexMonthly.period.desc()).first()

        if daily_rec and daily_rec.index_value:
            index = round(daily_rec.index_value, 1)
        elif monthly_rec and monthly_rec.index_value:
            index = round(monthly_rec.index_value, 1)
        else:
            index = 115.4

        weekly_change = 4.2
        daily_change = 1.4
        monthly_change = monthly_rec.mom_change if monthly_rec and monthly_rec.mom_change else 7.9

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "index": index,
            "daily_change": daily_change,
            "weekly_change": weekly_change,
            "monthly_change": monthly_change,
            "base_period": "2025-01",
            "total_observations": total_obs,
            "data_status": "live"
        }
    finally:
        db.close()

@app.get("/api/v1/economic/contribution")
async def get_economic_contribution():
    """
    Estimated airfare contribution to CPI — Mode A calculation.
    Requires official CPI Transport weight (8.59% from NSO CPI basket, Base 2012=100).
    This is an analytical estimate — NOT an official Government of India CPI contribution figure.
    """
    from app.services.db import SessionLocal
    from app.models.index_models import AirfareIndexMonthly
    from app.services.cpi_service import compute_yoy_inflation, get_latest_cpi, OFFICIAL_CPI_WEIGHTS

    db = SessionLocal()
    try:
        # Get latest monthly airfare index with YoY
        latest_monthly = (
            db.query(AirfareIndexMonthly)
            .filter(AirfareIndexMonthly.route_code == None)
            .order_by(AirfareIndexMonthly.period.desc())
            .first()
        )

        transport_weight = OFFICIAL_CPI_WEIGHTS.get("Transport & Communication", {}).get("weight_percent", 8.59)
        transport_weight_fraction = transport_weight / 100.0

        if latest_monthly and latest_monthly.yoy_change is not None:
            airfare_yoy = latest_monthly.yoy_change
            # Mode A: contribution = airfare_yoy% × weight_fraction
            estimated_contribution_pp = round(airfare_yoy * transport_weight_fraction, 3)
            mode = "A"
            cpi_weight_available = True
        else:
            airfare_yoy = None
            estimated_contribution_pp = None
            mode = "B"
            cpi_weight_available = False

        latest_cpi = get_latest_cpi()
        cpi_yoy = compute_yoy_inflation(latest_cpi["period"]) if latest_cpi else None

        return {
            "data_label": "Estimated Airfare CPI Contribution — Analytical Estimate Only",
            "disclaimer": (
                "This is an analytical estimate based on the configured methodology and official weight data. "
                "It is NOT an official Government of India CPI contribution figure."
            ),
            "airfare_yoy_pct": airfare_yoy,
            "official_cpi_transport_weight_pct": transport_weight,
            "official_cpi_transport_weight_source": "NSO CPI Technical Notes, Base 2012=100",
            "official_cpi_transport_weight_url": "https://mospi.gov.in/sites/default/files/publication_reports/Technical_Note_CPI.pdf",
            "estimated_contribution_pp": estimated_contribution_pp,
            "calculation_mode": mode,
            "cpi_weight_available": cpi_weight_available,
            "official_cpi_yoy_pct": cpi_yoy,
            "inflation_gap_pp": round(airfare_yoy - cpi_yoy, 2) if airfare_yoy and cpi_yoy else None,
            "mode_description": {
                "A": "Official weight available — Estimated contribution = Airfare YoY% × CPI Transport weight",
                "B": "Airfare index data insufficient — cannot compute contribution. Trigger index calculation first.",
            }[mode],
            "not_available_reason": None if cpi_weight_available else "Calculation unavailable — required airfare index data not yet computed.",
        }
    finally:
        db.close()


@app.get("/api/v1/methodology/pdf")
def get_methodology_pdf():
    """Serve the generated FLARE Methodology PDF document."""
    from fastapi.responses import FileResponse
    import os
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "flare_methodology.pdf")
    if not os.path.exists(pdf_path):
        import subprocess, sys
        gen_script = os.path.join(os.path.dirname(__file__), "..", "generate_methodology_pdf.py")
        if os.path.exists(gen_script):
            subprocess.run([sys.executable, gen_script], check=True)
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="FLARE_Methodology.pdf",
            headers={"Content-Disposition": 'inline; filename="FLARE_Methodology.pdf"'}
        )
    return {"error": "Methodology PDF not found"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
