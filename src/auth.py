import json
import hashlib
import hmac
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_FILE = BASE_DIR / "data" / "users.json"


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_secret_admin():
    """Read Admin credentials from Streamlit Secrets."""
    try:
        admin = st.secrets.get("admin", {})
        email = str(admin.get("email", "")).strip().lower()
        password = str(admin.get("password", ""))
        name = str(admin.get("name", "Admin")).strip() or "Admin"
        company = str(admin.get("company", "HCM Lite")).strip() or "HCM Lite"

        if email and password:
            return {
                "id": 1,
                "company": company,
                "name": name,
                "email": email,
                "password": password,
                "role": "Admin",
            }
    except Exception:
        pass

    return None


def load_users():
    users = []

    if AUTH_FILE.exists():
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as file:
                stored_users = json.load(file)

            if isinstance(stored_users, list):
                users = stored_users
        except (json.JSONDecodeError, OSError):
            pass

    # Secrets-based Admin is available even without users.json.
    secret_admin = get_secret_admin()

    if secret_admin:
        users = [
            user for user in users
            if user.get("email", "").lower() != secret_admin["email"]
        ]
        users.insert(0, {
            key: value
            for key, value in secret_admin.items()
            if key != "password"
        })

    return users


def save_users(users):
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(AUTH_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


def create_admin(company_name, name, email, password):
    # Don't create another Admin when Secrets already defines one.
    if get_secret_admin():
        return False, "Admin Secrets mein pehle se configured hai."

    users = load_users()

    if any(user.get("role") == "Admin" for user in users):
        return False, "Admin account pehle se bana hua hai."

    if any(
        user.get("email", "").lower() == email.strip().lower()
        for user in users
    ):
        return False, "Ye email pehle se registered hai."

    users.append({
        "id": 1,
        "company": company_name.strip(),
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": hash_password(password),
        "role": "Admin",
    })

    save_users(users)
    return True, "Admin account successfully create ho gaya!"



def authenticate(email, password):
    secret_admin = get_secret_admin()
    entered_email = email.strip().lower()

    if secret_admin:
        saved_email = secret_admin["email"].strip().lower()
        saved_password = secret_admin["password"]

        if (
            hmac.compare_digest(entered_email, saved_email)
            and hmac.compare_digest(password, saved_password)
        ):
            return {
                key: value
                for key, value in secret_admin.items()
                if key != "password"
            }

    entered_hash = hash_password(password)

    for user in load_users():
        saved_email = user.get("email", "").strip().lower()
        saved_hash = user.get("password_hash", "")

        if (
            hmac.compare_digest(entered_email, saved_email)
            and saved_hash
            and hmac.compare_digest(saved_hash, entered_hash)
        ):
            return user

    return None

