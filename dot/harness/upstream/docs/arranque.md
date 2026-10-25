# Arranque rápido: destino antes de arquitectura

Primera decisión explícita con el usuario: ¿local_simple, docker_local o cloudflare? Registrar respuesta/referencia antes de diseñar arquitectura o spec técnica; no sustituir la pregunta por preferencia o detección automática. Sin respuesta, permanecer en descubrimiento. Survey actual: conservar local y candidato aceptado, sin migración, rediseño ni publicación.

| Destino | Consecuencia técnica mínima | Autoridad que no concede |
|---|---|---|
| local_simple | App sencilla; baseline compatible con Cloudflare, Wrangler dev local; assets estáticos sin build/framework/servicios adicionales cuando basten | Instalar servicios, publicar o crear recursos remotos |
| docker_local | Aislar dependencias/servicios o configuración que no se quiere en el host; mantener interfaz/baseline Workers compatible donde aplique y Wrangler dentro del entorno local elegido | Instalar/iniciar Docker sin permiso; un contenedor arbitrario no es un Worker desplegable |
| cloudflare | Diseñar para Workers y Static Assets; bindings locales compatibles solo si necesarios; configuración/destino versionados | Cuenta, login, credenciales, recursos remotos o deploy sin autorización específica |

Baseline para los tres: runtime/APIs Workers compatibles y pruebas con Wrangler local cuando corresponda. No añadir D1, R2, LLM, servicios o capas si assets estáticos resuelven el problema. Si un requisito exige algo incompatible, documentar excepción/razón, consecuencias y aprobación explícita antes de implementar. Compatibilidad local no certifica producción ni elimina la revisión de configuración, rutas/dominio, secretos, bindings y verificación remota antes de publicar.

Si la app usa LLM o agentes en runtime, usar OpenRouter como AI Gateway. Definir modelo/allowlist, presupuesto, privacidad y componente servidor/broker; claves nunca en assets/browser. Esta regla es para la aplicación, no para el coder: el adaptador del piloto mantiene GO exacto sin fallback. Una app sin LLM no necesita gateway ni coste de inferencia.

Si se eligen passwords, el default es mínimo8 caracteres y permite más largos; definir la política común de UI/backend/provisioning y sus pruebas según autenticacion.md0.8. No imponer passwords a otros mecanismos.

Antes de arquitectura, definir autenticación, roles y recursos protegidos según [AUTH MUST](autenticacion.md). Se incluye por defecto; solo una petición explícita del usuario permite omitirla. Local/simple/demo no son excepciones.

## Secuencia corta

1. Conversar idea y destino; producir [plan](../templates/plan.json.example) pequeño con decisiones explícitas de stack/runtime AI. check_plan.py verifica registros; no puede demostrar por sí solo que la referencia corresponde a una decisión humana real: el coordinador debe comprobarla.
2. Preflight mínimo antes de montar infraestructura completa: runtime/binario/version/help ya disponibles, compatibilidad y una comprobación acotada de readiness/sesión propia sin inferencia usando --preflight-only. No instalar ni ampliar infraestructura por un smoke; si hay bloqueo, devolver causa pronto. No posponer aislamiento ni integridad exigidos para ejecutar código no confiable.
3. UI: al menos dos mockups desktop/móvil con estados relevantes y aprobación explícita vigente; spec/tarea/aceptación trazan plan, opción/version y hashes. Los mockups del survey actual se conservan como propuestas, sin aplicarlos.
4. Congelar una tarea pequeña; un writer, generación inicial +máximo dos reparaciones y luego blocked/escalación al usuario, modelo exacto, tiempo acotado. Plan v3 exige authentication y execution.max_repairs y --round explícita para inferencia; planes v1 mantienen su límite de una reparación. Nuevo driver exige --plan y verifica destino/gateway/mockups antes de arrancar CLI; versión soportada2.0.32, readiness, PWD/directorio y sesión propios. --preflight-only no requiere elegir mockup porque no implementa ni infiere.
5. Validar copia Git del SHA con controles externos congelados; elegir worktree de control al comienzo. Nuevo contrato opta explícitamente por incidental_metadata_policy=record-ds-store-outside-public-v1 y require_external_controls=true; no cambiar contratos activos. .DS_Store regular Bud1, no ejecutable, sin enlaces y fuera de public/ se registra por hash antes/después, no integra el artefacto ni provoca ciclos. Cualquier otro cambio inesperado continúa bloqueando. Contratos antiguos siguen estrictos.
6. Estado/heartbeat y tiempos por fase; state.json y progress.jsonl del adaptador son evidencia de su invocación, no un nuevo orquestador ni garantía de reanudación automática. Tras interrupción, reconciliar out/proceso/sesión existentes, no reusar --out ni relanzar inferencia automáticamente. Verde CLI no acepta entrega: suite congelada+dot por SHA.
7. Entregar URL local y receta reproducible (SHA, versión/hash de plan/controles, runtime, comandos exactos, configuración, pruebas/exclusiones, coste reportado o desconocido), luego retro saneada. Validar Back→recarga y reanudar como casos explícitos de UI; no asumirlos por un verde genérico. Publicar es otro permiso.

Controles nuevos probados offline con CLI/servidor falsos y fixtures Git; no prueban Docker, despliegue remoto, nuevas inferencias GO, un sandbox general de backends ni una arquitectura LLM en producción. La adopción0.7 requiere plan v3/contrato v5 y gate de auth de entrega; no migrar corridas activas. El survey mantiene su pin0.3.1 y los scripts anteriores. 0.4 introdujo --plan y contrato v3. La adopción0.6 exige plan v2, contrato v4 y ronda explícita para inferencia; no autoactualizar consumidores.

Cada proyecto define el mapa canónico de proyectos.md e incluye DASH-01 según seguimiento.md. Destino de app y dashboard son distintos; dashboard puede quedar pending mientras se define observabilidad. Esto no autoriza implementarlo/desplegarlo sin decisión.

Para una entrega desplegable, definir temprano runtime target y plan de verificación según [despliegue](despliegue.md). Probes, recursos, límites y deploy requieren autoridad separada. No diferir la compatibilidad crítica de auth hasta después del rollout.
