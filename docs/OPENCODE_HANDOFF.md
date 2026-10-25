# Handoff a OpenCode · GrowWithAI r4
Estado vigente: backend local autorizado por el usuario con OpenCode GO; ejecución por tarea supervisada sin UI nueva. Guard y configuración offline ya implementados; estado actual en dot/STATUS.md. No esperar al portal para preparar el frente Python.

Checkpoint de implementación: driver local file-map/no-tools operativo; configuración/SQLite/campañas/auth núcleo/versiones/exportación integrados y probados. Regresión de siete suites:123/123 (incluye guard27); ver dot/implementation/regression-after-T-07B.json. T-08A registro manual de distribución en curso; modelo GO exacto. Secciones A/B describen la secuencia inicial ya ejecutada, no una prohibición de continuar el backend autorizado. HTTP/UI y modelo app aún pendientes.

## Orden de lectura
1. [AGENTS.md](../AGENTS.md): límites actuales y roles; prevalece la instrucción del usuario.
2. [Decisiones](../dot/DECISIONS.md) y [checkpoint](../dot/STATUS.md): alcance confirmado, sin repetir entrevista.
3. [Índice specs r4](specs/sponsor-materials/README.md), después overview → user-stories → acceptance. La matriz AC es la autoridad de aceptación.
4. technical-design → data-model → schema-proposal.sql y configuración [config/README.md](../config/README.md). SQL es referencia, no migración aplicada.
5. tasks.md y la única tarea asignada; leer ux/visual-design si toca UI. [Propuesta del driver](../dot/ADAPTER_PROPOSAL.md) es preparación, no motor Python ya verificado.

Los documentos de etapas anteriores no sustituyen r4. Scope: campaña general, empresas/contactos, mismo email para todos y registro manual por destinatario; no sender, bandeja o personalización. OpenRouter app y modelo coder son decisiones separadas; .env no se lee por el coder o tests.

## A. Preparación del driver, antes de entregar código al coder
Primer paso acotado: **HARNESS-PY-01 / perfil y contrato offline**, responsabilidad del coordinador. Producir solamente `dot/driver-python-profile.md` y `dot/driver-python-plan.json` (nuevos), con agente por contrato y modelo coder ya elegido `opencode-go/deepseek-v4.1-flash` por la suscripción GO del usuario, file-map sin herramientas, rutas exactas, controles/fixtures protegidos, Python/virtualenv, límites y matriz de pruebas falsas. Estado draft si falta base/modelo/frontera real; no rellenar hashes/aprobaciones ficticias.

Criterios: identificar y retirar del perfil la dependencia implícita survey-coder/GO/UI estática; definir validador backend y puerto/proceso propios de un futuro preflight; no usar servicio global49374, configuración personal o secretos; conservar deny-all hasta contrato válido. Preparar pruebas de CLI/servidor falsos, modelo equivocado, ruta extra, validador alterado, timeout y reentrada. Esto **no** implementa app ni demuestra aislamiento/compatibilidad real; cambiar código del adaptador es otra tarea acotada posterior al perfil revisado.

Antes del primer run real: base Git acordada (hoy repo sin commits, no commit automático), modelo efectivo principal/auxiliar GO verificado y uso dentro de la suscripción existente, sin compra/recarga/fallback, driver compatible/controles externos/aislamiento comprobados y snapshot de entradas congelado. No ampliar permisos persistentes ni ejecutar el adaptador upstream de UI como si sirviera para Python. Una tarea/un writer, ronda0 + dos reparaciones; después blocked, sin cambiar modelo/tests para forzar pase.

## B. Primera tarea de app, cuando el driver y entorno estén listos
Asignación mínima: **T-02A / configuración offline**, subunidad de T-02 y AC-24. Solo crear `app/__init__.py` y `app/config.py`. Dependencias/lock/tests los prepara y congela previamente el coordinador en T-02; no dar permiso de instalación o edición de tests al coder por esta guía.

Entradas: contrato congelado, config de ejemplo y objeto de variables **sintéticas** que entrega el test; no abrir .env real. Interfaz propuesta: `load_config(env: Mapping[str, str], config_path: Path) -> AppConfig`; sin cliente SDK, red o efectos de arranque. La carga del .env del operador en servidor es una tarea posterior explícita.

Aceptación acotada:
- Disabled por defecto: validar estructura sin clave/modelo y sin crear cliente ni request.
- Enabled: clave/modelo explícitos requeridos; error por nombre de campo, nunca valor. Sin elegir modelo económico por cuenta propia o fallback.
- Booleanos/enteros/rangos y coherencia de límites según config/README.md; endpoint fijo OpenRouter, presupuesto económico en API key sin campo USD obligatorio.
- Ningún log/exception/repr que exponga clave ficticia; ningún import que arranque app, lea .env o invoque LLM.
- Modelo configurable pendiente no bloquea esta unidad offline; la evaluación real sí lo espera.

Prueba protegida prevista: `tests/test_config.py` escrita por coordinador y copiada fuera del writable; casos disabled, faltante, límite inválido, no fallback, no red y redacción. No ejecutar todo el backlog o añadir UI/tracking/SQLite en esta tarea. El revisor verifica y acepta; el coder solo reporta archivos/resultados.

## Comandos: disponibles versus futuros
Desde la raíz del repo, hoy (sin inferencia ni app):
```sh
.venv/bin/python scripts/verify-specs.py
# verify-preparation.py: aplazar hasta ajustar su comparación literal de plantilla (ver nota al final).
.venv/bin/python --version
.venv/bin/python -m pip check
```
Los dos verificadores son de documentos/setup/DDL en memoria; no tests de aplicación. No reinstalar el entorno si esas comprobaciones pasan. OpenCode se ejecuta únicamente por tarea acotada con sesión GO/no-tools y controles vigentes; no lanzar backlog completo.

Después de T-02/contrato, previsto para el validador, **no disponible ni ejecutado hoy**: `.venv/bin/python -m pytest -c /ruta/control/pytest.ini /ruta/control/tests/test_config.py`. Esa ruta es ejemplo explícito: el coordinador la sustituye por el control protegido real y fija argv/cwd/env/runtime/hash/timeout antes de correr. No resolver suite/config desde fuentes editables del candidato. Config offline no requiere servidor UI. Dev/Playwright aparecen en las tareas posteriores; no se adjudican resultados a un comando no ejecutado.

## Pendientes genuinos y trabajo paralelo
- Modelo LLM económico de app aún por elegir; presupuesto monetario en API key ya decidido. No inferencia hasta modelo/prueba autorizada.
- Driver/base y controles antes de run; el modelo coder ya está elegido/configurado: `opencode-go/deepseek-v4.1-flash`. No significa que el alcance esté sin confirmar.
- Detalles visuales B v2 por aprobar antes de coder UI; B v1 ya elegida. No bloquea esta preparación o backend offline.
- DASH-01 es frente separado: metadata mínima autorizada, acceso/audiencia/mecanismo portal aún por verificar. No es dependencia de HARNESS-PY-01/T-02A. En esta pasada no investigar ni modificar portal.

Reporte esperado al cerrar cualquier unidad: tarea/run/ronda, rutas tocadas, pruebas realmente ejecutadas y not_run, errores/riesgos y estado de validación; sin claves o afirmaciones de enviado/publicado. Sin commit/push/deploy/Library automáticos.

## Modelo coder elegido y verificado en catálogo GO
Decisión explícita del usuario: DeepSeek 4.1 Flash con la suscripción OpenCode GO. Catálogo real `opencode models --standalone` terminó con exit0 y contiene coincidencia exacta **opencode-go/deepseek-v4.1-flash**. Otras rutas free/OpenRouter son proveedores diferentes y no sustituyen esta elección. Disponibilidad observada = presente en catálogo; no se probaron inferencia, cuota o facturación efectiva.

Configuración exclusiva del proyecto `opencode.json`: model y small_model apuntan al mismo ID exacto, sin fallback auxiliar a otro modelo; permission permanece deny. No se modificó configuración global/autenticación/suscripción. Esto selecciona modelo, no habilita herramientas o ejecución. El adaptador aún debe verificar agente/sesión/modelo efectivo antes de run; no se ejecutó ni se habilitó en esta tarea.

La app sigue usando OpenRouter con APP_LLM_MODEL por elegir; no inferir que el modelo coder sea también el de la app. Presupuesto app en API key del usuario, sin leerla.

Nota de compatibilidad del verificador: scripts/verify-preparation.py línea14 compara opencode.json byte por byte con el ejemplo upstream sin modelo; tras esta selección autorizada esa igualdad literal deja de aplicar aunque permission siga deny. No se modifica el verificador en esta tarea restringida a configuración+guía. Antes de reutilizarlo, actualizar ese control en tarea propia para validar el modelo GO elegido y los permisos conservados, manteniendo pin del ejemplo intacto. Las comprobaciones puntuales de esta selección no equivalen a aprobar ejecución del driver o app.

Actualización de control: la comparación literal del verificador fue sustituida por checks del GO exacto y permiso deny, bajo autorización de adaptación local. Model coder ya decidido. El progreso real actual prevalece sobre pasos iniciales descritos como preparación.
