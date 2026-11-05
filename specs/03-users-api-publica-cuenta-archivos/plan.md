# PLAN-03 — Plan técnico de implementación de SPEC-03

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/03-users-api-publica-cuenta-archivos/spec.md` (v1.0.0, `APROBADO` 2026-11-03) |
| **Estado del plan** | `BORRADOR` — 2026-11-03 |
| **Perfil** | 1 |
| **Entrega** | Cuatro PRs de backend y tres de frontend, en el orden de §2 (D-01) |

---

## 1. Punto de partida (`develop` al 2026-11-03)

| Elemento | Situación | Impacto en el plan |
| --- | --- | --- |
| `app/database.py` | `async_sessionmaker(..., autoflush=False)`, igual que el `sessionmaker_` de los tests | `datos_publicos_por_ids` no emite cambios pendientes del llamador. **EC-35 del spec dice lo contrario** (ver §9) |
| `tests/conftest.py` | `TRUNCATE` de una lista fija de tablas con `CASCADE`; base creada con `create_all`; `crear_usuario` agrega al usuario en la sesión `db` | Las tablas nuevas con FK a `usuarios` se vacían solas por el `CASCADE`; `intentos_recuperacion` (sin FK) hay que sumarla a `_TABLAS`. Los tests de la Fase A llaman a la función con **otra** sesión, porque `db` ya tiene a los usuarios en su *identity map* (AC-68) |
| `app/core/security.py` | `crear_access_token` y `TokenPayload(sub, tv)` sin `auth_time` | B3 agrega el claim con valor por defecto, sin romper el helper `auth()` de los tests |
| `app/main.py` | Registro explícito de routers | B2 monta `files` en `/api/v1/files` |
| `alembic/env.py` | Importa los modelos de cada módulo | B2 registra `app.modules.files.models` |
| Migraciones | Última: `0010_inventory_gestion`. SPEC-05 prevé `0011_loans_ciclo_entrega` | El número de las de B1 y B2 se fija al abrir cada PR (EC-45) |
| Frontend | Sin React Router (`App.tsx` decide la pantalla con estado); `src/lib/api.ts` con `apiRequest`, `tokenStore` en `sessionStorage` y `ApiError`; `AuthContext.tsx` con `login`, `logout`, `aplicarToken` | Las pantallas públicas de B1 se resuelven en `App.tsx` leyendo el fragmento; B2 extiende `apiRequest` para `FormData` y `Blob` |

---

## 2. Ramas y orden de entrega

| Orden | Fase | Backend | Frontend | Depende de |
| --- | --- | --- | --- | --- |
| 1 | A | `feat/users-datos-publicos` | — | — |
| 2 | B1 | `feat/users-recuperacion` | `feat/auth-recuperacion` | — |
| 3 | B2 | `feat/files-almacenamiento` | `feat/users-foto` | B1 mergeado (comparte `settings.py`, `conftest.py` y la numeración de migraciones) |
| 4 | B3 | `feat/auth-renovacion` | `feat/auth-renovacion` | — (puede ir en paralelo con B2: no comparte archivos salvo `settings.py` y `.env.example`) |

Todas salen de `develop` actualizado y entran por PR hacia `develop` con una revisión. La Fase A se puede mergear apenas esté, sin esperar al resto: desbloquea los ítems K1 y K2.

---

## 3. Dependencias nuevas

| Repo | Paquete | Fase | Justificación |
| --- | --- | --- | --- |
| Backend | `python-multipart>=0.0.9` | B2 | FastAPI la exige para `UploadFile` y formularios multipart |
| Backend | `Pillow>=10.4` | B2 | Volver a codificar la foto, quitar EXIF y neutralizar políglotas (D-11) |
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

---

## 5. Fase B1 — Correo y recuperación de contraseña

### 5.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/settings.py` | Modificar | `EMAIL_BACKEND`, `SMTP_*`, `EMAIL_FROM`, `FRONTEND_URL`, `RECUPERACION_*` (spec §5.1 y §5.2) |
| `app/core/email.py` | Crear | `TipoCorreo`, `CorreoRenderizado`, `ErrorEnvioCorreo`, `renderizar_correo`, `enviar_correo`, backends `smtp` y `memoria` (`bandeja_memoria()` y `vaciar_bandeja_memoria()` para tests) |
| `app/core/plantillas_correo/RECUPERACION_PASSWORD.txt` | Crear | Asunto en la primera línea; cuerpo con `$nombre`, `$enlace` y `$vigencia_minutos` |
| `app/modules/users/models.py` | Modificar | `TokenRecuperacion`, `IntentoRecuperacion` |
| `app/modules/users/schemas.py` | Modificar | `SolicitudRecuperacion {email}`, `ConfirmacionRecuperacion {token, password_nueva}` (reutiliza el validador de RN-03), `MensajeResponse {detail}` |
| `app/modules/users/service.py` | Modificar | `solicitar_recuperacion`, `confirmar_recuperacion`, `_invalidar_tokens_recuperacion`; `actualizar_perfil` y `editar_por_admin` invalidan los tokens si cambia el email (RN-53) |
| `app/modules/users/router.py` | Modificar | `POST /auth/recuperacion` (con `Request` y `BackgroundTasks`) y `POST /auth/recuperacion/confirmar` |
| `alembic/versions/00NN_users_recuperacion.py` | Crear | Las dos tablas e índices; `downgrade` las borra |
| `tests/conftest.py` | Modificar | `intentos_recuperacion` en `_TABLAS`; `EMAIL_BACKEND=memoria` para la sesión de tests; fixture `correos` que vacía y devuelve la bandeja |
| `tests/core/test_email.py` | Crear | AC-100, AC-101 |
| `tests/users/test_recuperacion.py` | Crear | AC-71…AC-79 |
| `tests/users/test_migracion_recuperacion.py` | Crear | AC-80 (como `test_spaces_migrations.py`) |
| `.env.example`, `README.md` | Modificar | Variables nuevas sin valores reales; cómo levantar Mailpit; el flujo de recuperación |

### 5.2 Diseño

- **Plantillas.** `renderizar_correo` lee `plantillas_correo/<tipo>.txt` con `importlib.resources` (funciona igual en Docker) y usa `Template.substitute`, que lanza `KeyError` si falta una variable; se traduce a `ValueError` con el nombre del tipo y de la variable, nunca con los valores (RN-71, RN-74). Las plantillas se cachean.
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

Verificación: `upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo.

---

## 6. Fase B2 — Archivos y foto de perfil

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
| `alembic/versions/00NN_files_init.py` | Crear | Enum, tablas, índice y FK `usuarios.foto_id` |
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

## 9. Observación sobre el spec aprobado

**EC-35** dice que "el *autoflush* de SQLAlchemy puede emitirlos antes de la consulta". No es así en este proyecto: `app/database.py` y los tests crean las sesiones con `autoflush=False`, de modo que los cambios sin `flush` del llamador **no** se emiten y la consulta no los ve. El contrato no cambia (la función sigue sin confirmar nada, RN-42). Se propone corregir el texto en una v1.0.1 documental: "Con `autoflush=False` (configuración del proyecto) los cambios sin `flush` no se emiten: la consulta no ve usuarios agregados y sin `flush` por el llamador, y la función no confirma nada (RN-42)". Requiere el visto bueno del Perfil 1 (AGENTS.md §4).

---

## 10. Documentación y coordinación al cerrar cada fase

| Cuándo | Qué |
| --- | --- |
| Al hacer el commit del spec (cuando lo pida el Perfil 1) | `MEMORY.md`: ADR con las decisiones de SPEC-03 (D-03, D-05, D-07, D-10…D-13, D-16…D-18), ítems K1…K10 en §5, snapshot de §1 |
| Fase A mergeada | Avisar a los Perfiles 3 y 4 (K1, K2); `docs/perfiles.md` §5, interfaz "Datos públicos de usuarios" como publicada |
| B1 mergeada | README del backend (variables, Mailpit); PR al ERS de K7 (DT-29 + CU de USR-02) |
| B2 mergeada | `AGENTS.md` §3 y §2 y `docs/perfiles.md` con el módulo `files` (D-12, K9); avisar al Perfil 3 (K3) |
| B3 mergeada | Nota en ADR-015: sigue vigente, con renovación deslizante |

---

## 11. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| Choque de numeración con la `0011` de `loans` | Fijar el número al abrir el PR y rebasar si `loans` mergea antes (EC-45) |
| El ciclo de FK `usuarios.foto_id` ↔ `archivos.propietario_id` rompe `create_all` | `use_alter=True` en `foto_id`; un test de esquema lo cubre implícitamente al crear la base de tests |
| Pillow ante imágenes maliciosas | `MAX_IMAGE_PIXELS`, decodificación en un hilo, tamaño máximo de entrada y `422` ante cualquier error |
| Un SMTP lento demora el servidor | `to_thread` con `timeout=10`; el envío de USR-02 ocurre después de responder |
| El `BYTEA` crece más de lo previsto | Revisar al superar ~5 GB (D-10); el servicio aísla el almacenamiento |
