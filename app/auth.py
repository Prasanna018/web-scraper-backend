from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])

class GoogleToken(BaseModel):
    id_token: str


# post route for authentication
@router.post("/google")
def verify_google_token(payload: GoogleToken):
    """
    Verify Google ID token from frontend and return basic profile info.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="server missing GOOGLE_CLIENT_ID")

    try:
        idinfo = id_token.verify_oauth2_token(payload.id_token, g_requests.Request(), client_id)
        # Basic fields
        sub = idinfo.get("sub")
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        if not sub:
            raise ValueError("Invalid token: missing sub")

        return {"ok": True, "user": {"id": sub, "email": email, "name": name, "picture": picture}}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {e}")
