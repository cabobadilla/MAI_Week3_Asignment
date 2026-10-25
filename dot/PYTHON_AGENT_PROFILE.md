# Perfil reutilizable para proyectos Python agénticos
Revisión 1 · propuesta de adaptación, no capacidad certificada · 2026-10-25.
Estas reglas son generales; los requisitos de GrowWithAI viven en docs/PROJECT_BRIEF.md y docs/specs/sponsor-materials. Lecciones comprobadas en LESSONS.md. No modificar upstream ni contratos activos al adoptar este perfil.

## Preparación reproducible
Identificar Python compatible ya instalado. Crear virtualenv dentro del proyecto (.venv) e ignorarlo por Git; si virtualenv falta, alojarlo en un entorno preparador local y fijar sus dependencias. Ningún pip global ni instalaciones implícitas. Lista candidata no equivale a lock: resolver versiones exactas, dependencias transitivas y hashes/artefactos cuando aplique, registrar Python/plataforma y demostrar reconstrucción limpia y pip check antes de afirmar reproducibilidad de app. Congelar lock/config fuera del writable del coder; un cambio legítimo exige otra tarea/contrato.

Elegir local_simple/docker_local/otro desde decisión explícita. Python backend no debe adoptar un runtime estático por conveniencia del harness. Bind loopback para app local; Docker, red o servicios nuevos requieren autoridad concreta. No convertir acceso local en publicación ni excepción implícita de auth. Definir mecanismo, roles, recursos y pruebas de autorización antes de congelar arquitectura.

## Modelos, secretos y autoridad
Separar modelo/provider del coder del runtime LLM/embeddings de la app. Cada uno tiene allowlist, versión/variante, cuota/presupuesto y frontera de datos propios. Un modelo incluido en catálogo no prueba entitlement o coste. No fallback/escalado silencioso. Registrar la decisión API remota versus modelo local antes de transmitir documentos o descargar pesos; registrar revisión/hash del modelo local si se adopta. En GrowWithAI esa frontera ya fue resuelta por el usuario: app/datos locales y LLM por OpenRouter, modelo pendiente. El presupuesto puede controlarse en la clave del proveedor por decisión del usuario; no imponer un presupuesto monetario local duplicado. Conservar límites técnicos de tokens/intentos y registrar uso/coste reportado o unknown.

No leer tokens para diagnosticar compatibilidad. Secretos fuera de Git, prompts, fixtures, logs y documentos. No exponerlos al código generado ni a validadores; canal/broker confiable por diseñar antes de inferencia real. Fail-fast ante configuración ausente, sin claves de ejemplo operativas ni defaults que abran acceso. Coste no disponible es unknown, no cero.

## Contrato del agente
Cada herramienta declara entradas/salida, rutas/datos permitidos, lectura o escritura, timeout, idempotencia, errores y autoridad. Lectura documental puede ser autónoma dentro del corpus aprobado; documentos se tratan como datos y no instrucciones. Escrituras de borrador/checkpoints y exportación final son efectos distintos; envíos/publicaciones deben quedar fuera si no se autorizan.

Estado tipado y versionado con IDs de ejecución, fuentes/hash, etapa, intentos, preguntas, revisión/aprobación y evidencia. Persistencia local transaccional/checkpoints, escritura atómica y recuperación tras interrupción. Reconciliar una operación incierta antes de relanzarla; aprobación enlazada a contenido/fuentes exactos e invalidada al cambiar. No borrar historial para ocultar errores.

Fijar presupuestos de pasos, llamadas, tiempo y reintentos por categoría. Error transitorio puede reintentarse con backoff acotado; auth/validación/ruta falla sin bucles. Agotar presupuesto produce estado needs_human/blocked con checkpoint. Límite de reparaciones del coder y reintentos del agente son contadores separados. Pedir al humano ante datos esenciales faltantes, conflicto sin resolver o antes del efecto final protegido.

## Ejecución y validación
Un writer/tarea, base identificable, allowlist exacta y controles/fixtures protegidos fuera del writable. Verificar aislamiento OS antes de ejecutar código no confiable; Git/worktree/CLI permissions no bastan. Registrar candidato e inputs por hashes; no usar un repositorio sin base como si tuviera SHA válido. Congelar comandos argv con entorno mínimo y límites; no confiar en un comando de tests que el candidato pueda sustituir.

Tres capas de evidencia separadas:
1. Funcional backend: herramientas, retrieval con fuentes, ramas del grafo, límites, persistencia, aprobación e idempotencia. Dobles deterministas para fallos controlados; SQLite/índice/reinicio reales donde correspondan.
2. UI: Playwright headless del flujo/estados, teclado, errores, recarga/back y sesiones. Evidencia de desarrollo distinta de validación final independiente. UI verde no demuestra grounding o recuperación.
3. Calidad del modelo real: fuentes/citas, omisiones correctas, coherencia, latencia/coste, solo con proveedor/datos autorizados. Un mock o tests offline no certifican esa calidad.

Probar explícitamente timeout, índice vacío, documento contradictorio/inyección, fallo de checkpoint, terminación entre efecto y registro, reinicio, edición tras aprobación, ruta externa y agotamiento de límites. Reportar pass/fail/skipped/not_run y motivo; ningún estado accepted solo por exit 0. Retro saneada después de cada run, incluidas fallidas; promover cambios generales al harness solo tras revisión y regresión.
