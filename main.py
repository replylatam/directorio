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
    creds_json = json.loads(os.environ[{
  "type": "service_account",
  "project_id": "directorio-484214",
  "private_key_id": "16950ea6bd724b1bbaf3b88cbf65649ff400f46f",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDAopIeOjLotHJ4\nKhAvVD4IGkYLgXlBkx+jg1PfvQZ5MURblyz53sHB80oWN+l/8uWVwA3W7vbFmy6B\n3ntLK9BVF0thaYpe1dgsaO2M4tqHOYFuYEEq6lZDkDhlFJL4OijKxrgzy4/gfc5c\ngOk4PAVsKm9t/2Z9Tyf4SWSkjIbqaFBm4kHn6fiS8QoefnBQvTd4T9On+Uy6BQsv\nUT9sBJeiB/Bv7PCB1xHNfgyQSMnKmFH5GLDtalL59t9fjxAg3KkRTSBNlRm0yniV\nwCOdfCUZq1JT7lOrxVKM8QXNV27xPoVbosp4voYNY4n8pASWxS8XMWWSj064IPPO\nkGbWTFQZAgMBAAECgf98SGb9buRplAJGhNzsVu2uoe+PJ3mT/9fp0aZ2M6kkMnpn\n8qE8lPttUV9QoReFSrEqbJPWmADz0lWvHwYXpFeajpeTwa6vK54iXjrlKszSxxyP\n7zTG+2msgt/frJEl6wq7ySS5m3Fi5R1pkReRsH0kducYO4S5qYL1gw9BGr6bfJDN\nlSUDoqU1xPaCuSvxTCqskS/9H2o1ODcE1MXrV/IveAKNfboS8K+hFzjL9muZ+Pf7\n8e/rYUUDciKKYDOA91lCdarvVro64TL2Tc+JE60/8iYOuo+IJLwDUQuRUgwFY6ur\navlA+la3B9M01wknn9TIbJwxBcS34xbwmEak46MCgYEA/IK8hjU2ev/mH0kqeEDv\n66K67stH4AjuKzdXAaJyapECoupwEguLExT8U1ZLFz0xntPEfyfJMTVEiPox3QQF\nTac6iVmcWIstFbPMa+6eeQ3Xp6v1QJniRhFje9UPINr28Q1sMZKXE5hM6hEHr1ed\npliO1vo7f5DxMkAjxt5uRW8CgYEAw0wFyDS4qwVaut4Up7lPlLnWNNst1AalEr9V\nPF2rLxaT2oiWAobUPu+eHJkG60jaUhUwJp2dOOypUw8RIsQ8Ev3fjdEWd/MzUxyW\nTDXixJjwwaRJvzogolOxGQDBzGUq3dY2ojDiltcyNBcDB3++7y9iqIGlwqN1SO23\n+slfCvcCgYBTX7ttuM43SJ0sAVWDhTVyoTWFuRsPTwOMw2X4BTIwG5c6QZwlaShP\ncaNqxNhgYPUsUxHTRki49bSeYbXrGvPBUxER3sOvvKxzOP2rOYubvsVQ+IcvAGBk\n8ELf1VZ8a7AToXHy4Er/zk6/DkZyT8Se8yietNrGYQ4yoFjvxeu1AwKBgQCzE7yh\njiZfO3OssgMCoNumJpmSsf/d0ZIAFM3VopZbgTpmQqQ7AOMSKqoy0ucTTCRU6/TR\nE+mczvWcoc42sPXc/EnHQph1uN2xMh9nFmovl4X8Kectn+FYt6FGqfkKsSGTdN93\n7Zd4dS8lsIwojizIKg0vMmKKjVP4YXI4Vfn+lQKBgQDScKeX5tmhgZmpGRAZnDHZ\n/Fz2DU06iuX44RqOnJKG8wKCSabolcZJsNGV7IM/b3pgTQmiFTxOgnBP6rZkS6Cz\nOgTGxGLi6bs0qFTzvSaDgfsvo4Y7a0TEDAhC6MOgvqKxRaYqczv+xYENZLmJUuvC\nB1tOIWzjxsi12nTLUq9HHA==\n-----END PRIVATE KEY-----\n",
  "client_email": "bot-lector-qr@directorio-484214.iam.gserviceaccount.com",
  "client_id": "114793138783898320041",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/bot-lector-qr%40directorio-484214.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
])
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
