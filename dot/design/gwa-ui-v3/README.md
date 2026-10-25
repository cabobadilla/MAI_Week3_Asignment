# B/v3 · revisión visual pendiente
Propuesta local no funcional; datos ficticios, sin guardado, llamadas LLM, envío o publicación. Estilo B elegido; estas vistas nuevas requieren revisión.

- [Organizaciones](organizations.html): un formulario aportante/beneficiaria, tres pares nombre/correo, primero obligatorio; sin límite rígido de tres. Revisión1 corrige únicamente tipografía.
- [Publicaciones generales](tracking.html): pieza/versión, medio, fecha y nota manual; exportar no equivale a publicar.
- [Comunicaciones dirigidas](directed.html): hilo contextual por organización/contacto, envío declarado externamente, respuesta/nota manual; sin CRM.

Capturas desktop/mobile: `screenshots/organizations-desktop.png`, `organizations-mobile.png`, `tracking-desktop.png`, `tracking-mobile.png`, `directed-desktop.png`, `directed-mobile.png`.
Desde la raíz del proyecto en macOS: `open dot/design/gwa-ui-v3/organizations.html`; seguir los enlaces locales a las otras vistas. El renderer aislado comprobó las tres rutas file:// y sus seis tamaños de captura. No se requiere servidor ni instalación para abrir los HTML.
Hashes y límites: design-manifest.json. QA: evidence-organizations-tracking-directed.json. No declarar este prototipo como aplicación operativa ni como aprobación visual ya recibida.

La apertura file:// mediante el panel browser de Codex devolvió «Remote file URLs cannot be opened in the local browser». No es un fallo del HTML: las seis vistas file:// se renderizaron en Chromium local aislado. Usa los archivos/capturas locales; las aperturas de PNG solicitadas al panel quedaron queued, no se afirma que ya estén visibles.
