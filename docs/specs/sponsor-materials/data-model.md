# SQLite y trazabilidad · modelo r4
Modelo implementable de referencia, no BD/migración productiva. [schema-proposal.sql](schema-proposal.sql) define forma y constraints básicos; validación documental/DDL se registra aparte. Reglas transaccionales, hash/aprobación y autorizaciones se implementan en servicios y se prueban, no quedan “resueltas por JSON”.

## Tablas mínimas y razón
| Tabla | Por qué existe y campos | Cardinalidad/autoridad |
| --- | --- | --- |
| company | nombre, notas, archived_at; agrupa contactos sin CRM ampliado | 1 empresa→N contactos; alta no acredita alianza. Solo empresas destinatarias en MVP |
| contact | company_id, nombre (legacy puede estar vacío; nuevas filas usadas requieren nombre), email/email_key, archived_at | email para seleccionar destinatario; unique por empresa+email_key; no quitar +/puntos de dirección ni adivinarla |
| campaign | título/tema/objetivo/segmento/tono/formatos, config_revision, archived_at | una campaña general→múltiples piezas/destinos. Campaña es agrupador confirmado, no etiqueta pendiente |
| campaign_recipient | campaign_id/contact_id, snapshot nombre/email/empresa, email_key, selected_at/archived_at | N campañas↔N contactos; unique campaña+email_key evita duplicados incluso entre empresas. Archivar quita de nuevos lotes, no del pasado |
| generation_run | campaña, run_id, estado/paso, config/source/context snapshots, métricas/errores saneados | guarda evidencia de fuentes/historia/config sin claves; checkpoints LangGraph en otro SQLite |
| content_version | campaña, formato/variante/revisión, texto/hash, parent_version, origin, run_id | texto append-only, variantes de anuncios separadas; editar crea versión. No tabla “pieza” extra: identidad lógica campaña+formato+variante |
| approval | campaña/run, manifiesto exacto IDs/hash de versiones, fuente/contexto, aprobado_por/fecha | bundle aprobado inmutable; una selección parcial no aprueba otras versiones |
| export_record | approval_id, archivos/hash, operation_id/fecha | idempotencia y receta local; no altera distribución |
| distribution_record | versión exacta, tipo email_sent/publication, destinatario nullable, canal, fecha declarada/registro, snapshot, batch/operation, supersedes | evento por destinatario o publicación pública; no un estado global de campaña. Correcciones append-only |
| followup_event | campaña/destinatario opcional/envío opcional, respuesta/nota/próximo paso, fecha/fecha objetivo opcional, supersedes | seguimiento manual, sin bandeja o automatizaciones; correcciones trazadas |

Auth usa operator_credentials separado del dominio (singleton hash/salt/algoritmo), sesiones en memoria del servidor y logout/reinicio invalida sesión. No nuevas cuentas en nube. Fuentes conservan manifiestos/bytes en disco; generation_run almacena referencias/hash y selección, evitando tablas de documentos/CRM innecesarias. El catálogo company se reutiliza internamente para Organizaciones con roles propuestos en r5; no tablas duplicadas por rol, leads/funnels o métricas de apertura.

## Versiones, aprobaciones y estados
No columna única generado→enviado. Estado de run describe ejecución (prepared/running/waiting_input/needs_review/finished/failed/cancelled); badges de aprobación/export/distribución se derivan de registros independientes. `finished` solo termina generación/revisión, nunca aprueba o envía.
Cambiar texto crea content_version nueva y aprobación nueva para exportarla; la antigua conserva su aprobación/export/envíos. Cambiar objetivo/audiencia/formatos/fuentes/contexto seleccionado aumenta config_revision y exige revisión nueva del bundle de trabajo. Editar contacto o añadir destinatarios no cambia contenido general ni invalida aprobación del texto: la selección de destinatarios se confirma separadamente en el registro manual.
Approval manifest ordena versiones (ID/hash), fuente/contexto hash y config_revision; servidor recalcula antes de aprobar/exportar. Bloquea errores materiales sin resolver. Datos incorporados después no reescriben evidencia: al generar nuevamente se consulta historia actual; si el operador actualiza fuentes/contexto del bundle existente debe volver a revisarlo. Conservar snapshots históricos.

## Registro de correo por contacto y lote
Solo acción del operador: seleccionar versión de email común, destinatarios activos y fecha, vista previa de todos y checkbox “Declaro que estos envíos se realizaron fuera de la app”. Batch crea N registros con mismo batch_id pero versión/fecha/destino por fila, en una única transacción. operation_id + payload_hash y operation_item_key únicos permiten retry idempotente; cambiar payload con la misma operación se rechaza. No iniciar SMTP/API de correo. No auto-marcar envío por exportar/asociar destinatario.
El snapshot conserva a quién se declaró enviar aunque contacto cambie después. Duplicado exacto por campaña/destinatario/versión advierte; una repetición real puede registrarse con nueva operation_id, fecha y razón confirmadas. Retry de la misma acción nunca crea reenvío ficticio. Datos sensibles mínimos quedan locales y no van al LLM para redactar email general.
Publicación: versión/canal/fecha y URL opcional, sin destinatario; unique operation_item_key y sin visitas remotas. No multiplicarla por lista de contactos ni inferir lectura/impacto.

## Correcciones, notas y copias externas
Corregir agrega sustituto del mismo tipo/campaña con supersedes_id y motivo/actor/recorded_at; original no se borra. Una única rama de corrección, sin ciclos, proyección vigente = eventos no sustituidos; mostrar también auditoría. La corrección no realiza un nuevo envío. Asociar respuesta a evento/campaña/destinatario coherentes; si no se conoce envío, no inventar vínculo. Próximo paso opcional con fecha es nota, no automatización.
Texto externo distinto puede registrarse como versión origin=manual_external, no aprobada por app; las distribuciones manuales no exigen aprobación retrospectiva falsa. Si no hay texto exacto, guardar nota de seguimiento, no fingir versión/hash enviado. Exportar desde app sí exige aprobación. No deletes/cascadas de registros referenciados: archivar; purga/borrado masivo fuera del MVP para evitar pérdida accidental, sin prometer cumplimiento o conservación eterna.

## Integridad adicional de servicio
Foreign keys ON, transacciones BEGIN IMMEDIATE para batch, UNIQUE para operación/duplicados, comprobación de misma campaña en versión/destinatario/seguimiento/aprobación, hashes/manifest y de cadena de corrección. JSON validado con DTO, tamaño/límites y enums; nada de ejecutar SQL/HTML desde mensajes. Las piezas no pueden cambiar de formato/variante entre parent/revisión. Tests DB/DIST/AUDIT incluyen concurrencia de dos clics, rollback de lote y cross-campaign IDs. No se ha ejecutado app ni migración de usuario.

## Delta r5
Migración propuesta2 añade roles_json a company manteniendo IDs y 1:N contactos. Tabla/columna de rol no confirma patrocinio. Followup next_step se conserva por compatibilidad histórica; no nuevas acciones públicas de tareas/recordatorios. Ver scope-r5-organizations-tracking.md para criterios y pruebas de migración/formulario.
