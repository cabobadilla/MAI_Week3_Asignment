# Aprendizaje obligatorio por ejecución

Cada ejecución, reparación, fallo, bloqueo o cancelación produce una retro breve; no requiere éxito del coder. Dot/coordinador la conserva en el consumidor bajo `dot/` usando [la plantilla](../templates/retro.md). El coder puede informar fricción, pero no recibe escritura en dotHarness ni autoridad para cambiar controles.

Registrar run ID/ronda/estado, versión y SHA del harness, base/candidato, versiones de herramientas, fricción, impacto y tiempo medido o no disponible, evidencia trazable, causa comprobada separada de hipótesis, solución temporal, mejora propuesta y prueba de regresión con su estado real. Un mismo reporte puede agrupar varias rondas siempre que las identifique.

El coordinador devuelve una copia saneada a `lecciones/<proyecto>-<run-id>.md` en dotHarness, con referencia al reporte consumidor, su commit/hash y las corridas. Quitar credenciales, tokens, sesiones privadas, datos personales, respuestas de usuarios, PDF y rutas personales; conservar IDs técnicos propios y hashes necesarios. Resumir evidencia sensible por hash y tipo, sin copiar su contenido. La copia no concede permiso de publicación ni comunicación externa.

La retro es salida de auditoría, no parte editable del candidato. Su ubicación y el momento de escritura deben fijarse antes del run. Si un contrato ya congelado no permite agregar archivos después, preservar el candidato y guardar el reporte en una rama/worktree de auditoría del mismo repositorio bajo `dot/`; registrar esa ubicación expresamente. No desactivar dirty/untracked, cambiar baselines silenciosamente ni reescribir un contrato activo para guardar la retro.

Las propuestas ingresan como `propuesta`, con responsable dot/coordinador. Revisar causa, alcance y regresión; probar la mejora fuera de corridas activas y registrar resultado antes de promoverla a otra versión. Una solución observada en un piloto no es garantía general. Los cambios documentales pasan revisión estática; los controles ejecutables requieren su regresión real. Puede marcarse `en_prueba`, `promovida` (versión/commit/pruebas), `descartada` (motivo) o `pendiente_evidencia`.

Actualizar VERSION, docs/contratos/plantillas afectados y digest al promover. Los consumidores conservan su pin y overrides hasta una actualización deliberada; ninguna lección cambia instrucciones o aceptación a mitad de tarea. `lecciones/` es un registro versionado de propuestas y evidencia, no instrucciones activas ni contenido del paquete copiado a consumidores. No requiere servicio, scheduler ni agente nuevo.
