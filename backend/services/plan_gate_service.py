from fastapi import HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from supabase_client import supabase

FREE_LIMITS = {
    "uploads_per_hour": 1,
    "mcq_per_day": 1,
    "essay_questions": False
}

PAID_LIMITS = {
    "uploads_per_hour": float('inf'),
    "mcq_per_day": float('inf'),
    "essay_questions": True
}

def get_plan_limits(user: Optional[Dict[str, Any]]) -> dict:
    if user and user.get("plan") == "paid":
        return PAID_LIMITS
    return FREE_LIMITS

def assert_feature_access(user: Optional[Dict[str, Any]], feature: str) -> bool:
    """
    Asserts whether a user has access to a specific feature based on their tier.
    Queries the database to verify upload counts securely.
    Raises HTTPException 403 if limit is exceeded.
    """
    limits = get_plan_limits(user)
    
    if feature not in limits:
        raise HTTPException(status_code=400, detail=f"Unknown feature: {feature}")

    limit_val = limits[feature]
    
    # Check boolean access
    if type(limit_val) is bool:
        if not limit_val:
             raise HTTPException(
                status_code=403, 
                detail=f"Access denied for feature: {feature}. Please upgrade your plan."
            )
        return True

    # Check database counts for PDF uploads using a rolling 1-hour window
    if feature == "uploads_per_hour" and user and limit_val != float('inf'):
        try:
            now = datetime.now(timezone.utc)
            one_hour_ago = (now - timedelta(hours=1)).isoformat()
            
            # Synchronous supabase-py execute looking strictly at the rolling window
            res = supabase.table("pdf_documents").select("created_at").eq("user_id", user["id"]).gte("created_at", one_hour_ago).order("created_at", desc=False).execute()
            
            current_count = len(res.data) if res.data else 0
            
            if current_count >= limit_val:
                # Calculate the precise unlocking time based on the oldest document occupying the rolling window
                oldest_in_window = res.data[0]["created_at"]
                
                # Trim unpredictable Postgres fractional seconds entirely avoiding '< Python 3.11' parser tracebacks
                if "." in oldest_in_window:
                    clean_iso = oldest_in_window.split(".")[0] + "+00:00"
                elif "Z" in oldest_in_window:
                    clean_iso = oldest_in_window.replace("Z", "+00:00")
                else:
                    clean_iso = oldest_in_window
                    
                oldest_dt = datetime.fromisoformat(clean_iso)
                retry_dt = oldest_dt + timedelta(hours=1)
                
                # Enforce absolute ISO mapping for the front-end to safely convert against Timezones natively
                retry_time_str = retry_dt.isoformat()
                if retry_time_str.endswith("+00:00"):
                    retry_time_str = retry_time_str.replace("+00:00", "Z")
                
                # Throw specialized structured detail allowing JSONResponses upstream
                raise HTTPException(
                    status_code=429, 
                    detail={
                        "error": "limit_reached", 
                        "message": "You have reached your free upload limit.",
                        "retry_time": retry_time_str
                    }
                )
        except HTTPException:
            raise
        except Exception as e:
            # If DB fails, fail securely or log. Let's pass it as a 500
            raise HTTPException(status_code=500, detail=f"Could not verify plan limits: {str(e)}")

    return True
