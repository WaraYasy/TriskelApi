# Guía de Linters

## Requisitos

```bash
pip install isort black ruff
```

## Comandos

### 1. isort (ordenar imports)
```bash


```

### 2. black (formatear código)
```bash
black --line-length=100 app/ tests/
```

### 3. ruff (lint + autofix)
```bash
ruff check . --fix
```

## Ejecutar todos de una vez

```bash
isort . --profile black --line-length=100 && black --line-length=100 app/ tests/ && ruff check . --fix
```

## Solo verificar (sin modificar)

```bash
isort . --check --profile black --line-length=100
black --check --line-length=100 app/ tests/
ruff check .
```
