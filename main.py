import os
import io
import json
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
# ID de la carpeta en Drive donde pones la imagen del QR
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID') 
# Nombre del archivo de imagen (ej: qr.png)
IMAGE_NAME = 'qr_auth.png' 

def main():
    print("--- Iniciando proceso ---")
    
    # 1. Cargar Credenciales desde Secret de GitHub
    # Asumimos que usas la misma cuenta de servicio para Drive y Firebase
    creds_json = json.loads(os.environ['GCP_SA_KEY'])
    g_creds = service_account.Credentials.from_service_account_info(creds_json)

    # 2. Conectar a Google Drive
    print("Conectando a Drive...")
    drive_service = build('drive', 'v3', credentials=g_creds)
    
    # Buscar la imagen en la carpeta especificada
    query = f"'{DRIVE_FOLDER_ID}' in parents and name = '{IMAGE_NAME}' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print(f"No se encontró el archivo {IMAGE_NAME} en la carpeta.")
        return

    file_id = items[0]['id']
    print(f"Archivo encontrado: {file_id}. Descargando...")

    # Descargar imagen en memoria
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    fh.seek(0) # Volver al inicio del archivo en memoria

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
    # El formato suele ser: otpauth://totp/Example:user?secret=JBSWY3DPEHPK3PXP&issuer=Example
    parsed_url = urlparse(qr_data)
    qs = parse_qs(parsed_url.query)
    
    if 'secret' not in qs:
        print("El QR no contiene un parámetro 'secret'.")
        return
        
    secret = qs['secret'][0]
    
    # Opcional: Generar código actual para probar
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    print(f"Secreto extraído exitosamente. Código actual de prueba: {current_code}")

    # 5. Enviar a Firebase
    print("Conectando a Firebase...")
    if not firebase_admin._apps:
        cred = credentials.Certificate(creds_json)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.environ.get('FIREBASE_DB_URL')
        })

    ref = db.reference('google_auth_data')
    ref.set({
        'secret': secret,
        'last_updated': firebase_admin.db.ServerValue.TIMESTAMP,
        'status': 'active'
    })
    
    print("¡Éxito! Secreto guardado en Firebase.")

if __name__ == '__main__':
    main()
