# Casos de uso e historias · r4
Alcance vigente: campaña general + empresas/contactos + seguimiento manual; envío fuera de la app confirmado. Criterios normativos AC en [acceptance.md](acceptance.md); no mantener otra lista contradictoria de estados.

| Historia | Caso de uso y resultado | Criterios |
| --- | --- | --- |
| US-01 Acceso sencillo | Operador configura contraseña propia al primer inicio, entra y cierra sesión. Ninguna clave por chat. | AC-01, AC-02 |
| US-02 Organizaciones y contactos | Dar de alta empresa o beneficiaria con el mismo formulario; tres pares nombre/email por defecto, uno obligatorio y dos opcionales vacíos; filas usadas completas, sin límite rígido de tres. Archivar sin perder pasado. | AC-03, AC-04 |
| US-03 Campaña general | Elegir tema, objetivo, audiencia/tono y formatos; asociar múltiples destinatarios de distintas empresas sin personalizar texto por empresa. | AC-05, AC-06 |
| US-04 Base confiable | Revisar fuentes vigentes y hechos respaldados; detectar datos ausentes sin inventarlos. Handout no prueba hechos de negocio. | AC-07, AC-08 |
| US-05 Memoria útil | Consultar historia por tema/campaña antes de redactar, priorizar distribuido manualmente y respuestas relevantes; advertir repeticiones/contradicciones. | AC-09, AC-10 |
| US-06 Generación y revisión | Preparar cuatro formatos para caso 3D, revisar grounding/coherencia y devolver salida no aprobada ante fallos. | AC-11, AC-12 |
| US-07 Retomar y recuperarse | Conservar contexto, preguntas, intentos y versiones por campaña; fallo de historia no equivale a vacío. | AC-13, AC-14 |
| US-08 Aprobar/exportar | Revisar bundle exacto con fuentes e historia, editar sin alterar pasado, aprobar y exportar localmente sin envío. | AC-15, AC-16, AC-17 |
| US-09 Registrar distribución | Declarar envío externo por contacto o lote (versión/fecha), o publicación pública sin destinatario ficticio. | AC-18, AC-19, AC-20 |
| US-10 Seguimiento humano | Registrar respuesta, nota y próximo paso; alertar duplicado por destinatario/campaña/versión, corregir errores con trazabilidad. | AC-21, AC-22, AC-23 |
| US-11 Operación segura | OpenRouter configurable económico, secretos solo backend, límites técnicos sin presupuesto monetario local duplicado y ninguna acción externa automática. | AC-24, AC-25, AC-26 |
| US-12 Mesa editorial | Navegar Campañas/Organizaciones/Seguimiento(editor de Publicaciones y Comunicaciones dirigidas)/editor en desktop/móvil, reanudar trabajo, foco/errores claros y aprobación visual de cambios materiales. | AC-27, AC-28 |
| US-13 Evidencia de ejecución | Distinguir status del agente app, controles del coder, pruebas realizadas/omitidas y coste unknown; seguimiento local solo lectura. | AC-29, AC-30 |

Ejemplo integral sintético: campaña “Acompañamiento digital”, dos empresas de ejemplo y tres contactos ficticios; mismo email general v1, envío externo declarado para dos y pendiente para uno. Editar genera v2; los dos registros históricos siguen unidos a v1. Una respuesta manual y un próximo paso aparecen solo en su destinatario. Un post LinkedIn se registra por publicación, nunca multiplicado por contactos.
