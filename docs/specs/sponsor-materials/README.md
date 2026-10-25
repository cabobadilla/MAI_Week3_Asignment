# Alcance vigente r5
Leer primero [delta confirmado Organizaciones/Seguimiento](scope-r5-organizations-tracking.md), que prevalece sobre r4 en registro de beneficiarias, contactos y estructura de Seguimiento. Estado de implementación en ../../../dot/STATUS.md.

# Especificaciones GrowWithAI · r4
Estado: especificación funcional/técnica redactada para implementación por tareas; no app construida, no contrato ready ni aceptación de producto. Alcance confirmado por usuario Sentinel_83058765897481918dd7fe55e183ae63 (“esto si me sirve... procede a generar las specs”). Esta revisión reemplaza recortes previos incompatibles; no volver a pedir confirmación del envío fuera de la app.

| Documento canónico | Contenido |
| --- | --- |
| [overview.md](overview.md) | Problema, one-liner Week 3, alcance y decisiones |
| [user-stories.md](user-stories.md) | Casos de uso e historias |
| [acceptance.md](acceptance.md) | Criterios, casos positivos/negativos, test IDs y gates |
| [ux.md](ux.md) | Campañas, Empresas, Seguimiento, editor y estados B |
| [visual-design.md](visual-design.md) | Elección B v1 y gate acotado para detalles B v2 |
| [technical-design.md](technical-design.md) | Arquitectura, herramientas, grafo/estado, auth, secretos y fallos |
| [data-model.md](data-model.md) | SQLite, justificación de tablas, versiones y distribución |
| [schema-proposal.sql](schema-proposal.sql) | DDL de referencia, no migración aplicada a una app |
| [tasks.md](tasks.md) | Backlog ordenado y responsabilidades/archivos |
| [evaluation-demo.md](evaluation-demo.md) | Pruebas/evaluaciones, trazabilidad handout y demo ≤5min |
| [future-scope.md](future-scope.md) | Exclusiones/fase posterior |
| [spec-verification.json](spec-verification.json) | Evidencia de validación documental/DDL, no tests de app |

Pendientes de producto: modelo LLM exacto y revisión visual de detalles nuevos. Preparación de ejecución: perfil/driver Python, modelo coder y controles externos/aislamiento, base Git elegida por usuario y lock instalado verificado. Esas tareas técnicas no son dudas sobre alcance. OpenCode sigue deny-all; no inferencia, app, push, deploy o Library en esta entrega.

Entrada práctica para el coder: [OPENCODE_HANDOFF.md](../../OPENCODE_HANDOFF.md), con preparación del driver y primera unidad offline; DASH-01 se gestiona en paralelo.
