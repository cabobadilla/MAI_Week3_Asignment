# Plantilla mínima de documentación del proyecto

Copiar/adaptar al consumidor tras inspección. No copiar el AGENTS del harness. Crear README/STATUS y documentos por etapa; conservar specs existentes como canónicas si procede. El índice es mapa, no duplicación. REPLACE bloquea congelación, no autoriza implementación/publicación.

## dot/README.md (índice)

Proyecto: REPLACE. Harness versión/digest: REPLACE. Fuente canónica por etapa:

| Tema | Ruta canónica existente o sugerida | Revisión/estado |
|---|---|---|
| Brief/decisiones destino | dot/01_brief.md | REPLACE |
| Requisitos/AC-ID | dot/02_requisitos.md o spec existente | REPLACE |
| Mockups/arquitectura | dot/03_diseno.md | REPLACE |
| Plan/tareas | dot/04_plan.md | REPLACE |
| Handoffs/ejecución | dot/05_ejecucion.md | REPLACE |
| Pruebas/evidencia | dot/06_pruebas.md | REPLACE |
| Entrega/runbook | dot/07_entrega.md | REPLACE |
| Retro/devolución | dot/08_retro.md | REPLACE |

Punto de reanudación: STATUS.md. Control/journal/proyección: referencia relativa autorizada REPLACE, fuera del área writable del coder. Decisiones humanas: referencias a inputs aprobados. Evidencias grandes/privadas en control local, no Git.

## dot/STATUS.md (handoff compacto)

Observado en: REPLACE. Último cursor/event ID: REPLACE o no disponible. Foco: REPLACE. Run/task/round: REPLACE. Base/candidato/contrato: referencias REPLACE. Último hito/evidencia: REPLACE. Pendiente/bloqueo: REPLACE. Siguiente acción/rol: REPLACE. No es estado live; consultar proyección/journal canónicos.

## Fila obligatoria en dot/04_plan.md

DASH-01 — Dashboard de seguimiento de lectura. required=true; estado pending; dirección central documentada cuando aplique; diseño/auth/implementación/despliegue pending, sin inferir autorización. Referencia de contrato: seguimiento v1 y plan del proyecto. Alcance/criterios según docs/seguimiento.md del harness copiado y fijado. Mockups aprobados antes de UI. No marcar completado por tener estructura de eventos ni crear recursión de dashboards.

## AUTH-01 — autenticación MUST

Toda app nueva requiere autenticación por defecto. Antes de arquitectura: enfoque, roles y recursos protegidos REPLACE. Plan v3/contrato v5 fijan authentication y tests por grupo: unauthenticated, session_logout, authorization. Sin definición: blocked. Omitir solo por petición explícita del usuario, con excepción/razón/referencia verificadas; local/simple/demo no son excepción.

Checklist de entrega: verificar rutas/URLs/API sin sesión, login/sesión/logout y autorización según roles/propiedad del alcance; enlazar test IDs y resultados finales al SHA/plan exactos. Pasar check_delivery.py con reporte protegido; un fixture de identidad no es autenticación implementada ni prueba de producción. Conservar delivery_accepted=false hasta revisión dot. No proveedor, servicio, instalación ni migración implícitos. Ver docs/autenticacion.md del snapshot fijado.
