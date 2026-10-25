# GrowWithAI · instrucciones del consumidor dotHarness

## Alcance
Specs r4 y backend local autorizados mediante OpenCode GO; UI nueva sigue pendiente de revisión. No implementar envío/publicación o ampliar alcance. Índice canónico docs/specs/sponsor-materials/README.md. Campañas generales + empresas/contactos + seguimiento manual; envío fuera ya confirmado. Coordinador conversa requisitos, congela controles y revisa evidencia; OpenCode implementa una tarea pequeña con allowlist exacta y no acepta su propio trabajo.
Preservar Git/origin, referencias y definición social. No git init, commit, push, despliegue, publicación ni envío externo. No abrir soluciones modelo del curso. No secretos, nuevas credenciales ni permisos persistentes. Python 3.11 con virtualenv en .venv; sin paquetes globales.

## Harness fijado y gates
Índice dot/README.md; identidad/hashes dot/harness/manifest.json. Snapshot físico bajo dot/harness/upstream, sin herencia viva. El AGENTS de mantenimiento upstream no se copia. Las plantillas son referencias, no controles aprobados ni permisos de ejecución.
opencode.json está deny-all. No lanzar driver upstream como ejecutor Python: es de UI estática. Se autoriza adaptación local file-map/no-tools por invocación y backend con GO exacto; mantener deny-all persistente y validar controles antes de integrar código. Conservar configuración global del usuario sin leer secretos ni cambiar modelos.
Antes de run: revisar definición, modelo coder/presupuesto autorizados, base Git acordada, controles externos congelados, aislamiento OS comprobado y allowlist de archivos. Una tarea/un writer; generación inicial y máximo dos reparaciones; agotamiento bloquea. Reconciliar operaciones inciertas antes de reintentar. Permisos de CLI no equivalen a sandbox OS.
Antes de UI: dos mockups versionados desktop/móvil y aprobación explícita de opción/versión/hashes. Auth por contraseña propia/simple y operador local especificados; pendiente implementación/pruebas, no decisión de alcance. DASH-01 requerido con dirección portal central; metadata mínima ya autorizada; acceso/audiencia/mecanismo reales pendientes, separado de app local y no bloqueante del handoff Python. No publicar por esta definición. App/almacenamiento locales y LLM por OpenRouter por decisión del usuario. Modelo app pendiente; preferencia por modelos baratos. Presupuesto app controlado por el usuario en su API key, que ingresará por su cuenta en .env. No leer claves ni ejecutar inferencia de app mientras modelo OpenRouter siga pendiente. Coder GO autorizado por usuario y modelo efectivo verificado; no fallback.
Perfil general dot/PYTHON_AGENT_PROFILE.md; requisitos específicos docs/specs/sponsor-materials; lecciones observadas dot/LESSONS.md. Coder no modifica controles, dot/, referencias ni Git. Cambiar alcance legítimo exige otro contrato. Distinguir pruebas funcionales, UI y calidad real del modelo.

## Comandos disponibles
- `sh scripts/setup-local.sh`: prepara virtualenv local, requiere red PyPI; no app.
- `.venv/bin/python scripts/verify-preparation.py`: verifica setup/procedencia sin inferencia.
- `.venv/bin/python --version` y `.venv/bin/python -m pip check`.
- `.setup-venv/bin/python -m virtualenv --version`.
- `opencode --version`: binario existente; puede necesitar acceso a su log normal.
Backend parcial y tests protegidos disponibles: `.venv/bin/python scripts/run_protected_tests.py --suite guard` y suites config/storage/campaign/auth/versions. Cada suite prueba un snapshot aislado sin red. UI/HTTP/LLM de app y MVP completo no verificados. No presentar preparación ni unit tests como validación end-to-end.

## Granularidad vigente de OpenCode
Antes de cada nueva tarea/reparación aplicar dot/TASK_SIZING.md: una capacidad pequeña verificable, no simplemente un archivo; una sola inferencia activa por host,600s máximo y dos reparaciones tras inicial. Contadores por familia en task-sizing-audit.json; no usar sufijo de carpeta para reiniciarlos. No inventar límite numérico de LOC/tokens/archivos. Conservar pin y controles.
