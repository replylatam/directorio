import os
import json
import firebase_admin
from firebase_admin import credentials, db

# ========= CONFIG =========
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL")
GCP_SA_KEY = os.environ.get("GCP_SA_KEY")

if not FIREBASE_DB_URL or not GCP_SA_KEY:
    raise Exception("Faltan variables de entorno")

# ========= INIT =========
creds_json = json.loads(GCP_SA_KEY)
cred = credentials.Certificate(creds_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": FIREBASE_DB_URL
    })

root = db.reference("/")

# ========= CREATE USERS =========
users_ref = root.child("users")
if not users_ref.get():
    users_ref.set({})

admin_ref = users_ref.child("admin")
if not admin_ref.get():
    admin_ref.set({
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "status": "active"
    })

# ========= CREATE CLIENTS =========
clients_ref = root.child("clients")
if not clients_ref.get():
    clients_ref.set({})

client_ref = clients_ref.child("cliente_1")
if not client_ref.get():
    client_ref.set({
        "name": "Cliente A",
        "secret": "TEMPORAL",
        "status": "active"
    })

print("✅ Firebase inicializado correctamente")
