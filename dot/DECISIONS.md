# Decisiones vigentes GrowWithAI · r4
Alcance confirmado por Sentinel_83058765897481918dd7fe55e183ae63, tras propuesta explícita: campaña general + lista de empresas/contactos + seguimiento manual por destinatario; fuera envío integrado/bandeja/automatización/personalización individual. No volver a pedir esa confirmación.
- B v1 Mesa editorial elegida; nuevos detalles de Campañas/Empresas/Seguimiento/editor se revisan en T-01 antes de UI. No aprobación visual nueva inferida.
- Campaña agrupa múltiples piezas/formatos y destinos; suite académica cuatro formatos. Público sin destinatarios ficticios; email general común a lista, sin personalización.
- Registro manual individual/lote de versión/fecha/contacto, respuesta/nota/próximo paso; público por publicación. Exportado/aprobado/generado no equivale a enviado. Correcciones/versiones conservan historia. Empresas/contactos sí en MVP; catálogo de organizaciones beneficiarias queda futuro.
- App/datos Python locales y virtualenv; LLM OpenRouter, modelo económico exacto pendiente, presupuesto controlado en API key por usuario. Clave la ingresa en .env, no se lee ni se transmite en esta entrega.
- Contraseña propia/simple y operador local; auth detallada en specs, no implementada. No Cloudflare/deploy, push/commit, publicación externa, lectura de correo o Library. Fuente social v0.2 preservada, forma jurídica abierta, sin alianzas/resultados/precios inventados.
- Arquitectura técnica r4 propone FastAPI/Jinja2 para B y auth de rutas, reemplazando propuesta preliminar Streamlit no instalada. Dependencias candidatas; lock/benchmarks/instalación por tarea futura, sin instalaciones globales.
Specs canónicas docs/specs/sponsor-materials/README.md. Esta autorización es generar specs, no ejecutar aplicación/coder. Base Git, driver Python/modelo coder/controles y aislamiento se preparan antes de run; no son dudas de alcance. Harness compartido/pin intactos. Historial de decisiones resumido en DECISION_HISTORY.md.

Portal aclarado (solo lectura): DASH-01 obligatorio con dirección central, separado de app local. Nuestra adaptación previa local-only se corrigió documentalmente; registro/sync no ejecutados ni autorizados. Detalle/evidencia de pin y login observado en dot/portal-tracking.md (desde raíz). No desplegar GrowWithAI.

Autorización posterior del usuario Sentinel_a90194c6c15c81919b2bb003de894a47: registrar GrowWithAI en portal solo seguimiento con metadata mínima, no app/archivos/contactos. Registro aún no efectuado: portal permanece en login, audiencia/duplicados/mecanismo sin verificar. Preview local en dot/portal-registration-preview.json. Login manual del usuario necesario para continuar sin eludir auth o crear permisos.

## Decisión posterior r5
Sentinel_689d058304f0819183b2ff7ba6763601: tres nombres/emails iniciales,1obligatorio; Sentinel_23821873ff748191aec709897ef099c8: mismo formulario para beneficiarias; Sentinel_b00bdae4771c819188c03c122a276d91: Seguimiento dividido en registro público y hilo dirigido para contexto, no CRM; Sentinel_6b09aed4b94081918097d7c06237d9b5: seguir hacia producto funcional. Scope-r5 canónico; roles múltiples representación propuesta flexible, no relación confirmada. Variantes B/v2 supersedidas, no elegirlas otra vez.

## Modelo app elegido
Sentinel_998e1fefe2248191b30a4466a676b7a6: qwen/qwen3.8-flash vía OpenRouter, configurable/evaluable posteriormente. Ejemplo sin secretos, enabledfalse; .env real no leído/modificado. No autoriza pruebas pagas amplias. No cambia modelo GO del coder.
