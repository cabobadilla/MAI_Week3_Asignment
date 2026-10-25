# Opciones de diseño GrowWithAI · gwa-ui-v1
Estado: design_review, no aprobado. Prototipos locales independientes, sin app/LLM/red ni autenticación real.
Abrir index.html (doble clic o navegador local); enlaces relativos a option-a.html y option-b.html. Pantallas seleccionables arriba; parámetros ?screen=login|home|empty|sources|brief|question|running|error|review|export.
A v1 Ruta guiada: recomendada para primer uso. B v1 Mesa editorial: navegación lateral para trabajo frecuente. Mismos requisitos y datos de ejemplo.
No introducir contraseñas reales. Acceso/alta simulados con literal ilustrativo readonly. Sin carga real de archivos, exportaciones ni envío. Las capturas Playwright y sus resultados se registran por separado en evidence.json y design-manifest.json; no son pruebas del producto.
