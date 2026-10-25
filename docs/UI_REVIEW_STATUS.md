# Revisión visual pendiente · estado comprobado
Estilo Mesa editorial B/v1 elegido por el usuario. Los artefactos históricos bajo dot/design/gwa-ui-v1 se preservan, con su metadata original de creación; decisión posterior en dot/design-decisions/gwa-ui-v1-B-selection.json.

## Qué existe y cómo verlo
Abrir con doble clic en navegador local `dot/design/gwa-ui-v1/option-b.html` o `index.html`. HTML autónomo sin servidor ni conexión. Capturas desktop/móvil en `dot/design/gwa-ui-v1/screenshots/b-*.png`. Evidencia de visualización previa en `evidence.json`; estas son pantallas v1 y no la ampliación de Empresas/Seguimiento.

## Qué aún no existe
Actualización: ya existe propuesta local dot/design/gwa-ui-v2/index.html con B/v2.1 (campaña) y B/v2.2 (central), 34 checks automáticos de prototipo pasados, aún sin aprobación humana. Se preserva la definición textual en `docs/specs/sponsor-materials/ux.md`, secciones Rutas y pantallas y Detalles de interacción para revisión B v2. No presentar v1 como aprobación de esos detalles nuevos.
T-01 presentó dos disposiciones acotadas de seguimiento dentro del estilo B: tabla con panel lateral o pestaña de campaña; alta de empresas/contactos, preview de lote, duplicado, corrección y estados móvil/error. Revisar versión/hash/capturas y obtener decisión antes de coder visual. No se implementaron estas pantallas.

## Backend que puede avanzar independientemente
Núcleo configuración/SQLite/empresas/contactos/campañas/destinatarios/auth/versiones/aprobación/exportación y registro manual ya tiene tests. Seguimiento/correcciones T-09A integrado25/25 después de este checkpoint. Después: fuentes e historia/vector RAG T-05, grafo y recuperación/errores con proveedor simulado T-06, HTTP/sesión/CSRF e integración T-10, evaluación T-11. Elegir modelo OpenRouter antes de pruebas reales; nunca sustituir el coder GO por el LLM de app.
Sin Library, servidor público, despliegue ni modificación de dotHarness compartido. UI y calidad LLM no se certifican con suites backend.

## Paquete de revisión local para iOS (sin transferir)
B/v2.1 Campaña con seguimiento concentra el trabajo dentro de una campaña y muestra contenido/destinatarios/seguimiento juntos. Recomendada para el MVP: la versión y el grupo de contactos quedan en contexto. B/v2.2 Seguimiento central facilita revisar varias campañas por filtros de campaña/empresa/canal. Mismo directorio Empresas en ambas. El usuario aún debe ver y elegir; estilos/labels de maquetación no son reglas finales de negocio.
Capturas validadas, rutas desde raíz: `dot/design/gwa-ui-v2/screenshots/campaign-tracking-normal-mobile.png`, `central-tracking-normal-mobile.png`, `campaign-companies-normal-mobile.png`; desktop cambia sufijo mobile por desktop. No URL pública ni Library. Las rutas locales por sí solas no dan acceso desde iOS; requieren un medio de visualización aprobado del chat, sin inventar enlace.
