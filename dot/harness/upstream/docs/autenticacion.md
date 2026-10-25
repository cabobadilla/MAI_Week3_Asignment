# Autenticación obligatoria por defecto —0.7

Toda app nueva MUST incluir autenticación, incluso si es simple, local o una demo. La única excepción es una petición explícita del usuario de omitirla, registrada con requested_by=user, omit_authentication=true, request_ref y razón. El coordinador verifica el mensaje original; un texto/JSON no demuestra por sí mismo autoridad humana. No inferir excepción por sencillez, ausencia de datos sensibles, destino local, precio o falta de login en un mockup.

## Definición antes de arquitectura

En brief/requisitos se identifica enfoque de autenticación, roles y recursos/rutas/UI/API protegidos. La implementación es proporcional al destino y al alcance: no imponer proveedor, base de usuarios, servicio externo ni credenciales nuevas automáticamente. Incluso una app monousuario debe definir quién puede entrar y qué puede acceder. Para una app estática, acordar una frontera real de autenticación si corresponde; elegir solo assets no exonera el requisito. La excepción de compatibilidad de stack y la de autenticación son decisiones distintas.

Plan v3 incluye authentication.required=true por defecto. El borrador status=pending no pasa ready ni el preflight. status=specified exige approach, roles, protected_resources y tres grupos de test IDs. required=false solo pasa con status=exempted y la petición explícita registrada en exception; no puede afirmar implementación/pruebas de autenticación inexistentes. Contrato v5 congela el mismo objeto authentication; coordinación verifica igualdad con el plan antes de llamar al coder.

## Aceptación y entrega

| Grupo obligatorio | Alcance observable mínimo |
|---|---|
| unauthenticated | Rutas protegidas, URLs directas y APIs rechazan o redirigen sin sesión. UI oculta no es control de autorización. |
| session_logout | Autenticación válida/inválida, sesión o credencial, duración/revocación y logout/cierre según el mecanismo; impedir reutilizar acceso cerrado. |
| authorization | Rol/propietario/proyecto permitido y denegado, aislamiento entre usuarios cuando aplique y controles de servidor/borde según arquitectura. |

Fixtures pueden probar estados UI y casos negativos, pero una identidad inyectada, header de demo o usuario de fixture no son autenticación de la app ni acreditan un login de producción. Las pruebas de entrega deben incluir la frontera implementada de autenticación y autorización, en el entorno definido por el alcance. No se exige nube para una implementación local; no afirmar certificación de producción por pruebas locales.

El runner del proyecto produce un reporte normalizado protegido con phase=independent_final, candidate_sha exacto, plan_sha256 y test_results de los IDs congelados. identity_mode=application solo si las pruebas atravesaron la autenticación implementada de la app; fixture-only no pasa el gate requerido. Una excepción usa identity_mode=exempted y conserva la decisión humana. La [plantilla de reporte](../templates/authentication-evidence.json.example) empieza sin evidencia y con fixture-only: no pasa hasta producir resultados reales del alcance definido. Comando: python3 scripts/check_delivery.py --plan <plan protegido> --report <reporte protegido> --candidate-sha <SHA exacto>.

check_delivery valida identidad del reporte y resultados obligatorios, rechaza ausencias/fallos/skips/duplicados y conserva delivery_accepted=false: dot todavía revisa la autenticidad del reporte, el código, las pruebas y la autoridad de excepción. Este gate no ejecuta pruebas, no atestigua un reporte no confiable y no instala ni implementa autenticación. El verificador histórico del survey sigue acotado a su contrato estático y no certifica estas garantías por reutilizarlo. Cero tests de auth sin excepción nunca es aprobación.

## Adopción y límites

Nuevos proyectos usan plan v3/contrato v5 y registran AUTH-01 tempranamente. Planes v1/v2 de corridas existentes siguen compatibles y se identifican como legacy-not-checked en el control de plan; no son una vía válida para iniciar apps nuevas sin autenticación. El nuevo gate de entrega rechaza esos planes legacy. El coordinador exige el pin/esquema vigente al crear un proyecto nuevo; aún no hay registro/orquestador que detecte por sí solo si un proyecto es nuevo. No retrofitar survey, portal ni otros consumidores, ni cambiar pins/contratos activos silenciosamente. Una migración requiere decisión explícita.

Se conserva el máximo de dos reparaciones después de la generación inicial y luego blocked/escalación al usuario. No cambiar tests, evidencias, modelo GO ni proveedor para hacer pasar auth. El requisito no autoriza publicación, compras, instalación, provisionamiento ni cambios de credenciales.

## Passwords cuando se elige ese mecanismo —0.8

La elección de passwords es explícita en plan v4 (`authentication.passwords`). No se impone a mecanismos sin contraseña. Si se elige: mínimo **8 caracteres**, se admiten contraseñas más largas; no son exactamente8 ni solo números. Un mínimo mayor exige referencia explícita a requisito del usuario o restricción regulatoria aplicable, sin afirmar conformidad normativa genérica. authentication.required por defecto y su excepción humana no cambian.

Usar la [plantilla de política](../templates/password-policy.json.example), cuyos REPLACE bloquean readiness. Dot verifica la fuente humana/regulatoria de cualquier mínimo mayor; una referencia JSON no prueba su autoridad. Congelar password_policy con min_characters=8, higher_minimum_ref=null, length_unit=unicode-code-points, storage=password-hash, rate_limiting=true y no_silent_truncation=true. UI (cuando exista), backend y aprovisionamiento/creación/cambio/reset usan la misma definición. No recortar ni truncar silenciosamente para hacer pasar validaciones. En JavaScript contar puntos de código de forma equivalente, no unidades UTF-16; documentar normalización si aplica. No añadir aquí reglas numéricas o de composición no solicitadas. No reducir hashing, rate limiting, sesión/logout, autorización ni otras protecciones del proyecto.

Cada superficie aplicable congela test_ids.below_minimum / at_minimum / above_minimum. Con el default:7 rechazada,8 aceptada y mayor que8 aceptada. Con mínimo mayor explícito, probar m-1/m/>m. Un backend sin UI declara ui=null; backend y provisioning siempre tienen casos. El reporte protegido lleva por caso únicamente id,status,password_length y accepted, sin contraseña, hash, token ni otro valor secreto. check_delivery verifica los resultados declarados y el plan/SHA, no ejecuta implementación ni acredita seguridad por sí solo. Los tests reales del consumidor deben atravesar las tres superficies aplicables y conservar la semántica ante creación/cambio y login; aceptación de longitud no equivale a autenticación exitosa de una contraseña incorrecta.

Ocho ofrece menos margen frente a adivinación que un mínimo mayor. Este valor es la preferencia solicitada, no una certificación de seguridad o cumplimiento; mantener controles de intentos y almacenamiento hash apropiados, sin guardar texto plano. No se elige algoritmo ni vendor automáticamente. Los planes v3 conservan sus bytes/semántica previos; el nuevo campo password_policy_checked indica si se aplicó0.8. Ningún consumidor se retrofita ni migra silenciosamente. Nuevas apps usan plan v4/contrato v6; el portal se gestiona por su tarea separada.

## Compatibilidad y rollout de auth0.9

Probar las features/parámetros de autenticación en el runtime real y medir su presupuesto CPU antes del rollout; workerd local no certifica límites remotos. Ningún algoritmo, librería o parámetro del portal se convierte en default universal. Revisar integridad/origen y fijar dependencias. Aplicar [despliegue verificable](despliegue.md); no subir límites ni conceder permisos sin autorización propia.
