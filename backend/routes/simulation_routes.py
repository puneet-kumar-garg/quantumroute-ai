from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from services.auth_service import get_current_user, require_admin
from models.models import User
from database.db import get_db
from sqlalchemy.orm import Session
from models.schemas import UserOut
from typing import List

router = APIRouter(prefix="/simulation", tags=["simulation"])

@router.get("/data")
def get_simulation_data(current_user: User = Depends(get_current_user)):
    return {
        "scenario_id": "chandigarh-monsoon-peak-v1",
        "scenario_label": "Synthetic Chandigarh monsoon peak-hour scenario",
        "provenance": "deterministic_synthetic_scenario",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active_vehicles": 420,
        "accidents": [
            {"id": "acc-rock-garden", "lat": 30.7526, "lng": 76.8089,
             "type": "accident", "severity": "high",
             "description": "Scenario collision near Rock Garden access road"},
        ],
        "road_closures": [
            {"id": "closure-isbt43", "lat": 30.7076, "lng": 76.7916,
             "type": "road_closure", "severity": "medium",
             "description": "Scenario maintenance restriction near ISBT Sector 43"},
        ],
        "traffic_hotspots": [
            {"lat": 30.7414, "lng": 76.7842, "intensity": 0.88, "label": "Sector 17 Plaza"},
            {"lat": 30.7333, "lng": 76.7794, "intensity": 0.72, "label": "Sector 22 Market"},
            {"lat": 30.7196, "lng": 76.7839, "intensity": 0.81, "label": "Sector 35 Market"},
            {"lat": 30.7056, "lng": 76.8013, "intensity": 0.67, "label": "Elante Mall"},
        ],
        "weather_alerts": [
            {"type": "rain", "severity": "medium", "message": "Scenario rainfall reduces speeds in northern sectors"},
        ],
    }


admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(User).all()

@admin_router.patch("/users/{user_id}/toggle")
def toggle_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id and user.is_active:
        raise HTTPException(400, "You cannot deactivate your own active administrator account")
    if user.role == "admin" and user.is_active:
        active_admins = db.query(User).filter(User.role == "admin", User.is_active.is_(True)).count()
        if active_admins <= 1:
            raise HTTPException(400, "At least one active administrator is required")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}
