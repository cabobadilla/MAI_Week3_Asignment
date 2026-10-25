# Verificación de preparación dotHarness · 2026-10-25
Alcance: setup/procedencia/configuración; no app, inferencia ni bootstrap upstream.

La operación incierta anterior no se había ejecutado: se comprobó ausencia de manifiesto y presencia de integración anterior; el intento había vencido por tiempo en revisión automática. Tras reconexión se aplicó la migración una vez.

Snapshot dotHarness 0.9.0-pilot, SHA y digest/inventario en dot/harness/manifest.json. Remote identificado localmente; fetch anterior 0/0. Copias desde blobs del commit; se preservan cambios ajenos del harness. AGENTS upstream de mantenimiento no se adoptó como instrucciones del consumidor.

Retirados tres documentos de integración anterior; reemplazados AGENTS/opencode y actualizadas specs/setup/checkpoints. opencode.json replica el ejemplo deny-all. Perfil Python, requisitos particulares y lecciones están separados en dot/. El adaptador es UI estática; adaptación Python solo propuesta.

Verificador scripts/verify-preparation.py comprueba pin/digest/hashes de copias, hashes de fuentes/extracciones, JSON/TOML, deny-all, ausencia de referencias al flujo anterior, ignores y origin original. Versiones/paquetes y pip check se comprueban por separado. Validación aislada de configuración OpenCode no implica enforcement completo o aislamiento OS.

Pendientes antes de coder: base Git (main sin commits), modelo app OpenRouter pendiente y modelo/driver coder autorizado, aislamiento y controles externos; auth y mockups aprobados antes de UI. No hay contrato ready, app, RAG, pruebas de producto, inferencia, navegador ni resultados de calidad medidos. Sin instalación adicional, commit/push, publicación o despliegue en esta corrección.

## Resultados efectivamente ejecutados
Verificador local: PASS para pin/digest, 44 copias fijadas, hashes de fuentes/extracciones, JSON/TOML, deny-all, ausencia de integración retirada, ignores y origin. Python 3.11.16, virtualenv 21.14.13, pip check correcto; .venv solo pip 26.2.2 y setuptools 84.2.1. Único .git: raíz de entrega. Atributos Library de identidad/versión presentes. Working tree compartido del harness conserva los dos cambios previamente observados.

OpenCode --version aislado: v2.0.32, exit 0. debug config aislado: exit 1 porque el puerto de servicio administrado 49374 en 127.0.0.1 ya está ocupado. No se detuvo el proceso ajeno ni se cambió puerto/configuración persistente; configuración efectiva nueva y compatibilidad operativa quedan sin verificar. No se ejecutó inferencia. Evidencia saneada: dot/setup-evidence.json.

Actualización OpenRouter: decisión API/local resuelta por usuario, presupuesto controlado en API key. Comprobados ejemplo con clave/modelo vacíos y disabled, límites técnicos coherentes, .env ignorado y .env.example versionable. Checker actualizado y ejecutado; ninguna clave real leída ni llamada. No se valida aún loader, retry real, SDK, límites efectivos o coste: solo esquema/propuesta.

Fase de diseño: dos prototipos standalone locales, 48 comprobaciones/54 capturas Playwright headless (desktop 1280×800 y móvil 375×812), cero console/page errors, cero solicitudes externas y sin overflow en pantallas probadas. Interacciones simuladas: navegación, alta ilustrativa, aprobación bloqueada hasta checkbox, edición que revoca aprobación y exportación sin descargas. Inspección visual de comparador desktop y revisión móvil. Hashes en design-manifest.json; aprobación humana pendiente. No aceptación funcional de producto.

## Specs r4 · evidencia vigente
Índice canónico docs/specs/sponsor-materials/README.md. scripts/verify-specs.py valida30 criterios/30 test IDs planeados, cobertura de14 tareas,24 enlaces internos, ausencia de placeholders y DDL de referencia con13 comprobaciones SQLite en memoria/sintéticas (constraints FK/dedup/inmutabilidad/correcciones/rollback). Reporte spec-verification.json distingue app_tests=not_run; no implementación o inferencia. No convertir pruebas de DDL en calidad del agente.
Fuentes y60 assets de diseño v1/pin44 copias del harness con hashes intactos. Git main/origin preservados y virtualenv sin dependencias de app nuevas. Portal: metadata mínima autorizada posteriormente, registro pendiente de login/audiencia/flujo, sin mutación. Detalle dot/portal-tracking.md.
