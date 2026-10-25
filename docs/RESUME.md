# Retomar GrowWithAI

Proyecto: /Users/bobadillachristian/CodeLab/MAI_Week3_Asignment. Demo actualizada en http://127.0.0.1:8501; ver docs/TRY_DEMO.md. Datos/contraseña preservados en data/demo; QA usa otra BD temporal. No borrar ni reinicializar datos del usuario.

Recorrido DEMO conectado: Organizaciones con roles y varios contactos → campañas → seis piezas simuladas/cuatro formatos → edición/versiones → aprobación humana → exportación → registro público o envío externo declarado manualmente → hilo y respuestas/notas. No envía ni publica. 33 checks de navegador + 3 tras reiniciar QA; regresión HTTP/UI 90/90; pip check correcto. Evidencia dot/implementation/FULL-DEMO-E2E-01 y HTTP-REGRESSION-FINAL.

Generación DEMO usa plantillas y fuentes/contexto sintéticos; no prueba calidad de IA real. Pendientes: grafo/generación/revisión agéntica, recuperación e historia selectiva conectadas a ese flujo, cliente/evaluación real Qwen, y UI/API completa de correcciones auditadas. App elegida qwen/qwen3.8-flash por OpenRouter; configurable y sin llamadas reales en esta fase. Bootstrap normal .env implementado/probado con datos ficticios; DEMO omite .env por completo. La clave real nunca se leyó ni modificó.

Embeddings locales MiniLM384 conservados por decisión del usuario. RAG nativo/FAISS/Torch siguen suspendidos por conflicto OpenMP; aislamiento probado solo con mocks. No reproducir caída, no KMP_DUPLICATE_LIB_OK ni cambios de librerías del sistema.

Coder exclusivo opencode-go/deepseek-v4.1-flash. Una GO activa/host;600s/ronda; inicial+dos reparaciones sin reiniciar contador. UI-DIRECTED-RECORD-01 agotó sus dos reparaciones y pasó QA. UI-APPROVAL-01 consumió la única excepción explícita para exportación y pasó QA; no rondas extra implícitas. Consultar dot/implementation/resume-next.json y task-sizing-audit.json antes de otra llamada.

B/v3 aprobado; hashes en dot/design/gwa-ui-v3/decision.json. Git main/origin original intactos; sin commit/push/deploy. .venv y .env ignorados por Git. No modificar AGENTS.md (intento anterior denegado), harness compartido, fuentes ni permisos persistentes. Cloudflare/multiusuario quedan como evolución futura, sin refactor ahora. DASH-01 metadata portal separado/no bloqueante, acceso/audiencia/mecanismo pendientes; nada registrado. Sin Library ni envíos externos.

Informe editable guardado en dot/GrowWithAI_Project_Report_EN.docx, 38.924 bytes y SHA verificado en dot/implementation/report-transfer.json; bytes idénticos a las dos páginas revisadas en cloud.
