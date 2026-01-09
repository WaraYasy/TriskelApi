# Dominio Web - Triskel

Portal web del juego Triskel con Flask integrado en FastAPI.

## 📁 Estructura

```
web/
├── app.py                      # Flask app principal
├── __init__.py                 # Exports del dominio
├── analytics/                  # Dashboard de métricas
│   ├── __init__.py
│   ├── routes.py              # Blueprint con endpoints
│   ├── service.py             # Lógica de agregación
│   └── templates/
│       └── analytics/
│           └── index.html     # Dashboard principal
├── admin/                      # Panel admin (futuro)
│   ├── routes.py
│   └── templates/
├── public/                     # Landing pública (futuro)
│   ├── routes.py
│   └── templates/
├── templates/                  # Templates compartidos
│   ├── base.html              # Layout base
│   ├── index.html             # Home del portal
│   ├── 404.html               # Error 404
│   └── 500.html               # Error 500
└── static/                     # Assets estáticos
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    └── images/
```

## 🚀 Endpoints

### **Dashboard (Analytics)**
- `GET /dashboard/`         → Métricas globales
- `GET /dashboard/players`  → Análisis de jugadores
- `GET /dashboard/games`    → Análisis de partidas
- `GET /dashboard/choices`  → Decisiones morales
- `GET /dashboard/export`   → Exportar datos CSV

### **Home**
- `GET /`                   → Landing page principal

### **Admin** (futuro)
- `GET /admin/`             → Panel de administración

### **Public** (futuro)
- `GET /public/`            → Contenido público

## 🔧 Integración con FastAPI

En `main.py`:

```python
from fastapi.middleware.wsgi import WSGIMiddleware
from app.domain.web import flask_app

# Montar Flask app
app.mount("/web", WSGIMiddleware(flask_app))
```

Resultado:
```
http://localhost:8000/web/                  → Landing page
http://localhost:8000/web/dashboard/        → Dashboard
http://localhost:8000/web/dashboard/players → Análisis
```

## 📊 Stack Tecnológico

- **Flask** - Framework web
- **Bootstrap 5** - UI framework
- **Plotly** - Gráficos interactivos
- **Pandas** - Procesamiento de datos
- **Jinja2** - Templates HTML

## 🎨 Personalización

### CSS
Editar `static/css/style.css` para cambiar estilos.

### JavaScript
Editar `static/js/main.js` para añadir funcionalidad.

### Variables de tema
En `style.css`:
```css
:root {
    --triskel-primary: #4a90e2;
    --triskel-secondary: #6c757d;
    /* ... */
}
```

## 📝 TODO

- [ ] Implementar AnalyticsService completo
- [ ] Crear gráficos con Plotly
- [ ] Implementar exportación a CSV
- [ ] Añadir panel de administración
- [ ] Crear landing page pública
- [ ] Añadir autenticación para admin
- [ ] Implementar actualización en tiempo real
