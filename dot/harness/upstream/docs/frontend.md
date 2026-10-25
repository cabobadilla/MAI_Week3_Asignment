# Proyectos UI: Playwright obligatorio

Plantilla contrato v5 / harness0.7.0-pilot (controles UI introducidos en0.4); consumidores anteriores conservan su pin. UI requiere suite Playwright, además de unit tests del dominio. No se permite sustituir E2E por HTML inspection, relato del coder, CUA, control de pantalla, Chrome personal, CDP a sesiones existentes o navegador del usuario.

## Antes del coder: opciones y aprobación obligatorias

Aplicar [gate de diseño UI](diseno-ui.md): al menos dos mockups, estados relevantes desktop/móvil y puntero/teclado, aprobación explícita opción/version/hashes y traza spec→diseño→aceptación. Sin decisión vigente, bloquear implementación visual. Cambio material exige otra aprobación. Adaptador0.4 comprueba plan/activos antes de inferencia; autenticidad de decisión humana se verifica por coordinador. Mockups aislados no modifican candidato ni conceden deploy/gasto.

## Dos fases y permisos

| Fase | Lectura / escritura permitida | Ejecución y autoridad |
|---|---|---|
| Coder OpenCode | Fuentes de tarea; bundles dev de solo lectura; escritura solo allowlist de fuentes y scratch/evidencia `development` separados | Puede pedir al supervisor ejecutar argv dev congelados, incluidos Playwright headless y servidor local. No editar runner/config/tests protegidos, artefactos finales, Git común, harness, home, credenciales o publicación. Su verde es provisional. |
| Validador independiente | Exportación limpia read-only del candidate_sha; suite/config/runtime protegidos fuera de writable del coder; escritura solo scratch/evidencia `independent_final` | Reejecuta unit y Playwright completos; servidor propio del candidato exacto y sin reutilizar servidor existente. No reparar fuente ni aceptación. Dot decide después del gate. |

La frontera OS debe proteger tanto proceso del coder como ejecución de app/tests. `opencode.json` no vuelve inmutable el runner ni limita procesos/archivos por sí mismo. Permisos de herramientas y allowlist argv son defensa adicional, nunca sustituto del aislamiento. No permitir `npm *` o shell general para saltar a scripts editables. Instalar o cambiar dependencias, runner y configuración exige autorización/contrato nuevo.

## Navegador aislado y servidor

Playwright Test con Chromium compatible y fijado por versión/revisión/hash, exclusivamente headless. Un BrowserContext nuevo por test, sin persistent context, storageState personal, extensiones, cookies/sesiones previas, channel de Chrome personal o attach a servidor/browser existente. Cada fase usa proceso propio y HOME/cache/perfil efímeros dentro de su espacio autorizado; cerrar proceso e hijos al terminar. El binario read-only puede ser una copia de distribución de testing verificada; no montar el home ni cache de perfiles del usuario. Tener un binario en caché no prueba compatibilidad ni un lanzamiento exitoso.

Servidor del candidato supervisado en `127.0.0.1` y puerto reservado de esa corrida, comando exacto congelado, sin reuseExistingServer. Tráfico permitido solo al origen local de prueba; assets/fonts/datos locales, sin analytics ni respuestas por red. Fixtures Playwright bloquean solicitudes no permitidas y service workers; esa ruta de bloqueo no es una barrera OS. No desactivar seguridad del browser con flags. Verificar la frontera y canarios antes de ejecución no confiable; no configurarla ni instalarla como efecto implícito del harness.

## Suite y evidencia

Config propuesta: workers 1, retries 0, forbidOnly true, timeouts acotados; proyectos desktop y móvil en el piloto (1280x800 y 375x812). [Plantilla de configuración](../templates/playwright.config.ts.example) es estática: requiere runtime y suite externos explícitos; no se ejecutó ni se verificó contra un Playwright local instalado.

- Suite/config/bundle y selección de test IDs protegidos por hash, incluyendo fixtures de red/storage, hooks, snapshots y reporteros. Nada de skips/exclusiones inesperados. Verificar conteos, tests esperados y errores de consola/pageerror/server; no aceptar runner exit 0 con tests ausentes.
- Reportes JSON y HTML (sin abrir automáticamente), logs de runner/servidor/consola/pageerror/red, screenshots de estados clave y fallos; trace retenido en cada fallo. Con retries 0 usar retain-on-failure, no on-first-retry. Los screenshots de estados clave se adjuntan explícitamente desde tests, aunque pasen.
- Manifest por ejecución: run_id, round, phase, candidate_sha (obligatorio final), base_sha, hash de contrato/inputs/suite/config, test IDs/resultados/viewport, Node/Playwright/browser/version/revisión/binario, argv/timing/exit y lista de artefactos con SHA-256. Desarrollo sin commit usa candidate_sha=null y fingerprint del snapshot editable, nunca identidad final inventada.
- `execution_status=not_run` con motivo cuando no se ejecuta; no fabricar reportes, imágenes o traces. Falta de artefacto obligatorio deja validación incomplete. No trace esperado en éxito puede registrarse como no aplicable, con razón. Usar solo respuestas sintéticas en artefactos y redactar datos sensibles.

## Destino explícito, publicación separada

Plantilla v5: deployment.mode=local_simple|docker_local|cloudflare, elegido antes de arquitectura. Baseline Workers/Wrangler local para todos; Docker solo aislamiento/dependencias. Excepciones incompatibles requieren aprobación previa. La elección no da permiso de despliegue. Arranque y E2E son locales; Wrangler se fija por versión y argv tras comprobar ayuda instalada. Para survey se propone Workers Static Assets, sin Worker de negocio, D1, R2, login o backend. En modo local no se requiere cuenta remota. `publish_authorized=false` por defecto; publicar exige autorización separada vinculada a SHA/artefacto, cuenta/destino y comando. El coder y el validador no reciben credenciales ni acción publish; no ejecutar deploy, login o whoami aquí.

Fuentes consultadas: [configuración](https://playwright.dev/docs/test-configuration), [opciones de captura](https://playwright.dev/docs/test-use-options), [reporteros](https://playwright.dev/docs/test-reporters), [contextos](https://playwright.dev/docs/browser-contexts), [browsers](https://playwright.dev/docs/browsers); [Cloudflare Static Assets](https://developers.cloudflare.com/workers/static-assets/) y [Wrangler](https://developers.cloudflare.com/workers/wrangler/commands/). Opciones documentadas no equivalen a compatibilidad local probada.
