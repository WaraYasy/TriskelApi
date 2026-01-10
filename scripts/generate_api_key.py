#!/usr/bin/env python3
"""
Autora: Wara ⭐️

Este script genera API Keys criptográficamente seguras para proteger
los endpoints administrativos de la API.

Características:
- Generación segura con secrets.token_urlsafe()
- API Keys de 32 bytes (43 caracteres en base64 URL-safe)
- Instrucciones detalladas de configuración
- Compatibilidad con local (.env) y Railway (variables de entorno)

Uso:
    python3 scripts/generate_api_key.py

Salida:
    - API Key generada aleatoriamente
    - Instrucciones para configuración local (.env)
    - Instrucciones para configuración en Railway
    - Ejemplo de uso en requests con curl

Seguridad:
    Las claves generadas son criptográficamente seguras y únicas.
    Nunca reutilices claves ni las compartas públicamente.

Arquitectura:
- Capa 1: Generación segura con módulo secrets
- Capa 2: Formateo y presentación de resultados
- Capa 3: Documentación de instrucciones de uso
"""

import secrets

def generate_api_key():
    """
    Genera una API Key aleatoria y criptográficamente segura.

    Utiliza el módulo secrets de Python que genera tokens seguros
    adecuados para aplicaciones de seguridad como tokens de autenticación.

    Returns:
        str: API Key de 43 caracteres en formato base64 URL-safe.
             Ejemplo: 'aBcD123XyZ789-_qWeRtY456...' (sin caracteres especiales)

    Note:
        La función token_urlsafe(32) genera 32 bytes aleatorios y los
        codifica en base64 URL-safe, resultando en aproximadamente 43
        caracteres seguros para uso en URLs y headers HTTP.

    Example:
        ```python
        key = generate_api_key()
        print(f"Tu nueva API key: {key}")
        # Output: Tu nueva API key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t
        ```
    """
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    api_key = generate_api_key()
    print("=" * 70)
    print("🔑 NUEVA API KEY GENERADA")
    print("=" * 70)
    print(f"\n{api_key}\n")
    print("=" * 70)
    print("📝 INSTRUCCIONES:")
    print("=" * 70)
    print("\n1. Copia la API Key de arriba")
    print("\n2. LOCAL - Agrégala a tu archivo .env:")
    print(f"   ADMIN_API_KEY={api_key}")
    print("\n3. RAILWAY - Agrégala como variable de entorno:")
    print("   Dashboard → Variables → Add Variable")
    print("   Nombre: ADMIN_API_KEY")
    print(f"   Valor: {api_key}")
    print("\n4. USO - Incluye en tus requests:")
    print('   curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/admin/force-import')
    print("\n⚠️  IMPORTANTE: Guarda esta clave en un lugar seguro. No la compartas.\n")
    print("=" * 70)
