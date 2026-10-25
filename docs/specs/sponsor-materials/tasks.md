# Backlog ejecutable por tareas · r4
Estado actualizado: recorrido DEMO conectado y validado; la IA real y los pendientes específicos no se dan por terminados. Evidencia en dot/implementation/FULL-DEMO-E2E-01 y HTTP-REGRESSION-FINAL. Alcance ya confirmado, no repetir entrevista de envío. Un writer y tarea pequeña; coder no acepta entrega. Pruebas/fixtures y controles los prepara/revisa coordinador y congela fuera del writable antes del run; listarlos no autoriza al coder a editarlos. Cada ruta listada es (nuevo) salvo requirements-app.in y documentos existentes citados.

## Preparación común
Definir base Git con usuario (repo sin commits), snapshot/allowlist exactos, modelos coder/principal/auxiliar autorizados, lock/runtime, presupuesto de cuota permitido y frontera OS/controles externos. No instalación global, secretos, inference o cambios de servicio implícitos. Generación coder ronda0 + dos reparaciones, después blocked. Las tareas dependientes no se marcan hechas por specs.

## T-01 · Detalle visual B v3 aprobado
- Estado: B/v3 aprobado por el usuario; opción/versión/hashes en dot/design/gwa-ui-v3/decision.json.
- Ejecutor/cierre: coordinador + usuario
- Depende de: ninguna (alcance confirmado)
- Archivos esperados: `dot/design/gwa-b-v2-a.html`, `dot/design/gwa-b-v2-b.html`, `dot/design/gwa-b-v2-evidence.json`, `dot/design-decisions/gwa-b-v2.json`
- Criterios: AC-28; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no, aprobación humana real
- Aceptación específica: Presentar dos variantes de detalle dentro de estilo B elegido; Campañas/Empresas/Seguimiento/editor y lote/corrección en desktop/móvil. Capturas/hash y aprobación humana exacta. No reabrir alcance o afirmar aprobado lo no visto.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-02 · Entorno, configuración y lock
- Estado: virtualenv/lock/config y bootstrap implementados; runtime DEMO validado y activo; pip check correcto. No lectura de .env real ni inferencia de app.
- Ejecutor/cierre: coordinador para dependencias/controles; OpenCode solo módulos permitidos después
- Depende de: HARNESS-PY-01 para coder; trabajo de lock/preparación puede ser coordinador antes
- Archivos esperados: `requirements-app.in`, `requirements-app.lock`, `pyproject.toml`, `app/config.py`, `tests/test_config.py`
- Criterios: AC-24; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para instalación limpia; sí para config con valores ficticios
- Aceptación específica: Resolver Python3.11/virtualenv y lock exacto con hashes; instalar solo .venv tras tarea autorizada. Validar disabled/modelo/secretos/endpoint y no red al validar. .env del usuario nunca leído por tests; cliente falso.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-03 · SQLite, empresas y contactos
- Estado: SQLite/organizaciones/contactos y UI conectados en recorrido DEMO con DB real aislada; roles y varios contactos preservados.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-02
- Archivos esperados: `app/storage.py`, `app/migrations/001_initial.sql`, `app/companies.py`, `tests/test_schema.py`, `tests/test_companies.py`
- Criterios: AC-03, AC-04; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no, SQLite real
- Aceptación específica: Implementar DDL adaptado a migración revisada; transacciones/FK/archivo/dedup, nombres similares sin merge. Fixture dos empresas/tres contactos example.invalid, sin datos reales. No convertir alta en alianza.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-04 · Campañas y destinatarios
- Estado: campañas, selección explícita de contactos y snapshots conectados; 6/6 HTTP de selección y recorrido DEMO integrado.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-03
- Archivos esperados: `app/campaigns.py`, `app/recipients.py`, `tests/test_campaigns.py`
- Criterios: AC-05, AC-06; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para persistencia
- Aceptación específica: Objetivo/tema/segmento/tono/formatos, suite académica, N contactos y snapshots. No personalización, no envío, público sin destino. Control revision y duplicate email campaña.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-05 · Fuentes RAG e historia pertinente
- Estado: parcial: ingestión y recuperación unitarias disponibles; RAG nativo suspendido por OpenMP. Aislamiento solo mocks; recuperación/historia agéntica reales pendientes.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-04; fixtures históricos se crean por coordinador sin esperar UI
- Archivos esperados: `app/ingestion.py`, `app/retrieval.py`, `app/history_context.py`, `tests/test_retrieval.py`, `tests/test_history_context.py`
- Criterios: AC-07, AC-08, AC-09, AC-10; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para vector/SQLite real y calidad de recuperación; sí para branches con fixture
- Aceptación específica: Fuente v0.2/manifest citables; embeddings locales modelo/revisión fijados antes de descarga; top-k/ampliación acotados. Historia por tema/campaña prioriza distribuido/respuestas y distingue borrador; inyección no ejecutable.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-06 · Grafo, generación y revisión
- Estado: parcial: runs persistentes y generación DEMO de seis piezas; grafo y revisión/generación agéntica reales pendientes.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-05
- Archivos esperados: `app/state.py`, `app/graph.py`, `app/generation.py`, `app/review.py`, `app/prompts.py`, `tests/test_graph.py`, `tests/test_resume.py`, `tests/test_failures.py`, `tests/test_limits.py`
- Criterios: AC-11, AC-12, AC-13, AC-14, AC-25; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para calidad LLM real, sí para control con transporte falso y SQLite real
- Aceptación específica: Cuatro formatos/variantes, evidencia, preguntas e historia snapshot; checks/reintentos/timeout/token budget, aislamiento campaña y reinicio real. SDK retry único. Modelo app pendiente no impide transporte falso; real no se llama sin elección/prueba autorizada.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-07 · Versiones, aprobación y export
- Estado: versiones, aprobación humana, exports y descargas exactas conectados y comprobados en DEMO; sin validar flujo real de IA.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-06
- Archivos esperados: `app/versions.py`, `app/approval.py`, `app/export.py`, `tests/test_versions.py`, `tests/test_approval.py`, `tests/test_export.py`
- Criterios: AC-15, AC-16; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para filesystem/DB reales
- Aceptación específica: Hashes/manifiesto exactos, error material bloquea, editar nueva versión no cambia pasado. Export seguro/idempotente/crash reconciliado; ningún evento de envío/publicación automático.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-08 · Distribución externa registrada manualmente
- Estado: registro público y envío externo manual conectados; idempotencia, doble clic y duplicados verificados. Sin envío/publicación real; UI de corrección auditada pendiente.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-07
- Archivos esperados: `app/distribution.py`, `tests/test_distribution.py`, `tests/test_batch_idempotency.py`
- Criterios: AC-17, AC-18, AC-19, AC-20; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para transacciones/concurrencia/DB reales
- Aceptación específica: Email general por destinatario o lote con preview/declaración; versión/fecha/contact snapshot, transacción atómica/idempotente. Publicación sin destinatario. Texto externo no falsifica aprobación; nota sin texto no finge versión.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-09 · Seguimiento, duplicados y correcciones
- Estado: hilo por organización y respuestas/notas conectados, con historia exacta y correcciones conservadas; UI de correcciones e integración del historial en agente real pendientes.
- Ejecutor/cierre: OpenCode + revisor
- Depende de: T-08
- Archivos esperados: `app/followup.py`, `app/history_views.py`, `tests/test_followup.py`, `tests/test_distribution_duplicates.py`, `tests/test_audit.py`
- Criterios: AC-21, AC-22, AC-23; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para integridad de historial real
- Aceptación específica: Respuesta/nota/próximo paso manuales, duplicado advierte y reenvío deliberado con razón; cadena de correcciones conserva original, sin cross-campaign ni delete. Proyección vigente, no opens/read inferidos.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-10 · Mesa editorial y rutas protegidas
- Estado: interfaz B/v3 y rutas protegidas conectadas para recorrido DEMO; sin afirmar acabado del MVP con IA real.
- Ejecutor/cierre: OpenCode + validador independiente
- Depende de: T-01 aprobado; AUTH-01; T-04/T-09 para flujo completo; UI parcial puede usar fixtures protegidos
- Archivos esperados: `app/web.py`, `app/templates/login.html`, `app/templates/campaigns.html`, `app/templates/companies.html`, `app/templates/tracking.html`, `app/templates/editor.html`, `app/static/app.css`, `app/static/app.js`, `tests/ui/test_workflow.spec.ts`, `tests/ui/test_auth.spec.ts`
- Criterios: AC-26, AC-27; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no, navegador/servidor/candidato reales
- Aceptación específica: Implementar solo B v2 aprobado, nada de sender. Bind loopback/Host/Origin/CSRF/sesión backend; keyboard/focus/mobile/error/loading/restart; Playwright development y final separados.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## T-11 · Evaluación y demo
- Estado: DEMO funcional:33 checks navegador+3 reinicio;90 pruebas HTTP/UI. Evaluación real de RAG/modelo y video del usuario pendientes.
- Ejecutor/cierre: coordinador + usuario; OpenCode solo correcciones por contrato
- Depende de: T-10; modelo LLM exacto antes de evaluación real
- Archivos esperados: `docs/EVALUATION.md`, `docs/DEMO.md`, `tests/test_end_to_end.py`
- Criterios: AC-29; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no, flujo real y modelo seleccionado
- Aceptación específica: Ejecutar matriz obligatoria y evaluaciones reales autorizadas; registrar not_run si falta modelo. Documentación prompts/iteraciones/learning y demo<=5min sin envío/publicación. Ningún push/entrega de curso automático.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## AUTH-01 · Password/sesión local
- Estado: password/Argon2, HTTP/CSRF y UI conectados; persistencia de contraseña y nueva sesión tras reinicio verificadas con datos sintéticos.
- Ejecutor/cierre: OpenCode + validador independiente
- Depende de: T-02/T-03; prueba UI final con T-10
- Archivos esperados: `app/auth.py`, `scripts/manage_operator.py`, `tests/test_auth.py`, `tests/test_password_policy.py`
- Criterios: AC-01, AC-02; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no, autenticación implementada real
- Aceptación específica: Hash Argon2id parámetros probados, singleton local, setup/getpass/reset local supervisado; no contraseña real en reporte. 7/8/>8 en UI/backend/provisioning, sesión/logout/expiry/CSRF/origin/autoridad. No servicio externo.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## HARNESS-PY-01 · Preparación de driver Python offline
- Estado: adaptación local file-map/no-tools operativa; fake CLI y guard27/27; no driver Python general ni aceptación Git final
- Ejecutor/cierre: coordinador; cambio de código requiere tarea acotada autorizada
- Depende de: ninguna; no código en esta entrega de specs
- Archivos esperados: `dot/driver-python-profile.md`, `dot/driver-python-plan.json`, `tests/harness/test_python_profile.py`
- Criterios: AC-29; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no para preflight real; offline no prueba ejecución backend general
- Aceptación específica: No ejecutar driver survey como Python. Parametrizar agent/model exactos/allowlist, validators backend, proceso/puerto propio, file-map mínimo/controles externos y aislamiento. Primero fixtures/CLI falsos; no cambiar repo compartido/permisos/modelo. Base Git acordada por usuario antes de coder.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## DASH-01 · Registro/tracking del proyecto en portal
- Estado: pendiente
- Ejecutor/cierre: coordinador/publisher autorizado, nunca coder
- Depende de: metadata mínima autorizada; pendiente login/audiencia/duplicados y flujo soportado verificados, sin ampliar exposición/permisos
- Archivos esperados: `dot/portal-tracking.md`, `dot/portal-event-example.json`, `dot/portal-registration-plan.md`
- Criterios: AC-30; ver acceptance.md
- Sensible: sí
- Cerrable con dobles: no, integración destino/autenticación reales
- Aceptación específica: DASH obligatorio según pin; metadata/eventos saneados y journal local; portal central separado del despliegue app local. API/publicador no implementados en pin; no registrar/subir specs o claves hoy. Capturar cursor/stale/unknown y entrega ligada a SHA/gate; registry por administrador.
- Invariante: ningún envío/publicación de contenidos ni pérdida del historial o modificación de fuentes/controles. Inferencia solo en tarea con modelo autorizado; DASH-01 solo metadata mínima autorizada tras verificar acceso/audiencia/mecanismo. Cambiar archivos permitidos exige otro contrato.

## Contratos y validación
Antes de cada coder run, el coordinador completa copia congelada de spec/acceptance/config/harness manifest y tests con hashes/base/modelos/argv/cwd/env/timeout fuera de writable. No usar ejemplo upstream con REPLACE/null como ready. Cambios de dependencia/config/migración/runner son tarea específica revisada, no permisos generales del coder. Ningún modelo inferido de otro piloto. Mismos IDs de test de acceptance; final independiente por candidato exacto y no fixtures de auth como evidencia real.
No despliegue de app: uvicorn loopback futuro, sin Cloudflare. Portal/tracking es metadata y eventos, no aplicación; registro metadata mínima autorizado por usuario; sync/flujo real pendiente de login/audiencia/mecanismo verificados y sin ampliar permisos/exposición. Library no autorizada. Índice no crea servicios.

## Descomposición operativa vigente
Antes de la siguiente inferencia consultar [dot/TASK_SIZING.md](../../../dot/TASK_SIZING.md) y evidencia task-sizing-audit.json. Los T-05/T-06/T-10 anteriores son capacidades paraguas, no tareas para una sola llamada. Ejecutar subunidades de esa tabla con un solo resultado verificable, rutas/tests exactos,600s y contador de dos reparaciones. B/v2 y primera búsqueda excedieron la granularidad recomendable; evidencia de timeout conservada, causa no demostrada. Sin modificar harness compartido.
