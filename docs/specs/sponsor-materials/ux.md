# UX Mesa editorial ajustada · r4
Base B v1 elegida explícitamente; nuevos detalles B v2 descritos, no dibujados/aprobados en esta tarea. No bloquear redacción de specs por eso: gate de T-01 limitado al layout y estados nuevos antes de coder UI. Estilo común con sidebar y editor+evidencia. En móvil sidebar pasa a navegación compacta, contenido apilado y acciones visibles sin hover.

## Rutas y pantallas
| Pantalla/ruta propuesta | Contenido/acción principal | Estados importantes |
| --- | --- | --- |
| /setup, /login | crear contraseña propia/confirmar o entrar; sin pedir API key en UI | primer acceso, contraseña inválida, intento limitado, sesión vencida; no guardar texto plano |
| /campaigns | campañas por tema/última actividad, crear/retomar | vacío, cargando, error SQLite; generado/revisión/registro manual como badges separados |
| /campaigns/new, /campaigns/{id} | tema/objetivo/segmento/tono, formatos/suite académica, fuentes y lista de contactos destinatarios opcional | sin contactos válido para público; email general, no personalización; cambios de brief revisados |
| /companies, /companies/{id} | lista/búsqueda local, alta nombre empresa, tres pares nombre/email (uno obligatorio, dos opcionales; más si existen), editar/archivar | posible nombre duplicado advierte; email duplicado/incorrecto, sin contactos; no alianzas ficticias |
| /campaigns/{id}/work | fuentes y antecedentes seleccionados, preguntas, progreso; iniciar/reanudar | historia vacía≠error, espera humana, timeout recuperable, agotamiento sin aprobación |
| /campaigns/{id}/review | tabs LinkedIn/email/artículo/anuncios; versión y evidencia lateral; editar/aprobar/exportar | borrador sin aprobación, errores materiales, repetición advisory, v1 enviada/v2 nueva, aprobación revocada para edición |
| /tracking | filtro campaña/empresa/contacto/canal y vista por destinatario o público; respuestas/notas para contexto | seleccionado≠enviado, exportado≠enviado; fecha desconocida no se inventa; sin métricas de apertura |
| diálogo registro manual | tipo correo/publicación; versión exacta, fecha, contactos múltiples o canal público; preview y confirmación | duplicado advertido, razón de reenvío, corrección con motivo, lote atómico; botón nunca “Enviar” |

## Recorridos
Nuevo: login→campaña/objetivo→fuentes/antecedentes→preparar→pregunta si falta→revisión cuatro formatos→aprobar→exportar. Email es general para todos, sin nombres/variables por empresa. Destinatarios solo asociación y seguimiento; no cambian automáticamente texto.
Correo real ocurre fuera de la app. Después: Seguimiento→Registrar envío externo→elegir versión/fecha/contactos→revisar lote/duplicados→declarar registro. La app muestra “Envío registrado manualmente”, nunca “entregado/verificado”. Público: Registrar publicación externa sin destinatario. Corrección preserva evento anterior; nota/respuesta/próximo paso son manuales.
Volver tras cerrar: login y retomar campaña/run; preservar pregunta, no relanzar LLM automáticamente. Guardar borrador/selección explícito o autoguardado local señalizado; no confundir con aprobado. En error ofrecer retomar último checkpoint/revisar/cancelar, sin contador falso de avance.

## Detalles de interacción para revisión B v2
Dos variantes acotadas de la nueva distribución (A: tabla de destinatarios con panel lateral; B: detalle de campaña con pestaña Seguimiento), ambas dentro de estética B elegida, desktop/móvil. Presentarlas con captura y hashes; el usuario no tiene que volver a elegir estilo A original. Layout/acciones adicionales requieren aprobación de versión. Foco visible, labels y mensajes junto al campo, tablas reflow/apiladas en móvil, botones ≥44px táctil y modales con foco/escape/restauración. No clave real en captura.
No mockups B v1 alterados ni aprobación nueva inferida. Datos ficticios: empresas/contactos example.invalid, nunca contactos reales. Tests UI-01 y AUTH-* futuros; 48 comprobaciones previas solo prototipo v1.

## Estructura vigente r5 que sustituye variantes B/v2
Organizaciones comparte formulario para empresas/beneficiarias y campos de contacto completos. Seguimiento: /tracking/publications (item/medio/fecha, nota manual opcional) y /tracking/directed (hilo por organización/contactos/versión/fecha/respuestas/notas). El usuario ya confirmó esta estructura: no pedir elegir tabla global vs pestaña de campaña. Detalles visuales nuevos aún deben reflejarse en mockup y revisarse. Registros de tareas antiguos solo auditoría/notas históricas; sin control para crear próximos pasos comerciales.
