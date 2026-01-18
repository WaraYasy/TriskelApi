"""
Dominio Web

Portal web de Triskel que integra:
- Dashboard de analytics (métricas y visualizaciones)
- Panel de administración (futuro)
- Landing page pública (futuro)

Este dominio usa Flask y se monta en FastAPI.
"""

from .app import flask_app

__all__ = ["flask_app"]
