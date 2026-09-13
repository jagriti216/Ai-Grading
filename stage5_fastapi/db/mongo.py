"""
MongoDB Atlas connection and collections.
"""

import logging
import os
import json
import uuid
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Try loading from the root .env first
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(root_env)
else:
    # Fallback to stage1_extraction/.env
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "stage1_extraction", ".env"))
    # Generic load_dotenv searching current & parent directories
    load_dotenv()

# Support both MONGODB_URI and MONGO_URI
MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")

# Fail fast if connection string is missing
if not MONGODB_URI:
    raise RuntimeError(
        "Critical Configuration Error: MONGO_URI or MONGODB_URI environment variable is missing. "
        "Please configure it in your .env file or environment."
    )

_client = None
_use_local_fallback = None


class LocalJSONCollection:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.filepath = os.path.join("uploads", f"local_db_{collection_name}.json")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = []
        else:
            self.data = []

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def insert_one(self, document):
        self._load()
        doc = dict(document)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        self.data.append(doc)
        self._save()
        class InsertOneResult:
            inserted_id = doc["_id"]
        return InsertOneResult()

    def find_one(self, query):
        self._load()
        for doc in self.data:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, query):
        self._load()
        matched = []
        for doc in self.data:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                matched.append(dict(doc))
        return matched

    def update_one(self, query, update):
        self._load()
        set_dict = update.get("$set", {})
        updated = False
        for doc in self.data:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                for uk, uv in set_dict.items():
                    doc[uk] = uv
                updated = True
                break
        if updated:
            self._save()
        class UpdateResult:
            modified_count = 1 if updated else 0
        return UpdateResult()

    def delete_one(self, query):
        self._load()
        deleted = False
        for i, doc in enumerate(self.data):
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                self.data.pop(i)
                deleted = True
                break
        if deleted:
            self._save()
        class DeleteResult:
            deleted_count = 1 if deleted else 0
        return DeleteResult()

    def delete_many(self, query):
        self._load()
        initial_count = len(self.data)
        self.data = [doc for doc in self.data if not all(doc.get(k) == v for k, v in query.items())]
        num_deleted = initial_count - len(self.data)
        if num_deleted > 0:
            self._save()
        class DeleteResult:
            deleted_count = num_deleted
        return DeleteResult()



def get_masked_uri(uri: str) -> str:
    """Masks the password in the MongoDB URI for safe logging."""
    try:
        if "@" in uri:
            prefix, rest = uri.split("@", 1)
            if "://" in prefix:
                proto, credentials = prefix.split("://", 1)
                if ":" in credentials:
                    user, _ = credentials.split(":", 1)
                    return f"{proto}://{user}:*****@{rest}"
                return f"{proto}://{credentials}:*****@{rest}"
            return f"masked_uri@{rest}"
    except Exception:
        pass
    return "masked_mongodb_uri"


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, server_api=ServerApi("1"), serverSelectionTimeoutMS=3000)
    return _client


def get_db():
    return get_client()["grading_db"]


def use_local_fallback():
    global _use_local_fallback
    if _use_local_fallback is None:
        _use_local_fallback = not ping()
    return _use_local_fallback


# collections
def exams():
    if use_local_fallback():
        return LocalJSONCollection("exams")
    return get_db()["exams"]


def submissions():
    if use_local_fallback():
        return LocalJSONCollection("submissions")
    return get_db()["submissions"]


def results():
    if use_local_fallback():
        return LocalJSONCollection("results")
    return get_db()["results"]


def users():
    if use_local_fallback():
        return LocalJSONCollection("users")
    return get_db()["users"]


def subject_papers():
    if use_local_fallback():
        return LocalJSONCollection("subject_papers")
    return get_db()["subject_papers"]


def seed_admin_if_missing():
    """
    Creates the first admin account on startup if no admin exists yet.
    Without this, nobody could ever log in to create the first
    teacher/student account (admin is the only role that can create
    other accounts).
    """
    from stage5_api.auth import hash_password
    import uuid
    from datetime import datetime as _dt

    existing_admin = users().find_one({"role": "admin"})
    if existing_admin:
        return

    username = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "admin")
    password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "change_me_immediately")

    users().insert_one({
        "user_id": str(uuid.uuid4()),
        "username": username,
        "name": "Administrator",
        "role": "admin",
        "password_hash": hash_password(password),
        "must_change_password": True,
        "created_at": _dt.utcnow().isoformat(),
    })
    logger.info("Bootstrap admin account created: username='%s' — change the password immediately.", username)


def seed_demo_users_if_missing():
    """
    Optionally creates a demo teacher and demo student account on startup,
    so a deployed instance can be logged into without an admin having to
    manually create accounts first. Opt-in via SEED_DEMO_USERS=true — this
    should stay off for real deployments with real students, since the
    credentials are fixed/known and the accounts skip the forced
    password-change step.
    """
    if os.getenv("SEED_DEMO_USERS", "false").lower() not in ("1", "true", "yes"):
        return

    from stage5_api.auth import hash_password
    import uuid
    from datetime import datetime as _dt

    demo_accounts = [
        {
            "username": os.getenv("DEMO_TEACHER_USERNAME", "demo_teacher"),
            "password": os.getenv("DEMO_TEACHER_PASSWORD", "demo1234"),
            "name": "Demo Teacher",
            "role": "teacher",
            "roll_no": None,
            "class_name": None,
            "subject_codes": [],
        },
        {
            "username": os.getenv("DEMO_STUDENT_USERNAME", "demo_student"),
            "password": os.getenv("DEMO_STUDENT_PASSWORD", "demo1234"),
            "name": "Demo Student",
            "role": "student",
            "roll_no": os.getenv("DEMO_STUDENT_ROLL_NO", "DEMO001"),
            "class_name": "Demo Class",
            "subject_codes": None,
        },
    ]

    for account in demo_accounts:
        username = account["username"]
        if users().find_one({"username": username}):
            continue

        users().insert_one({
            "user_id": str(uuid.uuid4()),
            "username": username,
            "name": account["name"],
            "role": account["role"],
            "password_hash": hash_password(account["password"]),
            "must_change_password": False,
            "roll_no": account["roll_no"],
            "class_name": account["class_name"],
            "subject_codes": account["subject_codes"],
            "created_at": _dt.utcnow().isoformat(),
        })
        logger.info("Demo %s account seeded: username='%s'", account["role"], username)


def ping():
    global _use_local_fallback
    try:
        masked = get_masked_uri(MONGODB_URI)
        db_name = get_db().name
        logger.info("Connecting to MongoDB at: %s", masked)
        logger.info("Target Database: %s", db_name)
        get_client().admin.command("ping")
        logger.info("MongoDB Atlas connected successfully")
        _use_local_fallback = False
        return True
    except Exception as e:
        logger.warning("MongoDB connection failed: %s", e)
        logger.warning("Falling back to local JSON database.")
        _use_local_fallback = True
        return False


if __name__ == "__main__":
    ping()

