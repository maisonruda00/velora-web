from db_client import db

def verify_access_code(code: str):
    user = db.get_user_by_code(code)
    
    if user:
        print(f"✅ User authenticated: {user.get('code')}")
        return {
            "status": "success",
            "user_id": user.get("id", "unknown"),
            "role": user.get("role", "member"),
            "invites_remaining": user.get("invites_remaining", 0)
        }
    
    return {
        "status": "fail",
        "message": "Invalid Access Code."
    }
