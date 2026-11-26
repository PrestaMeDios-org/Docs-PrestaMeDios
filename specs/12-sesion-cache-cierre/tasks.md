# TASKS-12 — Sesión aislada por pestaña: API sin caché y cierre de sesión en el servidor

> **Spec:** `specs/12-sesion-cache-cierre/spec.md` v1.0.1 (`APROBADO` el 2026-11-24) · **Plan:** `specs/12-sesion-cache-cierre/plan.md` v1.0.1 · **Estado:** `EN CURSO` — Fase A implementada y verificada en local, en `fix/api-sin-cache` (backend y frontend), en revisión: backend PR #51 y frontend PR #35
> Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo. Cada bloque es un PR (plan §2). **Orden de merge: A antes que B (D-06).**
> Comandos de backend desde `Backend-PrestaMeDios/` (venv activo, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Bloque 0 — Preparación

- [ ] **T-00 · Documentación de la aprobación.** ADR-028, estado de SPEC-12 y H1…H2 en `MEMORY.md`; estado del Perfil 1 en `AGENTS.md` §3 (plan §7, fila "Al aprobar el spec").
  *Verificación:* PR a `Docs-PrestaMeDios` sin conflictos con `main`.
- [x] **T-01 · Línea base.** `develop` actualizado en backend y frontend; `pytest -q`, `alembic heads` (una sola cabeza); `npm run typecheck`, `npm run build` y `npm test`.
  *Verificación:* resultados anotados en el PR del bloque A; si algo falla de entrada, se informa antes de seguir.
  ✔ 2026-11-26: ramas `fix/api-sin-cache` desde `origin/develop` (backend `7893021`, frontend `53dca15`). Backend: 1026 pasados en 11:42. Frontend: typecheck limpio, 532 tests (72 archivos).

## Bloque A — API sin caché (backend `fix/api-sin-cache`)

- [x] **A-01 · Tests primero.** `tests/core/test_cache.py` con AC-123…AC-125, anotados con `# AC-NN`.
  *Verificación:* AC-123 falla porque falta el encabezado; AC-124 y AC-125 ya pasan.
  ✔ 2026-11-26: 8 tests; sin el middleware, los 6 de AC-123 fallan (`KeyError: 'cache-control'`) y los de AC-124 y AC-125 pasan. AC-123 suma un caso que exige un solo encabezado.
- [x] **A-02 · Middleware.** `app/core/cache.py` (`SinCacheMiddleware`, ASGI puro) y su registro en `main.py` (plan §4.1).
  *Verificación:* AC-123…AC-125 en verde; `pytest -q` completo en verde. *Cubre:* RN-90.
  ✔ 2026-11-26: registrado después de CORS y antes de `ProxyHeadersMiddleware` (SPEC-11), que sigue siendo el más externo. Los 8 tests en verde. En el navegador, contra el backend local: el `GET /auth/me` del estudiante con `cache: "force-cache"`, después de uno del superadministrador, ahora devuelve `ESTUDIANTE` (antes, `SUPERADMIN`; spec §2.3).
- [ ] **A-03 · Cierre del backend A.** README ("Seguridad transversal"); PR hacia `develop` con la trazabilidad de spec §12.
  *Verificación:* `curl -i http://localhost:8000/api/v1/auth/me` con token → `cache-control: no-store`.
  ⏳ 2026-11-26: README actualizado; suite completa con el middleware: 1034 pasados (1026 + 8 nuevos) en 10:47. Desde el navegador, `/auth/me` responde `cache-control: no-store`. Backend PR #51 hacia `develop` (2026-11-26).

## Bloque A-F — API sin caché (frontend `fix/api-sin-cache`)

- [x] **AF-01 · Cliente sin caché.** `cache: "no-store"` en `apiRequest` y su test en `api.test.ts`.
  *Verificación:* `npm test` en verde. *Cubre:* RN-91, parte de AC-134.
  ✔ 2026-11-26 (`fix/api-sin-cache` desde `develop` `53dca15`): `cache: "no-store"` antes de `...rest`; el test verifica dos pedidos (con y sin token).
- [x] **AF-02 · Identidad del token.** `features/auth/sesion.ts` con `leerIdentidadToken` (decodificación compartida con `leerTiemposToken`, sin cambiar su contrato) y `sesion.test.ts`.
  *Verificación:* `npm test` en verde, incluidos los tests de `renovacion.test.ts`.
  ✔ 2026-11-26: `leerClaimsToken` (compartida), `leerIdentidadToken` y `esDuenoDelToken`; `renovacion.ts` usa `leerClaimsToken` y sus tests siguen en verde.
- [x] **AF-03 · Rehidratación verificada.** En `AuthContext.tsx`, descartar un `/auth/me` cuyo `id` no sea el `sub` del token, con el aviso de RN-92.
  *Verificación:* test de la comparación en `sesion.test.ts`; `npm run typecheck` y `npm run build`. *Cubre:* RN-92, AC-134.
  ✔ 2026-11-26: si el `id` no coincide, `logout` con el aviso de RN-92; si el token cambió mientras llegaba la respuesta, se ignora. Línea base: typecheck limpio y 532 tests; después: typecheck y build limpios, 541 tests (73 archivos).
- [ ] **AF-04 · Recorrido manual y PR.** Spec §2.3 en Chrome y Firefox con el backend de la Fase A: la copia muestra siempre al dueño de su token; en Network, `/auth/me` nunca sale de caché.
  *Verificación:* recorrido anotado en el PR. *Cubre:* AC-135.
  ⏳ 2026-11-26: verificado en el navegador integrado: la sesión válida de un estudiante se rehidrata bien (RN-92 no la descarta), sin errores en consola. Falta el recorrido con "Duplicar pestaña" en Chrome y Firefox, que el navegador integrado no permite.

## Bloque B — Cierre de sesión en el servidor (backend `feat/auth-logout`)

- [ ] **B-01 · Tests primero.** `tests/users/test_logout.py` con AC-126…AC-132 y `tests/users/test_migracion_0022.py` con AC-133.
  *Verificación:* fallan por lo que falta (`sid` ausente, `404` de `/auth/logout`, tabla inexistente), no por errores del test.
- [ ] **B-02 · Modelo y migración.** `SesionCerrada` en `users/models.py`; `0022_users_sesiones_cerradas.py` (plan §5.2).
  *Verificación:* AC-133 en verde; ciclo upgrade → downgrade → upgrade sobre la base de desarrollo; `alembic heads` con una sola cabeza.
- [ ] **B-03 · Claim `sid`.** `crear_access_token` y `TokenPayload` en `security.py`; `SesionActual.sid` en `deps.py`; `_emitir_token`, login, `cambiar_password`, `renovar_sesion` y `cerrar_sesiones` en `users/service.py`; tests de `tests/core/test_security.py` ajustados.
  *Verificación:* AC-126 y AC-127 en verde; los tests de renovación de SPEC-03 (AC-91…AC-94) siguen en verde. *Cubre:* RN-93.
- [ ] **B-04 · Endpoint y validación.** `cerrar_sesion` (plan §5.3), `POST /auth/logout` y el rechazo `401 TOKEN_SESION_CERRADA` en `_sesion_autenticada`.
  *Verificación:* AC-128…AC-132 en verde. *Cubre:* RN-94…RN-96, D-07, D-08.
- [ ] **B-05 · Cierre del backend B.** `pytest -q` completo; cobertura de lo nuevo ≥ 85 %; README (endpoint y código de error); PR hacia `develop`.
  *Verificación:* suite en verde; `alembic heads` con una sola cabeza después del rebase. *Cubre:* NFR-26, NFR-28.

## Bloque B-F — Cierre de sesión en el servidor (frontend `feat/auth-logout`)

- [ ] **BF-01 · Canal de sesión.** `crearCanalSesion` en `sesion.ts` con constructor inyectable, y sus tests.
  *Verificación:* `npm test` en verde. *Cubre:* RN-98.
- [ ] **BF-02 · Logout en el servidor.** `cerrarSesionEnServidor(token)` en `authApi.ts`; `logout` de `AuthContext.tsx` con el orden de RN-97 y la distinción de RN-99; escucha del canal; mensaje de `TOKEN_SESION_CERRADA`; botones de `App.tsx` y `ChangePasswordForm.tsx`.
  *Verificación:* tests de AC-137; `npm run typecheck` y `npm run build`. *Cubre:* RN-97…RN-99.
- [ ] **BF-03 · Recorrido manual y PR.** AC-136 en Chrome y Firefox: cerrar sesión en una copia lleva a la otra al login sin recargar; la sesión del mismo usuario en otro navegador sigue abierta; un pedido con el token viejo responde `401 TOKEN_SESION_CERRADA`.
  *Verificación:* recorrido anotado en el PR. *Cubre:* AC-136.

## Cierre

- [ ] **C-01 · Trazabilidad y estado.** Spec §12 con los archivos de test de cada fila, verificada contra `develop`; spec, plan y tareas en `IMPLEMENTADO`/`COMPLETADO`; `MEMORY.md` y `AGENTS.md` (plan §7).
  *Verificación:* cada AC de backend con al menos un test anotado `# AC-NN`.
