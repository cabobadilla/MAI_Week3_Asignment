# Contrato de seguimiento por proyecto — v1

Requisito obligatorio: cada proyecto incluye DASH-01 en su plan y criterios. Entregable futuro: vista de lectura para saber qué hace el coordinador/OpenCode. Dirección elegida por el usuario: cloudflare_central. Diseño/auth/implementación/publicación siguen pendientes y requieren decisiones/autoridad específicas. El contrato y documentación sí se definen ahora con dashboard.deployment.status=pending y mode=cloudflare_central. Esta versión no incluye servicio, publisher, normalizador ni UI live de proyecto; el adaptador actual solo emite estado/eventos de su propia invocación.

## Autoridad y datos

Propuesta: un journal append-only por proyecto, protegido fuera de writable del coder y escrito por un único coordinador/ejecutor autorizado. Project ID + event_id + seq monotónica permiten reenvío idempotente y detección de huecos; reconectar no implica lanzar otra tarea. state/status.json es proyección derivada con last_seq/hash, no otra autoridad editable. Dashboard lee esa proyección; STATUS.md solo guarda un handoff y cursor observado. Los progress.jsonl actuales son entradas crudas de una invocación: hace falta mapearlos/verificarlos antes de afirmar que existe el journal normalizado de proyecto.

[Esquema](../templates/seguimiento-evento.schema.json) y [ejemplo sintético](../templates/seguimiento-evento.json.example). El esquema define forma, no autenticidad del actor, orden/idempotencia persistida, privacidad ni decisión humana: esas garantías requieren el publisher/coordinador y pruebas de DASH-01. Coder no puede auto-certificar accepted ni recibir claves de publicación.

Mostrar: etapa/run/task/round, actor/agente, execution_mode, modelos solicitado/efectivo (unknown si no verificado), estado observado/último heartbeat/tiempo, bloqueos/decisiones pendientes, tests esperado/ejecutado/pass/fail/skipped/not_run y fase, base/candidate/contract/gate/artifact SHA. Coste reportado con fuente/kind o unknown/null; no convertir desconocido en cero. Progreso por hitos y tareas sobre inventario acordado; ningún porcentaje inventado. Heartbeat ausente significa stale/unknown, no fallo ni éxito; la vista no relanza agentes ni aprueba cambios.

Saneamiento antes de proyectar/publicar: solo campos permitidos; no prompts completos, razonamiento privado, credenciales/headers, claves, PDF, respuestas de usuarios, nombres/emails/rutas home ni logs crudos. Logs/evidencias solo por artefactos revisados, ID relativo y hash, con acceso acotado. Los límites de longitud/JSON Schema no prueban ausencia de secretos. La vista de usuario es read-only; ingesta de un publisher separado necesita autoridad/auth propia. Journal local puede ser autoridad y réplica central declarar cursor/atraso.

## Alojamiento: dirección central elegida, implementación pendiente

| Modo | Diseño mínimo propuesto | Ventaja | Límite |
|---|---|---|---|
| local_wrangler | Assets + status.json saneado materializado por coordinador; Wrangler dev127.0.0.1 y polling corto/no-store | Menor setup, sin nube | Solo la máquina local mientras esté activo; no hay sincronización remota implícita |
| docker_local | Misma vista/contrato y Wrangler local en contenedor; solo volumen de proyección saneada | Aísla dependencias/config | Docker necesita permiso; contenedor arbitrario no es un Worker |
| cloudflare_central | Assets/Worker, lectura autenticada, publisher local de eventos saneados, ingesta idempotente y persistencia (por ejemploD1) | Varios proyectos y acceso desde otros dispositivos | Recursos/auth/costes y deploy separados; el ejecutor debe publicar, no se mueve OpenCode a la nube |

Decisión del usuario: dirección cloudflare_central para reunir proyectos con login y API de progreso. local_wrangler y docker_local se conservan como alternativas de desarrollo/aislamiento, no como decisión pendiente de alojamiento. Destino de app y dashboard son decisiones diferentes; no elegir por el usuario. Para esta dirección: required=true, task_id=DASH-01, deployment.status=pending, mode=cloudflare_central, decision_ref=user-dashboard-central-direction; design/auth/implementation.status=pending. La selección conceptual no autoriza despliegue. Nada de esto autoriza instalar o desplegar.

Para MVP basta polling2–5s configurable con versión/cursor; no obligar a WebSockets/SSE ni introducir un nuevo bus. Si no llegan eventos, mostrar último dato y stale. Hosting central puede mantenerse visible mientras el agente local está desconectado, pero no fingir que sigue vivo. Los enlaces de artefactos deben respetar acceso y mostrar unavailable si no se publicaron.

## DASH-01: tarea y aceptación

Incluirla temprano en04_plan sin crear recursión de dashboards: una vista reutilizable/configuración por proyecto, no un dashboard por sub-tarea. Debe figurar como pendiente hasta implementarse/verificarse; el proyecto no la marca hecha por existir un JSON. Aplazamiento requiere decisión explícita registrada. El diseño/auth pendiente bloquea implementar/publicar el dashboard hasta acordarlos; no bloquea definir su contrato/documentación ni publicar el harness tras revisión.

Criterios observables futuros: evento controlado actualiza vista con cursor/identidad; replay no duplica y detecta huecos; heartbeat ausente muestra stale; unknown cost y tests not_run se conservan; lectura no permite ejecutar/modificar y datos sensibles quedan fuera; accepted enlaza SHA+gate+revisión exactos. Mockups desktop/móvil muestran activo, decisión pendiente, bloqueado, stale y validación final. El modelo de amenazas y las pruebas de auth/ingesta se definen al elegir alojamiento.

Fuentes oficiales para la evaluación: [Wrangler local](https://developers.cloudflare.com/workers/local-development/), [Static Assets](https://developers.cloudflare.com/workers/static-assets/), [D1](https://developers.cloudflare.com/d1/), [Access](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/). Compatibilidad local no certifica producción ni costes cero. Esta fase define; no despliega ni implementa esos componentes.

## Contrato conceptual de proyectos, corridas y API

Un proyecto tiene project_id, título saneado, pin de harness, referencia de sus specs y permisos de lectura/publicación. Una corrida tiene run_id, task_id/ronda, actor/modelo/modo de ejecución, hashes base/candidato/contrato y estado observado. Un evento pertenece a proyecto/corrida y lleva event_id/seq; un artefacto tiene ID/hash y acceso propio, no una ruta arbitraria del host. El registry de proyectos se configura por autoridad administrativa, no por el coder ni por el lector.

Rutas propuestas, no endpoints existentes: GET /api/projects; GET /api/projects/{id}/runs; GET /api/projects/{id}/status?after_seq=N; GET /api/projects/{id}/artifacts/{artifact_id}; POST /api/projects/{id}/runs/{run_id}/events para publisher autorizado. Lectura paginada por cursor; ingesta con clave idempotente, identidad/proyecto acotados, verificación de orden y validación/saneamiento antes de proyectar. HTTP exitoso no equivale a accepted. Permisos de registro/administración quedan fuera de la vista read-only y se diseñan por separado.

Auth de lector: login sencillo con sesión y acceso solo a proyectos permitidos; decidir entre protección gestionada (por ejemploAccess) o login de app sin diseñar una base de contraseñas por defecto. Auth de publisher: credencial distinta, revocable y limitada por proyecto, mantenida por coordinador/broker en la máquina ejecutora; nunca en HTML/assets ni en herramientas del coder. La sesión del lector no publica eventos; credencial de publisher no acepta entregas ni ejecuta código. Diseño concreto y provisión de credenciales: pending; no se generan aquí.

Opciones de frontend por evaluar: (A) HTML por proyecto más API común: simple de entregar, pero duplica vistas/versiones y exige controlar scripts/origen de cada HTML; nunca servir HTML no confiable en el origen autenticado con secretos. (B) UI común parametrizada por project_id más API común: contrato uniforme, una implementación de auth/filtros/replay y menos deriva visual; los proyectos publican datos saneados, no código UI. (C) HTML autónomo exportado estático: útil como informe portable sin conexión, pero snapshot, no seguimiento live. Recomendación técnica para varios proyectos: UI común+API; no es una aprobación de diseño ni implementación. La decisión final y mockups se registran antes de codificar.

## Proyecto de referencia acordado (separado)

El portal fábrica de software será el primer proyecto de referencia construido con el nuevo harness, en tarea/repositorio separado. Dirección acordada: Cloudflare, subdominio swfactory.chrisbob.uk y MVP de lectura con UI común/API de eventos. Esto es una decisión de alcance/destino, no un portal existente ni autorización ejecutada de DNS/deploy. Antes de código UI: brief/spec, arquitectura/auth y dos mockups con aprobación explícita. El proyecto consumirá un commit/digest explícito del harness publicado; sus pruebas y lecciones volverán saneadas para mejorar versiones posteriores. No se inicia aquí el proyecto ni se generan credenciales.
