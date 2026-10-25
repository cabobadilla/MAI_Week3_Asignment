# Tamaño de tareas OpenCode · regla fijada y aplicación
Fuentes canónicas y snapshot byte-idénticos: docs/definicion.md:5 «congela una unidad pequeña verificable»; docs/arranque.md:24 «Congelar una tarea pequeña»; docs/despliegue.md:18 «batches/capacidades pequeños». docs/workflow.md:43 una tarea activa por host; :47 inicial+dos reparaciones sin reiniciar contador; :77 timeout600s máximo. Evidencia/hashes y rutas absolutas en implementation/task-sizing-audit.json.
No se encontró umbral numérico de archivos, líneas o tokens en estas copias. Los topes de caracteres sugeridos por el coordinador en prompts anteriores no son regla del harness y no deben citarse como tal. Un único archivo puede contener demasiadas capacidades.

## Corrección aplicada
B/v2 inicial reunió demasiadas pantallas/estados y terminó en timeout. Primera búsqueda reunió índice, persistencia y cargador de modelo y terminó en timeout. La causa del timeout no se instrumentó; no afirmar que tamaño fue la única causa. Se preservan intentos y se reconcilió cada sesión/proceso antes de continuar.
Actual: una llamada GO VectorStore ya activa al detectar esta regla; no duplicarla, no cambiar su aceptación/modelo en vuelo. Prototipo B/v2 reducido ya respondió y está en validación. Próximas llamadas se secuencian una a una, con una capacidad observable, rutas exactas y tests congelados. Preparación/pruebas del coordinador pueden avanzar sin otra inferencia.

## Unidades siguientes para vertical local
| Unidad | Único resultado observable | Alcance de coder |
| --- | --- | --- |
| T-05B1 | consulta vectorial en memoria con procedencia | app/retrieval.py: build/search; estado de corrida activa preservado |
| T-05B2 | guardar/reabrir índice JSON validado sin pickle | app/retrieval.py: save/load, después de B1 si necesita cambios |
| T-05B3 | convertir texto a vectores con modelo local fijado y sin red | app/local_embeddings.py |
| T-05C1 | contexto actual de campaña acotado, sin contactos y con hash | app/history_context.py: selección actual |
| T-05C2 | advertencias de repetición/destinatario, sin bloquear envío ficticio | funciones concretas del mismo módulo |
| T-06A1 | crear/consultar/transicionar run persistente | app/runs.py |
| T-06A2 | reservar/reconciliar intentos y tokens de forma atómica | funciones concretas de runs.py |
| T-06B | grafo con lectura y pausa humana persistente | app/graph.py, sin proveedor real |
| T-06C | generar/revisar suite mediante proveedor simulado explícito | app/generation.py y su integración acotada |
| T-06D | reinicio/fallo/cancelación recuperables con límites conservados | cambios concretos en grafo; tests de reinicio |
| T-10A | sesión/CSRF/Host/Origin protegidos en HTTP | app/web.py: frontera auth, sin pantallas nuevas |
| T-10B | empresas/contactos por API, luego campañas en otra tarea | router/grupo exacto por contrato |
| T-10C | iniciar/revisar/aprobar/exportar un run por API | ruta/acción concreta por tarea |
| T-10D | registrar distribución/corrección manual por API | ruta/acción concreta por tarea |
| T-10E | pantalla Empresas, luego Seguimiento | solo después de decisión B/v2, una pantalla por tarea |
| T-11 | seed sintético/arranque y recorrido completo con regresión | scripts/docs; luego prueba independiente |
La tabla es orden de integración, no evidencia de implementación. Cambios legítimos de alcance abren contrato nuevo; no reiniciar rondas para eludir reparaciones. No ampliar permisos ni cambiar GO. Modelo app pendiente; mock no representa inferencia real. UI nueva pendiente de aprobación de versión/hash.
