# TASKS-03 — API pública de `users`, recuperación, archivos y renovación de sesión

> **Spec:** `specs/03-users-api-publica-cuenta-archivos/spec.md` v1.1.0 (`APROBADO` 2026-11-08) · **Plan:** `specs/03-users-api-publica-cuenta-archivos/plan.md` v1.1.0 (`BORRADOR`) · **Estado:** `BORRADOR` · **Fecha:** 2026-11-08 (v1.0.0: 2026-11-03) · **Perfil:** 1
> Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo. Cada bloque es un PR (plan §2). **Orden de los bloques de la Fase B: B2 → B1 → B3 (D-20).**
> Comandos de backend desde `Backend-PrestaMeDios/` (venv activo, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Bloque 0 — Preparación

- [x] **T-00 · Línea base.** Actualizar `develop` en backend y frontend (`git fetch` + `git pull` en `develop`; hoy no tienen upstream configurado, se usa `origin/develop` explícito). Correr `pytest -q`, `npm run typecheck`, `npm run build` y `npm test`, y anotar el resultado: la suite completa no se corre desde el PR #16 de `loans`.
  *Verificación:* resultados anotados en el PR de la Fase A; si algo falla de entrada, se informa antes de seguir.
  *Estado 2026-11-06 (backend, `origin/develop` `b51b5ae`):* el primer intento falló por configuración local (`TEST_DATABASE_URL` con la plantilla en el puerto 5432; el PostgreSQL 18 local escucha en el 5433). Ya corregida la variable, la suite de backend de la rama de la Fase A (`develop` + 16 tests nuevos) dio **386 pasados**: los 370 de `develop` están en verde. El frontend no se corrió: la Fase A no lo toca.
- [x] **T-01 · Aprobar la v1.1.0.** El Perfil 1 aprueba el spec v1.1.0 (D-20…D-22, RN-77, AC-67 y EC-35 corregidos) y este plan; se registra en `MEMORY.md` lo de plan §10, fila "Al aprobar la v1.1.0".
  *Verificación:* spec en `APROBADO` con la fecha en §15. Sin esto no empieza ningún bloque de la Fase B (AGENTS.md §4).
  ✔ 2026-11-08: spec `APROBADO` (v1.1.0); en `MEMORY.md` quedan ADR-024, los ítems K de §13 y el estado de DT-30. El plan y las tareas siguen en `BORRADOR`, como en la v1.0.0, y se ajustan a medida que avanza cada bloque.
- [ ] **T-02 · Línea base de la Fase B.** Antes de abrir cada bloque: `develop` actualizado; `pytest -q` y `alembic heads` (una sola cabeza); en frontend, `npm run typecheck`, `npm run build` y `npm test`. Anotar el resultado en el PR del bloque.
  *Verificación:* sin fallos de entrada; si los hay, se informan antes de seguir.

## Bloque A — Datos públicos de usuarios (`feat/users-datos-publicos`)

- [x] **A-01 · Tests primero.** `tests/users/test_datos_publicos.py` con `pytestmark = pytest.mark.integracion`, fixture local de conteo de consultas y los casos AC-61…AC-70 (plan §4.3).
  *Verificación:* fallan por `ImportError` (la función no existe). ✔ 2026-11-06: 16 tests (AC-63 y AC-70 parametrizados por forma de entrada); falla la recolección por `ImportError`.
- [x] **A-02 · Función.** `DatosPublicosUsuario` y `datos_publicos_por_ids` en `users/service.py`, en la sección "API pública para otros módulos", según plan §4.2, con docstring que cite C2 de SPEC-05, RN-39 y RN-43.
  *Verificación:* `pytest tests/users/test_datos_publicos.py -q` en verde. *Cubre:* AC-61…AC-70.
  ✔ 2026-11-06: 16 pasados contra PostgreSQL 18. El SQL emitido es `WHERE usuarios.id = ANY ($1::INTEGER[])`: un solo parámetro aun con 40 000 ids, y sólo las columnas `id`, `nombre` y `apellido`.
- [x] **A-03 · Cierre.** `pytest -q` completo; cobertura de `app/modules/users` ≥ 85 %; una línea en el README del backend.
  *Verificación:* suite en verde; PR hacia `develop` con la trazabilidad RN-35…RN-43 → AC-61…AC-70 y la mención de la enmienda 1.1.1 (spec §2.3).
  ✔ 2026-11-06: `pytest -q` completo con 386 pasados; cobertura de `app/modules/users` 94 % (`service.py` 98 %, con la función nueva cubierta entera); README actualizado (párrafo "API pública de `users` para otros módulos"). Commit `9341c59`, **backend PR #18 mergeado en `develop`**.
- [ ] **A-04 · DT-30 (`fix/users-test-dataclass`).** Ajustar el test de AC-67 a la redacción de la v1.1.0 (plan §4.4): `FrozenInstanceError` al asignar `nombre`, cualquiera de `FrozenInstanceError`, `TypeError` o `AttributeError` al asignar `dni`, y sin `__dict__`. Sin cambios en `users/service.py`.
  *Verificación:* `pytest tests/users/test_datos_publicos.py -q` en verde en 3.14 y en 3.12 o 3.13 (con los Perfiles 2 o 5). PR hacia `develop` que cierre DT-30. *Cubre:* AC-67.
- [ ] **A-05 · Documentación de la Fase A.** Lo de plan §10, fila "Fase A mergeada": `docs/perfiles.md` §4 y §5, `AGENTS.md` §3 y `MEMORY.md` §5; avisar a los Perfiles 3 y 4 (K1, K2).
  *Verificación:* PR a `Docs-PrestaMeDios`; los avisos quedan registrados en `MEMORY.md` §5.

## Bloque B2 — Archivos y foto de perfil (`feat/files-almacenamiento`) — primero (D-20)

- [ ] **B2-01 · Dependencias y settings.** `python-multipart` y `Pillow` en `requirements.txt` (plan §3); variables `ARCHIVO_*`.
  *Verificación:* `pip install -r requirements-dev.txt` limpio en las versiones de Python del equipo; la app arranca.
- [ ] **B2-02 · Modelos y migración.** Módulo `files` (enums y modelos), `Usuario.foto_id` con `use_alter=True`, registro en `alembic/env.py`, migración `0014_files_init` con `down_revision` = la cabeza de `develop` (D-22).
  *Verificación:* la base de tests se crea con `create_all` (ciclo de FK resuelto); upgrade → downgrade → upgrade; `alembic heads` con una sola cabeza. *Cubre:* AC-90.
- [ ] **B2-03 · Servicio interno.** Lectura con límite, detección de tipo, `procesar_foto`, cuota y `limpiar_huerfanos`.
  *Verificación:* `tests/files/test_service.py` (firmas, tamaños en el borde, imagen corrupta, EXIF eliminado, cuota, limpieza idempotente). *Cubre:* AC-82, AC-87, AC-88 (parte de servicio).
- [ ] **B2-04 · API pública de `files`.** `vincular_archivo`, `abrir_archivo`, `respuesta_descarga` y `ArchivoContenido`, con docstrings que las declaren públicas (P3.3, enmienda 1.1.1).
  *Verificación:* `tests/files/test_api_publica.py`. *Cubre:* AC-86.
- [ ] **B2-05 · Router de `files`.** `POST /archivos` y `GET /archivos/{id}/contenido`, montado en `main.py` con el tag "Archivos".
  *Verificación:* `tests/files/test_archivos.py`, incluida la matriz de descarga con estudiante, docente, ambos tipos de administrador y `SUPERADMIN`. *Cubre:* AC-81, AC-82, AC-85.
- [ ] **B2-06 · Foto de perfil.** `reemplazar_foto`, `quitar_foto` y `quitar_foto_por_admin` en `users`; endpoints `PUT`/`DELETE /auth/me/foto` y `DELETE /users/{id}/foto`; `foto_id` en los esquemas de usuario.
  *Verificación:* `tests/users/test_foto.py`; los tests de esquemas de `users` actualizados por el campo nuevo. *Cubre:* AC-83, AC-84, AC-89.
- [ ] **B2-07 · CLI.** `python -m app.modules.files.cli limpiar-huerfanos`.
  *Verificación:* test del CLI como `tests/users/test_cli.py`. *Cubre:* AC-88.
- [ ] **B2-08 · Cierre del backend.** Suite completa, cobertura ≥ 85 % de `app/modules/files`, `/docs` revisado (multipart y encabezados de descarga), README. Avisar al Perfil 3 que ya puede quitar el rechazo de alta gama (K3).
  *Verificación:* suite en verde.
- [ ] **B2-09 · Frontend (`feat/users-foto`).** `api.ts` con `FormData` y `Blob` (+ test), `useArchivoUrl`, DTOs con `foto_id`, foto en `ProfilePage`, avatar en `Navbar` y "Quitar foto" en `UsersPage`.
  *Verificación:* typecheck, build, tests; recorrido manual; en la pestaña de red, ninguna URL lleva el token. *Cubre:* AC-97.

## Bloque B1 — Correo y recuperación de contraseña (`feat/users-recuperacion`) — segundo (D-20)

- [ ] **B1-01 · Settings.** Variables de correo y de recuperación en `core/settings.py` (spec §5.1 y §5.2), con valores por defecto seguros y sin secretos; `.env.example`. Si B2 ya está mergeada, rebasar sobre ella (comparten `settings.py`, `.env.example` y `conftest.py`).
  *Verificación:* la app arranca con el `.env` actual sin variables nuevas.
- [ ] **B1-02 · Transporte de correo.** `core/email.py` y las plantillas `RECUPERACION_PASSWORD.txt` y `NOTIFICACION.txt` (plan §5.1 y §5.2, RN-77); fixture `correos` y `EMAIL_BACKEND=memoria` en `conftest.py`.
  *Verificación:* `tests/core/test_email.py`: las dos plantillas se renderizan; `NOTIFICACION` arma el asunto con prefijo y el pie con `FRONTEND_URL`; una variable faltante falla sin enviar; un `enlace_app` del llamador se rechaza; llamada desde un servicio fuera de una request; un fallo del transporte simulado llega como `ErrorEnvioCorreo`; el log (con `caplog`) no tiene el contexto. *Cubre:* AC-100, AC-101.
- [ ] **B1-03 · Modelos y migración.** `TokenRecuperacion` e `IntentoRecuperacion`; `intentos_recuperacion` en `_TABLAS`; migración `0015_users_recuperacion` con `down_revision` = la cabeza de `develop` (D-22).
  *Verificación:* suite existente en verde; `alembic upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo; `alembic heads` con una sola cabeza; `tests/users/test_migracion_recuperacion.py`. *Cubre:* AC-80.
- [ ] **B1-04 · Esquemas.** `SolicitudRecuperacion`, `ConfirmacionRecuperacion` y `MensajeResponse`, con `_INPUT_CONFIG` y ejemplos.
  *Verificación:* `python -c "from app.main import app; app.openapi()"` sin errores.
- [ ] **B1-05 · Solicitud.** `solicitar_recuperacion` y `POST /auth/recuperacion` con respuesta neutra, límite por email y por IP y envío con `BackgroundTasks`.
  *Verificación:* `tests/users/test_recuperacion.py`. *Cubre:* AC-71, AC-72, AC-78, AC-79.
- [ ] **B1-06 · Confirmación.** `confirmar_recuperacion` y `POST /auth/recuperacion/confirmar` con el `UPDATE ... RETURNING` atómico y RN-52.
  *Verificación:* tests de éxito, tokens inválidos, contraseña débil y concurrencia (dos confirmaciones con `asyncio.gather`, una sesión por request, ADR-013). *Cubre:* AC-73, AC-74, AC-76, AC-77.
- [ ] **B1-07 · Invalidaciones.** Tokens anteriores al pedir uno nuevo, todos al restablecer y los pendientes al cambiar el email en `actualizar_perfil` y `editar_por_admin`.
  *Verificación:* tests; los de `test_perfil.py` y `test_edicion.py` siguen en verde. *Cubre:* AC-75.
- [ ] **B1-08 · Cierre del backend.** `pytest -q` completo; cobertura ≥ 85 % del código nuevo; `/docs` revisado (`202`, `422`, `429`); README con variables y Mailpit; prueba manual de un correo real contra Mailpit. Avisar al Perfil 5 que `TipoCorreo.NOTIFICACION` está disponible (Fase C de SPEC-06).
  *Verificación:* suite en verde y correo visible en Mailpit con el enlace correcto.
- [ ] **B1-09 · Frontend (`feat/auth-recuperacion`).** `authApi.ts`, `recuperacion.ts` (+ test), `RecoverPasswordPage`, `ResetPasswordPage`, enlace en `LoginPage` y detección del fragmento en `App.tsx` (plan §8). Rebasar sobre `develop` antes del PR: `App.tsx` lo tocan también otros perfiles.
  *Verificación:* `npm run typecheck`, `npm run build`, `npm test`; recorrido manual completo con el enlace de Mailpit. *Cubre:* AC-95, AC-96.

## Bloque B3 — Renovación de sesión (`feat/auth-renovacion`)

- [ ] **B3-01 · Token con `auth_time`.** `crear_access_token` y `TokenPayload` (plan §7.1); defecto de expiración en 30 min y `JWT_SESION_MAX_HORAS`.
  *Verificación:* la suite existente sigue en verde (el helper `auth()` no cambia).
- [ ] **B3-02 · Endpoints.** `get_sesion_actual`, `renovar_sesion`, `cerrar_sesiones`, `POST /auth/renovar` y `POST /auth/me/sesiones/cerrar`.
  *Verificación:* `tests/users/test_renovacion.py`. *Cubre:* AC-91…AC-94.
- [ ] **B3-03 · Frontend.** `renovacion.ts` (+ test de `debeRenovar`), temporizador en `AuthContext`, "Cerrar todas mis sesiones" en `ProfilePage`.
  *Verificación:* typecheck, build, tests; recorrido manual con `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=2` y `JWT_SESION_MAX_HORAS` bajo, con y sin actividad. *Cubre:* AC-98.

## Bloque C — Cierre

- [ ] **C-01 · Frontend completo.** `npm run typecheck`, `npm run build` y `npm test` sobre `develop` con las tres ramas de frontend mergeadas. *Cubre:* AC-99.
- [ ] **C-02 · Trazabilidad.** Matriz requisito → función o endpoint → test completa (spec §14), con cada test anotado `# AC-NN`.
- [ ] **C-03 · Documentación.** Lo indicado en plan §10 para cada fase; spec a `IMPLEMENTADO` con su historial.
