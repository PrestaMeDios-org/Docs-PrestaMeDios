# SPEC-12 — Sesión aislada por pestaña: API sin caché y cierre de sesión en el servidor

| Campo | Valor |
| --- | --- |
| **ID** | SPEC-12 |
| **Perfil responsable** | Perfil 1 — Identidad, Usuarios, Permisos, Configuración Global y Despliegue |
| **Estado** | `APROBADO` — 2026-11-24 por el Perfil 1, con las recomendaciones de §10 (D-01…D-08; ADR-028) |
| **Versión** | 1.0.1 |
| **Requisitos cubiertos** | USR-01 ("determinando sus permisos y vistas en base a su rol"), Constitución P4 (seguridad por defecto) y P6 (privacidad: datos personales sólo a quien corresponde), ADR-015 (computadoras compartidas: cerrar la pestaña cierra la sesión) |
| **Responde a** | Hallazgo del 2026-11-24, en la preparación de demos: una pestaña duplicada muestra la vista y los datos de otro usuario (§2.3) |
| **Depende de** | SPEC-01 v1.0.0, SPEC-02 v1.0.1 y SPEC-03 v1.1.0 (B3, renovación de sesión), `IMPLEMENTADO`, en `develop` |
| **Módulos afectados** | Backend: `app/core` (`security.py`, `deps.py`, middleware nuevo), `app/main.py`, `users` (servicio, router, modelo y migración `0022`) · Frontend: `src/lib/api.ts`, `features/auth` |
| **Módulos ajenos** | Ninguno se modifica. Todos los módulos del frontend piden a la API por `apiRequest` (único `fetch` de `src/`), y en el backend el middleware actúa sobre todas las respuestas sin tocar los routers |
| **Relación con SPEC-11** | El proxy de producción no debe agregar caché a `/api/` (§11, H1). `Cache-Control: no-store` (RN-90) ya lo impide en proxies que respetan el estándar |
| **Constitución** | v1.1.0 |
| **Plan y tareas** | `specs/12-sesion-cache-cierre/plan.md` y `tasks.md` |

> **Regla SDD:** spec `APROBADO`. Un cambio de alcance o de contrato se propone como versión nueva y vuelve a aprobarse.

> **Numeración:** el 07 está reservado para `assistant` (Perfil 5) y el 11 es SPEC-11, así que este spec es el 12. Es del dominio de identidad y sesión, así que sigue la numeración de SPEC-01, SPEC-02, SPEC-03 y SPEC-09: `AC-123…`, `RN-90…`, `EC-60…`, `NFR-26…`. Las decisiones empiezan en `D-01`.

---

## 0. Resumen ejecutivo

Duplicar una pestaña del navegador con la aplicación abierta puede mostrar **la vista y los datos de otro usuario** que usó la misma computadora. La causa: las respuestas de la API no traen `Cache-Control`, el navegador las guarda atadas sólo a la URL (sin distinguir el token) y, al restaurar una pestaña duplicada, prefiere la caché. `GET /auth/me` devuelve entonces a la última persona que lo pidió en cualquier pestaña, y la interfaz arma el menú con ese rol. El backend sigue autorizando con el token de la pestaña, así que **no hay escalada de permisos** (las escrituras responden `403`), pero sí **exposición de datos personales** y una interfaz que no corresponde a quien la usa. Lo agrava que "Cerrar sesión" sólo borra el token de la pestaña: las copias de esa pestaña siguen abiertas y el token sigue valiendo en el servidor.

Dos fases, cada una con su PR:

- **Fase A — API sin caché (urgente, sin migración).** Toda respuesta de `/api/` lleva `Cache-Control: no-store`; el cliente del frontend pide sin caché; y al recargar, el frontend descarta un `/auth/me` que no sea del dueño del token.
- **Fase B — Cierre de sesión en el servidor.** El token lleva un identificador de sesión (`sid`) que se conserva al renovar. `POST /auth/logout` cierra esa sesión en el servidor (y con ella todas las copias de la pestaña) sin afectar las sesiones de otros dispositivos, y las demás pestañas de la misma sesión vuelven al login al instante.

---

## 1. Alcance

### 1.1 Dentro del alcance

| # | Capacidad | Requisitos | Fase |
| --- | --- | --- | --- |
| A1 | Middleware que agrega `Cache-Control: no-store` a toda respuesta de `/api/`, de éxito o de error, salvo que el endpoint fije su propio `Cache-Control` (§4.1) | P4, P6, USR-01 | A |
| A2 | `apiRequest` pide con `cache: "no-store"` (§4.2) | P6 | A |
| A3 | Al rehidratar la sesión, el frontend compara el `id` de `GET /auth/me` con el `sub` del token y descarta la sesión si no coinciden (§4.2) | USR-01 | A |
| B1 | Claim `sid` en el access token: nuevo en cada login y en cada cambio de contraseña; se conserva al renovar y al cerrar las demás sesiones (§5.1) | ADR-015 | B |
| B2 | Tabla `sesiones_cerradas` y migración `0022_users_sesiones_cerradas` (§5.2) | P7 | B |
| B3 | `POST /api/v1/auth/logout`: cierra la sesión del token en el servidor; `204`, idempotente (§5.3) | ADR-015, USR-01 | B |
| B4 | Toda autenticación rechaza un token de una sesión cerrada con `401 TOKEN_SESION_CERRADA` (§5.4) | P4 | B |
| B5 | Frontend: "Cerrar sesión" llama a `POST /auth/logout` y avisa a las demás pestañas por `BroadcastChannel`; las de la misma sesión vuelven al login (§5.5) | ADR-015 | B |

### 1.2 Fuera del alcance

| Capacidad | Motivo |
| --- | --- |
| Pasar el token a una cookie `HttpOnly` o agregar un refresh token | Ya decidido en D-13 de SPEC-03 (renovación deslizante, ADR-015 vigente). Este spec no cambia dónde vive el token |
| Que una pestaña duplicada **no** herede la sesión | Lo define el estándar: duplicar copia `sessionStorage`. Es lo esperado en cualquier sitio (una pestaña duplicada sigue con la sesión). Lo que este spec corrige es que la copia muestre a **otro** usuario y que cerrar sesión en una copia no cierre las demás |
| Listado de sesiones activas por usuario ("dónde tengo la sesión abierta") | D-03: no hace falta para el hallazgo. Si se pide, la tabla de sesiones activas (opción d de D-03) se evalúa en un spec aparte |
| Cambiar "Cerrar todas mis sesiones" (RN-69) | Sigue igual: incrementa `token_version` |
| Encabezados de caché de los archivos estáticos del frontend | No contienen datos de usuario; los define SPEC-11 en el `nginx.conf` |

---

## 2. Estado actual

### 2.1 Verificado en `develop` (backend `9ab4774`, frontend `de511a4`, 2026-11-24)

| Elemento | Estado |
| --- | --- |
| Encabezados de caché de la API | Ninguna respuesta trae `Cache-Control`, salvo la descarga de archivos (`files/service.py:431`, `private, no-store`). `GET /auth/me` responde `200` con `vary: Origin` (lo agrega CORS) y sin `Vary: Authorization` |
| `src/lib/api.ts` | Único `fetch` del frontend (`:128`), sin opción `cache`. El token va en `sessionStorage` (`:9`, SPEC-02 D-06) |
| Rehidratación (`AuthContext.tsx:40`) | Con token en `sessionStorage`, pide `GET /auth/me` y usa la respuesta como usuario de la sesión, sin compararla con el token |
| Cierre de sesión (`AuthContext.tsx:33`) | Sólo `tokenStore.clear()` y estado local. No hay endpoint de logout: el token sigue valiendo hasta su `exp` (30 min) y la pestaña que lo tenga puede renovarlo hasta `JWT_SESION_MAX_HORAS` (8 h) |
| Claims del token (`security.py:84`) | `sub`, `rol`, `sede`, `tv`, `iss`, `iat`, `auth_time`, `exp`, `jti`. `jti` cambia en cada renovación; no hay identificador de sesión estable |
| Autenticación (`deps.py:40`) | `_sesion_autenticada` valida firma, `token_version` y estado `ACTIVO`. Es el punto común de `get_current_user`, `get_sesion_actual` y `get_current_user_permitiendo_cambio` |
| Emisión de tokens (`users/service.py`) | Login (`:256`) y cambio de contraseña (`:515`) inician sesión nueva; `renovar_sesion` (`:913`) y `cerrar_sesiones` (`:928`) conservan `auth_time` vía `_emitir_token` (`:902`) |

### 2.2 Brechas

| ID | Brecha | Requisito |
| --- | --- | --- |
| G-1 | El navegador guarda en su caché (en disco) respuestas con datos personales de cualquier usuario, y las reutiliza para otra pestaña con otro token | P6, USR-01 |
| G-2 | La interfaz puede mostrar el rol, el menú y los datos de una persona distinta de la dueña del token | USR-01 |
| G-3 | "Cerrar sesión" no cierra las copias de la pestaña, y el token sigue valiendo en el servidor | ADR-015 |

### 2.3 Reproducción (2026-11-24)

Con dos cuentas (Superadministrador y Estudiante), en Chrome:

1. Pestaña A: sesión de Superadministrador. Pestaña B: duplicado de A; en B se cierra sesión y se entra como Estudiante (Lucía). Al recargar B, `GET /auth/me` llega al servidor y la caché queda con Lucía.
2. Se duplica A (token de `SUPERADMIN`): la copia muestra **a Lucía y la vista de estudiante**. Al recargar con F5, vuelve al Superadministrador.
3. Se inicia sesión como Superadministrador en otra pestaña y se duplica B (token de `ESTUDIANTE`): la copia muestra **la vista de Superadministrador** y abre los formularios de "Nuevo equipo" y "Editar equipo".

Verificado contra el backend local: un `GET /auth/me` con el token del estudiante y `cache: "force-cache"` (lo que hace la restauración de una pestaña duplicada) devuelve `rol: SUPERADMIN`; el mismo pedido con `cache: "no-store"` devuelve `ESTUDIANTE`. Con el token del estudiante, `PATCH /inventory/equipamiento/{id}` y `POST /inventory/equipamiento` responden `403 PERMISO_INSUFICIENTE`: la autorización del servidor (P4.2) funciona.

---

## 3. Actores

| Actor | Fase A | Fase B |
| --- | --- | --- |
| Cualquier usuario con sesión | Ve siempre sus propios datos, aun en una pestaña duplicada | "Cerrar sesión" cierra esa sesión en todas las copias de la pestaña; sus sesiones en otros dispositivos siguen abiertas |
| Navegador y proxies | No guardan respuestas de la API | — |
| Operador | — | Nada que programar: la tabla se limpia sola (RN-95) |

---

## 4. Fase A — API sin caché

### 4.1 Backend

| ID | Regla |
| --- | --- |
| RN-90 | Toda respuesta cuya ruta empiece con `/api/` lleva `Cache-Control: no-store`, sea de éxito o de error (`AppError`, `422` de validación, `401` de autenticación). Si el endpoint ya fijó un `Cache-Control` (hoy, la descarga de archivos), se respeta. Lo aplica un middleware de `app/core/` registrado en `main.py`; ningún router cambia |

`/health`, `/docs` y `/openapi.json` quedan fuera: no tienen datos de usuario.

### 4.2 Frontend

| ID | Regla |
| --- | --- |
| RN-91 | `apiRequest` manda `cache: "no-store"` en todos los pedidos. Es una segunda capa por si un proxy o una versión vieja del backend no manda el encabezado |
| RN-92 | Al rehidratar (con token en `sessionStorage`), si el `id` de `GET /auth/me` no es el `sub` del token, el frontend borra el token y muestra el login con el aviso "No pudimos confirmar tu sesión. Iniciá sesión nuevamente." Se lee el `sub` sin verificar la firma, como ya hace `leerTiemposToken` |

---

## 5. Fase B — Cierre de sesión en el servidor

### 5.1 Identificador de sesión

| ID | Regla |
| --- | --- |
| RN-93 | El access token lleva el claim `sid` (UUID v4). El login y el cambio de contraseña (que ya inicia sesión nueva, con `auth_time` nuevo) generan un `sid` nuevo; `POST /auth/renovar` y `POST /auth/me/sesiones/cerrar` lo conservan, igual que `auth_time` (RN-65, RN-69). Un token sin `sid` (emitido antes de esta versión) recibe uno nuevo al renovarse |

Con `sid`, todas las copias de una pestaña comparten la sesión aunque cada una renueve su token por su lado (cada renovación cambia el `jti`, pero no el `sid`).

### 5.2 Modelo y migración `0022_users_sesiones_cerradas`

Tabla `sesiones_cerradas` en el módulo `users`:

| Columna | Tipo | Notas |
| --- | --- | --- |
| `sid` | `UUID` | Clave primaria |
| `usuario_id` | `Integer` | FK a `usuarios.id`, `ON DELETE CASCADE`, con índice |
| `cerrada_en` | `TIMESTAMPTZ` | `server_default now()` |
| `vence_en` | `TIMESTAMPTZ` | `auth_time` + `JWT_SESION_MAX_HORAS`. Pasado ese momento ningún token de la sesión es válido (RN-66), así que la fila ya no hace falta |

La migración es reversible (el downgrade borra la tabla) y el modelo se registra en `alembic/env.py`.

### 5.3 Endpoint

| Método y ruta | Autenticación | Respuestas |
| --- | --- | --- |
| `POST /api/v1/auth/logout` | `get_sesion_actual` (se permite con cambio de contraseña pendiente, D-07) | `204` · `401 TOKEN_*` o `NO_AUTENTICADO` como cualquier endpoint protegido |

| ID | Regla |
| --- | --- |
| RN-94 | `POST /auth/logout` inserta el `sid` del token en `sesiones_cerradas` (`ON CONFLICT DO NOTHING`: repetirlo es inocuo) y responde `204`. Con un token sin `sid` responde `204` sin cambios: ese token vence solo en 30 minutos como máximo (EC-63) |
| RN-95 | En la misma transacción borra las filas con `vence_en` anterior a ahora. No hace falta un comando programado |

### 5.4 Validación en cada pedido

| ID | Regla |
| --- | --- |
| RN-96 | `_sesion_autenticada` rechaza un token cuyo `sid` esté en `sesiones_cerradas` con `401 TOKEN_SESION_CERRADA` ("La sesión se cerró."). Como empieza con `TOKEN_`, el frontend ya cierra la sesión ante ese código (SPEC-02 §6.1). Es una lectura por clave primaria más por pedido autenticado (NFR-26) |

### 5.5 Frontend

| ID | Regla |
| --- | --- |
| RN-97 | "Cerrar sesión" (menú de la cuenta y pantalla de cambio obligatorio de contraseña) guarda el token, borra `sessionStorage` y muestra el login sin esperar; después manda `POST /auth/logout` con ese token. Si el pedido falla (sin conexión, `401`), no se muestra error: la sesión local ya se cerró y el token vence solo |
| RN-98 | Al cerrar sesión, la pestaña publica `{ tipo: "cierre", sid }` en el `BroadcastChannel` `prestamedios.sesion`. Toda pestaña cuyo token tenga ese `sid` cierra la sesión con el aviso "Cerraste esta sesión en otra pestaña. Iniciá sesión nuevamente." Si el navegador no tiene `BroadcastChannel`, la otra pestaña se entera en su próximo pedido (RN-96) |
| RN-99 | Los cierres automáticos (vencimiento por inactividad, `401 TOKEN_*`) no llaman a `POST /auth/logout`: el token ya no vale. Sí publican en el canal, para que las copias no sigan mostrando datos |

---

## 6. Códigos de error

| Código | HTTP | Cuándo | Mensaje del frontend |
| --- | --- | --- | --- |
| `TOKEN_SESION_CERRADA` | `401` | El `sid` del token está en `sesiones_cerradas` (RN-96) | "Esta sesión se cerró. Iniciá sesión nuevamente." |

Se reutilizan los demás `TOKEN_*`, `NO_AUTENTICADO` y `PERMISO_INSUFICIENTE` de SPEC-01…SPEC-03.

---

## 7. Criterios de aceptación

Cada criterio de backend tiene al menos un test anotado `# AC-NN`, con `pytestmark = pytest.mark.integracion` y PostgreSQL real (P9).

### 7.1 Fase A — `tests/core/test_cache.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-123 | `GET /api/v1/auth/me`, un listado de `inventory`, un `401` sin token, un `403` y un `422` de validación responden con `Cache-Control: no-store` | RN-90 |
| AC-124 | La descarga de un archivo conserva `Cache-Control: private, no-store` (no se duplica ni se pisa) | RN-90 |
| AC-125 | `/health` no lleva el encabezado | RN-90 |

### 7.2 Fase B — `tests/users/test_logout.py` y `tests/users/test_migracion_0022.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-126 | El token del login trae `sid`; el de `POST /auth/renovar` y el de `POST /auth/me/sesiones/cerrar` traen el mismo `sid`; el del cambio de contraseña trae uno distinto | RN-93 |
| AC-127 | Un token sin `sid` se renueva y el nuevo trae `sid` | RN-93 |
| AC-128 | `POST /auth/logout` → `204`; después, el mismo token y un token renovado de la misma sesión responden `401 TOKEN_SESION_CERRADA` en `GET /auth/me`, en `POST /auth/renovar` y en un endpoint de administración | RN-94, RN-96 |
| AC-129 | Otra sesión del mismo usuario (otro login) sigue funcionando después del logout | RN-94 |
| AC-130 | Repetir `POST /auth/logout` con el mismo `sid` (desde otra copia, con un token todavía no rechazado por carrera) no falla: `204` o `401 TOKEN_SESION_CERRADA`, nunca `500` | RN-94, EC-62 |
| AC-131 | `POST /auth/logout` con `debe_cambiar_password = true` → `204` | RN-94, D-07 |
| AC-132 | Una fila con `vence_en` pasado se borra en el siguiente logout de cualquier usuario | RN-95 |
| AC-133 | Migración `0022`: upgrade → downgrade → upgrade | §5.2 |

### 7.3 Frontend (`npm run typecheck`, `npm run build`, Vitest y verificación manual)

| ID | Criterio |
| --- | --- |
| AC-134 | Vitest: `apiRequest` llama a `fetch` con `cache: "no-store"`; la rehidratación con un `/auth/me` de otro `id` borra el token y deja el aviso (RN-91, RN-92) |
| AC-135 | Verificación manual de §2.3 en Chrome y en Firefox: la copia de una pestaña muestra siempre al dueño de su token; en DevTools → Network, `/auth/me` nunca aparece como `(disk cache)` o `(memory cache)` |
| AC-136 | Verificación manual: con A y su duplicado B abiertos, "Cerrar sesión" en B lleva a A al login con el aviso de RN-98, sin recargar; una sesión del mismo usuario en otro navegador sigue abierta |
| AC-137 | Vitest: "Cerrar sesión" manda `POST /auth/logout` con el token anterior y publica en el canal; un mensaje con otro `sid` no cierra la sesión. `npm run typecheck` y `npm run build` en verde |

---

## 8. Casos de borde

| ID | Escenario | Resultado |
| --- | --- | --- |
| EC-60 | Un proxy intermedio ignora `no-store` y entrega un `/auth/me` ajeno | RN-92 lo detecta al rehidratar; el resto de los pedidos los autoriza el servidor con el token (P4.2) |
| EC-61 | Se duplica una pestaña, cada copia renueva su token por su lado y después se cierra sesión en una | Las dos comparten `sid`: la otra recibe el aviso por el canal y, si no, `401 TOKEN_SESION_CERRADA` en su próximo pedido (AC-128) |
| EC-62 | Dos copias cierran sesión casi a la vez | `ON CONFLICT DO NOTHING`: la segunda responde `204` o `401`; el frontend ignora el resultado (RN-97) |
| EC-63 | Token emitido antes de la Fase B (sin `sid`) | Funciona hasta vencer o hasta renovarse (con lo que recibe `sid`); su logout es sólo local (RN-94). Pasados 30 minutos del despliegue no quedan tokens sin `sid` sin renovar |
| EC-64 | Se cierra sesión sin conexión | La pestaña vuelve al login; las copias se enteran por el canal (es local, no usa red). El token vence solo |
| EC-65 | Un administrador da de baja la cuenta mientras tiene sesiones cerradas en la tabla | Las filas se borran en cascada con el usuario, o vencen (RN-95) |
| EC-66 | Una pestaña abierta con un token anterior a la Fase A (sin `no-store` en su caché) | La caché vieja sigue en el navegador hasta que se pide de nuevo: RN-91 hace que el frontend nuevo no la use. Para la demo, alcanza con recargar o vaciar la caché una vez |

---

## 9. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| NFR-26 | La validación de RN-96 agrega como máximo una consulta por clave primaria por pedido autenticado |
| NFR-27 | Sin dependencias nuevas en backend ni frontend (`BroadcastChannel` es nativo) |
| NFR-28 | Cobertura ≥ 85 % del código nuevo de `core` y `users`. Todos los AC de backend automatizados contra PostgreSQL |

---

## 10. Decisiones

> **Resueltas el 2026-11-24:** el Perfil 1 adoptó todas las recomendaciones (columna "Decisión").

| ID | Pregunta | Opciones | Decisión |
| --- | --- | --- | --- |
| D-01 | ¿Dónde se evita la caché? | (a) Backend (`no-store`) y frontend (`cache: "no-store"`) · (b) Sólo frontend · (c) Sólo backend · (d) `Cache-Control: private` con `Vary: Authorization` | **(a)**. El backend es la causa y cubre proxies y cualquier otro cliente; el frontend es una línea y protege aunque falle el encabezado. (d) sigue guardando datos personales en disco y depende de que el navegador respete `Vary` en la restauración |
| D-02 | ¿A qué rutas aplica `no-store`? | (a) Todo `/api/` · (b) Sólo endpoints autenticados | **(a)**. Una regla sin excepciones que mantener. Las respuestas públicas (portada, sedes) son JSON chicos: perder su caché no se nota |
| D-03 | ¿Cómo se cierra una sesión en el servidor? | (a) `sid` estable + tabla de sesiones cerradas · (b) Incrementar `token_version` (cierra todas las sesiones del usuario) · (c) Lista de `jti` revocados · (d) Tabla de sesiones activas, consultada en cada pedido | **(a)**. (b) no necesita migración, pero cerrar sesión en la computadora del laboratorio cerraría también el celular, y eso ya lo ofrece "Cerrar todas mis sesiones". (c) no alcanza: cada copia renueva su token con otro `jti` y sobrevive. (d) escribe en cada login y sólo suma valor si se quiere listar sesiones (fuera de alcance) |
| D-04 | ¿Cómo se enteran las demás pestañas? | (a) `BroadcastChannel` · (b) Nada: el próximo pedido responde `401` · (c) Evento `storage` de `localStorage` | **(a)**, con (b) como respaldo automático. (c) obliga a escribir en `localStorage`, que ADR-015 evita para la sesión |
| D-05 | ¿Se compara `/auth/me` con el `sub` del token (RN-92)? | (a) Sí · (b) No, alcanza con `no-store` | **(a)**. Son tres líneas y cubren proxies o extensiones que ignoren el encabezado (EC-60) |
| D-06 | ¿Cómo se entrega? | (a) Fase A primero, en PRs propios (backend y frontend), y después la B · (b) Todo junto | **(a)**. La A no tiene migración, corrige la exposición de datos y conviene tenerla antes de la próxima demo |
| D-07 | ¿Se puede cerrar sesión con el cambio obligatorio de contraseña pendiente? | (a) Sí (`get_sesion_actual`) · (b) No (`get_sesion_operativa`) | **(a)**. La pantalla de cambio obligatorio tiene botón "Cerrar sesión" (`ChangePasswordForm.tsx:94`); con (b) ese cierre quedaría sólo local |
| D-08 | ¿Código nuevo o `TOKEN_REVOCADO`? | (a) `TOKEN_SESION_CERRADA` · (b) `TOKEN_REVOCADO` | **(a)**. El mensaje de `TOKEN_REVOCADO` habla de "un cambio en tu cuenta", que acá no es cierto. El frontend ya trata todo `TOKEN_*` igual |

---

## 11. Coordinación

| ID | Para | Pedido | Origen |
| --- | --- | --- | --- |
| H1 | Perfil 1 (SPEC-11) | El `nginx.conf` de producción no agrega caché (`proxy_cache`, `expires`) a `/api/` y deja pasar el `Cache-Control` del backend | RN-90, EC-60 |
| H2 | Equipo | Mientras no esté la Fase A en `develop`: en demos, no duplicar pestañas; para cambiar de usuario, cerrar sesión y cerrar la pestaña. Después del despliegue, vaciar la caché del navegador una vez en las computadoras del laboratorio (EC-66) | §2.3 |

Ningún otro perfil tiene que cambiar código.

---

## 12. Trazabilidad

| Requisito | Función o endpoint | Criterios | Bordes | Fase |
| --- | --- | --- | --- | --- |
| P6, USR-01 (no mostrar datos de otro usuario) | Middleware de `app/core/`, `apiRequest`, rehidratación de `AuthContext` | AC-123…AC-125, AC-134, AC-135 | EC-60, EC-66 | A |
| ADR-015, USR-01 (cerrar sesión en una computadora compartida) | Claim `sid`, `sesiones_cerradas`, `POST /auth/logout`, `_sesion_autenticada`, `logout` de `AuthContext` | AC-126…AC-133, AC-136, AC-137 | EC-61…EC-65 | B |

---

## 13. Historial de cambios

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 1.0.1 | 2026-11-26 | Perfil 1 (con asistencia de IA) | Editorial, sin cambio de contrato: la migración de la Fase B pasa a `0022_users_sesiones_cerradas`, porque `0021` la tomó `core_envios_correo` (SPEC-11), mergeada en `develop` después de redactar el spec |
| 1.0.0 | 2026-11-24 | Perfil 1 | **Aprobado**, con las recomendaciones de §10 (D-01…D-08). Plan y tareas en `plan.md` y `tasks.md` |
| 0.1.0 | 2026-11-24 | Perfil 1 (con asistencia de IA) | Borrador inicial a partir del hallazgo de la pestaña duplicada (§2.3). Fase A (API sin caché) y Fase B (cierre de sesión en el servidor con `sid`). Decisiones D-01…D-08 con recomendación |
