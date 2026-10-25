# Workflow y piloto separado

## Estados explícitos

Este vocabulario es propuesto; no hay motor implementado.

| Transición | Condición |
|---|---|
| `draft → destination_decided` | Usuario elige destino explícito antes de arquitectura/spec técnica; stack/LLM runtime en plan protegido |
| `destination_decided → design_review` (UI) | Dos o más mockups versionados con estados relevantes desktop/móvil y foco; pendientes de decisión del usuario |
| `design_review → design_approved` (UI) | Aprobación explícita del usuario de opción/versión/hashes, vinculada a spec y aceptación |
| `design_approved → ready` (UI), `destination_decided → ready` (otros) | Spec/aceptación acordadas; contrato válido, hashes reales, modelos/límites/autoridad explícitos. En UI aprobación visual vigente |
| Definición de app nueva → `ready` | Plan v3 con autenticación especificada y pruebas previstas, o excepción explícita del usuario. Contrato v5 congela la misma política; ver autenticacion.md |
| `ready → prepared` | Lock, base limpia, snapshot íntegro, compatibilidad, validadores y frontera OS comprobados |
| `prepared → running` | Persistir intención de launch/operation ID; iniciar solo adaptador autorizado y guardar proceso/sesión propios |
| `running → candidate_ready` | Proceso e hijos terminados; captura completa, diff permitido, candidato congelado |
| `candidate_ready → validating` | Exportación limpia del SHA e inputs/validadores íntegros |
| `validating → review_pending` | Todos los checks deterministas obligatorios pasan con evidencia completa |
| `review_pending → accepted` | Dot revisa requisitos/riesgos y registra aprobación de esa identidad |
| `validating/review_pending → rejected` | Fallo determinista o incumplimiento razonado |
| `rejected → prepared` | Nueva ronda dentro de límites; diagnóstico acotado y candidato anterior intacto |
| Cualquier no terminal → `blocked` | Falta autoridad, compatibilidad, presupuesto, integridad o datos; guardar causa y punto de retorno |
| `running → outcome_unknown` | Interrupción con resultado o proceso incierto; no relanzar |
| `outcome_unknown → candidate_ready/blocked` | Reconciliar proceso/sesión, archivos e identidad |
| `blocked → ready/prepared/candidate_ready` | Causa resuelta, contrato intacto y punto seguro conciliado; revalidar evidencia antes de avanzar. Si cambió, nuevo run `draft` |
| Cualquier no terminal → `cancelled` | Parada confirmada; si no se confirma, `outcome_unknown` |

`accepted` y `cancelled` son terminales; no se reescriben. Un aceptado modificado requiere otro run; el anterior certifica únicamente su SHA.

Un cambio visual material abre nueva revisión y deja la nueva versión en design_review; no reutilizar aprobación anterior. El coordinador verifica decisión humana; el adaptador0.4 comprueba plan, opción/version y hashes antes del CLI. Ver [arranque](arranque.md).

## Gate determinista primero

1. Verificar identidad, entradas congeladas, modelo/config efectivos y compatibilidad. Rechazar sentinelas de plantilla. No activar proveedor real sin autorización.
2. Inventariar committed y estado completo: `git status --porcelain=v2 -z --untracked-files=all`, staged/unstaged y diff de árboles **base→candidate**, además de archivos ignored. No limitarse a HEAD o triple punto. Revisar rutas, tipos, modos, renames, borrados y hashes protegidos.
3. Bloquear todo cambio fuera de allowlist y dirty/untracked/ignored inesperado para revisión de integridad, sin reparación automática. Proteger tests y cómo se seleccionan/ejecutan, incluyendo package.json/config/scripts. Guard/checker siempre de origen confiable externo; conservar cambios rechazados sin borrarlos.
4. Ejecutar validadores congelados contra el SHA limpio. Registrar argv/cwd, entorno no secreto, runtime, inicio/fin, timeout, exit, IDs y conteos esperado/ejecutado, skips/exclusiones y logs. Cero tests, faltantes o resultados malformados no son pass. Excluir exige autorización previa y nunca elimina criterios obligatorios.
5. Confirmar identidad e integridad después de las pruebas. Solo un gate íntegro con todos los criterios obligatorios pasa a revisión dot.
6. Dot evalúa requisitos, bordes, regresiones y riesgos; no repara ni cambia aceptación durante revisión. Puede rechazar verde; no convertir rojo en aceptación. Problema de spec/test exige nuevo contrato, no debilitar pruebas.

## Reentrada y reparación

Una tarea activa por host y un writer por worktree. Lock local registra host, PID+inicio, run/worktree; no recuperarlo solo por antigüedad. Confirmar parada de procesos e hijos antes de tomarlo. Estado incierto bloquea otro writer.

Operation ID = run + ronda + acción. Antes de crear branch/worktree buscar lo ya creado y verificar repo, ruta real, propietario, base y ronda; reutilizar únicamente si coincide, preservando cambios. No repetir create ni forzar reset/remove. Antes de repetir launch reconciliar registro, proceso y sesión; no usar “última sesión” o `--continue` global. `--session` local puede crear si no existe: comprobar identidad/existencia antes de reanudar. Resultado desconocido nunca autoriza relanzar.

Cada reparación conserva candidato, resultados y revisión previos y crea ronda siguiente. Puede partir del candidato anterior inspeccionado, pero el diff permitido sigue comparándose con `base_sha` contractual original; registrar `parent_candidate_sha`. No heredar gate/aprobación. Máximo dos reparaciones después de la generación inicial: ronda 0 inicial, 1 primera reparación, 2 segunda reparación. Si falla la última reparación permitida (dos por defecto, o menos si el contrato lo limita), guardar `blocked` y escalar al usuario antes de otro intento. No crear otro run ni reiniciar el contador para eludir el tope. Una ampliación requiere autorización humana explícita y un nuevo contrato/override trazable, con evidencia previa intacta; nunca modifica silenciosamente el contrato activo. Cambiar requisitos, aceptación o config abre nuevo contrato/run. No prometer exactamente una vez: reconciliar efectos para evitar duplicados lógicos.

## Gate de passwords0.8

Plan v4/contrato v6 declaran si se usan passwords. Si sí, default mínimo8 y sin truncación silenciosa; mayor mínimo requiere referencia explícita. check_plan valida la política y test IDs comunes; check_delivery exige evidencias de7/8/mayor (o m-1/m/>m con mínimo mayor) en UI aplicable/backend/provisioning, sin contraseñas crudas. Se conserva la autenticación MUST, hashing, rate limiting, dos reparaciones y pins existentes. No es un acelerador ni implementación de login.

## Gate de autenticación0.7

Plan v3 exige autenticación desde definición y antes del CLI, también con --preflight-only. Pendiente/ausente bloquea; omisión requiere petición explícita humana. Antes de entrega ejecutar check_delivery.py sobre reporte protegido del SHA/plan exactos y revisar la frontera de autenticación implementada, no solo fixtures. Ver [política](autenticacion.md). El gate de evidencia no implementa auth ni reemplaza revisión dot; controles v1/v2 se conservan solo para corridas legacy, no para proyectos nuevos.

## Gate de ronda 0.6 y adopción

Plan v2 (también v3) fija `execution.max_repairs` entre 0 y 2 (plantilla: 2). Para inferencia, `run_opencode.py --round 0|1|2` comprueba el límite antes de invocar siquiera `--version`; ronda superior al límite produce `blocked`, `escalation_required=true` y ninguna llamada CLI. `--preflight-only` no consume reparación ni exige ronda. Plan v1 conserva el límite anterior de 1 y el valor inicial por defecto por compatibilidad; no admite la nueva clave execution.

Este control valida una ronda declarada, no cuenta ejecuciones de modo durable. El coordinador debe comprobar que execution.max_repairs coincide con limits.max_repairs del contrato protegido y contrastar la ronda con el historial protegido de task/run, intentos e identidades antes de cada launch. No falsear ronda 0, reutilizar --out ni relanzar un resultado incierto. Un fallo de preflight sin inferencia no es una reparación del código. Pruebas protegidas, fallos/candidatos de rondas previas y modelo GO exacto se conservan. El gate no autoriza más presupuesto ni fallback. El contrato v4 admite max_repairs=2; contratos/pins previos conservan sus límites salvo override humano documentado, sin reemplazar sus bytes.

## Retro y devolución obligatorias

Después de cada ejecución, incluso fallo/bloqueo/cancelación, dot/coordinador completa [retro](aprendizaje.md) con la [plantilla](../templates/retro.md), la conserva bajo dot/ del consumidor y devuelve copia saneada a lecciones/ del harness. Registrar run/versiones/SHAs, fricción/impacto/tiempo, evidencia, causa comprobada vs hipótesis, solución, mejora y regresión. Esto no reescribe estados terminales ni habilita al coder a tocar el harness. Revisar/probar propuestas antes de promover versión; pins activos se mantienen. Ubicación de auditoría se acuerda antes del run para no invalidar el candidato.

## Piloto UI ejecutado en proyecto separado

La propuesta normalize_tags se sustituye por `<PROJECTS_ROOT>/genai-value-survey`, survey estático GenAI Adoption & Value Check. Spec/preguntas/scoring propios en ese repo; no usar dotHarness como piloto. Resultado y evidencia reales en dot/evidence/historical-summary.json del harness; la planificación previa queda como historia. El consumidor conserva su pin 0.3.1-pilot; esta política 0.3.2 no modifica su contrato activo.

UI obliga Playwright headless según [frontend](frontend.md), más unit tests de scoring independientes. OpenCode puede correr dev suites; validación final reejecuta bundles protegidos sobre SHA exacto, con reportes, capturas, traces de fallos y logs. No pruebas con CUA, pantalla o navegador del usuario. No se sustituye llamada real de OpenCode por implementación escrita por dot.

deployment.mode=cloudflare para el piloto, sin publish autorizado; estático compatible con Workers Static Assets y Wrangler local, sin D1/R2/login/backend. Otros proyectos pueden elegir local. El piloto histórico usó una tarea y una reparación; no se reescribe su evidencia ni su pin. La política nueva permite dos reparaciones para adopciones explícitas, sin remoto/publicación automática.

## Iteración rápida y reproducible

Preflight mínimo --preflight-only antes de infraestructura completa; no inferencia/implementación UI sin plan aprobado. Ver arranque.md. Readiness sola no resuelve sesión/directorio; comprobaciones de versión/agent/location son obligatorias. Estado/heartbeat por invocación, timeout600s máximo y hasta dos reparaciones; no relanzamiento ante resultado incierto. Validation usa worktree/copias congeladas; política incidental solo en contrato nuevo. Registrar setup/inferencia/validación por separado, pruebas de Back/recarga, URL y receta reproducible, sin reescribir evidencia histórica.

## Documentación y seguimiento de proyecto

Aplicar proyectos.md y seguimiento.md: índice/STATUS, fuentes canónicas y DASH-01 en el plan. El journal normalizado/proyección son contrato propuesto, no el progress de una invocación ya convertido en live de proyecto. Alojamiento pending no impide escribir contrato; sí impide implementar/publicar dashboard sin decisión. El requisito es documental en esta versión; el adaptador no certifica DASH-01 completada.

## Release y aprendizaje0.9

accepted del código no implica producción verificada. Antes del rollout aplicar docs/despliegue.md: parámetros/runtime real, presupuesto/autoridad, suite y expected congelados. Después del despliegue autorizado, recopilar recibo exacto y smoke autenticado; check_release.py devuelve review_pending, nunca aceptación por sí solo. Confirmación del usuario y checks públicos se registran aparte. Fallo de release conserva candidato/evidencia; reparación dentro del máximo2 existente, sin cambiar expected/tests ni fallback. Propuesta de estados de release no añade un motor implementado.
