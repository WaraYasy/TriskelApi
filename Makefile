.PHONY: help install test test-unit test-integration test-e2e test-security test-coverage lint format security clean run dev

# Colores para output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo "$(BLUE)Triskel API - Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Instalar dependencias
	@echo "$(BLUE)Instalando dependencias...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev: ## Instalar dependencias de desarrollo
	@echo "$(BLUE)Instalando dependencias de desarrollo...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install ruff black isort bandit safety pre-commit
	pre-commit install

test: ## Ejecutar todos los tests con cobertura
	@echo "$(YELLOW)Ejecutando todos los tests...$(NC)"
	pytest

test-unit: ## Ejecutar solo tests unitarios
	@echo "$(YELLOW)Ejecutando tests unitarios...$(NC)"
	pytest -m unit -v

test-integration: ## Ejecutar tests de integración
	@echo "$(YELLOW)Ejecutando tests de integración...$(NC)"
	pytest -m integration -v

test-e2e: ## Ejecutar tests end-to-end
	@echo "$(YELLOW)Ejecutando tests E2E...$(NC)"
	pytest -m e2e -v

test-security: ## Ejecutar tests de seguridad
	@echo "$(YELLOW)Ejecutando tests de seguridad...$(NC)"
	pytest -m security -v

test-coverage: ## Generar reporte de cobertura HTML
	@echo "$(YELLOW)Generando reporte de cobertura...$(NC)"
	pytest --cov=app/domain --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Reporte generado en: htmlcov/index.html$(NC)"

test-fast: ## Ejecutar tests sin cobertura (más rápido)
	@echo "$(YELLOW)Ejecutando tests rápidos...$(NC)"
	pytest --no-cov -v

lint: ## Ejecutar linters (ruff, black, isort)
	@echo "$(BLUE)Ejecutando linters...$(NC)"
	ruff check app/ tests/
	black --check --line-length=100 app/ tests/
	isort --check-only --profile black --line-length 100 app/ tests/

format: ## Formatear código automáticamente
	@echo "$(BLUE)Formateando código...$(NC)"
	black --line-length=100 app/ tests/
	isort --profile black --line-length 100 app/ tests/
	ruff check app/ tests/ --fix
	@echo "$(GREEN)✓ Código formateado$(NC)"

security: ## Ejecutar análisis de seguridad
	@echo "$(BLUE)Ejecutando análisis de seguridad...$(NC)"
	@echo "$(YELLOW)Running bandit...$(NC)"
	bandit -r app/ -ll || true
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	safety check || true

clean: ## Limpiar archivos temporales y cache
	@echo "$(BLUE)Limpiando archivos temporales...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml
	@echo "$(GREEN)✓ Limpieza completada$(NC)"

run: ## Ejecutar la aplicación FastAPI
	@echo "$(BLUE)Iniciando Triskel API...$(NC)"
	uvicorn app.main:app --reload

dev: ## Ejecutar en modo desarrollo (API + Dashboard)
	@echo "$(BLUE)Iniciando en modo desarrollo...$(NC)"
	uvicorn app.main:app --reload --port 8000

ci: ## Simular CI localmente (tests + lint + security)
	@echo "$(BLUE)Simulando pipeline de CI...$(NC)"
	@echo ""
	@echo "$(YELLOW)1/4 - Linting...$(NC)"
	@make lint
	@echo ""
	@echo "$(YELLOW)2/4 - Tests unitarios...$(NC)"
	@make test-unit
	@echo ""
	@echo "$(YELLOW)3/4 - Tests completos...$(NC)"
	@make test
	@echo ""
	@echo "$(YELLOW)4/4 - Seguridad...$(NC)"
	@make security
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)   ✓ Pipeline CI completado$(NC)"
	@echo "$(GREEN)========================================$(NC)"

pre-commit: ## Ejecutar pre-commit hooks manualmente
	@echo "$(BLUE)Ejecutando pre-commit hooks...$(NC)"
	pre-commit run --all-files

coverage-open: ## Abrir reporte de cobertura en el navegador
	@echo "$(BLUE)Abriendo reporte de cobertura...$(NC)"
	open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Por favor abre manualmente: htmlcov/index.html"

# Comandos Git helpers
git-status: ## Ver estado de git con resumen de tests
	@echo "$(BLUE)Estado del repositorio:$(NC)"
	@git status
	@echo ""
	@echo "$(BLUE)Última ejecución de tests:$(NC)"
	@if [ -f .coverage ]; then coverage report --skip-empty; else echo "No hay datos de cobertura. Ejecuta: make test"; fi

# Default target
.DEFAULT_GOAL := help