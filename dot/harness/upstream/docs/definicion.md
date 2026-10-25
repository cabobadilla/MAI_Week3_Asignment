# Definición funcional y técnica

## Producto mínimo

Entrada: idea conversada. Salida: candidato por SHA, pruebas realmente ejecutadas y decisión independiente trazable. Dot aclara ejemplos, escribe spec y pruebas, revisa ambigüedades con el usuario y congela una unidad pequeña verificable. OpenCode implementa esa unidad. Dot revisa el candidato desde requisitos y evidencia obtenida por el ejecutor, sin asumir que el relato del coder es verdadero.

| Rol | Responsabilidad y autoridad |
|---|---|
| Usuario + dot | Requisitos, aceptación, excepciones, modelos, presupuesto y decisiones |
| Ejecutor local futuro | Exclusión, estado durable, preparación, snapshots, captura y gate determinista |
| OpenCode/coder | Cambiar solo archivos permitidos de una tarea; reporte sin autoridad para aceptar |
| Validador protegido + dot | Pruebas del SHA y revisión semántica; no reparar durante revisión |

Fuera del MVP: varios hosts, concurrencia, cola remota, daemon, UI, PR/deploy, actualización automática y gestión de secretos. Se propone después un pequeño ejecutor local por invocación, sin servicio permanente. Hoy no hay implementación de ese ejecutor.

## Confianza y aislamiento

Un worktree separa cambios Git; no protege el host y comparte metadatos del repositorio. Propuesta: el ejecutor conserva Git y el worktree; el coder recibe una vista/exportación mínima sin `.git`, con escritura solo en archivos permitidos. Al terminar, el ejecutor importa un diff verificado y crea el commit candidato local del consumidor. Un writer por vista/worktree, incluyendo editor humano; validación en otra exportación limpia del SHA.

Para una corrida real se debe elegir y comprobar una frontera OS efímera ya disponible: sin acceso al home, dotHarness, otros proyectos, credenciales, sockets o publicación; fuentes mínimas, controles fuera de writable, red limitada a lo autorizado. Los tests ejecutan código no confiable: runner separado sin secretos, validadores read-only y scratch externo. Worktree, AGENTS y `opencode.json` no sustituyen esa frontera. Su mecanismo está pendiente; no impide revisar esta definición. Si una corrida exige aislamiento y no puede demostrarse, queda `blocked`.

Para inferencia futura, las credenciales no deben quedar disponibles a herramientas o código generado; se requiere un mecanismo confiable separado (por ejemplo broker acotado) que se evalúe antes de activar el coder real. No existe ni se configura aquí. El piloto inicial será offline con adaptador falso y canarios sintéticos, nunca secretos reales.

## Bootstrap fijo

Fuente local versionada → copia física `dot/harness/` en consumidor + manifiesto → snapshot confiable del run fuera de writable. Ver [manifiesto](../templates/manifiesto.json.example). No copiar el AGENTS del harness ni sobrescribir el del consumidor: producir instrucciones específicas desde [tarea](../templates/tarea.md).

Reutilizable: estructura, estados, gate y formatos. Específico: problema, runtime, interfaces, datos, rutas exactas, pruebas, modelos y autorización de gasto. Cada override registra clave, valor anterior/nuevo, razón y quién lo acordó. No puede eliminar identidad, integridad, exclusión ni revisión. Dot revisa overrides antes de congelar. Configuración heredada desconocida impide preparar una corrida real; no se heredan reglas silenciosamente.

Cada run conserva manifiesto completo/hash, versión y digest del paquete según README, source SHA si existe, hashes de copias y overrides. El snapshot local sin commit se identifica como `local-snapshot`, nunca como release. Si cambian sus bytes, cambia identidad. Spec, aceptación y contrato conservan revisiones: editar cualquiera genera nuevo run, sin reescribir una aprobación histórica.

## Contrato de entrada

[JSON Schema](../templates/contrato.schema.json) valida forma. Los formatos de [spec](../templates/spec.md), [aceptación](../templates/aceptacion.md) y [tarea](../templates/tarea.md) completan significado. Precondiciones semánticas del ejecutor futuro:

- Identidad: `task_id`, `run_id`, `contract_version`, versión/digest de harness, `base_sha` completo y hashes SHA-256 de spec, aceptación, manifiesto/config y bundle de validación.
- Ronda: estado de ejecución separado del contrato (0 inicial, 1 primera reparación, 2 segunda reparación); no mutar el contrato congelado para avanzar de ronda.
- Base: commit existente del consumidor elegido tras inspección completa. Si hay dirty/untracked, preservar y bloquear hasta acordar snapshot explícito. No reset, stash ni commit automático del trabajo del usuario. El ejecutor solo crea después commits de candidatos propios.
- Alcance: `allowed_files` es lista de archivos relativos exactos, incluidos archivos nuevos previstos; deny por defecto fuera de ella. Proteger tests/fixtures, graders, scripts, selección/skips, manifiestos/lockfiles, configuración, AGENTS, OpenCode y `dot/`. Las rutas reales de esos elementos se enumeran en `protected_files`; solapamiento bloquea. Cambio legítimo exige otro contrato.
- Rutas: normalizar y resolver dentro de raíces autorizadas; rechazar absolutos, `..`, `.git`, enlaces simbólicos/duros, archivos especiales, colisiones de mayúsculas y submódulos en MVP. Revisar ambos lados de renames/copies, modos y borrados.
- Validación: comandos argv sin shell interpolado, runtime/version/hash y entorno mínimo explícitos. Ejecutar validadores externos congelados, no `npm test` resuelto desde scripts editables del candidato. Cada criterio obligatorio tiene test IDs e inventario esperado. Exclusiones autorizadas antes de iniciar no pueden cubrir criterios obligatorios.
- Modelos: allowlist exacta provider/model#variant cuando corresponda; principal y auxiliar seleccionados pertenecen a ella. No fallback, escalado ni selección implícita. Modelo efectivo distinto/desconocido o indisponible bloquea. Registrar llamadas auxiliares.
- Límites: propuesta futura USD 1 total por tarea, 10 minutos por ronda, máximo 2 reparaciones (3 rondas contando la inicial) según la política 0.6. Tras el último fallo permitido: blocked y escalación al usuario antes de otro intento. El presupuesto monetario sigue propuesto, no gasto autorizado. Plantillas fijan `spend_authorized=false`, límite cero. Registrar coste/uso observado o desconocido; desconocido no es cero; para GO incluido se aplica la autorización específica y se detiene ante aviso real de pago/compra/cuota agotada. Un tope local no garantiza corte de facturación del proveedor.

## Autenticación por defecto0.7

Toda app nueva incluye autenticación. Antes de arquitectura: enfoque, roles y recursos protegidos; excepción solo por petición explícita del usuario. Plan v3 y contrato v5 congelan authentication. Ver [política y gate](autenticacion.md). El presupuesto/destino no eximen auth. No migrar consumidores antiguos.

## Candidato y evidencia

Solo el ejecutor genera `candidate_sha`, `tree_oid` y digest de inventario tras confirmar fin del coder y descendientes. No aceptar staged/unstaged/untracked/ignored inesperados. Congelar candidato para revisión; exportación read-only del SHA, scratch aparte. La aprobación enlaza base, SHA, contrato y hashes; un cambio de código o inputs invalida evidencia y exige nueva validación.

Por run, un directorio durable de control local fuera de writable contiene: contrato/manifiesto, spec/aceptación, validadores/config congelados, `state.json`, `events.jsonl` y `round-000/`, `round-001/`, `round-002/`. Cada ronda conserva prompt, CLI/modelo efectivo, stdout/stderr redactados, exit/signal/timeout, estado Git e inventarios antes/después, diff, candidato, reportes de tests, gate y revisión dot. `artifacts.json` referencia archivos por ruta y SHA-256. No guardar secretos ni razonamiento privado.

`state.json` es autoridad; eventos auditables llevan secuencia, operation ID, from/to y hashes. Propuesta de durabilidad: lock exclusivo local; temporal + fsync + rename en mismo filesystem; intención antes del efecto y resultado después. Reconciliar snapshot/journal al arrancar; JSON truncado no se omite como si fuera válido. No usar carpeta sincronizada como almacén activo sin verificar locking/durabilidad. Esto sigue siendo diseño, sin motor de estado implementado.

[Resultado](../templates/resultado.md) separa `process_outcome`, `validation_outcome` y `delivery_outcome`. Dot puede rechazar un gate verde, pero nunca aprobar uno rojo/incompleto. La aprobación fija identidad de candidato, entradas, gate y artefactos; hashes no son firmas ni protegen de un host comprometido. Integración y publicación son decisiones posteriores fuera de este MVP.

## Extensión UI y destino — v2

project_kind es obligatorio; UI exige [Playwright](frontend.md) y validation.frontend completo. Modelos, herramientas, comandos y evidencia tienen autoridad distinta para coder/desarrollo y validador/final. En plantilla v5 (destinos introducidos en v3) deployment.mode es local_simple, docker_local o cloudflare: elección explícita previa a arquitectura según arranque.md. Baseline Workers/Wrangler local; una preferencia no sustituye la pregunta ni autoriza deploy. Arranque local por argv confiable y publish con autorización separada; ningún coder/validador recibe esa autoridad por pasar tests.

Para la ruta GO elegida por el usuario en el piloto: singleton opencode-go/deepseek-v4.1-flash; misma selección auxiliar si se usa, sin OpenRouter/otros/fallback. Autorización es uso de cuota existente, no recargas/compras/overage ni el antiguo USD1 propuesto. Cuota/facturación desconocidas se registran como no disponibles; detener ante aviso real de pago adicional, compra o cuota agotada. No exigir una prueba negativa previa de coste. Catálogo confirma ID, no entitlement, cuota o coste efectivo. La obligación OpenRouter corresponde al runtime LLM de apps, no al coder GO.

## Arranque0.4 y límites reales

Aplicar arranque.md antes de arquitectura. Plan externo protegido enlazado por planning en contrato v5 (enlace introducido en v3). check_plan y adaptador verifican destino/stack, gateway runtime y aprobación de mockups antes de inferencia. No comprueban la autenticidad humana de una referencia; dot la verifica. State/heartbeat son por invocación, sin servicio de coordinación ni reanudación automática implementados. El verificador estático sí exporta blobs Git del SHA y ahora puede registrar metadatos incidentales con política explícita, preservando bloqueos de integridad.
