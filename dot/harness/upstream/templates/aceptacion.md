# Aceptación — REPLACE_TASK_ID

Estado: draft. Revisión: REPLACE. Preparada por dot; acordada con: REPLACE.

| Criterio | Ejemplo positivo / borde / negativo | Test IDs | Obligatorio |
|---|---|---|---|
| AC-01 | REPLACE | TEST-01 | sí |

## Pruebas y entorno congelados

- Bundle externo: archivos y SHA-256; almacenado fuera del área editable del coder.
- Runtime: ruta permitida, versión y hash del ejecutable; sin instalaciones implícitas.
- Por comando: argv exacto, cwd de exportación del candidato, env permitido, timeout y test IDs esperados.
- Códigos de salida, resultados esperados e inventario total de tests: REPLACE.
- Regresiones obligatorias: REPLACE.
- Salidas permitidas: scratch externo y formato/recuento esperados.
- Exclusiones previas: ninguna / lista con motivo y autorización. Nunca omitir un criterio obligatorio.

## Gate y revisión

Requiere identidad exacta, entradas/validadores íntegros, alcance permitido y todas las pruebas obligatorias ejecutadas y aprobadas. Cero tests, faltantes, skip inesperado o reporte malformado = incomplete/fail. Dot revisa además requisitos y riesgos; ningún mensaje del coder puede convertir fallo en aceptación.

El hash se registra en el contrato; cualquier cambio genera revisión y run nuevos.

## UI obligatoria

Playwright independiente sobre SHA exacto; suite/config/hash/runtime/browser fijados y contexto nuevo headless, servidor local propio, sin navegador/perfil del usuario ni CUA. Matriz criterio→test IDs/viewports/estados screenshot; JSON+HTML, screenshots clave/fallos, trace de fallos y logs runner/server/console/pageerror/network. Registrar not_run y motivo si no corrió. Un dev run no sustituye gate final; salidas fuera del área editable. Validar deployment.mode y autorización separada de publish.

## UI: trazabilidad visual

Opción/version/hash y aprobación explícita REPLACE; criterio→estado desktop/móvil→captura/mockup→test ID REPLACE. Verificar puntero, teclado/foco y ausencia de overflow. Un test verde no sustituye aprobación visual humana. Cambio visual material invalida la aprobación para la nueva tarea.

Regresiones UI obligatorias cuando exista estado persistido: Back→recarga→Resume restaura vista/respuestas; editar→resultados recalcula; storage denegado/corrupto y reset. Vincular cada una a test ID congelado antes de implementar; la política no afirma ejecución en un consumidor hasta tener evidencia.

DASH-01: incluir actualización con cursor/identidad, replay/idempotencia/huecos, stale, unknown/not_run, acceso read-only/saneamiento y aceptación ligada a SHA/gate/revisión. Estas son pruebas futuras por proyecto; no afirmar ejecución por existir el contrato.

## AUTH-01 — autenticación MUST

Toda app nueva requiere autenticación por defecto. Antes de arquitectura: enfoque, roles y recursos protegidos REPLACE. Plan v3/contrato v5 fijan authentication y tests por grupo: unauthenticated, session_logout, authorization. Sin definición: blocked. Omitir solo por petición explícita del usuario, con excepción/razón/referencia verificadas; local/simple/demo no son excepción.

Checklist de entrega: verificar rutas/URLs/API sin sesión, login/sesión/logout y autorización según roles/propiedad del alcance; enlazar test IDs y resultados finales al SHA/plan exactos. Pasar check_delivery.py con reporte protegido; un fixture de identidad no es autenticación implementada ni prueba de producción. Conservar delivery_accepted=false hasta revisión dot. No proveedor, servicio, instalación ni migración implícitos. Ver docs/autenticacion.md del snapshot fijado.

Passwords, solo si se eligen: mínimo8 caracteres por defecto, permitir más largos, no numeric-only. Plan v4/contrato v6 fijan política común UI/backend/provisioning, hashing y rate limiting. Pruebas7rechaza/8acepta/mayoracepta en cada superficie aplicable; mayor mínimo solo con referencia explícita. Evidencia solo longitudes/resultados, sin credenciales. Ver docs/autenticacion.md0.8.

## Verificación de release0.9

- RUNTIME-COMPAT-01: sonda autorizada con parámetros reales en target; local no certifica remoto. CPU-01: CPU y wall/local y target separados, fuente, límite previo/nuevo y aprobación de subida.
- DEPLOY-ROOT-01: raíz con URL original/assets reales, sin rewrite del stub; fallo previo reproducido con mismo expected congelado y pase tras fix.
- DEPLOY-AUTH-01: independiente login→raíz/panel→API→logout→URL/API anónima denegada, desktop/móvil si UI. Separar checks públicos de E2E autenticado y confirmación humana.
- Recibo: candidato/plan/policy/config/version exactos, identidad y presencia de secretos sin valores, verificadores íntegros antes/después y limpieza de sondas autorizada. Pasar check_release.py; delivery_accepted sigue false hasta revisión dot. No copiar salida como expected ni permitir skip/faltantes.
