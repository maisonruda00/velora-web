import os
import json
from datetime import datetime

# Check for Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class DBClient:
    def __init__(self):
        self.use_supabase = bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_AVAILABLE)
        
        if self.use_supabase:
            try:
                print("🔌 Connecting to Supabase...")
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.mode = "supabase"
            except Exception as e:
                print(f"⚠️ Supabase failed: {e}. Falling back to JSON.")
                self.use_supabase = False
                self.mode = "json"
        else:
            print("📝 Using local JSON database mode")
            self.mode = "json"

    def get_user_by_code(self, code):
        if self.use_supabase:
            try:
                res = self.supabase.table("users").select("*").eq("access_code", code.upper()).execute()
                return res.data[0] if res.data else None
            except:
                return None
        else:
            users = self._load_json()
            for uid, data in users.items():
                if data.get("code") == code.upper():
                    return {"id": uid, **data}
            return None

    def create_user(self, access_code, invites_remaining=5, role="member", invited_by=None):
        if self.use_supabase:
            data = {"access_code": access_code, "invites_remaining": invites_remaining, "role": role}
            self.supabase.table("users").insert(data).execute()
        else:
            users = self._load_json()
            uid = f"user_{len(users)+1}"
            users[uid] = {
                "code": access_code,
                "invites_remaining": invites_remaining,
                "role": role,
                "invited_by": invited_by,
                "created_at": str(datetime.now())
            }
            self._save_json(users)

    def _load_json(self):
        try:
            with open("users.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_json(self, data):
        with open("users.json", "w") as f:
            json.dump(data, f)

db = DBClient()
