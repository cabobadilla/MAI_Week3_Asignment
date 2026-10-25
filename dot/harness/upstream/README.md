# dotHarness

**0.9.0-pilot — verificación de despliegue real y aprendizaje del portal, con0.8 preservado.**

Dot conversa con el usuario, mejora alcance y criterios, produce especificación y pruebas de aceptación, y entrega una tarea acotada a OpenCode con un modelo económico explícito. Un ejecutor local futuro captura un candidato identificable y aplica controles deterministas; dot revisa de forma independiente los requisitos y riesgos del mismo candidato. Éxito de CLI y entrega aceptada son resultados distintos.

Un host, un ejecutor y una tarea activa. Contiene documentación, contratos, plantillas y un adaptador/verificador acotado a UI estática. El piloto separado genai-value-survey fue implementado por OpenCode y validado; no es un ejecutor general ni autoriza publicación. Distinguir requisitos propuestos de controles observados en docs/verificacion.md.

## Presentación

[Cómo funciona dotHarness](docs/presentacion-harness.html): 12 slides en español, en un HTML autónomo para descargar y abrir sin conexión. Navegación con flechas, botones o deslizamiento, adaptable a móvil e impresión. El portal se muestra como proyecto separado en construcción.

## Mapa

- [Documentación por etapas](docs/proyectos.md) y [STATUS](dot/STATUS.md): fuentes canónicas para retomar/validar.
- [Seguimiento por proyecto](docs/seguimiento.md): DASH-01 obligatoria; dirección Cloudflare central; diseño/auth/despliegue pendientes, sin servicio implementado.
- [Definición](docs/definicion.md): responsabilidades, contrato, bootstrap y límites.
- [Autenticación MUST por defecto](docs/autenticacion.md): plan v4, contrato v6, excepción solo por petición explícita del usuario y gate documental de evidencia de entrega.
- [Arranque y destino](docs/arranque.md): elección local_simple/docker_local/cloudflare antes de arquitectura; baseline Wrangler local y OpenRouter solo para LLM de la app.
- [Diseño UI aprobado](docs/diseno-ui.md): mínimo dos mockups y decisión humana antes del coder; comprobación en adaptador 0.4; autenticidad de aprobación revisada por el coordinador.
- [Aprendizaje por ejecución](docs/aprendizaje.md): retro obligatoria, devolución saneada y promoción versionada.
- [Workflow y piloto](docs/workflow.md): estados, gates, reentrada y experimento separado.
- [Compatibilidad OpenCode](docs/compatibilidad.md): inspección local, fuentes y huecos explícitos.
- [Índice de coordinación](dot/README.md): orden de lectura y evidencia saneada.
- [Plantillas](templates/): spec, tarea, aceptación, resultado, manifiesto y JSON Schema de entrada.
- [Evidencia saneada](dot/evidence/README.md): checks de esta copia y límites de resúmenes históricos.

`AGENTS.md` mantiene este harness; no se copia como instrucciones del coder consumidor. Los análisis de cada proyecto viven en `dot/`. No usar dotHarness como proyecto piloto.

Para proyectos UI, [Playwright headless es obligatorio](docs/frontend.md): desarrollo y validación final independiente tienen evidencias separadas. El piloto actual es genai-value-survey; normalize_tags queda sustituido.

[Backlog ACCEL-01](dot/backlog/ACCEL-01.md) evalúa scaffolds y aceleradores versionados; no implementados.

## Bootstrap propuesto (manual)

1. Elegir una versión y snapshot de dotHarness; verificar el digest del paquete.
2. Copiar físicamente plantillas e instrucciones específicas al consumidor bajo `dot/harness/`. Preservar su AGENTS existente. Registrar origen, hashes, versión y overrides en el manifiesto.
3. Completar requisitos y pruebas del proyecto; dot congela spec, aceptación, contrato, comandos de validación y configuración. Antes de ejecutar, el ejecutor copia esos insumos a un área de control fuera del alcance editable del coder.
4. No usar symlinks privilegiados, instrucciones remotas, herencia viva o autoactualización durante una corrida. Actualizar exige otro manifiesto y run.

Identidad inicial sin commit: `VERSION` + SHA-256 del paquete. Paquete = README.md, AGENTS.md, VERSION, todos los archivos de docs/, templates/, scripts/ y tests/, y todos los Markdown de dot/. Excluye `.git/`, `dot/evidence/`, `dot/runs/` y `lecciones/` (evidencia/propuestas, no instrucciones activas). Ordenar paths POSIX por bytes UTF-8; emitir por archivo `path + TAB + sha256(bytes) + LF`; SHA-256 de la concatenación UTF-8. Rechazar enlaces y archivos especiales. La evidencia registra la lista. Así no hay hash autorreferente. Consumidores conservan los bytes copiados y el digest; `source_git_sha=null` solo en modo `local-snapshot`. Una release futura requiere commit explícito además del digest; la fase piloto permite commits locales revisados, sin remoto.

Las plantillas están en borrador: `REPLACE_*`, ceros y null sin completar bloquean preparación. Ninguna plantilla autoriza gasto. El ejemplo OpenCode es documental, deny-all y con compatibilidad local pendiente.

## Verificación de despliegue0.9

[Despliegue verificable](docs/despliegue.md): política/recibo v1, compatibilidad en target real, CPU separada de wall time, assets reales y recorrido autenticado. check_release.py valida evidencia normalizada; no despliega ni acepta por sí solo. Confirmación del usuario y checks públicos se registran por separado. Plan v4/contrato v6 y pins existentes se conservan.

## Política de reparación 0.6

Generación inicial (ronda 0) y hasta dos reparaciones (rondas 1 y 2). Si la segunda reparación falla, `blocked` y escalación al usuario antes de otro intento. Planes v2/v3/v4 fijan `execution.max_repairs=2` y el adaptador exige `--round` para inferencia; rechaza ronda 3 antes del CLI. El coordinador mantiene el historial protegido: este gate no es un contador durable ni impide falsear una ronda. Ver [workflow](docs/workflow.md) y [contrato v6](templates/contrato.schema.json) (la política de dos reparaciones se introdujo en v4). Planes v1 conservan máximo una reparación, sin migración automática.

## Verificación ejecutable 0.3

[scripts/verify_frontend.py](scripts/verify_frontend.py) implementa el gate de UI estática; [contrato operativo](docs/verificacion.md). No es un ejecutor general de backends. La autorización actual incluye commits locales revisados y cuota GO existente; no exige prueba negativa previa de cuota/cargos desconocidos. Detener ante aviso real de compra, pago adicional o cuota agotada; coste no reportado es no disponible. Sin remoto ni publicación.

El primer ciclo real de [lecciones](lecciones/genai-value-survey-survey-r1-final-isolated.md) conserva los fallos y la solución completa verificada de sesión/agente. Política nueva, sin cambio automático al pin 0.3.1 del piloto.

Regresión offline: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v. La prueba con servidor/CLI falsos requiere loopback local, nunca proveedor real. Nuevas interfaces: --plan obligatorio; plantilla contrato v6 y plan v4 (conserva límite de dos reparaciones). No migrar consumidores ni desplegar automáticamente.

## Uso reproducible (sin proveedor real en los tests)

Requisitos de mantenimiento: Python3 y Git en un entorno Unix; piloto verificado en macOS, sin certificación Windows. No se instala nada automáticamente. Desde la raíz:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/check_plan.py --help
python3 scripts/run_opencode.py --help
python3 scripts/verify_frontend.py --help
python3 scripts/check_release.py --help
```

Para un consumidor, copiar físicamente las plantillas/scripts elegidos según el manifiesto, fijar versión/digest y hash de cada copia. AGENTS.md de este repo no se copia. Completar plan/spec/aceptación y controles en un directorio externo protegido, con destino elegido y configuración local del coder; los REPLACE/null del ejemplo bloquean implementación. Rutas siguientes son parámetros de ejemplo, nunca rutas de esta Mac:

```sh
python3 scripts/check_plan.py /ruta/control/plan.json --preflight-only
python3 scripts/run_opencode.py --plan /ruta/control/plan.json --preflight-only --opencode /ruta/bin/opencode --cwd /ruta/control/coder --prompt /ruta/control/prompt.txt --out /ruta/control/preflight-001
```

Ese segundo comando inicia y detiene un servidor propio de compatibilidad sin inferencia. Para implementar con plan v4, omitir --preflight-only y añadir --round 0 (o 1/2 para reparación reconciliada) solo tras autorización/plan/mockups vigentes; usar otro --out nuevo y presupuesto/aislamiento acordados. No relanzar un resultado incierto. El adaptador sigue acotado al agente survey-coder y modelo GO del piloto; no se promete selección universal de agentes.

Validación UI requiere Node/Playwright/Chromium/Wrangler externos fijados y un contrato operativo completo según docs/verificacion.md; no basta ejecutar tests del harness. El bootstrap es manual, no un instalador ni un ejecutor general. Docker, recursos Cloudflare, proveedor real y publicación requieren permisos separados.

## Seguimiento y publicación

Cada proyecto incluye DASH-01 y el mapa de documentación canónica. La dirección de dashboard es Cloudflare central; resolver diseño/auth antes de implementarlo, sin bloquear definir su contrato. Estado de despliegue pending; no hay servicio live de proyecto en este repo. Esta copia tiene historia inicial saneada; el original y evidencias privadas permanecen fuera. No se publican rutas home ni artefactos locales. No usar resúmenes históricos para certificar candidatos nuevos.
