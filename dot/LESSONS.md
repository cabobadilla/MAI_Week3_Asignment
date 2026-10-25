# Lecciones observadas y propuestas · 2026-10-25
Estado: evidencia de setup; ningún run de app ni inferencia.

| Observación comprobada | Evidencia local | Lección / propuesta |
| --- | --- | --- |
| El intento anterior no migró: aún existían los tres documentos retirables y faltaba dot/harness/manifest.json | inspección tras reconexión; revisión automática anterior venció por timeout | comprobar efectos antes de reintentar; no confundir timeout con rechazo o éxito |
| Repo dotHarness existente con remote exacto y HEAD 2e5d217f55b3a26543d3d52edb39d7204e35c258; working tree contiene cambios ajenos | git status/remote/rev-parse; manifiesto pin | usar blobs del commit y hashes, no copiar cambios ajenos ni actualizar silenciosamente |
| Driver acoplado a survey-coder/modelo GO y UI estática | código fijado scripts/run_opencode.py y README | crear perfil Python y plan antes de reusar el ejecutor; no afirmar capacidad general |
| Python predeterminado no tenía virtualenv; se creó entorno de trabajo con virtualenv aislado | .setup-venv/requirements-setup.txt y versión registrada | conservar bootstrap local y distinguir dependencias del preparador de las de app |
| .venv tiene solo pip/setuptools; requirements-app.in es candidata | pip list y checkpoint | no presentar pip check como instalación o validación de LangGraph/Streamlit |
| Tres originales y extracciones disponen de hashes | docs/references/manifest.json y verificador | preservar bytes/procedencia y no confundir rutas cloud con archivos accesibles |

Propuestas generales no verificadas aún: perfil Python ejecutable, runner aislado, broker de secretos, gates backend y reanudación del ejecutor. Ver ADAPTER_PROPOSAL.md. Requisitos propios de GrowWithAI (formatos, piloto, RAG y límites) no son lecciones universales ni capacidades ya implementadas.

No se devolvió material al repo compartido: propuesta contenida en el proyecto para revisión; no se tocaron dot/README.md ni dot/plan-dos-macs.md del harness.

Observado adicional: debug config aislado intenta usar un servicio administrado en 127.0.0.1:49374 y falla por puerto ocupado (exit 1), mientras --version funciona. No se cambió el servicio ni se detuvo proceso ajeno. Lección: una HOME temporal no asegura puerto/servidor propios; preflight necesita instancia/puerto efímero explícitos y comprobar propiedad. Esta corrección no implementa ese control. Ver setup-evidence.json.

Decisión nueva (no prueba de ejecución): usuario confirma app/datos locales y OpenRouter para LLM, modelo pendiente y presupuesto controlado en API key. Lección de coordinación: registrar por separado destino de app, proveedor/modelo runtime y modelo coder; eliminar bloqueos resueltos sin inferir autorización de llamadas. Ninguna llamada realizada.

Observado en fase visual: Playwright 1.64.1 ya disponible en dependencia local y Chromium headless revisión 1248 compatible; pudo comprobarse mockup sin instalaciones, contexto/perfil personal o red externa. 48 comprobaciones/54 capturas, sin errores ni overflow en viewports probados. Evidencia en design/gwa-ui-v1/evidence.json. No generalizar a app Python: mockup no prueba login real, RAG, persistencia ni aislamiento del futuro coder. Decisión de acceso se registró antes de cierre de specs; diseño permanece sin elegir.

Cambio de alcance confirmado: usuario eligió B v1 y pidió organizaciones/comunicaciones e historia previa a redacción. Se registró elección sin alterar bytes/hashes del diseño original; pantallas nuevas se separan de la aprobación histórica. Lección de definición (sin pruebas de producto): generado/aprobado/exportado y envío manual son eventos distintos; no comprimirlos en estado único ni interpretar exportación como exposición real de un destinatario. Campañas y granularidad de versiones continúan propuestas/preguntas, no decisiones inventadas. No hubo subida a Library, inferencia o implementación.

Reconciliación de alcance: el usuario simplificó a difusión general antes de implementación. Se retiró expansión de organizaciones/individual del MVP y se conservó solo como backlog futuro, sin crear tablas/pantallas. Lección de definición: mantener decisiones posteriores como autoridad y separar histórico de instrucciones actuales; campaña como etiqueta mínima sigue propuesta. Nada de producto verificado por actualizar documentos.

Specs r4: el usuario confirmó campaña general + empresas/contactos + seguimiento manual, envío fuera. Se sustituyeron recortes contradictorios en documentos canónicos, manteniendo solo resumen histórico. Se separaron tablas/eventos de aprobación/export/distribución y destinatarios por campaña para no perder versión/fecha. Validación de referencia DDL en memoria comprobó13 invariantes; eso no prueba servicios/app. Se detectó y corrigió CHECK de motivo de corrección para rechazar NULL explícitamente (SQLite CHECK permite NULL); no se creó BD de usuario.
Auditoría portal: pin exige DASH-01 y dirección central; nuestra adaptación local-only confundía destino app con tracking de proyecto. Se corrigió contrato documental. Tras autorización de metadata mínima, portal sigue login; no registro o sync efectuado, audiencia/API pendientes. Sin credenciales leídas o permisos modificados. Compartido intacto.

Cierre de revisión r4:30 criterios con30 test IDs futuros cubiertos por14 tareas,24 enlaces internos comprobados,13 controles DDL in-memory. Tests de app/inferencia not_run. Se precisaron invariantes para no confundir prohibición de envío/publicación de contenido con LLM autorizado o metadata mínima del portal. Ningún progreso ficticio publicado.

## T-07A observado
La abreviatura de columnas hash64 en el prompt generó tres fallos SQL; pasar DDL literal a una reparación GO acotada resolvió 17/17 sin alterar esquema ni aserciones. Una invocación de validación usó ruta de fixture errónea; corregir el parámetro, sin regenerar código, recuperó la suite. Estado actual debe actualizarse en checkpoint.json además de la conversación.

## T-07B observado
El prompt del coordinador pidió contenedor files como objeto; guard correctamente lo rechazó antes de ejecutar. Se normalizó solo JSON a lista path/content, manteniendo SHA del código; guard sin cambios revalidó y tests14/14 pasaron. Futuras solicitudes deben usar exactamente el schema del guard. Crash de INSERT sintético/retry y archivo alterado probados; no equivalen a inyección de fallos del proceso/OS completo.

## T-08A observado
La prueba de fallo en transacción anidada tenía un INSERT de fixture con updated_at inexistente. Se corrigió solo el fixture contra DDL, sin cambiar código ni aserciones:25/25; evidencia conserva el error inicial. Dos clics concurrentes crean un único lote; fallo de segunda fila rollback completo incluso dentro de transacción externa; retry conserva destino ya registrado tras cambiar contacto. No son pruebas de envío real ni de UI.

## T-09A observado
OpenCode GO generó seguimiento y correcciones en un archivo;25/25 sin reparación. Tests cubren cadena de correcciones y una sola rama, retry/collision de operación, snapshots tras archivar contacto, referencias same-campaign y fallo SQL con transacción externa. El historial completo conserva original; proyección actual excluye superseded. No prueba que un correo haya sido realmente enviado ni UI/LLM.

## T-05B3 observado
Tras desconexión, supervisor murió y servidor propio quedó huérfano. Se verificó PID/cwd/PGID, se cerró solo ese servidor y exportó sesión propia: file-map completo GO recuperado, sin duplicar generación. No certificar límite600s durante esa pérdida de control. Prueba detectó symlink raíz9/10; reparación GO de una función pasó10/10. Localizador de parche omitió un newline final; primera preparación lo rechazó y shell siguió ejecutando candidato viejo: conservar ese fallo de control. Aplicación posterior secuencial, hash base y guard, sin debilitar tests. Mejorar cleanup de señal en otro contrato acotado si procede; no abrir plataforma nueva ahora.
