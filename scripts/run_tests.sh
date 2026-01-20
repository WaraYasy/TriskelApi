#!/bin/bash
#
# Script auxiliar para ejecutar tests de la API
#
# Uso:
#   ./scripts/run_tests.sh              # Ejecuta tests en producción
#   ./scripts/run_tests.sh local        # Ejecuta tests en local
#   ./scripts/run_tests.sh prod         # Ejecuta tests en producción
#   ./scripts/run_tests.sh --no-cleanup # No eliminar datos de prueba
#

PROD_URL="https://triskel.up.railway.app"
LOCAL_URL="http://localhost:8000"

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

case "$1" in
    local)
        echo -e "${BLUE}Ejecutando tests en LOCAL: ${LOCAL_URL}${NC}"
        python3 scripts/test_api_complete.py --base-url "$LOCAL_URL" "${@:2}"
        ;;
    prod)
        echo -e "${BLUE}Ejecutando tests en PRODUCCIÓN: ${PROD_URL}${NC}"
        python3 scripts/test_api_complete.py --base-url "$PROD_URL" "${@:2}"
        ;;
    --no-cleanup)
        echo -e "${BLUE}Ejecutando tests en PRODUCCIÓN (sin cleanup)${NC}"
        python3 scripts/test_api_complete.py --base-url "$PROD_URL" --no-cleanup
        ;;
    --help|-h)
        echo "Uso: $0 [local|prod|--no-cleanup]"
        echo ""
        echo "Opciones:"
        echo "  local         Ejecutar tests en http://localhost:8000"
        echo "  prod          Ejecutar tests en producción (Railway)"
        echo "  --no-cleanup  No eliminar datos de prueba al finalizar"
        echo "  --help        Mostrar esta ayuda"
        exit 0
        ;;
    *)
        echo -e "${BLUE}Ejecutando tests en PRODUCCIÓN (default): ${PROD_URL}${NC}"
        python3 scripts/test_api_complete.py --base-url "$PROD_URL" "$@"
        ;;
esac
