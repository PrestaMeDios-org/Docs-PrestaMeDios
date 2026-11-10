# PLAN-03 — Plan técnico de implementación de SPEC-03

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/03-users-api-publica-cuenta-archivos/spec.md` (v1.1.0, `APROBADO` 2026-11-08; la v1.0.0 se aprobó el 2026-11-03) |
| **Estado del plan** | `COMPLETADO` el 2026-11-10 — v1.1.0, aprobado por el Perfil 1 el 2026-11-08 (ver §12) |
| **Perfil** | 1 |
| **Entrega** | Cuatro PRs de backend y tres de frontend, en el orden de §2 (D-01, D-20). La Fase A ya está mergeada (PR #18) |

---

## 1. Punto de partida (`develop` al 2026-11-08: backend `3ad6b6b`, frontend `8f7832b`)

| Elemento | Situación | Impacto en el plan |
| --- | --- | --- |
| `app/database.py` | `async_sessionmaker(..., autoflush=False)`, igual que el `sessionmaker_` de los tests | `datos_publicos_por_ids` no emite cambios pendientes del llamador (EC-35, corregido en spec v1.1.0) |
| `tests/conftest.py` | `TRUNCATE` de una lista fija de tablas con `CASCADE` (desde SPEC-06 incluye `notificaciones` y `comunicados`); base creada con `create_all`; `crear_usuario` agrega al usuario en la sesión `db`. Desde SPEC-05 tiene además fábricas de `inventory` y `loans` (`crear_equipamiento`, …) | `TRUNCATE ... CASCADE` vacía también las tablas que tienen FK a las de la lista, así que `archivos` y `archivos_contenido` (B2) se vacían solas. `intentos_recuperacion` (B1, sin FK) hay que sumarla a `_TABLAS`. Para AC-86 se puede reutilizar `crear_equipamiento` si hiciera falta una orden real, pero `vincular_archivo` se prueba sin `loans` |
| `app/core/security.py` | `crear_access_token` y `TokenPayload(sub, tv)` sin `auth_time` | B3 agrega el claim con valor por defecto, sin romper el helper `auth()` de los tests |
| `app/main.py` | Registro explícito de routers; desde SPEC-06 monta también `notifications` | B2 monta `files` en `/api/v1/files` |
| `alembic/env.py` | Importa los modelos de cada módulo (incluido `notifications`) | B2 registra `app.modules.files.models` |
| Migraciones | Cabeza: `0013_notifications_init` (`down_revision = 0010`). `0011_loans_resolucion` está en `feat/loans-validar` (PR #23) con `down_revision = 0013`; SPEC-05 reserva también `0012` | Nombres fijos: `0014_files_init` (B2) y `0015_users_recuperacion` (B1), según D-22. `down_revision` = la cabeza de `develop` al abrir cada PR; `alembic heads` con una sola cabeza antes de mergear (EC-45) |
| `loans` | Fase 1 en `develop` (PR #21): `pdf_aval_id` en el esquema; todo alta gama responde `422 AVAL_REQUERIDO` | B2 es lo que lo destraba (K3, D-20). `loans` hace el cambio de su lado; este plan sólo publica `vincular_archivo` |
| Python | README: "≥ 3.11, validado con 3.12". En el equipo hay 3.12 (Perfil 5), 3.13 (Perfil 2) y 3.14 (Perfil 1) | DT-30: el test de AC-67 falla en 3.12 y 3.13 (A-04). Cada PR de la Fase B se corre al menos en dos versiones hasta que el despliegue fije una (K8) |
| Frontend | Sin React Router (`App.tsx` decide la pantalla con estado); `src/lib/api.ts` con `apiRequest`, `tokenStore` en `sessionStorage` y `ApiError`; `AuthContext.tsx` con `login`, `logout`, `aplicarToken`. El PR #12 del Perfil 5 (abierto) y la Fase 1 de `loans` también tocan `App.tsx` | Las pantallas públicas de B1 se resuelven en `App.tsx` leyendo el fragmento; B2 extiende `apiRequest` para `FormData` y `Blob`. Rebasar sobre `develop` antes de abrir cada PR de frontend |

---

## 2. Ramas y orden de entrega

| Orden | Fase | Backend | Frontend | Depende de |
| --- | --- | --- | --- | --- |
| 1 | A | `feat/users-datos-publicos` ✔ PR #18 | — | — |
| 1b | A (DT-30) | `fix/users-test-dataclass` | — | — |
| 2 | B2 | `feat/files-almacenamiento` | `feat/users-foto` | — |
| 3 | B1 | `feat/users-recuperacion` | `feat/auth-recuperacion` | Nada funcional. Comparte `settings.py`, `.env.example` y `conftest.py` con B2: si B2 ya está mergeada, se rebasa sobre ella |
| 4 | B3 | `feat/auth-renovacion` | `feat/auth-renovacion` | — (puede ir en paralelo con B2 o B1: sólo comparte `settings.py` y `.env.example`) |

Todas salen de `develop` actualizado y entran por PR hacia `develop` con una revisión. **B2 va antes que B1 (D-20):** la Fase 1 de `loans` ya está en `develop` y sin `files` rechaza todo pedido de alta gama. B1 sólo la espera la Fase C de SPEC-06, que está diferida.

---

## 3. Dependencias nuevas

| Repo | Paquete | Fase | Justificación |
| --- | --- | --- | --- |
| Backend | `python-multipart>=0.0.9` | B2 | FastAPI la exige para `UploadFile` y formularios multipart |
| Backend | `Pillow>=11.3` | B2 | Volver a codificar la foto, quitar EXIF y neutralizar políglotas (D-11). Mínimo 11.3 para tener paquetes binarios en Python 3.13 y 3.14, las versiones del equipo; confirmarlo con `pip install` en B2-01 |
| Desarrollo (opcional) | Mailpit (contenedor, no paquete de Python) | B1 | SMTP local para ver los correos sin enviarlos (NFR-22) |

B1 y B3 no agregan dependencias: `smtplib`, `string.Template`, `hashlib`, `hmac` y `secrets` son de la biblioteca estándar. El frontend no agrega ninguna.

---

## 4. Fase A — `datos_publicos_por_ids`

### 4.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/modules/users/service.py` | Modificar | Sección "API pública para otros módulos" con `DatosPublicosUsuario` y `datos_publicos_por_ids` |
| `tests/users/test_datos_publicos.py` | Crear | AC-61…AC-70 |
| `Backend-PrestaMeDios/README.md` | Modificar | Una línea en la sección de `users`: la función pública y para qué sirve |

### 4.2 Diseño

```python
async def datos_publicos_por_ids(db, ids):
    unicos = list(set(ids))                      # RN-35; consume el iterable una sola vez
    if not unicos:
        return {}                                # RN-36: sin consulta
    filas = await db.execute(
        select(Usuario.id, Usuario.nombre, Usuario.apellido)   # RN-40: sólo tres columnas
        .where(Usuario.id == any_(bindparam("ids", unicos, type_=ARRAY(Integer))))  # RN-41
    )
    return {f.id: DatosPublicosUsuario(f.id, f.nombre, f.apellido) for f in filas}
```

- Sin `commit`, `rollback` ni `flush` (RN-42).
- `ARRAY` de `sqlalchemy.dialects.postgresql`; un solo parámetro, así 40 000 ids no superan el límite de asyncpg (AC-70).
- Docstring con el requisito y la aclaración de RN-39 y RN-43, para que quien la use sepa que la autorización es suya.

### 4.3 Tests

- Contador de consultas: fixture local que registra un listener `before_cursor_execute` sobre `engine.sync_engine` y lo quita al terminar (AC-62, AC-63).
- Los usuarios se crean con `crear_usuario`; la función se llama con una sesión nueva de `sessionmaker_`, para comprobar que su *identity map* no tiene objetos `Usuario` (AC-68).
- AC-69: en la sesión nueva se agrega un `ParametroGlobal` modificado sin confirmar, se llama a la función, se verifica `session.in_transaction()`, se hace `rollback` y se comprueba en otra sesión que el cambio no quedó.
- AC-70: lote de 40 000 ids (casi todos inexistentes) desde una lista, un `set` y un generador.

### 4.4 Estado y corrección de DT-30

**Implementada** (commit `9341c59`, backend PR #18, 2026-11-06): 16 tests, la suite completa con 386 pasados contra PostgreSQL 18 y cobertura de `users` de 94 %.

**DT-30.** `test_datos_publicos_solo_tiene_id_nombre_y_apellido_e_inmutable` asigna `dni`, que no es campo, y espera `FrozenInstanceError`. En un `dataclass(frozen=True, slots=True)`, Python 3.12 y 3.13 lanzan `TypeError` en ese caso (lo reprodujeron el Perfil 2 con 3.13.12 y el Perfil 5 con 3.12.10): el `__setattr__` generado llama a `super()` con la clase original y no con la que crea `slots=True`. Python 3.14, con el que se escribió el test, ya no tiene ese problema. La función no cambia. El test se ajusta a AC-67 v1.1.0:

- asignar `nombre` → `pytest.raises(FrozenInstanceError)`;
- asignar `dni` → `pytest.raises((FrozenInstanceError, TypeError, AttributeError))`, y `not hasattr(datos, "__dict__")`.

Rama `fix/users-test-dataclass` desde `develop`. Verificación: el archivo en verde en 3.14 y en 3.12 o 3.13 (pedirle a los Perfiles 2 o 5 que lo corran).

---

## 5. Fase B1 — Correo y recuperación de contraseña

### 5.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/settings.py` | Modificar | `EMAIL_BACKEND`, `SMTP_*`, `EMAIL_FROM`, `FRONTEND_URL`, `RECUPERACION_*` (spec §5.1 y §5.2) |
| `app/core/email.py` | Crear | `TipoCorreo`, `CorreoRenderizado`, `ErrorEnvioCorreo`, `renderizar_correo`, `enviar_correo`, backends `smtp` y `memoria` (`bandeja_memoria()` y `vaciar_bandeja_memoria()` para tests) |
| `app/core/plantillas_correo/RECUPERACION_PASSWORD.txt` | Crear | Asunto en la primera línea; cuerpo con `$nombre`, `$enlace` y `$vigencia_minutos` |
| `app/core/plantillas_correo/NOTIFICACION.txt` | Crear | Asunto `$titulo`; cuerpo `$mensaje`, una línea en blanco y el pie fijo con `$enlace_app` (que `renderizar_correo` completa con `FRONTEND_URL`, sin que lo pase el llamador) y "Este es un aviso automático de PrestaMeDios" (RN-77, D-21) |
| `app/modules/users/models.py` | Modificar | `TokenRecuperacion`, `IntentoRecuperacion` |
| `app/modules/users/schemas.py` | Modificar | `SolicitudRecuperacion {email}`, `ConfirmacionRecuperacion {token, password_nueva}` (reutiliza el validador de RN-03), `MensajeResponse {detail}` |
| `app/modules/users/service.py` | Modificar | `solicitar_recuperacion`, `confirmar_recuperacion`, `_invalidar_tokens_recuperacion`; `actualizar_perfil` y `editar_por_admin` invalidan los tokens si cambia el email (RN-53) |
| `app/modules/users/router.py` | Modificar | `POST /auth/recuperacion` (con `Request` y `BackgroundTasks`) y `POST /auth/recuperacion/confirmar` |
| `alembic/versions/0015_users_recuperacion.py` | Crear | Las dos tablas e índices; `downgrade` las borra. `down_revision` = la cabeza de `develop` al abrir el PR (D-22) |
| `tests/conftest.py` | Modificar | `intentos_recuperacion` en `_TABLAS`; `EMAIL_BACKEND=memoria` para la sesión de tests; fixture `correos` que vacía y devuelve la bandeja |
| `tests/core/test_email.py` | Crear | AC-100 (las dos plantillas, incluida `NOTIFICACION`), AC-101 |
| `tests/users/test_recuperacion.py` | Crear | AC-71…AC-79 |
| `tests/users/test_migracion_recuperacion.py` | Crear | AC-80 (como `test_spaces_migrations.py`) |
| `.env.example`, `README.md` | Modificar | Variables nuevas sin valores reales; cómo levantar Mailpit; el flujo de recuperación |

### 5.2 Diseño

- **Plantillas.** `renderizar_correo` lee `plantillas_correo/<tipo>.txt` con `importlib.resources` (funciona igual en Docker) y usa `Template.substitute`, que lanza `KeyError` si falta una variable; se traduce a `ValueError` con el nombre del tipo y de la variable, nunca con los valores (RN-71, RN-74). Las plantillas se cachean. Antes de sustituir, al contexto del llamador se le suma `enlace_app` = `FRONTEND_URL`. Si el llamador manda una clave con ese nombre, se rechaza con `ValueError`, para que el pie no se pueda falsear.
- **Uso desde `notifications` (D-21).** Su comando `enviar-correos` (Fase C de SPEC-06) llama a `enviar_correo(TipoCorreo.NOTIFICACION, destinatario, {"titulo": …, "mensaje": …})` por cada notificación pendiente y captura `ErrorEnvioCorreo` para registrar el error. Este plan no toca `notifications`: sólo deja el tipo, la plantilla y AC-100.
- **Transporte.** `enviar_correo` renderiza y delega en el backend elegido por `EMAIL_BACKEND`. El de `smtp` arma un `EmailMessage` y lo envía con `smtplib.SMTP` o `SMTP_SSL` dentro de `asyncio.to_thread`, con `timeout=10`; cualquier `OSError` o `smtplib.SMTPException` se convierte en `ErrorEnvioCorreo` (RN-73, RN-75). Logger `app.core.email`: tipo, resultado y, si se pasa, `usuario_id`.
- **Solicitud** (`solicitar_recuperacion(db, email, ip) -> Pendiente | None`):
  1. Borra los intentos de más de 24 h.
  2. Calcula `email_hash = HMAC-SHA256(JWT_SECRET_KEY, email)`: con un hash simple, un diccionario de emails conocidos lo revertiría.
  3. Cuenta intentos de la última hora por `email_hash` y por `ip`; si supera alguno, `429 DEMASIADOS_INTENTOS` (RN-49). Registra el intento.
  4. Si la cuenta existe y está `ACTIVO`: invalida sus tokens pendientes, crea uno nuevo (`secrets.token_urlsafe(32)`, guarda `sha256`) y devuelve los datos para el correo (destinatario, nombre, enlace). Si no, devuelve `None`.
  5. `commit`. El router agenda el correo con `BackgroundTasks` sólo si hubo `Pendiente`, mediante un envoltorio que atrapa `ErrorEnvioCorreo` y lo registra sin el enlace. La respuesta es siempre el mismo `202`.

  Dos solicitudes simultáneas pueden pasar el límite por una: se acepta (el límite es de abuso, no de seguridad).
- **Confirmación** (`confirmar_recuperacion(db, token, password_nueva)`): `UPDATE ... RETURNING usuario_id` atómico (RN-50); bloquea al usuario con `FOR UPDATE`; si no está `ACTIVO`, `rollback` y `422` (RN-51). Aplica RN-52 en la misma transacción. La validación de la contraseña la hace Pydantic antes de tocar el token, así un `422` de RN-03 no lo consume (AC-77).
- **Enlace.** `f"{FRONTEND_URL}/#/restablecer?token={token}"` (RN-47).
- **IP.** `request.client.host`; sin lógica de proxies en esta fase (RN-54, ítem K8).

### 5.3 Migración

| `upgrade` | `downgrade` |
| --- | --- |
| `tokens_recuperacion` (FK `CASCADE`, `UNIQUE(token_hash)`, índice `(usuario_id, usado_en)`); `intentos_recuperacion` con índices `(email_hash, created_at)` y `(ip, created_at)`. Sin `CHECK` (no aplica DT-26) | Borra las dos tablas |

Verificación: `upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo, y `alembic heads` con una sola cabeza.

---

## 6. Fase B2 — Archivos y foto de perfil (se entrega antes que B1, D-20)

### 6.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/settings.py` | Modificar | `ARCHIVO_FOTO_MAX_MB`, `ARCHIVO_PDF_MAX_MB`, `ARCHIVO_HUERFANO_HORAS`, `ARCHIVO_MAX_PENDIENTES` (5) |
| `app/modules/files/enums.py` | Crear | `PropositoArchivo` (`StrEnum`, MAYÚSCULAS) |
| `app/modules/files/models.py` | Crear | `Archivo`, `ArchivoContenido` (`BYTEA` con `deferred`) |
| `app/modules/files/schemas.py` | Crear | `ArchivoResponse` |
| `app/modules/files/service.py` | Crear | Internas: `guardar_archivo`, `leer_con_limite`, `detectar_tipo`, `procesar_foto`, `puede_descargar`, `borrar_archivo`, `limpiar_huerfanos`. Públicas (spec §6.5): `vincular_archivo`, `abrir_archivo`, `respuesta_descarga`, `ArchivoContenido` |
| `app/modules/files/router.py` | Crear | `POST /archivos`, `GET /archivos/{id}/contenido` |
| `app/modules/files/cli.py` | Crear | `python -m app.modules.files.cli limpiar-huerfanos [--horas N]`, con la estructura del CLI de `users` |
| `app/modules/users/models.py` | Modificar | `Usuario.foto_id` (FK a `archivos.id` por nombre de tabla, `ondelete="SET NULL"`, `use_alter=True` por el ciclo con `archivos.propietario_id`) |
| `app/modules/users/schemas.py` | Modificar | `foto_id: UUID \| None` en `UsuarioResumen` (lo heredan `UsuarioPublico` y `UsuarioDetalle`) |
| `app/modules/users/service.py` | Modificar | `reemplazar_foto`, `quitar_foto`, `quitar_foto_por_admin` (bloquean al usuario con `FOR UPDATE`, EC-41; historial RN-59; reglas de UC-12 para el `ADMIN_LOCAL`, RN-64) |
| `app/modules/users/router.py` | Modificar | `PUT` y `DELETE /auth/me/foto`, `DELETE /users/{id}/foto` |
| `app/main.py`, `alembic/env.py` | Modificar | Montar el router con el tag "Archivos"; registrar los modelos |
| `alembic/versions/0014_files_init.py` | Crear | Enum, tablas, índice y FK `usuarios.foto_id`. `down_revision` = la cabeza de `develop` al abrir el PR (hoy `0013_notifications_init`, o `0011_loans_resolucion` si el PR #23 entra antes; D-22) |
| `requirements.txt` | Modificar | `python-multipart`, `Pillow` |
| `tests/files/` | Crear | AC-81…AC-88, AC-90; generadores de un JPEG con EXIF (con Pillow) y de un PDF mínimo |
| `tests/users/test_foto.py` | Crear | AC-83, AC-84, AC-89 |

### 6.2 Diseño

- **Lectura con límite (RN-56).** Primero se compara el `Content-Length` de la request con el máximo más un margen para el multipart y se rechaza de entrada si lo supera. Después `UploadFile.read(max + 1)`: Starlette ya guardó el cuerpo en un archivo temporal (en disco si pasa de 1 MB), así que sólo entra en memoria hasta el máximo. El tope de tamaño de cuerpo del proxy inverso queda para el despliegue (K8).
- **Tipo (RN-55).** Firmas: JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, WebP `RIFF....WEBP`, PDF `%PDF-`.
- **Foto (D-11).** `procesar_foto` corre en `asyncio.to_thread`: fija `Image.MAX_IMAGE_PIXELS` (unos 25 MP, contra imágenes "bomba"), abre, aplica `ImageOps.exif_transpose` (para no perder la orientación al quitar el EXIF), convierte a RGB, reduce a 512 px por lado y guarda JPEG calidad 85 sin metadatos. Si Pillow no puede leerla, `422 IMAGEN_INVALIDA`.
- **Contenido aparte (D-10).** `ArchivoContenido.datos` es `deferred`: listar o validar metadatos no lee los bytes.
- **Descarga (RN-60, RN-61).** `puede_descargar(actor, archivo, propietario)` decide por propósito; si no puede, `404`. `respuesta_descarga` arma un `Response` con los encabezados de RN-61 y un `Content-Disposition` con el nombre saneado (RFC 5987 para acentos).
- **Cuota (RN-58).** Cuenta los no vinculados del propietario antes de insertar.
- **Foto y transacción.** `reemplazar_foto` bloquea al usuario, guarda el archivo nuevo ya vinculado, apunta `foto_id` y borra el anterior, todo en una transacción.

### 6.3 Migración

| `upgrade` | `downgrade` |
| --- | --- |
| `proposito_archivo_enum`; `archivos` (FK `propietario_id` `RESTRICT`, `CHECK` de tamaño con SQL directo para esquivar DT-26, índice `(vinculado_en, created_at)`, `sede` con el `sede_enum` existente sin recrearlo); `archivos_contenido` (FK `CASCADE`); `usuarios.foto_id` con su FK | Quita la FK y la columna `foto_id`, borra las tablas y el enum |

Verificación: `upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo, y `alembic heads` con una sola cabeza (AC-90).

---

## 7. Fase B3 — Renovación de sesión

### 7.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/settings.py` | Modificar | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` por defecto 30; `JWT_SESION_MAX_HORAS` (8) |
| `app/core/security.py` | Modificar | `crear_access_token(..., auth_time: int \| None = None)` (si falta, usa el `iat`); `TokenPayload` suma `auth_time` (si el token no lo trae, toma `iat`, RN-68) |
| `app/core/deps.py` | Modificar | Dependencia `get_sesion_actual` → `SesionActual(usuario, auth_time)`, con las mismas validaciones que `get_current_user_permitiendo_cambio` |
| `app/modules/users/service.py` | Modificar | `renovar_sesion` (RN-65…RN-67) y `cerrar_sesiones` (RN-69) |
| `app/modules/users/router.py` | Modificar | `POST /auth/renovar`, `POST /auth/me/sesiones/cerrar` |
| `tests/users/test_renovacion.py` | Crear | AC-91…AC-94, con tokens emitidos a mano con `auth_time` viejo o sin el claim |
| `.env.example`, `README.md` | Modificar | Valor nuevo por defecto y variable nueva |

Sin migración.

---

## 8. Frontend

| Fase | Archivo | Acción | Contenido |
| --- | --- | --- | --- |
| B1 | `src/features/auth/authApi.ts` | Modificar | `solicitarRecuperacion`, `confirmarRecuperacion` |
| B1 | `src/features/auth/recuperacion.ts` (+ test) | Crear | `leerTokenDeRecuperacion(hash)` y limpieza con `history.replaceState` |
| B1 | `src/features/auth/pages/RecoverPasswordPage.tsx`, `ResetPasswordPage.tsx` | Crear | Spec §5.5; reutilizan `AuthLayout` y la validación de RN-03 del registro |
| B1 | `src/features/auth/pages/LoginPage.tsx`, `src/App.tsx` | Modificar | Enlace "¿Olvidaste tu contraseña?"; `App.tsx` detecta `#/restablecer` al cargar y muestra la pantalla fuera del layout |
| B2 | `src/lib/api.ts` (+ test) | Modificar | `apiRequest` acepta `FormData` (sin `Content-Type` JSON) y `responseType: "blob"`; `descargarArchivo(id)` |
| B2 | `src/lib/useArchivoUrl.ts` | Crear | Hook que descarga con `Authorization`, crea la URL con `URL.createObjectURL` y la libera al desmontar |
| B2 | `src/features/auth/types.ts`, `src/features/users/types/*`, `usersApi.ts` | Modificar | `foto_id` en los DTOs; `subirFoto`, `quitarFoto`, `quitarFotoDeUsuario` |
| B2 | `src/features/users/pages/ProfilePage.tsx`, `UsersPage.tsx`, `src/components/layout/Navbar.tsx` | Modificar | Subir, ver y quitar la foto; avatar con iniciales de respaldo; "Quitar foto" en el detalle para administradores |
| B3 | `src/features/auth/renovacion.ts` (+ test) | Crear | `debeRenovar(exp, ultimaActividad, ahora)` y el registro de actividad (teclado, mouse, navegación) |
| B3 | `src/features/auth/AuthContext.tsx`, `authApi.ts` | Modificar | Temporizador que renueva con `aplicarToken` si `debeRenovar`; `cerrarTodasLasSesiones` |
| B3 | `ProfilePage.tsx` | Modificar | Botón "Cerrar todas mis sesiones" |

Verificación de cada PR: `npm run typecheck`, `npm run build`, `npm test` y recorrido manual contra el backend local (AC-95…AC-99).

---

## 9. Observaciones sobre el spec

- **EC-35** decía que "el *autoflush* de SQLAlchemy puede emitirlos antes de la consulta". No es así en este proyecto: `app/database.py` y los tests crean las sesiones con `autoflush=False`. **Corregido en el spec v1.1.0** con el texto que proponía este plan. El contrato no cambia (RN-42).
- **AC-67** pedía `FrozenInstanceError` al asignar cualquier atributo. Eso depende de la versión de Python (DT-30, §4.4). **Corregido en el spec v1.1.0**: el tipo de excepción sólo se exige al asignar un campo existente.

---

## 10. Documentación y coordinación al cerrar cada fase

| Cuándo | Qué |
| --- | --- |
| Al aprobar la v1.1.0 | `MEMORY.md`: un ADR con las decisiones de SPEC-03 (D-03, D-05, D-07, D-10…D-13, D-16…D-18 y D-20…D-22), que la v1.0.0 nunca registró; ítems K1…K11 en §5 (K6 cerrado por ADR-023); DT-30 en curso; snapshot de §1 |
| Fase A mergeada (pendiente desde el 2026-11-06) | Avisar a los Perfiles 3 y 4 (K1, K2); `docs/perfiles.md` §4 (lo que queda pendiente del Perfil 1) y §5 (interfaz "Datos públicos de usuarios" como publicada); `AGENTS.md` §3, fila del Perfil 1; en `MEMORY.md` §5, el pedido del Perfil 4 → "Atendido (PR #18)" |
| DT-30 mergeada | `MEMORY.md`: DT-30 cerrada; respuesta al pedido del Perfil 2 |
| B2 mergeada | `AGENTS.md` §3 y §2 y `docs/perfiles.md` con el módulo `files` (D-12, K9); avisar al Perfil 3 que ya puede quitar el rechazo de alta gama (K3) |
| B1 mergeada | README del backend (variables, Mailpit); avisar al Perfil 5 que `TipoCorreo.NOTIFICACION` está disponible para la Fase C de SPEC-06; PR al ERS de K7 (DT-29 + CU de USR-02) |
| B3 mergeada | Nota en ADR-015: sigue vigente, con renovación deslizante |

---

## 11. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| Dos cabezas de Alembic: `loans` (`0011`, `0012`) y este spec (`0014`, `0015`) se integran en paralelo | Nombres fijos (D-22); `down_revision` a la cabeza de `develop` al abrir el PR; `alembic heads` antes de mergear y, si otra migración entró mientras tanto, rebasar y reapuntar `down_revision` (EC-45) |
| Versiones de Python distintas en el equipo (3.12, 3.13 y 3.14) | Correr cada PR al menos en dos versiones; no depender de detalles de la biblioteca estándar que cambian entre versiones (DT-30); fijar una versión en el spec de despliegue (K8) |
| Conflictos en `App.tsx` con el PR #12 del Perfil 5 y con `loans` | Rebasar sobre `develop` antes de abrir los PRs de frontend de B1 y B2; los cambios de `App.tsx` de este spec son mínimos (detectar `#/restablecer`) |
| El ciclo de FK `usuarios.foto_id` ↔ `archivos.propietario_id` rompe `create_all` | `use_alter=True` en `foto_id`; un test de esquema lo cubre implícitamente al crear la base de tests |
| Pillow ante imágenes maliciosas | `MAX_IMAGE_PIXELS`, decodificación en un hilo, tamaño máximo de entrada y `422` ante cualquier error |
| Un SMTP lento demora el servidor | `to_thread` con `timeout=10`; el envío de USR-02 ocurre después de responder |
| El `BYTEA` crece más de lo previsto | Revisar al superar ~5 GB (D-10); el servicio aísla el almacenamiento |

---

## 12. Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.1.0 | 2026-11-10 | **Completado.** Los cuatro PRs de backend (más el #25 de DT-30) y los tres de frontend están en `develop`; la documentación de §10 quedó al día en el PR de cierre a `Docs-PrestaMeDios` |
| 1.1.0 | 2026-11-08 | **Aprobado** por el Perfil 1. Alineado con el spec v1.1.0. §1 verificado contra `develop` (`3ad6b6b`): `conftest.py`, `main.py` y la cadena de migraciones de SPEC-05 y SPEC-06, `loans` con alta gama bloqueada y las versiones de Python. §2: B2 antes que B1 (D-20) y la rama de DT-30. §4.4: estado de la Fase A y corrección de DT-30. §5: plantilla `NOTIFICACION` y su uso desde `notifications` (D-21). §5.3 y §6.3: nombres fijos de migración (D-22). §9: EC-35 y AC-67 corregidos en el spec. §10 y §11 al día |
| 1.0.0 | 2026-11-03 | Plan inicial (`BORRADOR`) |
