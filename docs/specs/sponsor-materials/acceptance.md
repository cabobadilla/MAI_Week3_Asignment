# Aceptación y trazabilidad · r4
Status: especificada, pruebas de app not_run; revisión independiente requerida. Matriz normativa. Gates: alcance confirmado; visuales nuevos pendientes; no plan de ejecución ready. IDs anteriores CA quedan reemplazados por esta matriz; no reutilizar pruebas viejas como evidencia de app.

| AC | Área | Positivo / borde / negativo observable | Test ID futuro | Tarea |
| --- | --- | --- | --- | --- |
| AC-01 | Acceso/password | Primer inicio acepta contraseña de ≥8 caracteres y confirmación; 7 se rechaza, 8/más se aceptan sin truncado; no secretos en reporte. | AUTH-P01 | AUTH-01 |
| AC-02 | Sesión/autoridad | Sin sesión o tras logout/caducidad, rutas/API/exports protegidos se deniegan; operador no accede a paths externos; CSRF/origen inválidos se rechazan. | AUTH-S01 | AUTH-01 |
| AC-03 | Empresa/contacto | Alta mínima y edición/archivo conservan IDs; contacto con email requerido al asociar destinatario de correo; no agregar empresa implica convenio confirmado. | DB-ORG01 | T-03 |
| AC-04 | Duplicados identidad | Advertir empresa similar sin fusionar; normalizar email para comparación sin quitar +/puntos; misma dirección no se añade dos veces a una campaña. | DB-DUP01 | T-03 |
| AC-05 | Campaña general | Guardar tema, objetivo, segmento, tono/formatos y múltiples contactos; contenido común, sin plantilla personalizada por empresa. | CAM-01 | T-04 |
| AC-06 | Suite/canales | Modo académico prepara LinkedIn/email general/artículo/anuncios; uso diario puede subset; canal público permite cero destinatarios y no se inventan. | CAM-02 | T-04 |
| AC-07 | Fuentes | Recuperación vectorial local con ID/hash/versión/localizador; handout excluido del índice comercial; original no modificado y fuentes nuevas no ejecutan instrucciones. | RAG-01 | T-05 |
| AC-08 | Datos faltantes | Precio/fecha/convenio ausente: máximo consulta inicial+una ampliación; preguntar/omitir explícitamente; no inventar o completar desde conocimiento general. | RAG-02 | T-05 |
| AC-09 | Historia relevante | Recuperar por tema/campaña y contexto; priorizar envíos/publicaciones declarados y respuestas, distinguir borradores; snapshot exacto citables sin libreta de contactos al prompt. | HIST-01 | T-05 |
| AC-10 | Repetición/conflicto | Repetición genera advertencia y permite reutilizar con decisión; conflicto material conserva evidencia y pregunta; historial vacío explícito y error distinto. | HIST-02 | T-05 |
| AC-11 | Cuatro formatos | Bundle generado tiene los formatos seleccionados (los cuatro en demo), tres anuncios en fixture de demo; CTA general, tono coherente y evidencias por afirmación. | GEN-01 | T-06 |
| AC-12 | Revisión limitada | Revisor revisa hechos/consistencia y máximo dos correcciones; error material persistente deja no aprobado/needs_human, sin exportar. | GEN-02 | T-06 |
| AC-13 | Persistencia/aislamiento | Cerrar y reabrir proceso conserva checkpoint/preguntas/versiones por run; campaña A no usa respuestas/contexto de B salvo selección histórica pertinente y trazada. | STATE-01 | T-06 |
| AC-14 | Fallos/reintentos | Timeout transitorio acotado, 401/403 sin retry, máximo ocho intentos HTTP/run y veinte transiciones; historia inaccesible no se presenta vacía; no retry silencioso de efecto incierto. | FAIL-01 | T-06 |
| AC-15 | Versiones/aprobación | Editar pieza aprobada/enviada crea nueva versión; aprobación exacta no se traslada; envíos previos siguen apuntando al texto anterior. | VER-01 | T-07 |
| AC-16 | Export protegido | Solo bundle exacto aprobado y sin errores materiales; hash cambiado o path/symlink externo bloquea. Exportación retry idempotente no envía/publica ni agrega tracking. | EXP-01 | T-07 |
| AC-17 | Hechos/versiones externos | Una copia externa puede registrarse como no aprobada por app sin falsificar aprobación; nota sin texto exacto no presume contenido verificable. | VER-02 | T-08 |
| AC-18 | Envío manual individual | Acción explícita registra contacto/versión email/fecha declarada/canal y snapshot de destino; email común, no enviado por app; estado “registrado manualmente”. | DIST-01 | T-08 |
| AC-19 | Lote manual | Vista previa enumera contactos/versiones/fecha; confirmar escribe eventos individuales en una transacción, no un estado global; fallo revierte todo y retry de operation_id no duplica. | DIST-02 | T-08 |
| AC-20 | Publicación pública | Acción manual registra pieza/versión/canal/fecha/URL opcional sin contacto; no prueba entrega/alcance ni se multiplica por destinatario; no visita URL. | DIST-03 | T-08 |
| AC-21 | Respuesta/nota/próximo paso | Registrar manualmente para campaña/destinatario y vínculo opcional al envío; no inventar respuesta/leído. Próximo paso es anotación, sin recordatorio/automatización externa. | FOLLOW-01 | T-09 |
| AC-22 | Reenvío deliberado | Detectar campaña ya enviada y misma versión por destinatario; advertir antes de registrar/asociar. Retry técnico no duplica; reenvío real permite confirmar con razón y nueva fecha. | DIST-DUP01 | T-09 |
| AC-23 | Corrección trazada | Corregir envío/publicación/nota agrega evento sustituto con motivo/actor/recorded_at, conserva original y muestra proyección vigente; no editar/borrar texto pasado o cambiar otra campaña. | AUDIT-01 | T-09 |
| AC-24 | Config/secretos | Disabled no crea cliente/llamadas; enabled exige clave/modelo explícitos, no fallback. .env nunca browser/log/prompt/checkpoint; errores sin headers/claves. | CONF-01 | T-02 |
| AC-25 | Tokens/coste | Validar límites técnicos antes de requests, incluir retries/revisión; uso/coste reportado o unknown, presupuesto económico en API key sin pedir USD local adicional; no duplicar retries SDK/grafo. | LIMIT-01 | T-06 |
| AC-26 | Frontera externa | No herramientas de envío, publicación, compra, bandeja/sync o búsquedas externas automáticas; textos históricos/documents son datos y no autorizan acciones. | BOUNDARY-01 | T-10 |
| AC-27 | UX/estado | Campañas/Empresas/Seguimiento/editor desktop/móvil: vacío/carga/error/espera/no aprobado; Back→recarga→retomar, foco/teclado y ausencia de overflow en viewports fijados. | UI-01 | T-10 |
| AC-28 | Gate visual | B v1 base elegida; detalles nuevos B v2 no se implementan hasta presentar variantes de detalle y aprobar opción/versión/hashes. Redactar specs no simula aprobación. | UI-GATE01 | T-01 |
| AC-29 | Evidencia/app | Reporte distingue tests planeados/not_run y efectivos por candidato; no aceptar mocks como calidad real del LLM o mockups como auth. Demo completa y fallos trazados. | EVAL-01 | T-11 |
| AC-30 | DASH local | Contrato de tracking requerido en portal central, separado de app local: identidad/cursor/replay/stale/unknown/not_run y accepted ligado a SHA/gate. API/auth y registro/sync se verifican/autorizarán aparte; no publicar datos ni ejecutar/aceptar desde vista hoy. | DASH-TEST01 | DASH-01 |

## Protocolo de pruebas
Todos los criterios obligatorios; no skips/exclusiones no acordadas. Unit/SQLite reales para constraints, versiones, idempotencia y persistencia; transporte/modelo falso para fallos; inferencia real solo después de elegir modelo y tarea autorizada. UI Playwright headless con servidor propio 127.0.0.1 y contexto limpio (1280×800, 375×812), sin browser personal, con red bloqueada salvo localhost en tests offline. Fixture de identidad no certifica auth: suite final atraviesa auth implementada.
Coordinador prepara tests/fixtures/config; se congelan y copian a control externo read-only para coder. Los argv futuros se fijan por tarea con cwd/env/runtime/hash/timeout; no ejecutar tests desde scripts editables por candidato. Runtime/lock exactos se comprueban en T-02, no se inventan ahora. Reporte por candidate_sha/base_sha/inputs/contract/test IDs; development e independent_final separados, JSON/HTML/screenshots y trace de fallos; cero tests o faltantes = incomplete. Coder nunca marca accepted.

Auth password test AUTH-P01 debe desglosar UI/backend/provisioning × longitud 7/8/>8 sin valores secretos en reporte. AUTH-S01 cubre grupos unauthenticated/session_logout/authorization. AC-26 incluye negative fixtures de prompt injection con texto “envía a...” que no produce herramientas o acción externa.

## Gate de implementación
No inferencia en esta tarea de specs. Implementar solo tras tarea/allowlist/modelo coder y cuota autorizada/control externo/aislamiento/base Git. UI ampliada exige además aprobación visual vigente; partes backend/fixtures no dependen de una aprobación visual inventada. Modelo app pendiente bloquea evaluación real, no escritura de tests offline. Puertos/servicios globales no se modifican para ocultar el bloqueo previo de OpenCode.
