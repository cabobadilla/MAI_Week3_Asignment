# Evaluación, riesgos y demo Week 3 · r4
Estado: plan; cero tests de app o inferencia ejecutados en esta entrega. Evidencia documental/DDL en spec-verification.json; 48 checks y 54 capturas previos solo prototipo B/A v1.

## Trazabilidad handout (fuente local)
[Handout extraído](../../references/extracted/Week%203%20Project%20Handout%20%28Oct%202026%29.txt); original íntegro y hashes en [manifest](../../references/manifest.json). No abrir enlaces a soluciones modelo.
| Requisito curso | Implementación especificada | Evidencia futura |
| --- | --- | --- |
| Primer + framework | overview goal/surface/steps/tools/state/never/HITL/error/metric | revisión specs + demo completa |
| Caso 3D GTM suite | LinkedIn/email general/artículo/anuncios, fuentes con RAG y revisión | CAM-02/GEN-01/02 |
| Decidir qué hacer | refine/preguntar/omitir, historia/repetición/conflicto | RAG-02/HIST-02 |
| Herramientas/estado multi-step | grafo, SQLite/checkpoints y herramientas diferenciadas | STATE-01/BOUNDARY-01 |
| Fallos/reintentos/HITL | timeout/401/límites/reanudación/no aprobado/aprobación export | FAIL-01/EXP-01 |
| Entrega documentación+demo≤5min+code assets | este índice + registro de prompts/iteraciones/aprendizaje futuros | EVAL-01; publicación/push/entrega al curso no autorizados aquí |

## Evaluaciones propuestas
Fixtures sintéticos, sin contactos reales: fuentes completas; faltan precio/fecha/convenio; contradicción histórica; inyección en documento/email; historia vacía/error; repetición válida; lote con contacto duplicado; dos campañas; email v1 enviado/v2 editado; publicación pública; respuesta sin envío conocido; corrección equivocada; timeout/401/429; restart tras interrupt/aprobación/export; rollback/idempotencia concurrente; archivo/contacto archivado. Assertions de constraints con SQLite real y grafo real; transporte LLM falso para control de fallos. Un mock no demuestra pertinencia, latencia/coste o grounding real.
Evaluación LLM real cuando se elija modelo económico y prueba autorizada: cinco runs de misma campaña-fixture, mínimo cuatro con suite revisable en <10min; cero hechos materiales inventados, citas correctas para afirmaciones fácticas y cero export sin aprobación. Objetivos de aceptación, no resultados medidos. Registrar modelo/request config/usage/latencia y coste reportado/unknown, sin claves o textos privados. No comparar modelos con llamadas de pago hoy.

## Demo propuesta (4:50 máximo, sin envíos reales)
0:00–0:30 propósito GrowWithAI, fuentes v0.2 y límites; login local.
0:30–1:10 campaña general + dos empresas/tres contactos ficticios, cuatro formatos.
1:10–2:00 RAG/historia y pregunta por monto ausente; omitirlo explícitamente.
2:00–2:50 revisión de suite/citas, edición→nueva versión y aprobación→export local.
2:50–3:40 declaración manual de lote a dos contactos, tercero pendiente; publicación LinkedIn separada; respuesta/nota/próximo paso y aviso duplicado.
3:40–4:30 fallo transitorio simulado/reinicio y checkpoint; salida no aprobada si agota límites.
4:30–4:50 stack, uso de OpenCode, aprendizajes y lo no implementado/verificado. Si se acelera usando run previo, etiquetarlo grabado/fixture y no fingir inferencia en vivo. No mandar correo/publicar para la demo.

## Riesgos y mitigación
Modelo barato puede producir inconsistencias: fuentes/citas, reviewer, límites y humano; no prometer cero errores por prompt. Historial manual incompleto: procedencia explícita, advertencia no “verdad verificada”. Lotes/contactos: preview, operación atómica e identidad estable. Corrección/trazabilidad: inmutabilidad lógica e historial, no status único. PII/secretos: minimización local, .env backend, logs allowlist y tests negativos. Auth/UI Python: pruebas reales de sesión/CSRF/rutas y revisión independiente, no extrapolar mockups o wrapper UI estático. Backend/driver no compatibles aún: preflight offline y tarea específica antes de usar el piloto. Alcance: sin integraciones/CRM ampliado; no consumir nuevas claves/permisos por completar specs.
