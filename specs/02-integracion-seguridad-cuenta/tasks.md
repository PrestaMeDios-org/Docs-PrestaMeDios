# TASKS-02 — Descomposición en tareas de SPEC-02

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/02-integracion-seguridad-cuenta/spec.md` (v1.0.1) |
| **Plan** | `specs/02-integracion-seguridad-cuenta/plan.md` |
| **Estado** | `COMPLETADO` — 2026-10-08 (18/18 tareas) |

`[ ]` pendiente · `[x]` hecha. Cada tarea deja el repo ejecutable y se verifica con el criterio indicado.

## Backend — `feat/spec-02-integracion`

- [x] **T-01 · Core:** `tzdata`; `ZONA_HORARIA_LAB`/`ahora_lab()`; `sede_para_alta()`; cambio obligatorio de contraseña en `get_current_user` + variante permisiva. *Verifica:* tests de SPEC-01 en verde.
- [x] **T-02 · Migración `0008` y modelos de cuenta:** `debe_cambiar_password`, `usuarios_historial_cambios`.
- [x] **T-03 · Perfil propio (UC-10, UC-11):** `PATCH /auth/me`, `POST /auth/me/password`. *Verifica:* AC-46, AC-47, EC-29, EC-30.
- [x] **T-04 · Cambio obligatorio (A9):** flag en alta por admin y reseteo. *Verifica:* AC-48, EC-33.
- [x] **T-05 · Edición administrativa (UC-12):** `PATCH /users/{id}`. *Verifica:* AC-49.
- [x] **T-06 · Migración `0007` + modelos de `spaces`:** `sede`, FK `id_usuario`. *Verifica:* AC-39 (con datos de la forma anterior).
- [x] **T-07 · Contratos de `spaces`:** esquemas nuevos; `availability.py` parametrizado por horario.
- [x] **T-08 · Servicio de `spaces`:** alcance, V1–V8, transiciones §3.4, bloqueos.
- [x] **T-09 · Router de `spaces` + tests:** *Verifica:* AC-31…AC-38, EC-23…EC-28; casos de `test_spaces_availability.py`/`test_spaces_schemas.py` migrados (NFR-13).
- [x] **T-10 · `inventory`:** auth, alcance, PRE-19, `AppError`, default desde `config`. *Verifica:* AC-40…AC-45.
- [x] **T-11 · Cierre backend:** suite completa, cobertura ≥ 85 % (NFR-11), ciclo de migraciones, prueba de humo, README.

## Frontend — `feat/login-auth-ui`

- [x] **T-12 · Base:** `vitest`, scripts; `lib/api.ts`; `AuthContext`, `SedeContext`, `roles.ts`; tests unitarios. *Verifica:* NFR-14, NFR-15.
- [x] **T-13 · Pantallas de acceso:** login, registro, cambio obligatorio. *Verifica:* AC-50…AC-53, AC-58.
- [x] **T-14 · Layout:** Navbar/Sidebar con usuario real, selector de sede, cerrar sesión; sin `icse` ni selector de rol. *Verifica:* AC-54.
- [x] **T-15 · Mi perfil, gestión de usuarios, parámetros.** *Verifica:* AC-55…AC-57.
- [x] **T-16 · Adaptación de `spaces` e `inventory`.** *Verifica:* AC-59.
- [x] **T-17 · Cierre frontend:** `typecheck`, `build`, `test`; README actualizado. *Verifica:* AC-60.

## Cierre

- [x] **T-18 · Documentación:** SPEC-02 → `IMPLEMENTADO`, `MEMORY.md`, commits en ambas ramas (sin merge hasta después de la demo).

## Resultado de la verificación (2026-10-08)

| Verificación | Resultado |
| --- | --- |
| Backend tests (`TEST_DATABASE_URL`) | **257 passed** (suite completa: core, users, config, spaces, inventory) |
| Backend cobertura | **96 %** (`spaces` 94 %, `inventory` 92 %, `users` 98 %, `config` 98 %) sobre meta ≥ 85 % |
| Migraciones | `0007` y `0008` creadas; ciclo completo `upgrade head` → `downgrade base` → `upgrade head` verificado; AC-39 probado contra datos reales de la forma anterior |
| Frontend typecheck / build | `tsc --noEmit` y `vite build` en verde, sin errores |
| Frontend tests unitarios | **14 passed** (Vitest: `api.test.ts`, `roles.test.ts`) |
| Frontend E2E real (Playwright) | **11 verificaciones OK** (AC-50…AC-59) cubriendo: login con mensajes por código, registro con validación en línea, persistencia tras recarga, navegación real sin selector de rol ni 'icse', aprobación desde 'Pendientes', alta y cambio de sede vista por Superadministrador, edición de parámetro con aviso ante `CONFLICTO_VERSION`, bloqueo de navegación por cambio obligatorio de contraseña, reservas como estudiante con reglas de anticipación/horario de config y sin selector de usuario, y cierre de sesión automático ante `401 TOKEN_REVOCADO` |
| Commits | Backend `de28749` en `origin/feat/spec-02-integracion`; Frontend `af81452` en `origin/feat/login-auth-ui` (publicados, listos para merge post-demo) |
