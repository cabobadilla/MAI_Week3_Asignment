# Configuración de app · propuesta para implementar en T-02
Estado: loader offline app/config.py implementado y probado16/16; cliente LLM/servidor aún en integración. No se ha habilitado inferencia real.

App y almacenamiento locales, servidor 127.0.0.1. LLM por OpenRouter, modelo obligatorio configurable y aún no elegido. Se prefiere un modelo barato; no fijar uno ni resolver ausencias con defaults. El presupuesto monetario lo controla el usuario en la API key; no requerir importe local adicional. Esto no garantiza conocer cuota o coste efectivo antes de una llamada.

## Variables y secretos
.env.example contiene solo esquema/valores no secretos. El usuario crea/completa .env por su cuenta. No copiar, leer o imprimir claves existentes durante setup. .env/.env.* ignorados y .env.example permitido. Futuro loader solo servidor, sin override de variables existentes; .env nunca se sirve como asset ni se añade a checkpoint. APP_LLM_MODEL no corresponde al modelo de OpenCode.

## Validación antes de red
En modo deshabilitado (default), no construir cliente ni hacer llamadas; permitir pruebas con transporte falso. En modo habilitado exigir clave no vacía y modelo explícito en formato provider/model de OpenRouter; errores solo por nombre de campo, nunca valor. Validar booleanos estrictos, enteros positivos y max_retries entre 0 y 2. Un modelo no disponible falla, no fallback.

Propuesta inicial ajustable al elegir modelo: input hasta 12000 tokens, output hasta 4096, total por run 64000 y máximo 8 intentos HTTP incluyendo retries; timeout 30 s. Reservar consumo estimado antes de request y reconciliar con usage cuando se reporte. Comprobar contexto y max output admitidos por el modelo elegido; nunca asumir que un tokenizer genérico mide exactamente otro modelo. Sin contador compatible o política conservadora revisada, bloquear inferencia en vez de prometer límite exacto. No truncar fuentes/evidencia silenciosamente para caber.

Errores transitorios 429/timeout/5xx: como máximo dos retries adicionales con backoff 1 s/2 s, respetando Retry-After solo si cabe en deadline. SDK retries desactivados si el grafo ya reintenta: un único dueño del contador. Auth 401/403, modelo inválido o configuración/ruta inválida: sin retry automático. Máximo global de 8 intentos incluye fallidos; no multiplicar límites por nodo. Límite total cuenta input+output de todas las llamadas, incluyendo revisión; si uso no reportado, registrar unknown y conservar reserva conservadora. Agotamiento → checkpoint + intervención humana, no bucle.

## Registro seguro y pruebas
Log permitido: run_id, etapa, modelo solicitado/efectivo si reportado, latencia, código HTTP, número de intento, tokens/coste reportados o unknown y clase de error. No Authorization/headers, clave, .env, URL con credenciales, prompt/respuesta completa, chunks, CV o datos personales. Mensajes externos se saneán/normalizan antes de log; nunca volcar excepción SDK/request cruda. Deshabilitar trazas remotas por defecto.

Tests futuros sin red: config ausente, disabled sin clave, modelo ausente sin fallback, números inválidos, tokens/contexto, 401/403 sin retry, 429/timeout y agotamiento, SDK retry doble evitado, redacción de secretos ficticios y no modificación de .env. No inferencia con coste hoy; falta modelo y tarea de prueba acordada. Las pruebas de config no certifican calidad del LLM ni app completa.

## Recuperación local en integración
FAISS/Sentence Transformers instalados solo .venv; lock backend actualizado y pip check pasado. Pesos Safetensors fijados y hashes en embedding-model.json, ignorados bajo data/models. Smoke CPU dos textos sintéticos384dims con red denegada pasó; esto no prueba calidad RAG ni el LLM remoto. La capacidad del tokenizer es128; encode debe rechazar exceso explícitamente, sin cortar fuentes silenciosamente. App ingiere chunks300/overlap60 y consulta tema corto. No confundir embeddings con APP_LLM_MODEL, que sigue pendiente.
