# Documentación canónica por etapas

Cada proyecto mantiene un punto de entrada README.md que enlaza dot/README.md y dot/STATUS.md. Antes de definir arquitectura, dot define enfoque de autenticación, roles y recursos protegidos (obligatorio salvo petición explícita del usuario según autenticacion.md), destino app, runtime AI y dirección del dashboard (central elegida en esta definición; diseño/auth/despliegue pueden quedar pending mientras se define contrato). Usar [plantilla de proyecto](../templates/proyecto.md).

| Etapa | Ruta sugerida en dot/ | Fuente canónica |
|---|---|---|
| Inicio | README.md y STATUS.md | Índice y handoff compacto; enlazan estado observado, no métricas copiadas |
| Descubrimiento | 01_brief.md | Problema/alcance, decisiones y autoridad, destino antes de arquitectura |
| Requisitos | 02_requisitos.md | Requisitos y AC-ID; otras etapas enlazan IDs |
| Diseño | 03_diseno.md | Mockups/opción/version aprobados, arquitectura/interfaces/datos después de decidir destino |
| Plan | 04_plan.md | Tareas/dependencias/responsables/límites; AUTH-01 y DASH-01 obligatorias |
| Ejecución | 05_ejecucion.md | Handoffs, operación/run y punteros al control autorizado |
| Validación | 06_pruebas.md | AC-ID→test-ID→manifiesto/evidencia por SHA |
| Entrega | 07_entrega.md | SHA aprobado, URL, receta/runbook/límites/rollback |
| Aprendizaje | 08_retro.md | Fricción/evidencia/causa/impacto/propuesta y devolución saneada |

Estas rutas son la convención para proyectos nuevos, no una obligación de duplicar archivos existentes. Si docs/spec.md ya es la spec canónica, el índice la declara y enlaza; no crear 02_requisitos.md con otra copia. Crear documentos al llegar a la etapa y marcar pendientes explícitos. Cada documento tiene revisión/estado/autor-rol y referencias de decisión; el contrato congela hashes. Plantillas de spec/tarea/aceptación/resultado siguen siendo formatos del contenido correspondiente.

STATUS.md contiene máximo: última observación/cursor, foco actual, run/task/round, base/candidato/ref de contrato, decisiones o bloqueo, último hito con evidencia y siguiente acción/rol. No es un motor ni otra fuente de verdad: estado live, tests y costes vienen del journal/proyección; el Markdown referencia cursor/fecha para no fingir frescura. Dot/coordinador actualiza STATUS en un handoff o hito, no exige editar ocho documentos en cada heartbeat.

Para retomar: índice→STATUS→brief→spec/diseño canónicos→tarea concreta→último handoff/evidencia. El índice no amplía permisos del coder: solo recibe inputs aprobados/copias congeladas y allowlist. La documentación se deriva de inputs del usuario; una ambigüedad que cambia alcance/destino/criterios se resuelve antes de congelar. No recuperar contexto leyendo sesiones personales.

Un dato, una autoridad: requisitos02, diseño03, tareas04, journal/control para ejecución, manifiesto firmado por proceso confiable más revisión dot para aceptación (hashes no son firmas criptográficas). Resto de documentos enlaza. No editar controles/especificaciones a mitad de una corrida ni actualizar pins silenciosamente. Para consumidores existentes, una migración explícita define mapa de rutas y nueva versión; el survey no se reorganiza.
