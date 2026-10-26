# GrowWithAI · Week 3

Aplicación local para preparar materiales de comunicación de un proyecto de formación digital e IA. Combina fuentes del proyecto, generación y revisión automática, edición humana y exportación. Las publicaciones y los envíos se realizan fuera de la app.

## Funcionalidad implementada

- Acceso por contraseña y almacenamiento local persistente.
- Organizaciones y contactos, campañas y cuatro formatos: LinkedIn, email general, artículo y tres variantes de anuncio.
- Agente real con recuperación de fuentes, generador y revisor; muestra fuentes, estados y observaciones. Se detiene ante información insuficiente o límites de revisión.
- Edición mediante versiones inmutables, aprobación humana explícita y exportación de archivos. La revisión automática no constituye aprobación humana.
- Registro manual de publicaciones, comunicaciones dirigidas, respuestas y notas. El historial aporta contexto y ayuda a evitar repeticiones.

## Arquitectura

Python 3.11, FastAPI/Uvicorn y frontend HTML/CSS/JavaScript. LangGraph orquesta recuperación, generación, revisión y pausas; SQLite conserva campañas, versiones, resultados y checkpoints.

La generación usa **`qwen/qwen3.8-flash` mediante OpenRouter**, sin fallback de modelo. La recuperación utiliza MiniLM multilingüe local y FAISS, con procesos separados para los runtimes nativos. Los pesos y su revisión se fijan en [config/embedding-model.json](config/embedding-model.json).

## Arranque local

Desde la raíz del repositorio, con las dependencias instaladas en `.venv` y los pesos locales preparados:

```sh
.venv/bin/python -B -m app.runtime --real --port 8501
```

Abrir **http://127.0.0.1:8501** y mantener esa terminal abierta. Para un proceso independiente del terminal puede utilizarse `nohup` con redirección de entrada/salida; esto no configura inicio automático tras reiniciar el equipo.

El modo real requiere `OPENROUTER_API_KEY` en el archivo local `.env`, excluido de Git. No incluir claves ni contraseñas en el repositorio. Los datos y la contraseña del operador se conservan en `data/demo/app.sqlite`, también cuando se usa el modo real; `data/demo` es el nombre histórico del directorio.

Para probar el flujo sin proveedor externo:

```sh
.venv/bin/python -B -m app.runtime --demo --port 8503
```

Ese modo genera contenido **simulado** y comparte el directorio de datos predeterminado: no usarlo para QA destructiva sobre datos existentes. [scripts/setup-local.sh](scripts/setup-local.sh) prepara el entorno; las dependencias de app están en [requirements-backend.lock](requirements-backend.lock). La preparación del entorno no descarga los pesos locales.

## Fuentes y contexto

Los dos documentos autorizados del proyecto, versión 0.2, están en [docs/references/originals/](docs/references/originals/), con textos extraídos en [docs/references/extracted/](docs/references/extracted/). [manifest.json](docs/references/manifest.json) registra su procedencia y hashes. El material del curso se mantiene separado de la evidencia factual del proyecto.

El agente recupera cuatro fragmentos por consulta y conserva las fuentes utilizadas en cada ejecución. En la UI: **Campañas → Abrir mesa → Fuentes / Evidencia del agente real**.

## Validación y límites actuales

Existe una [prueba real histórica completada](dot/implementation/REAL-UI-E2E-01.json): seis piezas, revisión automática `pass`, edición, aprobación y exportación verificadas en QA aislado, incluida persistencia tras reiniciar. Esa evidencia no garantiza el resultado ni la disponibilidad de una nueva llamada al proveedor.

La [prueba real más reciente y su único reintento](dot/implementation/REPRO-TEST-20261026-RETRY1.json) terminaron con **HTTP 429** de OpenRouter, sin producir borradores; el coste de esos rechazos no fue informado. No se cambió de modelo ni se eludieron límites.

La respuesta a preguntas y continuación de un run desde la UI, y una vista de consulta completa del contexto, **siguen pendientes de completar y validar**. El transporte de aclaraciones y parte del grafo cuentan con pruebas offline; eso no acredita un flujo de continuación real terminado. Actualmente se muestran preguntas y fuentes recuperadas, sin una pantalla de carga o edición de documentos.

**Video pendiente de grabación.** Las [capturas en pics/](pics/) son evidencia provisional de la interfaz.

## Entregables y especificaciones

- [Informe del proyecto en inglés, versión 2](dot/GrowWithAI_Project_Report_EN_v2.docx).
- [Especificaciones r4](docs/specs/sponsor-materials/README.md).
- [Instrucciones del repositorio y dotHarness](AGENTS.md): implementación con OpenCode GO en unidades pequeñas y revisión independiente.
