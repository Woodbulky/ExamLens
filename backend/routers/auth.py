"""
Auth Router — Authentication verification and user profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    """
    Verify JWT token and return user profile information.
    Called by the frontend on app load to check if session is valid.
    """
    try:
        supabase = get_supabase()

        # Fetch profile from profiles table
        result = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user["id"])
            .execute()
        )

        profile = result.data[0] if result.data else None

        if profile:
            return {
                "user_id": user["id"],
                "email": user["email"],
                "display_name": profile.get("display_name", ""),
                "role": profile.get("role", "student"),
                "created_at": profile.get("created_at", ""),
            }
        else:
            # Profile might not exist yet if trigger didn't fire —
            # create it now as a fallback
            email = user["email"] or ""
            display_name = email.split("@")[0] if email else "User"

            supabase.table("profiles").insert({
                "id": user["id"],
                "display_name": display_name,
                "role": "student",
            }).execute()

            return {
                "user_id": user["id"],
                "email": user["email"],
                "display_name": display_name,
                "role": "student",
                "created_at": None,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user profile: {str(e)}",
        )
