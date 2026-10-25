# Verificación ejecutable con Chromium

El operador ejecuta python3 scripts/verify_frontend.py --contract <JSON externo>. El JSON fija kind=static-browser-only, phase=development|independent_final, repo, base_sha, candidate_sha, allowed_files, bundle/bundle_sha256, runtime/runtime_sha256, browser/browser_sha256/browser_version, playwright_version, node, wrangler, out externo, run_id, inputs {ruta:sha256} y baseline_ignored {ruta:sha256}. Sin sentinelas ni fuentes vivas.

Antes/después: árbol Git limpio, HEAD exacto, ignored conocidos, diff base→candidate limitado a cinco public/, entradas protegidas intactas. Exporta blobs regulares desde Git; rechaza enlaces, scripts/Worker inesperados y fuentes ejecutables. Arranca Wrangler4.129.0 exclusivamente local con configuración confiable. Playwright1.63.0 usa Chromium153.0.8010.12 headless, sandbox activado, contexto/perfil efímeros, escritorio1280 y móvil375, sin pantalla, CUA o Chrome personal.

Código candidato solo en el renderer OS-sandboxed de Chromium. Los unit tests de scoring usan un host de módulo protegido separado de UI; Node nunca importa/evalúa código candidato ni ejecuta scripts npm/build de su checkout. Esta modalidad estática no es un sandbox de backends. El perfil SBPL adicional no pasó renderer preflight y no se declara certificado.

Coder primario sin herramientas: entrega JSON de cinco archivos, validado por un guard mecánico de rutas/tipos antes de escribir; no se ejecuta el texto recibido en host. OpenCode solicita development_checks=[unit,frontend]; supervisor lanza suite congelada y registra requested_by=OpenCode/executed_by=executor. No afirmar ejecución shell nativa de OpenCode. Final repite independientemente la suite en candidato exacto.

Suite del consumidor:14 IDs ×2 viewports, flujos, scoring/unidades, errores, edición, persistencia, teclado y red. Evidencia JSON/HTML, capturas, traces de fallos, logs y versiones/run/SHA/test IDs/viewport. Zero tests, faltantes, skips o resultados malformados no pasan. Gate verde produce review_pending: dot revisa requisitos/riesgos por SHA antes de aceptar. --recheck <manifest> invalida evidencia si cambia código, working tree, contrato o controles.

OpenCode2.0.32: /openapi.json es la interfaz local comprobada. Registro de plugins asíncrono: catálogo privado fue0 y luego8 tras esperar1segundo; run --standalone inmediato daba AgentNotFound. Solución: servidor propio temporal autenticado en loopback, contraseña efímera propia no persistida, esperar agent readiness y comprobar modelo/permisos antes de run --server. Cliente utiliza GO existente internamente, sin leer/copy auth.json. Solo opencode-go/deepseek-v4.1-flash para principal y auxiliares, sin fallback, recargas ni compras. Cerrar servidor al terminar.

## Gate de autenticación0.7

Nuevas apps: plan v3/contrato v5 y check_delivery.py según [autenticacion.md](autenticacion.md). El adaptador bloquea auth pendiente/ausente antes del CLI. El gate de entrega comprueba reporte de pruebas externas e identidad del candidato, no ejecuta ni certifica por sí mismo autenticación. Fixture-only no pasa. El verificador del survey preserva su alcance y no se convierte en runner general de auth/backends.

## Gate de reparaciones0.6

Plan v2 fija execution.max_repairs=2; inferencia requiere --round explícita. El adaptador acepta ronda 0, 1 y 2 dentro del límite configurado, y bloquea ronda 3 antes del CLI con escalation_required=true. Después de una ronda 2 fallida, el coordinador marca blocked y escala al usuario, conserva tests y evidencia y no cambia modelo ni reinicia tarea/run para evadir el límite. El historial y su autenticidad siguen a cargo de coordinación: no hay contador durable automático. Planes v1, contratos anteriores y consumidores activos no se migran por esta publicación.

## Controles0.4, adopción explícita

Contrato nuevo puede fijar incidental_metadata_policy=record-ds-store-outside-public-v1; solo .DS_Store regular Bud1, sin enlaces/modo ejecutable y fuera de public/ se registra antes/después sin comparar su hash como fuente. El artefacto sigue exportado exclusivamente de Git. Los contratos sin esa clave mantienen el bloqueo anterior. require_external_controls=true bloquea bundle/runtime dentro del worktree; congelar/copiar antes del run. No reescribir contratos ni evidence previos. Tests offline verifican dirty/untracked, ignored desconocidos, metadato falso/en public/ y contrato legacy; no sustituyen la suite UI del consumidor.

Adaptador --plan: versión2.0.32, hash binario registrado, readiness, sesión own/location/model/permisos exactos. --preflight-only no infiere. state.json/progress.jsonl registran hitos/heartbeat20s/tiempo, sin razonamiento privado. Si se interrumpe, reconciliar en lugar de reusar --out. Pruebas con CLI/HTTP falsos y replay de formas saneadas observadas: no nueva certificación del proveedor, Docker ni runtime LLM.

## Evidencia target0.9

[Despliegue verificable](despliegue.md) complementa este verificador estático: assets reales/raíz, probes target, CPU y wall etiquetados y E2E autenticado independiente. check_release.py es un gate offline de reportes protegidos, no un runner remoto ni un deploy. Los tests locales nuevos no certifican de nuevo el portal.
