# Delta confirmado r5 · Organizaciones y contexto de comunicaciones
Autoridad: Sentinel_689d058304f0819183b2ff7ba6763601 (tres pares nombre/correo), Sentinel_23821873ff748191aec709897ef099c8 (mismo formulario para beneficiarias/municipalidades), Sentinel_b00bdae4771c819188c03c122a276d91 (dos subpantallas, no CRM), Sentinel_6b09aed4b94081918097d7c06237d9b5 (continuar producto funcional). Este delta prevalece sobre postergación de beneficiarias y opciones de Seguimiento anteriores. No altera propósito/fuentes del piloto ni autoriza envío/publicación.

## Contrato mínimo
UI Organizaciones: un catálogo/formulario para empresas y beneficiarias como municipalidades. Tres pares nombre/email por defecto: primer contacto obligatorio, dos opcionales. Cada fila usada tiene ambos valores; fila nueva completamente vacía se ignora; parcial inválida bloquea todo guardado. No límite rígido de tres: conservar/mostrar contactos adicionales y permitir añadir otro. Cambios por ID, contactos omitidos se preservan; no borrado implícito. Duplicado de email por organización según normalización existente; mismos emails entre organizaciones permitidos, dedup de destinatarios por campaña se mantiene. Un nombre similar no fusiona entidades automáticamente.
Roles: requerimiento firme de catálogo compartido aportante/beneficiaria. Representación propuesta flexible de uno o ambos roles; UI debe presentar esa posibilidad para revisión, sin asumir que una organización tenga ambos. El rol aportante significa relación prevista/potencial, nunca patrocinio/convenio confirmado. No nuevas funciones de beneficiarios.
Persistencia propuesta compatible: conservar tabla company e IDs/FKs como legado interno del catálogo, añadir roles_json mediante migración versionada2; no tres columnas de contacto ni tablas por rol. contact continúa 1:N. No renombrar/destruir tablas ni snapshots históricos. Nueva API pública valida nombre/email aunque servicios legacy permitan datos históricos sin nombre. Migración y formulario se prueban por separado; no afirmar ejecutada sobre BD de usuario.

## Seguimiento confirmado: dos subpantallas
1. Publicaciones: registro manual de item/versión exacta, medio y fecha de publicación externa; URL opcional. Sin destinatario inventado. Nota manual opcional de reacciones es propuesta mínima, no analítica/integración automática. Exportar no acredita publicar.
2. Comunicaciones dirigidas: elegir organización y ver hilo de interacciones con contactos, versión/mensaje declarado enviado, fecha, respuestas y notas manuales. Fin exclusivo: contexto selectivo para redactar y advertir repeticiones/contradicciones. No CRM, funnel, oportunidad, próxima tarea comercial, recordatorio, inbox o envío integrado. No personalización automática añadida por este delta.
Eliminar próximos pasos comerciales del flujo visible y de nuevas acciones públicas. Registros next_step antiguos se conservan y pueden mostrarse como notas históricas en auditoría, sin ejecutarlos como tarea/recordatorio ni perder sus valores. No destruir datos por cambio de alcance.
El historial alimenta generación solo tras selección pertinente; prioriza distribuciones declaradas y respuestas, no exportados. Textos históricos son datos no confiables. No copiar nombres/emails estructurados al LLM de email general. Repetición advierte, no bloquea toda generación por sí sola.

## Criterios adicionales trazables
- ORG-FORM01: 1/3/4 contactos válidos guardan; primer contacto requerido, otros vacíos no generan filas.
- ORG-FORM02: parcial/nombre faltante/email inválido/duplicado falla atómicamente; rollback incluso en transacción externa.
- ORG-EDIT01: edición por ID preserva contactos omitidos, históricos y organizaciones; ID ajeno rechazado.
- ORG-MIG01: fixture SQLitev1 migra a v2 con mismos IDs/FKs/snapshots/contenido; retry no duplica, fallo rollback, versión desconocida sin reset.
- ORG-ROLE01: catálogo compartido valida roles, sin convertir rol en alianza confirmada; campañas admiten selección explícita de contactos de cualquier rol y conservan dedup.
- TRACK-PUB01: registro público versión/medio/fecha, sin destinatario ni autoenvío; corrección conserva original.
- TRACK-DIR01: hilo local por organización con fecha/contacto/versión/respuestas/notas; aislamiento y contexto selectivo, sin tareas comerciales.
- TRACK-VIS01: mockup nuevo refleja las dos subpantallas, sin pedir elección entre variantes B/v2 supersedidas; detalles sustantivos se revisan antes de UI final.

## Orden de unidades
ORG-01 migración compatible (storage +002 SQL); ORG-02 guardado atómico de organización/contactos; ORG-03 mockup de formulario; TRACK-01 mockup de dos subpantallas; backend historia/runs/grafo por unidades de TASK_SIZING; luego HTTP/formularios/pantallas e integración. Una GO activa/host,600s/ronda, inicial+2reparaciones sin reiniciar contador. Mocks hasta elegir modelo OpenRouter. B/v1 estilo aprobado; B/v2 alternativas supersedidas, no declaración ficticia de aprobación visual nueva. Sin Library/push/deploy/harness compartido.
