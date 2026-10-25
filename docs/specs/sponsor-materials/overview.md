# GrowWithAI Sponsor Materials Agent · specs r4
Estado: alcance confirmado y especificación redactada, sin app implementada ni contrato de ejecución congelado. Esta revisión reemplaza alternativas previas incompatibles; índice canónico [README.md](README.md).

## Problema y resultado
Christian necesita comunicar el propósito/idea/valor de GrowWithAI de forma consistente, conservar qué contenido se usó y saber qué versión declara haber enviado a cada empresa/contacto. Hoy eso exige ensamblar documentos/borradores/listas y notas manualmente; no se ha medido un costo/tiempo base. El MVP reúne preparación y seguimiento local sin conectarse al correo o publicar.
Antes: un archivo exportado no permite saber a quién llegó qué versión. Después: una campaña general tiene fuentes/historia/piezas/versiones aprobadas y registro manual separado de envíos por contacto o publicaciones públicas. Ningún estado de exportación se interpreta como envío.

## One-liner Week 3
Mi agente ayuda a Christian a convertir fuentes verificadas e historia relevante de GrowWithAI en una campaña de cuatro formatos en una app local, reemplazando la preparación y trazabilidad dispersa entre archivos; recupera contexto, decide buscar más/preguntar y genera/revisa con estado persistente, entrega a una persona los vacíos/conflictos y la aprobación antes de exportar, y se considerará exitoso si produce una suite revisable en menos de 10 minutos en 4 de 5 pruebas, sin hechos materiales inventados ni exportación no aprobada. Es una meta de evaluación, no resultado observado.

## Framework del handout
| Campo | Decisión r4 |
| --- | --- |
| Objetivo | Suite general coherente con fuentes/historia y trazabilidad manual de distribución |
| Superficie | Web local Mesa editorial B, operador único con contraseña propia |
| Pasos | Campaña/destinos→fuentes/historia→decidir pregunta/ampliación→generar→revisar→aprobar/exportar; registro manual externo después |
| Herramientas | Lectura/RAG/historia/duplicados; borradores/checkpoints locales; pregunta; aprobar/exportar/registrar solo por acción humana |
| Memoria | SQLite negocio y checkpoints, versiones inmutables/context snapshots por campaña/run, sin mezcla accidental |
| Nunca | Enviar/publicar/comprar/leer bandeja o inventar patrocinio/precio/convenio/resultado; secretos o contactos al prompt |
| HITL | Vacíos/conflictos/límites, repetición advertida, aprobación exacta, preview/declaración de registro y corrección |
| Fallos | Reintentos/tiempos/pasos acotados; checkpoint/needs_human/no aprobado, reconciliar antes de repetir |
| Éxito | Evaluación end-to-end y fallos, tests reales por candidato y objetivo de calidad/tiempo anterior |

## Alcance confirmado por usuario
Sentinel_83058765897481918dd7fe55e183ae63: “esto si me sirve... procede a generar las specs”, después de propuesta campaña general + empresas/contactos + seguimiento manual, envío fuera.
1. Campaña con tema/objetivo/segmento/tono/formatos y múltiples contactos de empresas. El contenido de email es general, común, sin personalizar empresa/persona.
2. Caso académico 3D: LinkedIn, email general, artículo breve y variantes de anuncio. Uso cotidiano puede elegir subconjunto; demo cubre los cuatro.
3. Fuentes vigentes + historia temática por campaña; prioridad a contenido distribuido y respuestas relevantes, con evidencia, vacíos/contradicciones y advertencias de repetición. Historia por destinatario solo para seguimiento/duplicados, no personalización.
4. Revisión humana, versiones/aprobaciones/exportación local. Registro manual individual/lote de versión/destino/fecha y respuesta/nota/próximo paso; publicación pública sin contacto. No envío/publicación desde app.
5. Contraseña propia/simple, app/datos locales, Python virtualenv, LLM OpenRouter modelo configurable pendiente y barato preferido; presupuesto en API key del usuario.

## Contexto real del piloto
[Documento base v0.2](../../references/extracted/proyecto_formacion_digital_ia_base_v01.txt) p010/p012/p014/p016/p018/p020 y [resumen v0.2](../../references/extracted/resumen_formacion_digital_ia_chile.txt); hashes/procedencia en [manifest](../../references/manifest.json), decisiones sintetizadas en [PROJECT_BRIEF.md](../../PROJECT_BRIEF.md).
15 jóvenes de 18–29, dos perfiles de entrada; curso3 semanas con6 clases de90min (martes tarde-noche y sábados), tareas domingos y CV digital final; otras3 semanas de consultas escritas y sesión individual30min/alumno. Gratuito para jóvenes/comuna, patrocinio por conseguir y apoyo comunal flexible no confirmado. Usable desde celular; wifi propio o posible sala comunal. Certificado propio, 80% asistencia y aprobación tareas/CV; aliado certificador futuro sin convenio. Christian dirige alianzas y su socia ejecución; ambos crean contenidos/enseñan. Nombre GrowWithAI provisional, propósito social sin afirmar constitución legal; forma jurídica abierta. No fechas/montos/alianzas/resultados laborales inventados ni promesa de empleo.

## No alcance y pendientes verdaderos
[Fase futura](future-scope.md): workflows ampliados de beneficiarias/CRM, personalización, sender integrado, bandeja, sync, aperturas, automatizaciones/pagos/deploy. Registrar un próximo paso no crea recordatorio. No subir a Library.
Modelo LLM exacto pendiente; detalles visuales nuevos B v2 por aprobar (B v1 ya elegida). Backend/data/specs no se bloquean por aprobación visual ficticia. Antes de implementar: tareas con modelo coder/control externo/aislamiento/base Git/lock y driver Python verificados, no preguntas pendientes sobre alcance. Portal metadata/tracking DASH-01 obligatorio como requisito central pendiente de API/acceso/autorización, separado del despliegue app local; [diagnóstico](../../../dot/portal-tracking.md). Ninguna mutación del portal en esta tarea.

Delta vigente: catálogo único Organizaciones y Seguimiento en dos subpantallas según [r5](scope-r5-organizations-tracking.md). No hay próximos pasos comerciales visibles.
