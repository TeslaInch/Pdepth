from fastapi import HTTPException
from typing import Dict, Any, Optional

FREE_LIMITS = {
    "max_pdfs": 1,
    "mcq_per_day": 1,
    "essay_questions": False,
    "multi_pdf_chat": False
}

PAID_LIMITS = {
    "max_pdfs": float('inf'),
    "mcq_per_day": float('inf'),
    "essay_questions": True,
    "multi_pdf_chat": True
}

def get_plan_limits(user: Optional[Dict[str, Any]]) -> dict:
    if user and user.get("plan") == "paid":
        return PAID_LIMITS
    return FREE_LIMITS

def assert_feature_access(user: Optional[Dict[str, Any]], feature: str) -> bool:
    """
    Asserts whether a user has boolean access to a specific feature.
    Raises HTTPException 403 if they do not.
    """
    limits = get_plan_limits(user)
    
    if feature not in limits:
        raise HTTPException(status_code=400, detail=f"Unknown feature: {feature}")

    access = limits[feature]
    
    # Check boolean access
    if not access or access == 0:
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied for feature: {feature}. Please upgrade your plan."
        )
    return True
