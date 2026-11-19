import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore, storage

FIREBASE_APP = None
DB_CLIENT = None
BUCKET_CLIENT = None

def init_firebase() -> bool:
    """
    Initializes Firebase Admin SDK using:
    1. serviceAccountKey.json in project root
    2. FIREBASE_SERVICE_ACCOUNT env var (file path or raw JSON string)
    """
    global FIREBASE_APP, DB_CLIENT, BUCKET_CLIENT

    if FIREBASE_APP is not None:
        return True

    cred = None
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    # 1. Check direct individual keys from .env
    fb_project_id = os.getenv("FIREBASE_PROJECT_ID")
    fb_client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    fb_private_key = os.getenv("FIREBASE_PRIVATE_KEY")

    if fb_project_id and fb_client_email and fb_private_key:
        try:
            # Handle escaped newlines in private key
            formatted_key = fb_private_key.replace("\\n", "\n").strip()
            cred_dict = {
                "type": "service_account",
                "project_id": fb_project_id,
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", "key1"),
                "private_key": formatted_key,
                "client_email": fb_client_email,
                "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
            cred = credentials.Certificate(cred_dict)
            print("[Firebase] Successfully authenticated via direct environment keys!")
        except Exception as e:
            print(f"[Firebase Warning] Error initializing from direct keys: {e}")

    # 2. Check local key files
    if not cred:
        local_candidates = [
            Path("serviceAccountKey.json"),
            Path("firebase-key.json"),
            Path("firebase_credentials.json")
        ]
        for p in local_candidates:
            if p.exists():
                try:
                    cred = credentials.Certificate(str(p.resolve()))
                    print(f"[Firebase] Loaded credentials from {p}")
                    break
                except Exception as e:
                    print(f"[Firebase Warning] Error loading {p}: {e}")

    # 3. Check environment variable (raw JSON string or path)
    env_cred = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not cred and env_cred:
        try:
            if env_cred.strip().startswith("{"):
                cred_dict = json.loads(env_cred)
                cred = credentials.Certificate(cred_dict)
            elif os.path.exists(env_cred):
                cred = credentials.Certificate(env_cred)
            print("[Firebase] Loaded credentials from FIREBASE_SERVICE_ACCOUNT env")
        except Exception as e:
            print(f"[Firebase Warning] Error loading env credentials: {e}")

    if not cred:
        print("[Firebase] No credentials found. Running in Local Mode (will use SQLite & local files until serviceAccountKey.json is provided).")
        return False

    try:
        opts = {}
        if storage_bucket:
            opts["storageBucket"] = storage_bucket

        FIREBASE_APP = firebase_admin.initialize_app(cred, opts)
        DB_CLIENT = firestore.client()
        if storage_bucket:
            BUCKET_CLIENT = storage.bucket()
        print("[Firebase] Successfully connected to Firebase Cloud Firestore!")
        return True
    except Exception as e:
        print(f"[Firebase Error] Initialization failed: {e}")
        return False

def is_firebase_active() -> bool:
    """Returns True if Firebase Firestore is active and connected."""
    global DB_CLIENT
    if DB_CLIENT is None:
        init_firebase()
    return DB_CLIENT is not None

# ----------------- Firestore Database Methods -----------------

def save_clip_to_db(clip_id: str, clip_data: Dict[str, Any]) -> bool:
    """Saves clip metadata to Firestore collection 'clips'."""
    if is_firebase_active():
        try:
            doc_ref = DB_CLIENT.collection("clips").document(clip_id)
            doc_ref.set(clip_data, merge=True)
            return True
        except Exception as e:
            if "SERVICE_DISABLED" in str(e) or "Cloud Firestore API has not been used" in str(e):
                print("[Firebase Tip] Please click 'Create Database' under Firestore Database in Firebase Console (https://console.firebase.google.com/project/clipshorts-20ff0/firestore)")
            else:
                print(f"[Firebase Firestore Error] Failed to save clip: {e}")
    return False

def get_clips_from_db() -> List[Dict[str, Any]]:
    """Retrieves all clips from Firestore collection 'clips'."""
    if is_firebase_active():
        try:
            docs = DB_CLIENT.collection("clips").order_by("viral_score", direction=firestore.Query.DESCENDING).stream()
            clips = [doc.to_dict() for doc in docs]
            return clips
        except Exception as e:
            if "SERVICE_DISABLED" in str(e) or "Cloud Firestore API has not been used" in str(e):
                pass
            else:
                print(f"[Firebase Firestore Error] Failed to fetch clips: {e}")
    return []

def save_scheduled_post_to_db(post_id: str, post_data: Dict[str, Any]) -> bool:
    """Saves scheduled post to Firestore collection 'scheduled_posts'."""
    if is_firebase_active():
        try:
            doc_ref = DB_CLIENT.collection("scheduled_posts").document(str(post_id))
            doc_ref.set(post_data, merge=True)
            return True
        except Exception as e:
            if "SERVICE_DISABLED" in str(e) or "Cloud Firestore API has not been used" in str(e):
                print("[Firebase Tip] Please click 'Create Database' under Firestore Database in Firebase Console")
            else:
                print(f"[Firebase Firestore Error] Failed to save scheduled post: {e}")
    return False

def get_scheduled_posts_from_db() -> List[Dict[str, Any]]:
    """Retrieves scheduled posts from Firestore collection 'scheduled_posts'."""
    if is_firebase_active():
        try:
            docs = DB_CLIENT.collection("scheduled_posts").order_by("scheduled_time").stream()
            posts = []
            for d in docs:
                data = d.to_dict()
                data["id"] = d.id
                posts.append(data)
            return posts
        except Exception as e:
            if "SERVICE_DISABLED" in str(e) or "Cloud Firestore API has not been used" in str(e):
                pass
            else:
                print(f"[Firebase Firestore Error] Failed to fetch scheduled posts: {e}")
    return []

def delete_scheduled_post_from_db(post_id: str) -> bool:
    """Deletes scheduled post from Firestore."""
    if is_firebase_active():
        try:
            DB_CLIENT.collection("scheduled_posts").document(str(post_id)).delete()
            return True
        except Exception as e:
            print(f"[Firebase Firestore Error] Failed to delete scheduled post: {e}")
    return False

# ----------------- Firebase Cloud Storage -----------------

def upload_to_firebase_storage(local_file: str, destination_blob: str) -> Optional[str]:
    """Uploads file to Firebase Storage bucket and returns public URL."""
    if is_firebase_active() and BUCKET_CLIENT:
        try:
            blob = BUCKET_CLIENT.blob(destination_blob)
            blob.upload_from_filename(local_file)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print(f"[Firebase Storage Error] {e}")
    return None
