"""
Script de prueba para verificar la conexión con Firebase Firestore
"""
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
import os

def test_firebase_connection():
    """Prueba básica de conexión a Firebase"""

    print("=" * 50)
    print("PRUEBA DE CONEXIÓN A FIREBASE")
    print("=" * 50)

    # 1. Verificar que el archivo de credenciales existe
    cred_path = settings.firebase_credentials_path
    print(f"\n1. Verificando archivo de credenciales...")
    print(f"   Ruta: {cred_path}")

    if not os.path.exists(cred_path):
        print(f"   ❌ ERROR: No se encuentra el archivo de credenciales")
        return False
    else:
        print(f"   ✅ Archivo encontrado")

    # 2. Inicializar Firebase
    print(f"\n2. Inicializando Firebase...")
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(f"   ✅ Firebase inicializado correctamente")
    except Exception as e:
        print(f"   ❌ ERROR al inicializar Firebase: {e}")
        return False

    # 3. Conectar a Firestore
    print(f"\n3. Conectando a Firestore...")
    try:
        db = firestore.client()
        print(f"   ✅ Conexión a Firestore establecida")
    except Exception as e:
        print(f"   ❌ ERROR al conectar a Firestore: {e}")
        return False

    # 4. Crear un documento de prueba
    print(f"\n4. Creando documento de prueba...")
    try:
        test_ref = db.collection('test').document('connection_test')
        test_ref.set({
            'mensaje': 'Hola desde Python!',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'prueba': True
        })
        print(f"   ✅ Documento creado en colección 'test'")
    except Exception as e:
        print(f"   ❌ ERROR al crear documento: {e}")
        return False

    # 5. Leer el documento de prueba
    print(f"\n5. Leyendo documento de prueba...")
    try:
        doc = test_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"   ✅ Documento leído correctamente:")
            print(f"      - Mensaje: {data.get('mensaje')}")
            print(f"      - Timestamp: {data.get('timestamp')}")
            print(f"      - Prueba: {data.get('prueba')}")
        else:
            print(f"   ❌ El documento no existe")
            return False
    except Exception as e:
        print(f"   ❌ ERROR al leer documento: {e}")
        return False

    # 6. Eliminar el documento de prueba
    print(f"\n6. Limpiando documento de prueba...")
    try:
        test_ref.delete()
        print(f"   ✅ Documento eliminado")
    except Exception as e:
        print(f"   ⚠️  ADVERTENCIA: No se pudo eliminar el documento: {e}")

    print("\n" + "=" * 50)
    print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("=" * 50)
    print("\n🎉 Firebase está configurado y funcionando correctamente!\n")

    return True

if __name__ == "__main__":
    try:
        test_firebase_connection()
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
