# Especificación — REPLACE_TASK_ID

Estado: draft. Revisión: REPLACE_REVISION. Autor: dot + usuario.

## Problema y resultado observable

Usuario, situación actual, ejemplo concreto de antes/después y razón del cambio:

## Alcance

Incluido, excluido, interfaces/firma, entradas/salidas, errores y casos límite:

## Criterios

| ID | Dado / cuando / entonces observable | Obligatorio | Test ID externo |
|---|---|---|---|
| AC-01 | REPLACE | sí | TEST-01 |

## Límites y decisiones

Riesgos, requisitos no funcionales, regresiones y dudas que bloquean preparación:

## Congelación

Revisión acordada por/fecha; aceptación asociada/revisión; task_id y contrato.
El hash se guarda fuera de este documento en el contrato. Un cambio genera otra
revisión y run; la conversación no actualiza silenciosamente estos bytes.

## UI y destino (contrato v2)

project_kind: cli/backend/ui. Si UI, criterios E2E Playwright obligatorios, recorridos, viewports, privacidad y estados screenshot. deployment.mode: local_simple/docker_local/cloudflare; arranque local fijado, publish_authorized=false salvo permiso separado. No inferencia en runtime salvo requisito explícito.

## Diseño UI aprobado (obligatorio antes de implementar)

Design ID/version, registro dot/, hash, dos opciones+capturas desktop/móvil/estados, opción elegida y referencia de aprobación explícita del usuario: REPLACE. Estado inicial pending. Criterios visuales→estados→test IDs: REPLACE. Proteger registro/artefactos en contrato; un cambio visual material exige nueva versión y aprobación. Plan protegido verificado por adaptador; autenticidad humana verificada por dot.

## Decisiones previas a arquitectura

Plan/version/hash y referencia de elección explícita usuario REPLACE. Destino REPLACE (local_simple/docker_local/cloudflare); baseline Workers/Wrangler local, bindings solo necesarios; excepción incompatible aprobada REPLACE o ninguna. Runtime LLM sí/no y OpenRouter si sí, sin claves frontend; decisión separada de modelo del coder. Sin respuesta de destino no elaborar arquitectura definitiva.

## AUTH-01 — autenticación MUST

Toda app nueva requiere autenticación por defecto. Antes de arquitectura: enfoque, roles y recursos protegidos REPLACE. Plan v3/contrato v5 fijan authentication y tests por grupo: unauthenticated, session_logout, authorization. Sin definición: blocked. Omitir solo por petición explícita del usuario, con excepción/razón/referencia verificadas; local/simple/demo no son excepción.

Checklist de entrega: verificar rutas/URLs/API sin sesión, login/sesión/logout y autorización según roles/propiedad del alcance; enlazar test IDs y resultados finales al SHA/plan exactos. Pasar check_delivery.py con reporte protegido; un fixture de identidad no es autenticación implementada ni prueba de producción. Conservar delivery_accepted=false hasta revisión dot. No proveedor, servicio, instalación ni migración implícitos. Ver docs/autenticacion.md del snapshot fijado.

Passwords, solo si se eligen: mínimo8 caracteres por defecto, permitir más largos, no numeric-only. Plan v4/contrato v6 fijan política común UI/backend/provisioning, hashing y rate limiting. Pruebas7rechaza/8acepta/mayoracepta en cada superficie aplicable; mayor mínimo solo con referencia explícita. Evidencia solo longitudes/resultados, sin credenciales. Ver docs/autenticacion.md0.8.

## Despliegue real — RUNTIME-COMPAT-01 / DEPLOY-ROOT-01

Definir target/runtime, features/parámetros críticos, dependencia/version/integridad y CPU/wall/fuente por entorno. Congelar presupuestos y referencia humana para cualquier aumento. Expected viene de aceptación, no del candidato. `/`, panel y APIs deben probarse con assets reales; auth guard precede rewrite de app. Ver docs/despliegue.md y política/recibo v1. No presume deploy autorizado.
