import os
import io
import json
import time 
import pyotp
import firebase_admin
from firebase_admin import credentials, db
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
from pyzbar.pyzbar import decode
from urllib.parse import urlparse, parse_qs

# --- CONFIGURACIÓN ---
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID') 
IMAGE_NAME = 'qr_auth.png' 

def main():
    print("--- Iniciando proceso ---")
    
    # 1. Cargar Credenciales
    creds_json = json.loads(os.environ['GCP_SA_KEY'])
    g_creds = service_account.Credentials.from_service_account_info(creds_json)

    # 2. Conectar a Google Drive
    print("Conectando a Drive...")
    drive_service = build('drive', 'v3', credentials=g_creds)
    
    query = f"'{DRIVE_FOLDER_ID}' in parents and name = '{IMAGE_NAME}' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print(f"No se encontró el archivo {IMAGE_NAME} en la carpeta.")
        return

    file_id = items[0]['id']
    print(f"Archivo encontrado: {file_id}. Descargando...")

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    fh.seek(0)

    # 3. Leer el QR
    print("Procesando imagen QR...")
    image = Image.open(fh)
    decoded_objects = decode(image)

    if not decoded_objects:
        print("No se pudo detectar ningún código QR en la imagen.")
        return

    qr_data = decoded_objects[0].data.decode("utf-8")
    print("QR detectado.")

    # 4. Extraer el Secreto
    parsed_url = urlparse(qr_data)
    qs = parse_qs(parsed_url.query)
    
    if 'secret' not in qs:
        print("El QR no contiene un parámetro 'secret'.")
        return
        
    secret = qs['secret'][0]
    
    # Generar código de prueba para log
    totp = pyotp.TOTP(secret)
    print(f"Secreto extraído exitosamente. Código actual de prueba: {totp.now()}")

    # 5. Enviar a Firebase
    print("Conectando a Firebase...")
    if not firebase_admin._apps:
        cred = credentials.Certificate(creds_json)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.environ.get('FIREBASE_DB_URL')
        })

    ref = db.reference('google_auth_data')
    
    # AQUÍ ESTABA EL ERROR: Usamos time.time() de Python
    ref.set({
        'secret': secret,
        'last_updated': int(time.time() * 1000), 
        'status': 'active'
    })
    
    print("¡Éxito! Secreto guardado en Firebase.")

if __name__ == '__main__':
    main()
