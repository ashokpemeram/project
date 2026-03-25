import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_BACKEND, MONGO_DB, MONGO_URI, STORE_PATH


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _default_store() -> dict[str, Any]:
    return {
        "users": [],
        "sessions": [],
        "patients": [],
        "attacks": [],
    }


class JsonStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self._ensure()

    def _ensure(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_locked(_default_store())

    def _read_locked(self) -> dict[str, Any]:
        if not self.path.exists():
            self._write_locked(_default_store())
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for key, value in _default_store().items():
            data.setdefault(key, value)
        return data

    def _write_locked(self, data: dict[str, Any]) -> None:
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        tmp_path.replace(self.path)

    def create_user(self, name: str, email: str, password_hash: str, role: str = "doctor") -> dict[str, Any]:
        with self.lock:
            data = self._read_locked()
            normalized_email = email.strip().lower()
            if any(user["email"].lower() == normalized_email for user in data["users"]):
                raise ValueError("Email already registered.")

            user = {
                "id": uuid.uuid4().hex,
                "name": name.strip(),
                "email": normalized_email,
                "password_hash": password_hash,
                "role": role,
                "created_at": _now_iso(),
            }
            data["users"].append(user)
            self._write_locked(data)
            return user

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.lock:
            data = self._read_locked()
            normalized_email = email.strip().lower()
            return next((user for user in data["users"] if user["email"] == normalized_email), None)

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self.lock:
            data = self._read_locked()
            return next((user for user in data["users"] if user["id"] == user_id), None)

    def create_session(self, user_id: str, token: str) -> dict[str, Any]:
        with self.lock:
            data = self._read_locked()
            session = {
                "token": token,
                "user_id": user_id,
                "created_at": _now_iso(),
            }
            data["sessions"].append(session)
            self._write_locked(data)
            return session

    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        with self.lock:
            data = self._read_locked()
            session = next((s for s in data["sessions"] if s["token"] == token), None)
            if not session:
                return None
            return next((user for user in data["users"] if user["id"] == session["user_id"]), None)

    def add_patient(self, patient: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            data = self._read_locked()
            data["patients"].append(patient)
            self._write_locked(data)
            return patient

    def list_patients(self) -> list[dict[str, Any]]:
        with self.lock:
            data = self._read_locked()
            return list(data["patients"])

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        with self.lock:
            data = self._read_locked()
            return next((p for p in data["patients"] if p["id"] == patient_id), None)

    def update_patient(self, patient_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        with self.lock:
            data = self._read_locked()
            for idx, patient in enumerate(data["patients"]):
                if patient["id"] == patient_id:
                    patient.update(updates)
                    data["patients"][idx] = patient
                    self._write_locked(data)
                    return patient
            return None

    def add_attack(self, attack: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            data = self._read_locked()
            data["attacks"].append(attack)
            self._write_locked(data)
            return attack

    def list_attacks_for_patient(self, patient_id: str) -> list[dict[str, Any]]:
        with self.lock:
            data = self._read_locked()
            return [attack for attack in data["attacks"] if attack["patient_id"] == patient_id]


class MongoStore:
    def __init__(self, uri: str, db_name: str):
        try:
            from pymongo import MongoClient, ReturnDocument
            from pymongo.errors import DuplicateKeyError
            from bson import ObjectId
        except ImportError as exc:
            raise RuntimeError("pymongo is required for MongoDB. Install it with pip install pymongo.") from exc

        self._duplicate_error = DuplicateKeyError
        self._return_document = ReturnDocument
        self._object_id = ObjectId
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.sessions = self.db["sessions"]
        self.patients = self.db["patients"]
        self.attacks = self.db["attacks"]

        self.users.create_index("email", unique=True)
        self.sessions.create_index("token", unique=True)
        self.patients.create_index("id", unique=True)
        self.attacks.create_index("patient_id")

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, self._object_id):
            return str(value)
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items() if k != "_id"}
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        return value

    def _clean(self, doc: dict[str, Any] | None) -> dict[str, Any] | None:
        if not doc:
            return None
        return self._serialize_value(doc)

    def create_user(self, name: str, email: str, password_hash: str, role: str = "doctor") -> dict[str, Any]:
        normalized_email = email.strip().lower()
        user = {
            "id": uuid.uuid4().hex,
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": password_hash,
            "role": role,
            "created_at": _now_iso(),
        }
        try:
            self.users.insert_one(user)
        except self._duplicate_error:
            raise ValueError("Email already registered.")
        return self._clean(user)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        normalized_email = email.strip().lower()
        return self._clean(self.users.find_one({"email": normalized_email}))

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self._clean(self.users.find_one({"id": user_id}))

    def create_session(self, user_id: str, token: str) -> dict[str, Any]:
        session = {"token": token, "user_id": user_id, "created_at": _now_iso()}
        self.sessions.insert_one(session)
        return self._clean(session)

    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        session = self.sessions.find_one({"token": token})
        if not session:
            return None
        return self._clean(self.users.find_one({"id": session.get("user_id")}))

    def add_patient(self, patient: dict[str, Any]) -> dict[str, Any]:
        self.patients.insert_one(patient)
        return self._clean(patient)

    def list_patients(self) -> list[dict[str, Any]]:
        return [self._clean(doc) for doc in self.patients.find({}).sort("created_at", -1)]

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        return self._clean(self.patients.find_one({"id": patient_id}))

    def update_patient(self, patient_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        updated = self.patients.find_one_and_update(
            {"id": patient_id},
            {"$set": updates},
            return_document=self._return_document.AFTER,
        )
        return self._clean(updated)

    def add_attack(self, attack: dict[str, Any]) -> dict[str, Any]:
        self.attacks.insert_one(attack)
        return self._clean(attack)

    def list_attacks_for_patient(self, patient_id: str) -> list[dict[str, Any]]:
        return [self._clean(doc) for doc in self.attacks.find({"patient_id": patient_id}).sort("created_at", -1)]


def get_store() -> Any:
    backend = (DATA_BACKEND or "json").lower()
    if backend == "mongo":
        return MongoStore(MONGO_URI, MONGO_DB)
    return JsonStore(STORE_PATH)
