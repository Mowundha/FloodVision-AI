# backend/routers/reports.py
#
# WHAT THIS FILE DOES:
#   Community flood reporting system.
#   Users can:
#     1. Submit a flood report from their location
#     2. View reports near their location
#     3. View all recent reports for Tamil Nadu
#
# ALL REPORTS ARE SAVED IN FIRESTORE (permanent database)
# SUBMITTING A REPORT REQUIRES LOGIN (Firebase token)
# READING REPORTS IS PUBLIC (no login needed)

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import math

from backend.config import db
from backend.utils.firebase_auth import verify_token, verify_token_optional

# ── Import security settings and rate limiting controls ───────
from backend.utils.security import limiter, sanitize_text, sanitize_street_name, RATE_REPORT

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# DATA MODELS
# These define the shape of JSON Flutter sends and receives
# ─────────────────────────────────────────────────────────────

class ReportInput(BaseModel):
    """
    What Flutter sends when a user submits a flood report.
    All fields your friend needs to collect in the app.
    """
    latitude:      float = Field(..., ge=7.5,  le=14.0, description="User's latitude")
    longitude:     float = Field(..., ge=76.0, le=81.0, description="User's longitude")
    street:        str   = Field(..., min_length=2, description="Street name where flood is seen")
    city:          str   = Field(..., min_length=2, description="City name")
    water_depth_cm: float = Field(..., ge=0, le=500, description="Estimated water depth in cm")
    severity:      str   = Field(..., description="LOW, MEDIUM, or HIGH")
    description:   str   = Field("", max_length=500, description="Optional text description")
    image_url:     Optional[str] = Field(None, description="Optional photo URL")


class UpvoteInput(BaseModel):
    """What Flutter sends when a user confirms someone else's report."""
    report_id: str = Field(..., description="The Firestore document ID")


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def calculate_distance_km(lat1, lon1, lat2, lon2) -> float:
    """Calculates straight-line distance between two coordinates."""
    R = 6371  # Earth radius in km
    phi1  = math.radians(lat1)
    phi2  = math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)

    a = (math.sin(dphi/2)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def validate_severity(severity: str) -> str:
    """Makes sure severity is one of the three valid values."""
    valid = ["LOW", "MEDIUM", "HIGH"]
    upper = severity.upper()
    if upper not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"severity must be one of: {valid}. Got: '{severity}'"
        )
    return upper


# ─────────────────────────────────────────────────────────────
# ENDPOINT 1: Submit a flood report
# Requires login and rate limiting
# ─────────────────────────────────────────────────────────────

@router.post("/reports/submit")
@limiter.limit(RATE_REPORT)
def submit_report(
    request: Request,              # ← required for rate limiting
    report:  ReportInput,
    user:    dict = Depends(verify_token)   # ← verifies Firebase token
):
    """
    USER SUBMITS A FLOOD REPORT FROM THEIR LOCATION WITH SECURITY HARDENING.
    """
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not connected. Check Firebase config."
        )

    # Validate severity value
    severity = validate_severity(report.severity)

    # ── Input Sanitization (Cleans strings from script injection attacks) ──
    clean_street      = sanitize_street_name(report.street)
    clean_city        = sanitize_street_name(report.city)
    clean_description = sanitize_text(report.description)

    # Build the safe document to save in Firestore
    report_doc = {
        "user_uid":   user["uid"],
        "user_name":  user["name"],
        "user_email": user["email"],

        # Secure sanitized location strings
        "lat":    report.latitude,
        "lon":    report.longitude,
        "street": clean_street,
        "city":   clean_city,

        # Flood details
        "water_depth_cm": report.water_depth_cm,
        "severity":       severity,
        "description":    clean_description,
        "image_url":      report.image_url,

        # Metadata
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "verified":   False,   
        "upvotes":    0,       
        "upvoted_by": [],      

        "color": {
            "LOW":    "#1D9E75",
            "MEDIUM": "#EF9F27",
            "HIGH":   "#E24B4A"
        }.get(severity, "#EF9F27")
    }

    # Save to Firestore
    doc_ref = db.collection("flood_reports").add(report_doc)
    doc_id = doc_ref[1].id

    print(f"Report saved securely: {doc_id} by {user['name']} at {clean_street}")

    return {
        "success":    True,
        "report_id":  doc_id,
        "message":    "Flood report submitted successfully",
        "saved_data": {
            "street":        report_doc["street"],
            "city":          report_doc["city"],
            "severity":      severity,
            "depth_cm":      report.water_depth_cm,
            "submitted_by":  user["name"],
            "at":            report_doc["timestamp"]
        }
    }


# ─────────────────────────────────────────────────────────────
# ENDPOINT 2: Get reports near a location
# ─────────────────────────────────────────────────────────────

@router.get("/reports/nearby")
def get_nearby_reports(
    lat:           float,
    lon:           float,
    radius_km:     float = 10.0,   
    max_results:   int   = 20
):
    """RETURNS FLOOD REPORTS NEAR THE USER'S LOCATION."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        docs = (
            db.collection("flood_reports")
            .order_by("timestamp", direction="DESCENDING")
            .limit(200)   
            .stream()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )

    nearby = []
    for doc in docs:
        data    = doc.to_dict()
        rep_lat = data.get("lat", 0)
        rep_lon = data.get("lon", 0)

        dist_km = calculate_distance_km(lat, lon, rep_lat, rep_lon)

        if dist_km <= radius_km:
            nearby.append({
                "report_id":     doc.id,
                "street":        data.get("street", ""),
                "city":          data.get("city", ""),
                "lat":           rep_lat,
                "lon":           rep_lon,
                "severity":      data.get("severity", "MEDIUM"),
                "color":         data.get("color", "#EF9F27"),
                "water_depth_cm":data.get("water_depth_cm", 0),
                "description":   data.get("description", ""),
                "image_url":     data.get("image_url"),
                "user_name":     data.get("user_name", "Anonymous"),
                "verified":      data.get("verified", False),
                "upvotes":       data.get("upvotes", 0),
                "timestamp":     data.get("timestamp", ""),
                "distance_km":   round(dist_km, 2)
            })

        if len(nearby) >= max_results:
            break

    nearby.sort(key=lambda x: x["distance_km"])

    return {
        "reports":     nearby,
        "count":       len(nearby),
        "radius_km":   radius_km,
        "centre":      {"lat": lat, "lon": lon}
    }


# ─────────────────────────────────────────────────────────────
# ENDPOINT 3: Get all recent reports for Tamil Nadu
# ─────────────────────────────────────────────────────────────

@router.get("/reports/recent")
def get_recent_reports(limit: int = 50):
    """RETURNS THE MOST RECENT FLOOD REPORTS ACROSS ALL TAMIL NADU."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        docs = (
            db.collection("flood_reports")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )

    reports = []
    for doc in docs:
        data = doc.to_dict()
        reports.append({
            "report_id":      doc.id,
            "street":         data.get("street", ""),
            "city":           data.get("city", ""),
            "lat":            data.get("lat", 0),
            "lon":            data.get("lon", 0),
            "severity":       data.get("severity", "MEDIUM"),
            "color":          data.get("color", "#EF9F27"),
            "water_depth_cm": data.get("water_depth_cm", 0),
            "description":    data.get("description", ""),
            "image_url":      data.get("image_url"),
            "user_name":      data.get("user_name", "Anonymous"),
            "verified":       data.get("verified", False),
            "upvotes":        data.get("upvotes", 0),
            "timestamp":      data.get("timestamp", "")
        })

    return {
        "reports": reports,
        "count":   len(reports)
    }


# ─────────────────────────────────────────────────────────────
# ENDPOINT 4: Upvote a report
# ─────────────────────────────────────────────────────────────

@router.post("/reports/upvote")
def upvote_report(
    data:    UpvoteInput,
    user:    dict = Depends(verify_token)
):
    """USER CONFIRMS SOMEONE ELSE'S FLOOD REPORT IS ACCURATE."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    doc_ref = db.collection("flood_reports").document(data.report_id)
    doc     = doc_ref.get()

    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{data.report_id}' not found"
        )

    doc_data    = doc.to_dict()
    upvoted_by  = doc_data.get("upvoted_by", [])

    if user["uid"] in upvoted_by:
        return {
            "success": False,
            "message": "You have already confirmed this report",
            "upvotes": doc_data.get("upvotes", 0)
        }

    if doc_data.get("user_uid") == user["uid"]:
        return {
            "success": False,
            "message": "You cannot upvote your own report"
        }

    new_upvotes = doc_data.get("upvotes", 0) + 1
    doc_ref.update({
        "upvotes":    new_upvotes,
        "upvoted_by": upvoted_by + [user["uid"]]
    })

    return {
        "success": True,
        "message": "Thank you for confirming this flood report",
        "upvotes": new_upvotes
    }


# ─────────────────────────────────────────────────────────────
# ENDPOINT 5: Get a single report by ID
# ─────────────────────────────────────────────────────────────

@router.get("/reports/{report_id}")
def get_report(report_id: str):
    """RETURNS ONE SPECIFIC REPORT BY ITS ID."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    doc = db.collection("flood_reports").document(report_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail=f"Report '{report_id}' not found"
        )

    data = doc.to_dict()
    return {
        "report_id":      doc.id,
        "street":         data.get("street", ""),
        "city":           data.get("city", ""),
        "lat":            data.get("lat", 0),
        "lon":            data.get("lon", 0),
        "severity":       data.get("severity", ""),
        "color":          data.get("color", ""),
        "water_depth_cm": data.get("water_depth_cm", 0),
        "description":    data.get("description", ""),
        "image_url":      data.get("image_url"),
        "user_name":      data.get("user_name", "Anonymous"),
        "verified":       data.get("verified", False),
        "upvotes":        data.get("upvotes", 0),
        "timestamp":      data.get("timestamp", "")
    }