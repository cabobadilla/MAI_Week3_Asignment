# Ruta mínima a IA real y correcciones

Estado verificado tras reconexión: código de la app idéntico a los 41 archivos del snapshot final, SQLite íntegro, DEMO completa restablecida en localhost8501 sin borrar datos ni contraseña. Checkpoints reconciliados; ninguna llamada GO activa. La DEMO no es el agente real ni una evaluación de Qwen/RAG.

## Aislamiento actual y límites de evidencia

El proxy lanza un Python nuevo con `-I -B`, limpia el entorno, exige identidad/PID/dimensión y acota tiempo; worker y modelo fijados. Sus 11 pruebas actuales usan Popen simulado: prueban el contrato del transporte, no una carga nativa exitosa. Evidencia y hashes: `dot/diagnostics/native-readiness.json`.

Guardias integradas por OpenCode GO: `app/native_runtime_guard.py` (18 pruebas), `app/embedding_worker.py` (4) y `app/retrieval.py` (6). Son pruebas con módulos ficticios: rechazan Torch/SentenceTransformer/sklearn en el proceso vectorial y FAISS/sklearn en el de embeddings antes de importarlos. No prueban una carga nativa exitosa ni detectan por sí solas toda carga dinámica de bibliotecas.

La inspección estática `dot/diagnostics/native-linkage-readonly.json` confirma tres archivos libomp distintos enlazados desde Torch, FAISS y sklearn. SentenceTransformer y Transformers tienen rutas que importan sklearn; la guardia ahora las rechaza, pero no está resuelta una ruta de carga del modelo que conserve sus dependencias sin mezclar runtimes. El cargador directo sigue sin guardia obligatoria. El proxy mantiene close_fds=False. Por estos pendientes el protocolo nativo sigue NO LISTO y no se ejecutó; no se usó KMP_DUPLICATE_LIB_OK ni se alteraron librerías del sistema.

`app/llm_client.py` está integrado con 18 pruebas HTTP simuladas: proveedor/modelo configurables dentro de OpenRouter, límites por petición, errores saneados y resultado incierto sin reintento automático. No está conectado aún al grafo ni demuestra una generación real. La reserva atómica de límites se desarrolla en una unidad separada. La demo activa no se reinició ni se tocaron sus datos o contraseña.

## Unidades pequeñas propuestas para IA real

1. Guardias previas a imports nativos y frontera obligatoria del worker; probar ambos órdenes de importación con stubs. Mantener arquitectura local actual, sin cambiar proveedor ni librerías del sistema.
2. Revisar dependencias OpenMP y las guardias; después considerar UNA prueba nativa sintética acotada. Protocolo preparado en `dot/diagnostics/native-smoke-proposal.json`, estado NO LISTO. No se ejecutó. No basta con eliminar FAISS del worker si otro paquete introduce otra copia de OpenMP.
3. Conectar recuperación/documentos vigentes e historial selectivo con dobles primero: hechos enviados/publicados y respuestas, correcciones activas, aislamiento de campañas y texto histórico tratado como datos. Preguntar ante datos materiales faltantes; no inventar compromisos.
4. Adaptador OpenRouter configurable para qwen/qwen3.8-flash, probado con transporte falso: errores, timeout, respuesta inválida y logs sin credenciales. No leer ni modificar la clave del usuario ni hacer llamadas reales en esta preparación.
5. Reservar intentos/tokens de forma atómica y conectar el grafo persistente por transiciones pequeñas: recuperar contexto, decidir buscar/preguntar, generar, revisar y pausar ante el humano. Probar recuperación/reinicio y agotamiento con dobles. Los runs actuales no implementan por sí solos ese grafo.
6. Conectar el flujo real a la UI sin quitar DEMO; luego preparar evaluación sintética mínima de fidelidad/español/latencia/coste. Cualquier llamada real requiere el alcance de prueba concreto; no transmitir documentos o contactos implícitamente.

Límites existentes en config/local.toml: 12.000 tokens entrada, 4.096 salida,64.000 por run,8 intentos totales,2 reintentos y timeout30s; búsqueda2, revisión2, transiciones20. Son configuración/propuesta existente; no afirmar aplicación efectiva por un grafo todavía ausente. Presupuesto económico controlado en la API key. Coder GO y modelo de app separados.

## Correcciones de registros desde UI

Reutilizar `app/followup.py:331` correct_distribution, que agrega filas y conserva el original. La app no tiene aún un endpoint/formulario de corrección. Secuencia mínima: una unidad para POST de corrección con operation_id,reason,changes,confirmed; otra para el formulario público; otra para el dirigido. Cada acción fija registro/versión/campaña, valida pertenencia y muestra la corrección enlazada, nunca UPDATE/DELETE del original ni envío automático. El tipo público no recibe destinatario ficticio. Probar idempotencia, concurrencia, campos inválidos, aislamiento y conservación de notas/exportaciones; marcar antiguos superseded al recuperar contexto. La corrección de notas tiene su servicio separado y requerirá su propio contrato si se expone.

Cada unidad seguirá una GO activa,600s y máximo dos reparaciones; no modificar harness compartido ni reiniciar contadores agotados. No hay cambios de arquitectura, instalaciones, inferencia ni pruebas nativas autorizadas por este documento.
