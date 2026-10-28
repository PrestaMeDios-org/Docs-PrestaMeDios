# PLAN-01 — Plan técnico de implementación de SPEC-01

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/01-auth-users/spec.md` (v1.0.0, `APROBADO`) |
| **Estado del plan** | `EJECUTADO` — 2026-10-07 |
| **Repositorio** | `Backend-PrestaMeDios` · rama `feat/users-core` (desde `develop`) |
| **Fecha** | 2026-10-07 |

> Este plan define **cómo** se implementa SPEC-01. No agrega comportamiento: si algo de aquí contradice al spec, prevalece el spec y se corrige este documento.

---

## 1. Estrategia

Implementación de adentro hacia afuera, en incrementos verificables:

1. **Kernel `app/core/`** (settings, enums, errores, seguridad) — sin dependencias de base de datos, testeable con tests unitarios.
2. **Persistencia**: modelos ORM de `users` y `config` + migración `0005`.
3. **Servicios** de dominio (reglas de negocio puras sobre la sesión).
4. **Dependencias de autorización** (`get_current_user`, `require_roles`, `resolver_alcance_sede`).
5. **Routers** y registro en `main.py`.
6. **CLI** de bootstrap del Superadministrador.
7. **Tests de integración** de todos los AC contra PostgreSQL.

Frontend (`feat/login-auth-ui`) queda fuera de este plan; se especificará por separado consumiendo los contratos ya aprobados.

---

## 2. Dependencias nuevas (`requirements.txt`)

| Paquete | Uso | Justificación |
| --- | --- | --- |
| `PyJWT>=2.8` | Emisión/validación de JWT | Mantenido; reemplaza a `python-jose` |
| `pwdlib[argon2]>=0.2` | Hash Argon2id con rehash | Mantenido; reemplaza a `passlib` |
| `email-validator>=2.1` | `EmailStr` de Pydantic | Requerido por Pydantic para validar emails |

**Dependencias de desarrollo** — nuevo `requirements-dev.txt` (no se instalan en producción):

| Paquete | Uso |
| --- | --- |
| `pytest>=8` | Runner (hoy se usa sin estar declarado) |
| `pytest-asyncio>=0.23` | Tests async |
| `httpx>=0.27` | `AsyncClient` + `ASGITransport` para tests de API |
| `pytest-cov>=5` | Cobertura (NFR-07) |

`pydantic-settings` ya está declarado y se empieza a usar.

---

## 3. Variables de entorno

Nuevo archivo versionado `.env.example` (sin valores reales):

| Variable | Obligatoria | Default | Descripción |
| --- | --- | --- | --- |
| `DATABASE_URL` | Sí | — | `postgresql+asyncpg://user:pass@host:5432/prestamedios` |
| `CORS_ORIGINS` | No | `http://localhost:8443` | Lista separada por comas |
| `JWT_SECRET_KEY` | **Sí** | — | ≥ 32 bytes aleatorios (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). La app no arranca sin ella |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Vida del access token |
| `TEST_DATABASE_URL` | Sólo tests | — | Base dedicada `prestamedios_test` |
| `BOOTSTRAP_SUPERADMIN_PASSWORD` | No | — | Alternativa al prompt del CLI (§11.1 del spec) |

`app/database.py` mantiene su lectura actual de `DATABASE_URL` para no romper a los demás módulos; `Settings` la expone tipada para el código nuevo.

---

## 4. Archivos

### 4.1 A crear

| Archivo | Contenido | Ref. spec |
| --- | --- | --- |
| `.env.example` | Variables del §3 | NFR-03 |
| `requirements-dev.txt` | Dependencias de test | NFR-07 |
| `app/core/__init__.py` | — | — |
| `app/core/settings.py` | `Settings(BaseSettings)` + `get_settings()` cacheado; valida longitud de `JWT_SECRET_KEY` | §6.2 |
| `app/core/enums.py` | `SedeEnum` (movido), `RolUsuario`, `EstadoCuenta`; helper `enum_values()` | §3.1, D-01 |
| `app/core/errors.py` | `AppError(status, code, detail, **extra)` + `app_error_handler` | §6.1, §6.15 |
| `app/core/security.py` | `hash_password`, `verify_password` (con hash ficticio), `needs_rehash`, `crear_access_token`, `decodificar_token` | §6.2, RN-03, RN-06 |
| `app/core/deps.py` | `bearer_scheme`, `get_current_user`, `require_roles(*roles)`, `resolver_alcance_sede(usuario, sede)` | §6.2, RN-10, §12.1 |
| `app/modules/users/__init__.py` | — | — |
| `app/modules/users/models.py` | `Usuario`, `UsuarioHistorialEstado` | §4.2, §4.3 |
| `app/modules/users/schemas.py` | `RegistroRequest`, `LoginRequest`, `TokenResponse`, `UsuarioPublico`, `UsuarioResumen`, `UsuarioDetalle`, `PaginaUsuarios`, `UsuarioAdminCreate`, `CambioEstadoRequest` | §6.4–6.11 |
| `app/modules/users/service.py` | `registrar`, `autenticar`, `listar_directorio`, `obtener_en_alcance`, `crear_por_admin`, `cambiar_estado`, `_registrar_historial`, tabla `TRANSICIONES` | §3.2, §5, §7 |
| `app/modules/users/router.py` | `auth_router` (`/auth/*`) y `users_router` (`/users/*`) | §6.3 |
| `app/modules/users/cli.py` | `python -m app.modules.users.cli crear-superadmin …` (argparse + `getpass`) | §11.1 |
| `app/modules/config/__init__.py` | — | — |
| `app/modules/config/models.py` | `ParametroGlobal`, `ParametroGlobalHistorial` | §4.4, §4.5 |
| `app/modules/config/schemas.py` | `ParametroResponse`, `ParametroUpdate`, `ParametroHistorialItem` | §6.12–6.14 |
| `app/modules/config/service.py` | `listar`, `obtener`, `actualizar` (lock + versión + validación), `validar_valor(tipo, valor, min, max)`, `validar_reglas_cruzadas`, **`obtener_parametro(db, clave)`** (API pública para otros módulos) | §7 RN-18…21, §12.1 |
| `app/modules/config/router.py` | `/config/parametros*` | §6.3 |
| `app/modules/config/seed.py` | Constante `PARAMETROS_SEMILLA` (fuente única para migración y tests) | §11.2 |
| `alembic/versions/0005_users_y_parametros.py` | DDL §4.6 + semilla §11.2; `downgrade` completo (sin borrar `sede_enum` si lo usa `inventory`) | §4.6, §11.2 |
| `tests/conftest.py` | Engine de test, creación de esquema, sesión transaccional con rollback por test, `AsyncClient`, fábricas de usuarios y tokens por rol | NFR-08 |
| `tests/core/test_security.py` | Hash, verificación, JWT (alg none, firma, iss, exp) | AC-19 |
| `tests/users/test_registro.py` | AC-01…06 | §8.1 |
| `tests/users/test_estado.py` | AC-07…14 | §8.2 |
| `tests/users/test_login.py` | AC-15…19 | §8.3 |
| `tests/users/test_directorio.py` | AC-20…24 | §8.4 |
| `tests/config/test_parametros.py` | AC-25…30 | §8.5 |
| `pytest.ini` | `asyncio_mode = auto`, `testpaths = tests` | — |

### 4.2 A modificar (dentro del alcance del Perfil 1)

| Archivo | Cambio | Ref. |
| --- | --- | --- |
| `requirements.txt` | Agregar `PyJWT`, `pwdlib[argon2]`, `email-validator` | §2 |
| `app/main.py` | Registrar `auth_router` (`/api/v1/auth`, tag "Autenticación"), `users_router` (`/api/v1/users`, "Usuarios"), `config_router` (`/api/v1/config`, "Configuración Global"); `add_exception_handler(AppError, …)`; título "PrestaMeDios API" (DT-11); esquema de seguridad en OpenAPI | §6.1 |
| `alembic/env.py` | Importar modelos de `users` y `config` | AGENTS §6 |
| `.gitignore` | Agregar `*.log`, `uvicorn.err` (DT-07; el `git rm --cached` se hace sólo con autorización) | Constitución §7 |

### 4.3 Cambio mínimo en módulo ajeno (requiere visto bueno del dueño de `inventory`)

| Archivo | Cambio | Motivo |
| --- | --- | --- |
| `app/modules/inventory/enums.py` | Reemplazar la definición de `SedeEnum` por `from app.core.enums import SedeEnum  # re-export` | D-01: una sola definición. Sin cambios de comportamiento ni de base de datos: mismos valores y mismo `name="sede_enum"` |

Si el dueño no lo aprueba antes de implementar, `app/core/enums.py` **importa** `SedeEnum` desde `inventory` en lugar de moverlo (alternativa sin tocar el módulo ajeno), y se registra como deuda.

### 4.4 Fuera de este plan (coordinación, §12.2 del spec)

`spaces` (sede, FK de usuario, anticipación mínima, horario configurable), protección de endpoints de `inventory`/`spaces` con `require_roles`, y frontend.

---

## 5. Diseño de detalle

### 5.1 Capas dentro del módulo

```text
router.py  →  valida contrato (Pydantic) y permisos (Depends)  →  service.py
service.py →  reglas de negocio, transacciones, historial       →  models.py (ORM)
errores    →  AppError(code) desde service; IntegrityError → 409 en el commit
```

Los routers no contienen lógica de negocio; los servicios no conocen HTTP salvo `AppError`.

### 5.2 Transacciones y concurrencia

| Operación | Mecanismo |
| --- | --- |
| Registro concurrente (EC-12) | `UNIQUE(email)`, `UNIQUE(dni)` → `IntegrityError` → inspección del nombre de la restricción (`uq_usuarios_email` / `uq_usuarios_dni`) → `409` con el `code` correcto |
| Cambio de estado (RN-13, AC-11) | `select(Usuario).where(...).with_for_update()` dentro de la transacción; la transición se evalúa **después** del lock |
| Último superadmin (RN-16) | En la misma transacción: `SELECT count(*) … WHERE rol='SUPERADMIN' AND estado='ACTIVO' FOR UPDATE` antes de desactivar uno |
| Parámetros (AC-27) | `with_for_update()` sobre la fila + comparación de `version` |
| Historial (RN-22) | Insert en la misma sesión antes del `commit` |

### 5.3 Login en tiempo constante (RN-06)

`security.py` precalcula al importar un `DUMMY_HASH = hash_password(secrets.token_urlsafe())`. Si el email no existe, se ejecuta `verify_password(password, DUMMY_HASH)` y se devuelve `401`.

### 5.4 Validación de valores de parámetros (RN-19)

```text
ENTERO   → type(v) is int                     (excluye bool)
DECIMAL  → type(v) in (int, float)            (excluye bool)
BOOLEANO → type(v) is bool
TEXTO    → isinstance(v, str) and 1 ≤ len ≤ 300
HORA     → str con regex ^([01]\d|2[0-3]):[0-5]\d$
```

`ParametroUpdate.valor` se declara `StrictInt | StrictFloat | StrictBool | StrictStr` para que Pydantic no convierta tipos; la validación por `tipo` se hace en el servicio porque depende de la fila.

Reglas cruzadas (RN-20) evaluadas con el valor candidato sustituido en el conjunto vigente:

- `horario.apertura` < `horario.cierre`
- `prestamo.general.max_dias` ≤ `prestamo.notebook.max_dias`
- `solicitud.anticipacion_min_horas` < 24 × `reserva_espacio.anticipacion_max_dias`

### 5.5 `obtener_parametro` (contrato para otros módulos)

```python
async def obtener_parametro(db: AsyncSession, clave: str) -> int | float | bool | str | time:
    """Devuelve el valor tipado de un parámetro global (GLO-03). HORA → datetime.time."""
```

Sin caché en v1 (1 lectura por PK; volumen bajo). Si la clave no existe lanza `AppError(500, "PARAMETRO_NO_CONFIGURADO")`, porque indica una migración faltante, no un error del cliente.

### 5.6 Enums en SQLAlchemy

`rol_usuario_enum`, `estado_cuenta_enum`, `parametro_tipo_enum`: `SAEnum(..., values_callable=enum_values, name=...)`. `sede_enum` en `users`: `SAEnum(SedeEnum, ..., name="sede_enum", create_type=False)` porque el tipo es compartido y lo crea la migración de forma idempotente.

### 5.7 Estrategia de tests

- Base `prestamedios_test` real (Constitución P9). En `conftest.py`: al iniciar la sesión de pytest, `CREATE EXTENSION btree_gist` + `Base.metadata.create_all`; por test, conexión con transacción externa y `rollback` al final (aislamiento sin recrear el esquema).
- Los parámetros semilla se insertan en un fixture con los mismos valores de la migración (una constante compartida `PARAMETROS_SEMILLA` en `config/seed.py` usada por la migración y por los tests, para evitar divergencia).
- AC-11 y AC-27 (concurrencia) usan **dos sesiones independientes** con `asyncio.gather`, fuera del rollback por test, con limpieza explícita.
- La migración `0005` se valida aparte con `alembic upgrade head && alembic downgrade 0004_bloqueos_created_at && alembic upgrade head` sobre una base vacía.
- Si no hay PostgreSQL de test disponible, los tests de integración se marcan `skip` con un mensaje explícito (nunca caen a SQLite).

---

## 6. Migración `0005_users_y_parametros`

| Paso `upgrade` | Detalle |
| --- | --- |
| 1 | Crear `rol_usuario_enum`, `estado_cuenta_enum`, `parametro_tipo_enum` |
| 2 | Crear `sede_enum` sólo si no existe (`DO $$ … EXCEPTION WHEN duplicate_object`) |
| 3 | Crear `usuarios` con restricciones e índices (§4.6) |
| 4 | Crear `usuarios_historial_estado` |
| 5 | Crear `parametros_globales` y `parametros_globales_historial` |
| 6 | Insertar los 8 parámetros semilla (§11.2) |

| Paso `downgrade` | Detalle |
| --- | --- |
| 1 | Drop de las 4 tablas en orden inverso |
| 2 | Drop de los 3 enums propios |
| 3 | Drop de `sede_enum` **sólo** si ninguna columna lo usa (consulta a `pg_attribute`/`pg_type`), para no romper `inventory` |

**No** se agrega en esta migración la FK `reservas_espacios.id_usuario → usuarios.id`: pertenece a `spaces` y fallaría con datos de prueba huérfanos. Queda como coordinación.

---

## 7. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Tablas de `inventory` no existen vía Alembic (DT-04); `sede_enum` podría no existir o existir | Fallo de migración | Creación idempotente del tipo (§6) |
| Python local 3.14 vs equipo con otra versión | Incompatibilidades de wheels (`argon2-cffi`, `asyncpg`) | Fijar mínimo 3.11 en README; verificar instalación en CI/local antes de mergear |
| Cambio de `SedeEnum` en `inventory` sin acuerdo | Conflicto con otro perfil | Plan B del §4.3 (importar en lugar de mover) |
| Activar auth en `inventory`/`spaces` rompe al frontend actual | Demo del 09/10 caída | **Este plan no protege endpoints ajenos**; se hace coordinado después de la entrega |
| Entrega parcial en 2 días | Alcance excesivo | Orden de tareas prioriza registro + login + aprobación (demo mínima) antes que directorio avanzado y parámetros |

---

## 8. Criterio de finalización del plan

- Todas las tareas de `specs/01-auth-users/tasks.md` en estado completado.
- `pytest -q` en verde, cobertura ≥ 85 % en `app/core`, `app/modules/users`, `app/modules/config`.
- `alembic upgrade head` / `downgrade` / `upgrade` sin errores sobre base vacía.
- Swagger (`/docs`) muestra los 11 endpoints con ejemplos, errores y candado de seguridad.
- `MEMORY.md` actualizado; SPEC-01 pasa a `IMPLEMENTADO`.
