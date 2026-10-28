# TASKS-01 — Descomposición en tareas de SPEC-01

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/01-auth-users/spec.md` (v1.0.0, `APROBADO`) |
| **Plan** | `specs/01-auth-users/plan.md` |
| **Estado** | `COMPLETADO` — 2026-10-07 (22/22 tareas) |
| **Repositorio / rama** | `Backend-PrestaMeDios` · `feat/users-core` |

**Convenciones**
- Cada tarea es pequeña (≤ ½ día), deja el repositorio en estado ejecutable y se verifica con el comando indicado.
- `[ ]` pendiente · `[~]` en curso · `[x]` hecha.
- **Hito DEMO** = mínimo necesario para la entrega parcial del 09/10 (registro → aprobación → login).
- Commit sugerido por tarea (Conventional Commits); los commits sólo se realizan con autorización explícita.

---

## Fase 0 — Preparación

- [x] **T-01 · Dependencias y entorno**
  - Agregar `PyJWT`, `pwdlib[argon2]`, `email-validator` a `requirements.txt`; crear `requirements-dev.txt`, `pytest.ini`, `.env.example`; agregar `*.log` y `uvicorn.err` a `.gitignore`.
  - **Verifica:** `pip install -r requirements.txt -r requirements-dev.txt` sin errores; `pytest -q` sigue pasando los tests existentes de `spaces`.
  - *Ref.:* Plan §2, §3 · NFR-03

- [x] **T-02 · Base de datos de test y `conftest.py`**
  - Fixtures: engine sobre `TEST_DATABASE_URL`, creación de esquema + `btree_gist`, sesión con rollback por test, `AsyncClient` con `ASGITransport`, override de `get_db`. Skip explícito si no hay PostgreSQL.
  - **Verifica:** un test trivial `GET /health` → 200 pasa usando el cliente async.
  - *Ref.:* Plan §5.7 · NFR-08

## Fase 1 — Kernel `app/core/`

- [x] **T-03 · `settings.py`**
  - `Settings` con `JWT_SECRET_KEY` obligatoria (≥ 32 caracteres), expiración, CORS, `DATABASE_URL`; `get_settings()` con `lru_cache`.
  - **Verifica:** test unitario — falta de secreto o secreto corto lanza error de validación.
  - *Ref.:* Spec §6.2 · NFR-03

- [x] **T-04 · `enums.py`**
  - `RolUsuario`, `EstadoCuenta`, `TipoParametro`, `SedeEnum` (según decisión del Plan §4.3: mover con re-export o importar), helper `enum_values`.
  - **Verifica:** `pytest tests/test_spaces_schemas.py` y arranque de la app sin errores; `from app.modules.inventory.enums import SedeEnum` sigue funcionando.
  - *Ref.:* Spec §3.1 · D-01

- [x] **T-05 · `errors.py`**
  - `AppError` y handler que responde `{"detail", "code", **extra}`; registrar en `main.py`.
  - **Verifica:** test con endpoint de prueba que lanza `AppError(409, "X")` → body con `detail` string y `code`.
  - *Ref.:* Spec §6.1, §6.15

- [x] **T-06 · `security.py`**
  - Hash/verify Argon2id, `needs_rehash`, `DUMMY_HASH`, `crear_access_token` (claims §6.2), `decodificar_token` (alg fijo, `iss`, `leeway=30`), mapeo a `TOKEN_INVALIDO` / `TOKEN_EXPIRADO`.
  - **Verifica:** `tests/core/test_security.py` — round-trip, firma alterada, `alg: none`, `iss` distinto, token expirado.
  - *Ref.:* Spec §6.2 · AC-19 · EC-15 · RN-06

## Fase 2 — Persistencia

- [x] **T-07 · Modelos `users`** (**DEMO**)
  - `Usuario`, `UsuarioHistorialEstado` con todos los `CheckConstraint`, índices y `sede_enum` con `create_type=False`.
  - **Verifica:** `create_all` en la base de test genera las restricciones; test que inserta `SUPERADMIN` con sede → `IntegrityError`.
  - *Ref.:* Spec §4.2, §4.3 · RN-02

- [x] **T-08 · Modelos y semilla `config`**
  - `ParametroGlobal`, `ParametroGlobalHistorial`; `config/seed.py` con `PARAMETROS_SEMILLA` (8 claves, incluida `solicitud.anticipacion_min_horas = 24`).
  - **Verifica:** test que inserta la semilla y valida el `CHECK` de formato de clave.
  - *Ref.:* Spec §4.4, §4.5, §11.2 · D-07

- [x] **T-09 · Migración `0005_users_y_parametros`** (**DEMO**)
  - DDL según Plan §6, `sede_enum` idempotente, semilla desde `PARAMETROS_SEMILLA`, `downgrade` seguro; registrar modelos en `alembic/env.py`.
  - **Verifica:** sobre base vacía `alembic upgrade head` → `alembic downgrade 0004_bloqueos_created_at` → `alembic upgrade head` sin errores; `SELECT count(*) FROM parametros_globales` = 8.
  - *Ref.:* Spec §4.6 · Constitución P7

## Fase 3 — Autenticación (USR-01, USR-05)

- [x] **T-10 · Esquemas `users`** (**DEMO**)
  - Todos los esquemas del Plan §4.1 con `_INPUT_CONFIG`, `examples`, normalización de email, política de contraseña (RN-03), regex de DNI/teléfono/nombre, coherencia rol–sede en `UsuarioAdminCreate` y motivo condicional en `CambioEstadoRequest`.
  - **Verifica:** tests unitarios de esquemas (AC-03, AC-04, AC-05 a nivel contrato).
  - *Ref.:* Spec §6.4–6.11

- [x] **T-11 · Servicio + endpoint de registro** (**DEMO**)
  - `service.registrar` (incluye re-registro de `RECHAZADO`, FA-03) y `POST /api/v1/auth/register`; mapeo de `IntegrityError` por nombre de restricción.
  - **Verifica:** `tests/users/test_registro.py` — AC-01…AC-06, EC-12, EC-22.
  - *Ref.:* UC-01 · D-02 · D-04

- [x] **T-12 · Servicio + endpoint de login** (**DEMO**)
  - `service.autenticar`: hash ficticio, verificación antes de revelar estado, reactivación de suspensión vencida, rehash, `ultimo_login_en`; `POST /api/v1/auth/login`.
  - **Verifica:** `tests/users/test_login.py` — AC-15…AC-18, EC-01…EC-03, EC-05, EC-06, EC-14.
  - *Ref.:* UC-03 · RN-06…RN-09 · D-08

- [x] **T-13 · `deps.py` + `GET /auth/me`** (**DEMO**)
  - `get_current_user` (pasos 1–5 de §6.2 con lectura de BD y `token_version`), `require_roles`, `resolver_alcance_sede`; endpoint `/auth/me`.
  - **Verifica:** AC-15 (parte `/me`), AC-19, EC-16; tests unitarios de `resolver_alcance_sede` para los 4 casos de RN-10.
  - *Ref.:* UC-04 · §12.1

## Fase 4 — Gestión de cuentas (USR-04, USR-05, GLO-01)

- [x] **T-14 · Cambio de estado** (**DEMO**: aprobar/rechazar)
  - Tabla `TRANSICIONES`, `service.cambiar_estado` con `FOR UPDATE`, jurisdicción (RN-11/RN-12), protecciones (RN-15/RN-16), `token_version`, historial; `PATCH /api/v1/users/{id}/estado`.
  - **Verifica:** `tests/users/test_estado.py` — AC-07…AC-13, EC-04, EC-13, EC-17.
  - *Ref.:* UC-02, UC-07 · §3.2

- [x] **T-15 · Directorio**
  - `service.listar_directorio` (alcance efectivo, filtros, `q` con escape de `%`/`_`, orden estable, paginación) y `obtener_en_alcance`; `GET /api/v1/users`, `GET /api/v1/users/{id}`.
  - **Verifica:** `tests/users/test_directorio.py` — AC-20…AC-24, EC-07…EC-10.
  - *Ref.:* UC-05 · RN-10 · D-09

- [x] **T-16 · Alta directa por Superadministrador**
  - `service.crear_por_admin` y `POST /api/v1/users`.
  - **Verifica:** AC-14.
  - *Ref.:* UC-06 · GLO-01

- [x] **T-17 · CLI de bootstrap** (**DEMO**)
  - `python -m app.modules.users.cli crear-superadmin …` idempotente, contraseña por `getpass` o `BOOTSTRAP_SUPERADMIN_PASSWORD`.
  - **Verifica:** ejecutar dos veces → la segunda informa que ya existe; test del servicio subyacente.
  - *Ref.:* Spec §11.1

## Fase 5 — Parámetros globales (GLO-03)

- [x] **T-18 · Servicio de parámetros**
  - `validar_valor` (RN-19), `validar_reglas_cruzadas` (RN-20, incluida la de anticipación), `actualizar` (lock, versión, idempotencia, historial), `obtener_parametro` público.
  - **Verifica:** tests unitarios de validación (EC-20, AC-28) y de `obtener_parametro` (HORA → `time`).
  - *Ref.:* UC-09 · RN-18…RN-21 · D-07

- [x] **T-19 · Endpoints de parámetros**
  - `GET /config/parametros`, `GET /config/parametros/{clave}`, `PUT /config/parametros/{clave}` (sólo `SUPERADMIN`), `GET /config/parametros/{clave}/historial`.
  - **Verifica:** `tests/config/test_parametros.py` — AC-25…AC-30, EC-19.
  - *Ref.:* UC-08, UC-09 · D-05

## Fase 6 — Integración y cierre

- [x] **T-20 · Registro en `main.py` y OpenAPI**
  - Montar routers con prefijos y tags; título "PrestaMeDios API"; respuestas de error declaradas (`responses=`) en cada endpoint; esquema `HTTPBearer`.
  - **Verifica:** `uvicorn app.main:app` arranca; `/docs` lista los 11 endpoints con candado donde corresponde; los endpoints de `inventory`/`spaces` siguen respondiendo igual (sin auth).
  - *Ref.:* NFR-09

- [x] **T-21 · Prueba de humo end-to-end** (**DEMO**)
  - Script manual documentado: bootstrap superadmin → login → crear `ADMIN_LOCAL` Ushuaia → registrar estudiante Ushuaia → login estudiante (403 pendiente) → aprobar con admin local → login estudiante (200) → suspender → request con token viejo (401 revocado).
  - **Verifica:** todas las respuestas coinciden con el spec.

- [x] **T-22 · Cobertura, trazabilidad y documentación**
  - `pytest --cov=app/core --cov=app/modules/users --cov=app/modules/config` ≥ 85 %; verificar que cada AC-01…AC-30 tiene test (comentario `# AC-NN` en cada test); actualizar `MEMORY.md` (estado, deuda) y pasar SPEC-01 a `IMPLEMENTADO`.
  - **Verifica:** reporte de cobertura; checklist de la Definición de Hecho (Constitución §9).

---

## Resultado de la verificación (2026-10-07)

| Verificación | Resultado |
| --- | --- |
| `pytest -q` (con `TEST_DATABASE_URL`) | **157 passed** (3 corridas consecutivas estables, incluye tests de concurrencia) |
| Cobertura `app/core` + `users` + `config` | **95 %** (meta ≥ 85 %). Sin cubrir: parseo de argumentos del CLI (verificado en la prueba de humo) |
| Trazabilidad | AC-01…AC-30: todos con al menos un test (comentario `# AC-NN`) |
| Migración `0005` | `upgrade head` → `downgrade 0004` → `upgrade head` OK; esquema migrado = modelos ORM (sin diferencias); `downgrade` conserva `sede_enum` si otra tabla lo usa |
| Prueba de humo (T-21) | Flujo bootstrap → alta admin local → registro → 403 pendiente → aprobación → login → suspensión → 401 `TOKEN_REVOCADO` → 403 `CUENTA_SUSPENDIDA`: todo según spec |
| Hallazgo (resuelto) | `GET /api/v1/inventory/*` respondía 500 sobre una base creada sólo con Alembic (DT-04, preexistente). Se agregó la migración `0006_inventory_init` (idempotente); los endpoints responden 200 y `alembic downgrade base` deja la base limpia |
| Commit | `7b95956` en `Backend-PrestaMeDios` · `feat/users-core` (sin push) |

## Orden y dependencias

```text
T-01 → T-02 → T-03 → T-04 → T-05 → T-06
                         └→ T-07 → T-08 → T-09
T-06 + T-09 → T-10 → T-11 → T-12 → T-13 → T-14 → T-15 → T-16 → T-17
T-09 + T-13 → T-18 → T-19
T-17 + T-19 → T-20 → T-21 → T-22
```

**Ruta mínima para la DEMO del 09/10:** T-01 → T-07 → T-09 → T-10 → T-11 → T-12 → T-13 → T-14 → T-17 → T-20 → T-21 (con T-02…T-06 como prerrequisitos técnicos).

## Coordinación (no son tareas de este backlog)

| Destino | Pedido | Ref. |
| --- | --- | --- |
| Dueño de `inventory` | Visto bueno para mover `SedeEnum` a `app/core/enums.py` (T-04) | Plan §4.3 |
| Dueño de `spaces` | Sede como `SedeEnum`, FK de usuario, usuario desde token, horario y anticipación mínima desde `config` | Spec §12.2 · ADR-011 |
| Frontend | Login/registro, `AuthContext`, header `Authorization`, roles espejo sin `icse` | Spec §12.2 |
