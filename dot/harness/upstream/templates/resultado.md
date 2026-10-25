# Resultado — REPLACE_TASK_ID / REPLACE_RUN_ID / ronda REPLACE

Estado de este formato: draft. Fuente del reporte: coder / ejecutor / dot (indicar).

## Identidad certificada por ejecutor

contract_version y SHA-256 del contrato; base_sha; candidate_sha; tree_oid; parent_candidate_sha si aplica; digest de inventario; versión/digest de harness; hashes de manifiesto, spec/revisión, aceptación/revisión, configuración y bundle de validación; CLI/version/hash y modelos efectivos.

## Tres resultados separados

- process_outcome: `succeeded | failed | timeout | unknown`; exit/signal, inicio/fin, duración.
- validation_outcome: `pass | fail | incomplete`; gate y reporte por test.
- delivery_outcome: `accepted | rejected | blocked`; causa y evidencia de dot. El coder no certifica accepted.

| Test ID / criterio | argv/cwd/env/runtime | Esperado / ejecutado | Resultado / exit | Artefacto + hash |
|---|---|---|---|---|
| REPLACE | REPLACE | REPLACE | REPLACE | REPLACE |

Pruebas NO ejecutadas: REPLACE (ninguna o razón). Skips/exclusiones y autorización previa: REPLACE. Cambios prohibidos/dirty/untracked/ignored y archivos protegidos: inventario/diff + hashes. Logs redactados, timeout y captura incompleta: REPLACE.

Uso/coste observado o `unknown` con motivo; presupuesto total restante y reparaciones consumidas. No tratar coste desconocido como cero. Restricciones/riesgos residuales y siguiente acción: REPLACE.

## Revisión dot (solo tras gate pass)

Por cada criterio: evidencia independiente y juicio. Riesgos y regresiones revisados. Decisión/autor/fecha y referencias de autoridad. Vincular exactamente candidate_sha, base_sha, hash de contrato y manifiesto, hashes de spec/aceptación/config/validadores, gate y artifacts.json. Si cambian código o inputs, esta aprobación no aplica; no sobrescribirla.

## Reanudación o bloqueo

Estado durable anterior/nuevo y operation ID; acción/target exactos; resultado `denied | pending | uncertain | confirmed`; causa; qué ya ocurrió; conciliación pendiente. No repetir un efecto incierto sin comprobarlo. Ubicación del trabajo preservado: REPLACE.

## Evidencia UI por fase

phase=development|independent_final; execution_status=executed|not_run + motivo. run_id/ronda, candidate_sha obligatorio final; dev sin commit usa null más fingerprint del snapshot. test IDs/resultados/viewport; Node/Playwright/browser/version/revisión/hash, suite/config/inputs y argv; JSON+HTML, screenshots clave/fallos, trace de fallo y logs runner/server/console/pageerror/network con paths+hashes. No afirmar capturas o traces inexistentes. server PID/origen y perfil/contextos efímeros; parada confirmada. deployment.mode, local_argv, publish_authorized y referencia separada (actual false).

## Entrega reproducible

Destino/decisión explícita, plan/hash, candidato SHA, versiones/hashes runtime/config, comando exacto Wrangler local y URL, estado/proceso para detener preview, tests realmente ejecutados/exclusiones y fases setup/inferencia/validación. Coste reportado/desconocido (no cero por omisión); requested_by/executed_by y execution_mode. Configuración permanente necesaria antes de publicar; no confundir config temporal de test con despliegue.

## AUTH-01 — autenticación MUST

Toda app nueva requiere autenticación por defecto. Antes de arquitectura: enfoque, roles y recursos protegidos REPLACE. Plan v3/contrato v5 fijan authentication y tests por grupo: unauthenticated, session_logout, authorization. Sin definición: blocked. Omitir solo por petición explícita del usuario, con excepción/razón/referencia verificadas; local/simple/demo no son excepción.

Checklist de entrega: verificar rutas/URLs/API sin sesión, login/sesión/logout y autorización según roles/propiedad del alcance; enlazar test IDs y resultados finales al SHA/plan exactos. Pasar check_delivery.py con reporte protegido; un fixture de identidad no es autenticación implementada ni prueba de producción. Conservar delivery_accepted=false hasta revisión dot. No proveedor, servicio, instalación ni migración implícitos. Ver docs/autenticacion.md del snapshot fijado.

Passwords, solo si se eligen: mínimo8 caracteres por defecto, permitir más largos, no numeric-only. Plan v4/contrato v6 fijan política común UI/backend/provisioning, hashing y rate limiting. Pruebas7rechaza/8acepta/mayoracepta en cada superficie aplicable; mayor mínimo solo con referencia explícita. Evidencia solo longitudes/resultados, sin credenciales. Ver docs/autenticacion.md0.8.

## Recibo de despliegue real

Version/config/candidato y hash de política/suite antes/después: REPLACE. Identidad y presencia de secretos: solo resultado booleano, jamás valores. Probes target/parámetros y fuente, CPU frente a wall por entorno, presupuesto/autorización CPU, assets reales y raíz, smoke autenticado por viewport, evidencia negativa/fix, limpieza autorizada: REPLACE. Referencias separadas a local, público, remoto autenticado y confirmación humana. No reemitir accepted con evidencia ajena/incompleta. Adjuntar policy/receipt v1 y salida check_release.py; no despliegue implícito.
