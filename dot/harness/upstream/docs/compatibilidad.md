> Nota de publicación: evidencia local histórica saneada; rutas y logs originales no se distribuyen. La compatibilidad observada no certifica otra instalación.

# Compatibilidad OpenCode

Inspección inicial para 0.1.0 del 19/10/2026; ampliación de catálogo GO documentada abajo. no se consultaron credenciales, configuración privada ni sesiones. Se invocaron exclusivamente `--version`, `--help` y `run --help`, con entorno vacío y HOME/XDG temporales bajo `/tmp/dotharness-inspection`, cwd temporal y PATH de sistema. Ninguna tarea/modelo se ejecutó.

## Evidencia local

| Dato | Observado |
|---|---|
| Ejecutable | `<USER_HOME>/.opencode/bin/opencode`; no aparece en PATH de esta sesión |
| Versión | `opencode v2.0.32` |
| Formato | Mach-O 64-bit arm64 |
| SHA-256 | `e43ec2df6f36842fd17d1a71a866acb9a84884b489988376c19bf9a7250dabbf` |
| Firma declarada | Identifier `opencode`, TeamIdentifier `5NZ4Q7NXJ4`, runtime flag; codesign informa `Authority=(unavailable)` |
| Procedencia | Ruta y metadatos observados; instalador, descarga y autenticidad respecto a release oficial no acreditados |

Ayuda local: `opencode run [flags] [<message...>]`. Lista `--standalone`, `--server`, `--continue`, `--session`, `--fork`, `--model` (provider/model#variant), `--agent`, `--format` (default/json), `--file`, `--title`, `--thinking`, `--auto`. No lista `--dir` ni `--attach`. Ayuda raíz indica que `--session` puede continuar o crear si no existe. Esto verifica sintaxis anunciada, no ejecución, permisos ni configuración efectiva. En esa inspección inicial no se usó `debug config`, auth, models, stats o comandos de sesión; el catálogo models se consultó después con autorización específica.

## Fuentes oficiales y discrepancia

- [Config](https://opencode.ai/docs/config/): formatos JSON/JSONC, schema, modelo/auxiliar y composición de capas. Un archivo de proyecto no prueba aislamiento de configuración; otras capas pueden conservar reglas o tener mayor prioridad.
- [Permissions](https://opencode.ai/docs/permissions/): reglas allow/ask/deny, regla coincidente final y permisos por herramientas. Los permisos regulan comportamiento de OpenCode; no equivalen a sandbox OS.
- [Schema público](https://opencode.ai/config.json): descargado a `/tmp/dotharness-inspection/official-config-schema.json`; JSON válido, draft 2020-12. SHA-256 `786b5ffc800629bc22145325beaa1dc4c7e6bdbbd5c5e6afd8cd2d59d9fc863c`.

El schema consultado marca `permission`, `small_model`, `enabled_providers` y `autoupdate` como deprecated; también presenta `permissions` (ruleset) y `providers`. La guía aún ilustra varias claves antiguas. No se infiere qué migración acepta el binario local ni se inventan claves para gasto/allowlist de modelos. El schema web es mutable y no está vinculado aquí a una release local verificable.

## Ejemplo y siguiente verificación

[opencode.json.example](../templates/opencode.json.example) contiene únicamente `$schema` y `permission: "deny"`, expresados en la guía y admitidos por la rama legacy del schema público consultado. Es referencia **documental bloqueada**, no configuración operativa certificada para v2.0.32. No elige modelo, habilita edición ni autoriza llamadas. Se omite un ejemplo habilitado mientras no sea verificable localmente.

Antes de una fase real: fijar binario/procedencia/version/hash; verificar config y schema de esa release en entorno aislado sin auth; comprobar reglas efectivas y capas, instrucciones/plugins/MCP/servicios heredados y modelo principal/auxiliar explícitos. La allowlist y presupuesto pertenecen al contrato del ejecutor, no a supuestas claves OpenCode. No permitir fallback silencioso; registrar modelo efectivo o bloquear. Para arrancar más adelante se usará cwd explícito del proceso y superficie confirmada por ayuda local; no se publica ahora un comando de ejecución listo para copiar.

Un ejemplo parseable no demuestra enforcement. Quedan pendientes compatibilidad local de configuración, aislamiento, cancelación/descendientes, contabilidad y separación de credenciales. Son requisitos de la fase con agentes; no bloquean revisar esta definición ni acordar un piloto con adaptador falso.

## Preflight UI y Wrangler — 0.2.0-draft

Node 26.7.0 y npm 11.19.0 presentes. No se resolvieron @playwright/test, playwright o playwright-core desde CodeLab, ni se encontraron sus paquetes globales en el root npm inspeccionado; no equivale a ausencia en toda la máquina. Cache Playwright contiene Chromium/headless-shell revisión 1248, ejecutable disponible; metadata de Chrome for Testing indica 156.0.8078.4. No se lanzó browser ni leyó perfil personal. Sin paquete runner compatible fijado, UI no está lista para pruebas.

Wrangler global 4.129.0 presente, package engines Node >=22.0.0; --version y dev --help ejecutados con HOME temporal y métricas desactivadas solo para esos procesos. Ayuda confirma --local, --ip, --port y --assets; no se inició servidor ni consultó cuenta/auth. Un arranque futuro será argv local explícito, --local y bind 127.0.0.1, sin remote; config/puerto/artefactos pendientes del contrato. Nunca npx con instalación implícita. [Preflight observado](../dot/evidence/historical-summary.json).

OpenCode mantiene el hash de binario observado. No se inspeccionó configuración privada ni se ejecutó config efectiva; ejemplo propio deny-all sigue documental. Llamada real requiere compatibilidad local, fuente de modelo/proveedor/auxiliar allowlisted, disponibilidad de autenticación mediante canal seguro y coste autorizado. Si hace falta login/clave se informará sin leer ni pedir volcar secretos. No heredar modelos o presupuesto de tailCutter/otro proyecto. La implementación del piloto debe ser una prueba real de OpenCode, no código de dot presentado como si lo hubiera generado OpenCode.

### Ruta GO autorizada por usuario

Consulta CLI de solo lectura `opencode models --standalone`: exit0, catálogo incluye **opencode-go/deepseek-v4.1-flash**. La primera consulta restringida falló; la consulta de catálogo con acceso autorizado terminó sin stderr. No se imprimió configuración privada ni se leyó auth.json, claves, cookies o tokens; el cliente pudo usar acceso existente internamente. No se solicitó inferencia. La allowlist del piloto es ese singleton para principal/auxiliar; nunca OpenRouter/fallback. No es prueba de cuota restante, entitlement, facturación ni configuración efectiva de una sesión real. No activar recargas/compras/overage; coste adicional incierto detiene. Si hace falta login/grant nuevo, handoff sin reconfigurar acceso persistente.
