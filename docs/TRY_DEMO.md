# Prueba local del tramo DEMO

Dirección: http://127.0.0.1:8501

La generación está simulada y rotulada DEMO. No usa OpenRouter, no lee `.env` y no ejecuta RAG nativo. Registro público y comunicaciones dirigidas están conectados. Es un recorrido funcional DEMO; la orquestación con RAG y LLM reales sigue pendiente.

1. Ingresar con la contraseña existente, o crear una propia si es la primera apertura (mínimo 8 caracteres). No compartirla por chat.
2. En Organizaciones, registrar nombre, rol y al menos un contacto completo. Los dos pares adicionales pueden quedar vacíos.
3. En Campañas, completar nombre, tema, objetivo, audiencia y tono; mantener la suite académica de cuatro formatos.
4. Pulsar Generar demo. Aparecen seis piezas: LinkedIn, email general, artículo y tres variantes de anuncio.
5. Editar una pieza y guardar una nueva versión, o descartar los cambios.
6. Revisar las piezas, marcar la confirmación humana y Aprobar materiales.
7. Pulsar Exportar materiales y descargar los seis archivos Markdown. Esto no registra un envío ni una publicación.
8. En Registro y contexto → Publicaciones generales, elegir pieza exacta, medio y fecha. Confirmar que se publicó fuera de la app y Registrar publicación. Es una declaración manual; no publica nada.
9. En Comunicaciones dirigidas, elegir organización y marcar contactos. La selección se conserva al cambiar de organización. Preparar destinatarios fija los datos de destino; no declara envíos.
10. Elegir versión del email y fecha del envío externo, confirmar que ocurrió fuera de la app y Registrar envío externo. Repetir la misma versión al mismo destinatario requiere motivo explícito.
11. Elegir un envío relacionado y guardar una respuesta o nota con su fecha. El hilo sirve de contexto; no contiene embudos, tareas ni recordatorios comerciales.
12. Recargar: campaña, ediciones, exportaciones e historial se conservan. Editar piezas exige nueva aprobación; los exports anteriores conservan sus bytes. Tras reiniciar el servidor se vuelve a ingresar con la misma contraseña.

Arranque desde la raíz del proyecto:

```sh
.venv/bin/python -B -m app.runtime --demo --port 8501
```

Solo escucha en 127.0.0.1. Si el puerto está ocupado, comprobar el proceso antes de arrancar otro; no detener procesos ajenos. Los datos se conservan en `data/demo/app.sqlite` y los exports en `data/demo/exports`, ignorados por Git. No borrar esos directorios para reiniciar una prueba con datos del usuario.

Validaciones reproducibles offline:

```sh
.venv/bin/python scripts/run_protected_tests.py --suite runtime_demo
.venv/bin/python scripts/run_protected_tests.py --suite web_directed_write
```

Evidencia: `dot/implementation/FULL-DEMO-E2E-01/`: 33 comprobaciones de navegador y 3 tras reiniciar el proceso QA, con una BD temporal separada de la del usuario. `HTTP-REGRESSION-FINAL/`: 90 pruebas aprobadas. `pip check`: sin dependencias rotas.

Pendientes: generación/revisión agéntica y recuperación reales, validación del modelo Qwen y del aislamiento nativo de embeddings. La UI de corrección auditada de registros manuales todavía no está expuesta; el backend de correcciones se probó por separado. Ningún export o registro dispara envío, publicación o compra de publicidad.
