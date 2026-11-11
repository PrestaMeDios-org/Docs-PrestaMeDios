# PLAN-09 — Plan técnico de implementación de SPEC-09

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/09-config-sedes-telefono/spec.md` (v1.0.0, `APROBADO` el 2026-11-11) |
| **Estado del plan** | `BORRADOR` — 2026-11-11, se aprueba con el merge de su PR en `Docs-PrestaMeDios` |
| **Perfil** | 1 |
| **Entrega** | Dos PRs de backend y dos de frontend: primero la Fase A y después la B (D-12) |

---

## 1. Punto de partida (`develop` al 2026-11-11: backend `e54ad16`, frontend `8cbc76a`)

| Elemento | Situación | Impacto en el plan |
| --- | --- | --- |
| Migraciones | Cabeza: `0015_users_recuperacion`. `0016_loans_aval` está en `feat/loans-aval` (Perfil 3), sin mergear; `0012` sigue reservada para `loans` | `0017_config_sedes` con `down_revision` igual a la cabeza de `develop` cuando se abra el PR (hoy `0015`; `0016` si `loans-aval` entra antes). Antes de mergear, `alembic heads` con una sola cabeza (D-22 de SPEC-03) |
| `config/seed.py` | `PARAMETROS_SEMILLA` (ocho claves, sin campo `editable`) es la fuente que copia `0005` y con la que `tests/conftest.py` siembra la base de tests (`ParametroGlobal(**p)`) | Tiene que reflejar el estado **después** de `0017`; si no, los tests corren con las globales editables y sin las claves por sede (§4.2) |
| `tests/config/test_semilla.py` | Compara la copia congelada de `0005` con `PARAMETROS_SEMILLA`, como tuplas de siete campos | Pasa a reconstruir lo esperado aplicando `0005` y después `0017` (§4.2) |
| `config/service.py` | `actualizar` bloquea con `FOR UPDATE` sólo la fila editada; `validar_reglas_cruzadas` lee la otra clave del par sin bloquear (G-5). `TEXTO` exige de 1 a 300 caracteres | Cambia el bloqueo (§4.3). El correo vacío ya lo rechaza `TEXTO` (RN-80) |
| `config/schemas.py` | `ParametroUpdate` con `str_strip_whitespace=True` | Los espacios del correo ya se recortan; falta pasarlo a minúsculas (RN-80) |
| `config/router.py` | `GET /parametros`, `GET /parametros/{clave}` (`get_current_user`), `PUT /parametros/{clave}` (`SUPERADMIN`), `GET /parametros/{clave}/historial` (administradores) | Se suma `GET /sedes`, sin conflicto de rutas |
| `requirements.txt` | `email-validator>=2.1` | Valida el correo sin dependencias nuevas (NFR-25) |
| `users/schemas.py` | `Telefono` (`^\+?[0-9 \-]{6,20}$`); `_DatosCuentaBase.telefono: Telefono \| None = None` (lo heredan `RegistroRequest` y `UsuarioAdminCreate`); `PerfilUpdate` y `UsuarioAdminUpdate` con `Telefono \| None` | §5.1 |
| `users/cli.py` | `--telefono` con `default=None`; `crear_superadmin` recibe un `UsuarioAdminCreate` | Con el teléfono obligatorio en el esquema, la CLI tiene que exigirlo en `argparse` (D-11) |
| Tests de `users` | `test_registro.py`, `test_directorio.py`, `test_estado.py` y `test_perfil.py` registran o dan de alta cuentas, algunas sin teléfono | Se ajustan sus datos en la primera tarea de la Fase B, antes de cambiar los esquemas (§5.3) |
| Tests de migraciones | Hay un archivo por migración (`tests/files/test_migracion_0014.py`, `tests/users/test_migracion_recuperacion.py`…) | `tests/config/test_migracion_0017.py` sigue el mismo patrón |
| Frontend | `features/config` (`ParametersPage.tsx`, `services/configApi.ts`, `types/index.ts`); `RegisterPage.tsx` y `UsersPage.tsx` con "Teléfono (opcional)"; `ProfilePage.tsx` permite vaciarlo; `MainLayout.tsx` en `components/layout`; Vitest disponible | §4.5 y §5.4 |

---

## 2. Ramas y orden de entrega

| Orden | Fase | Backend | Frontend | Depende de |
| --- | --- | --- | --- | --- |
| 1 | A | `feat/config-sedes` | `feat/config-sedes` | — |
| 2 | B | `feat/users-telefono` | `feat/users-telefono` | Nada funcional. Puede avanzar en paralelo con la A; se mergea después (D-12) |

Todas salen de `develop` actualizado y entran por PR hacia `develop`. El PR de frontend de cada fase se mergea después del de backend.

---

## 3. Dependencias nuevas

Ninguna (NFR-25).

---

## 4. Fase A — Configuración por sede

### 4.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `alembic/versions/0017_config_sedes.py` | Crear | Copia congelada de las seis claves y de las dos obsoletas; upgrade y downgrade de §4.2 |
| `app/modules/config/seed.py` | Modificar | Estado posterior a `0017` (§4.2) |
| `app/modules/config/service.py` | Modificar | `SEGMENTO_SEDE`, reglas cruzadas por sede, bloqueo de §4.3, validación del correo, `DatosSede`, `datos_de_sede` y `datos_de_sedes` |
| `app/modules/config/schemas.py` | Modificar | `DatosSedeResponse` |
| `app/modules/config/router.py` | Modificar | `GET /sedes` |
| `tests/config/test_semilla.py` | Modificar | Lo esperado se reconstruye desde `0005` y `0017` |
| `tests/config/test_sedes.py` | Crear | AC-104…AC-111 |
| `tests/config/test_migracion_0017.py` | Crear | AC-102, AC-103 (parte de la migración) y AC-112 |
| `README.md` del backend | Modificar | Una línea sobre `GET /config/sedes` y `datos_de_sede` |

### 4.2 Migración y semilla

**`0017_config_sedes.py`**, con SQL con parámetros y sin importar código de la aplicación (como `0005`):

- Constantes congeladas: `CLAVES_NUEVAS` (las seis de spec §4.1, como tuplas `(clave, tipo, valor, descripcion, unidad, valor_min, valor_max)`), `CLAVES_OBSOLETAS = ("horario.apertura", "horario.cierre")` y `PREFIJO_OBSOLETA = "Obsoleta (SPEC-09): usar el horario de cada sede. "`.
- **Upgrade:**
  1. Lee `valor` de `horario.apertura` y `horario.cierre`.
  2. Inserta las seis claves con versión 1. Las cuatro de horario toman el valor leído y las de correo, `""` (D-03, D-05).
  3. Pone `editable = false` en las obsoletas y les antepone `PREFIJO_OBSOLETA` a la descripción. El resultado entra en los 300 caracteres de la columna.
- **Downgrade:**
  1. Borra las seis claves; su historial se borra por `ON DELETE CASCADE`.
  2. Devuelve las obsoletas a `editable = true` y les quita el prefijo (`substr` cuando la descripción empieza con él).

**`seed.py`**:

- `ParametroSemilla` suma `editable: NotRequired[bool]`. Si falta, vale `true`.
- `horario.apertura` y `horario.cierre` pasan a `editable: False`, con el prefijo en la descripción.
- Se agregan las seis claves nuevas con los valores de la semilla (`09:00`, `16:00` y `""`).
- El docstring aclara que la semilla refleja el estado después de la última migración que toca parámetros.

**`test_semilla.py`**: carga `0005` y `0017`. A la copia de `0005` le aplica `PREFIJO_OBSOLETA` y `editable = False` en las claves obsoletas, le suma `CLAVES_NUEVAS` y compara el resultado con `PARAMETROS_SEMILLA`, incluido `editable`. Ahí también va AC-109: cada `SedeEnum` tiene segmento y sus tres claves están en la semilla.

### 4.3 Servicio

- **`SEGMENTO_SEDE: dict[SedeEnum, str]`**, con `USHUAIA → "ushuaia"` y `RIO_GRANDE → "rio_grande"`. A partir de él, `clave_horario_apertura(sede)`, `clave_horario_cierre(sede)` y `clave_contacto(sede)` arman las claves (RN-78).
- **`_REGLAS_CRUZADAS`**: se suma un par por sede, generado desde `SEGMENTO_SEDE`, con el mismo mensaje que el par global.
- **Bloqueo (RN-79, G-5).** Una función `_claves_vinculadas(clave)` devuelve la clave y las de todos los pares de `_REGLAS_CRUZADAS` donde aparece. `actualizar` reemplaza su `select … with_for_update()` de una fila por una sola consulta:
  ```python
  select(ParametroGlobal)
      .where(ParametroGlobal.clave.in_(sorted(_claves_vinculadas(clave))))
      .order_by(ParametroGlobal.clave)
      .with_for_update()
      .execution_options(populate_existing=True)
  ```
  El parámetro editado sale de ese resultado. `validar_reglas_cruzadas` lee las mismas filas, ya bloqueadas en la transacción. Esto cubre también los tres pares globales.
- **Correo (RN-80).** Antes de `validar_valor`, cuando la clave cumple `^contacto\.[a-z_]+\.email$`:
  1. Pasa el valor a minúsculas.
  2. Lo valida con `email_validator.validate_email(valor, check_deliverability=False)` y exige un máximo de 254 caracteres. Si falla, responde `422 VALOR_PARAMETRO_INVALIDO`.
  3. Guarda el valor normalizado.
  La idempotencia de FA-05 se compara con el valor normalizado.
- **`DatosSede`, `datos_de_sede` y `datos_de_sedes`** (spec §4.4), en la sección "API pública para otros módulos":
  - Hacen una sola consulta `select(ParametroGlobal.clave, ParametroGlobal.tipo, ParametroGlobal.valor).where(clave.in_(…))`, sin `commit` ni `flush`.
  - `""` se devuelve como `None`.
  - Si falta una clave, responden `500 PARAMETRO_NO_CONFIGURADO` (RN-82).
  - `datos_de_sede` delega en una función común para no repetir la consulta.
  - El docstring cita GLO-02, GLO-03 y H1…H3.

### 4.4 Tests de la Fase A

- Con `pytestmark = pytest.mark.integracion` y cada test anotado con su `# AC-NN`.
- **AC-106 (concurrencia):**
  - Dos sesiones de `sessionmaker_` y dos tareas con `asyncio.gather`.
  - La primera bloquea el par y se demora en confirmar, con un `asyncio.Event` o un `pg_sleep` corto dentro de su transacción. Así la segunda queda esperando el bloqueo.
  - Se verifica: un `200`, un `422 PARAMETROS_INCONSISTENTES`, ningún error de *deadlock* (`40P01`) y el par final válido.
  - Se repite con el orden de las tareas invertido.
- **AC-108:** las consultas se cuentan con `before_cursor_execute`, como en `test_datos_publicos.py`.
- **AC-112:** sigue el patrón de `test_migracion_0014.py` (upgrade → downgrade → upgrade sobre una base aparte).

### 4.5 Frontend (`feat/config-sedes`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `src/features/config/types/index.ts` | Modificar | `DatosSedeDTO` (espejo `snake_case` de `DatosSedeResponse`) y su *view model* |
| `src/features/config/services/configApi.ts` | Modificar | `obtenerDatosSedes()` → `GET /api/v1/config/sedes` |
| `src/features/config/pages/ParametersPage.tsx` | Modificar | Las claves `contacto.*.email` se editan en un campo `type="email"` con validación en línea; con `""` se muestra "Sin configurar". Las claves por sede se agrupan por sede si la lista queda ilegible; si no, se dejan en orden de clave |
| `src/features/config/services/configApi.test.ts` | Crear | Mapeo de `obtenerDatosSedes()` (AC-122) |

---

## 5. Fase B — Teléfono obligatorio

### 5.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/modules/users/schemas.py` | Modificar | `_DatosCuentaBase.telefono: Telefono` (obligatorio). En `PerfilUpdate` y `UsuarioAdminUpdate`, si `telefono` está en `model_fields_set` y vale `None` → `ValueError("El teléfono no puede quedar vacío.")`, igual que hoy con el email |
| `app/modules/users/cli.py` | Modificar | `crear.add_argument("--telefono", required=True)` |
| `tests/users/test_telefono.py` | Crear | AC-113…AC-119 |
| Tests de `users` que crean cuentas | Modificar | Sumar un teléfono válido a los cuerpos de registro y de alta (§5.3) |
| `README.md` del backend y `AGENTS.md` §5 | Modificar | `crear-superadmin` con `--telefono` |

### 5.2 Re-registro y cuentas viejas

- El re-registro de una cuenta `RECHAZADO` ya usa `RegistroRequest`, así que exige el teléfono sin más cambios. AC-114 verifica que reemplaza al anterior.
- AC-118 crea la cuenta sin teléfono con `crear_usuario` (fixture), que escribe directo en la base, y recorre login, `GET /auth/me`, cambio de email, aprobación y suspensión.

### 5.3 Ajuste de los tests existentes

Primera tarea de la fase, antes de cambiar los esquemas:

1. Buscar los cuerpos de `POST /api/v1/auth/register` y `POST /api/v1/users` en `tests/`.
2. Sumarles un teléfono válido, o centralizarlos en un helper si se repiten.
3. La suite tiene que seguir en verde con los esquemas todavía sin cambiar.

### 5.4 Frontend (`feat/users-telefono`)

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `src/features/auth/pages/RegisterPage.tsx` | Modificar | "Teléfono" obligatorio, con la validación en línea actual |
| `src/features/users/pages/UsersPage.tsx` | Modificar | Lo mismo en el alta; en la edición no se puede guardar vacío |
| `src/features/users/pages/ProfilePage.tsx` | Modificar | No se puede guardar vacío |
| `src/components/layout/MainLayout.tsx` | Modificar | Si `usuario.telefono === null`, aviso no bloqueante "Completá tu teléfono en Mi perfil" con enlace; desaparece al guardarlo, porque Mi perfil ya llama a `setUsuario` de `AuthContext` después de `actualizarMe` |
| Test de Vitest | Crear | Validación del teléfono vacío y condición del aviso (AC-121, AC-122) |

---

## 6. Verificación por PR

| PR | Comandos | Además |
| --- | --- | --- |
| Backend A | `pytest -q`, `pytest --cov=app/modules/config` (≥ 85 % de lo nuevo, NFR-23), `alembic upgrade head` → `downgrade -1` → `upgrade head`, `alembic heads` | Trazabilidad de spec §12 en la descripción del PR |
| Backend B | `pytest -q`, `pytest --cov=app/modules/users` | `crear-superadmin` probado sin y con `--telefono` |
| Frontend A y B | `npm run typecheck`, `npm run build`, `npm test` | Recorrido manual: panel con las claves por sede; registro, alta, Mi perfil y aviso |

---

## 7. Documentación y coordinación

| Momento | Qué | Dónde |
| --- | --- | --- |
| Al aprobar el spec | ADR de SPEC-09 (D-01…D-12); DT nuevas: borrar `horario.apertura` y `horario.cierre` cuando nadie las lea (RN-81) y pasar `usuarios.telefono` a `NOT NULL` cuando no queden nulos (RN-87); pedidos H1…H4 en §5; preguntas de spec §10.1 en §6 | `MEMORY.md`, después del merge del Docs PR #29 para no repetir el conflicto de §1 |
| Fase A mergeada | Avisar a los Perfiles 3, 4 y 5 que `datos_de_sede` y `GET /config/sedes` están en `develop` (H1…H3). Publicar la interfaz | `MEMORY.md` §5, `docs/perfiles.md` §5, `AGENTS.md` §3 |
| Fase B mergeada | Estado de USR-05 | `MEMORY.md` §1, `AGENTS.md` §3 |
| Cuando H1…H3 estén en `develop` | Migración que borra las claves globales y cierra su DT | Spec o tarea nueva del Perfil 1 |

---

## 8. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| `0016_loans_aval` se mergea mientras está abierto el PR de la Fase A y quedan dos cabezas | Rebase sobre `develop` y ajuste de `down_revision` antes de mergear; `alembic heads` en la verificación |
| Hasta que los otros perfiles cambien la lectura, editar el horario de una sede no tiene efecto (EC-51), y Ushuaia ya anunció que va a extender el suyo | La descripción de las claves nuevas lo aclara en el panel. Los avisos de §7 salen el mismo día del merge, con el pedido de priorizar H1 y H2 |
| El cambio de bloqueo de `actualizar` afecta a los pares globales existentes | `tests/config/test_parametros.py` completo en verde y AC-106 también sobre un par global |
| Tests de otros módulos que crean cuentas por la API sin teléfono | La tarea de §5.3 recorre todo `tests/` y no sólo `tests/users/` |

---

## 9. Historial

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 0.1.0 | 2026-11-11 | Perfil 1 (con asistencia de IA) | Plan inicial sobre SPEC-09 v1.0.0 |
