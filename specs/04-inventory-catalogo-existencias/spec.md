# SPEC-04 — Catálogo y existencias (`inventory`)

> **Estado:** `IMPLEMENTADO` (Fase A, 2026-10-23, pendiente de revisión y PR; la Fase B sigue `APROBADA` y bloqueada por `loans`) · **Versión:** 1.0.1 · **Perfil:** 2 (Catálogo y existencias)
> **Requisitos:** PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 · **Deuda que cierra:** DT-22, DT-23 (y parte de DT-20)
> **Precedencia:** `docs/constitution.md` → `AGENTS.md` → `docs/perfiles.md` → este spec → `MEMORY.md`.
> **Numeración:** se usa 04 porque el Perfil 1 propone un SPEC-03 (USR-02, archivos, refresh token). Confirmar para no duplicar. `specs/` está vacía en este workspace, así que SPEC-01 y SPEC-02 no se pudieron consultar; sus reglas se tomaron de `MEMORY.md`, `AGENTS.md` y del código de `develop`.

---

## 1. Alcance

**Dentro** (módulo `inventory`, backend y frontend):

1. Conectar el catálogo del frontend a la API real y retirar `mockInventory.ts` (PRE-01, PRE-02, DT-22).
2. Vista de stock para administradores: tabla ordenable, filtrable por sede, con despliegue de unidades (PRE-12).
3. Gestión de estado de unidades: mantenimiento, fuera de servicio y rehabilitación (PRE-14).
4. Alta, edición y baja lógica de equipamiento y unidades, con sede automática (PRE-19, PRE-12).
5. `CHECK` de locker 1–7 en la base (DT-23).
6. Funciones de servicio públicas de `inventory` que consumirá `loans` (DT-20).

**Fuera** (otros perfiles; ver §10, ítems de coordinación):

- Disponibilidad por fechas y mini-calendario (parte de PRE-01) y el historial de usuarios por unidad (parte de PRE-12): necesitan datos de `loans`. Se especifica el contrato en §5.4 y §5.5, pero su implementación queda **diferida** hasta que `loans` exponga las funciones de lectura (Fase B).
- Cancelación forzada por mantenimiento (PRE-17), entrega y devolución (PRE-13): Perfil 3.
- Notificaciones al afectado: Perfil 5.
- Cualquier cambio en `core`, `users`, `config`, `loans`, `spaces`.

## 2. Actores y permisos

| Actor | Catálogo (lectura) | Stock y unidades | Altas, ediciones, estados |
| :---- | :---- | :---- | :---- |
| `ESTUDIANTE`, `DOCENTE` | Sí, sólo su sede | No | No |
| `ADMIN_LOCAL` | Sí, su sede | Sí, su sede | Sí, su sede |
| `SUPERADMIN` | Sí, ambas sedes o una elegida | Sí | Sí, sede obligatoria en altas |

Se reutiliza sin cambios: `get_current_user`, `require_roles(ADMIN_LOCAL, SUPERADMIN)`, `resolver_alcance_sede`, `sede_para_alta`, `puede_ver_sede`, `AppError`, `obtener_parametro`, `RolUsuario`, `SedeEnum`. No se definen roles, usuarios ni formatos de error propios. Un recurso de otra sede responde `404` (no `403`) para no filtrar su existencia (Constitución §4.2, P4.5).

## 3. Estado actual (verificado en `develop`)

| Elemento | Estado |
| :---- | :---- |
| `GET /categorias`, `POST /categorias` | Implementados |
| `GET /equipamiento` (filtros `sede`, `categoria`, `q`), `GET /equipamiento/{id}` | Implementados, con alcance de sede en la consulta SQL |
| `POST /equipamiento` (+ unidades), `POST /equipamiento/{id}/unidades` | Implementados, sede automática (PRE-19) |
| `GET /unidades`, `PATCH /unidades/{id}/estado` | Implementados (PRE-12, PRE-14) |
| Edición y baja de equipamiento o unidades | **No existen** |
| Frontend | `CatalogPage` usa `EQUIPMENT_INIT` y `CATEGORY_INIT` (mock); `inventoryApi.ts` no se usa |
| Tests | `tests/inventory/test_inventario.py` cubre AC-40…AC-45 de SPEC-02 (sesión, alcance de lectura, altas, plazo por defecto, errores homogéneos, estado de unidades). Los criterios INV-xx de este spec se agregan sin romper esos tests, salvo los cambios de contrato de D-02 y D-04, que se actualizan de forma explícita |

### Brechas detectadas

| ID | Brecha | Requisito / regla |
| :---- | :---- | :---- |
| G-1 | `EquipamientoResponse` devuelve `numero_serie`, `codigo_inventario` y todos los estados de unidad a **cualquier** rol, incluido estudiante | P4/P6 (mínimo dato necesario) |
| G-2 | `PATCH /unidades/{id}/estado` permite a un admin poner `prestado`, que es un estado derivado de `loans` (doble fuente de verdad, DT-20) | PRE-14, DT-20 |
| G-3 | Locker sólo con `CHECK locker >= 1` en la base; el tope 7 sólo está en Pydantic | P7.1, DT-23 |
| G-4 | `max_dias_prestamo` toma siempre `prestamo.general.max_dias`; los notebooks deberían tomar `prestamo.notebook.max_dias`. Además `CHECK max_dias_prestamo BETWEEN 1 AND 15` fija el tope 15 en código | P8, PRE-03/PRE-07 |
| G-5 | No hay forma de corregir un dato cargado mal ni de dar de baja un ítem del catálogo | PRE-12, P7.3 |
| G-6 | Sin mensaje de "sin resultados" ni manejo de carga y error en la UI | PRE-02 (flujo alternativo del CU) |

## 4. Reglas de negocio

- **RN-I1 (sede).** Toda lectura de unidades se filtra por sede en la consulta SQL (`resolver_alcance_sede`). Sólo `SUPERADMIN` puede elegir `sede`; pedir otra sede a un rol local responde `403 SEDE_FUERA_DE_ALCANCE`.
- **RN-I2 (alta, PRE-19).** `ADMIN_LOCAL`: sede automática, indicar otra responde `403 SEDE_FUERA_DE_ALCANCE`. `SUPERADMIN`: sede obligatoria (`422 SEDE_REQUERIDA`). La sede nunca se toma de otro lugar que `sede_para_alta`.
- **RN-I3 (estado, PRE-14).** El admin puede llevar una unidad a `disponible`, `mantenimiento` o `baja`. `prestado` lo gestiona sólo `loans` mediante las funciones de §6 (ver D-02). Una unidad en `baja` no vuelve a otro estado (D-03).
- **RN-I4 (stock lógico).** `cantidad_total` excluye `baja`; `cantidad_disponible` cuenta `disponible`; `en_mantenimiento` es verdadero si todas las unidades activas están en `mantenimiento`. Una unidad en `mantenimiento` o `baja` no se puede asignar a un préstamo (RN de `loans`, ver §6).
- **RN-I5 (baja lógica, P7.3).** Equipamiento y unidades no se borran físicamente. Un ítem dado de baja desaparece del catálogo de estudiantes y docentes y sigue visible para administradores (filtro `activo`). Un equipamiento sin unidades activas se muestra "No disponible".
- **RN-I6 (parámetros, P8).** El plazo por defecto sale de `obtener_parametro`: `prestamo.general.max_dias`, o `prestamo.notebook.max_dias` para la categoría de notebooks (D-05). No se codifican plazos.
- **RN-I7 (privacidad).** Las respuestas para `ESTUDIANTE` y `DOCENTE` no incluyen `numero_serie`, `codigo_inventario` ni el estado individual de cada unidad (D-04). El locker sí se muestra (ERS, CU de catálogo). Ninguna respuesta de este módulo expone identidad de solicitantes a esos roles.
- **RN-I8 (concurrencia, P7.2).** La unicidad de `codigo`, `numero_serie` y `codigo_inventario` se garantiza con `UNIQUE` y se traduce a `409 INVENTARIO_DUPLICADO`. Los cambios de estado sobre una misma unidad se serializan con `SELECT ... FOR UPDATE`.

## 5. Contratos (prefijo `/api/v1/inventory`, todos con sesión)

Errores en formato `{detail, code}` vía `AppError`; validación `422` estándar de FastAPI. Todos los payloads `*Create`/`*Update` usan `extra="forbid"` y `str_strip_whitespace`.

### 5.1 Lectura del catálogo (PRE-01, PRE-02)

| Método y ruta | Roles | Cambio |
| :---- | :---- | :---- |
| `GET /equipamiento` | Todos | Existente. Se agrega `incluir_inactivos: bool = false` (sólo admins; para otros roles se ignora). Respuesta según rol (RN-I7): `EquipamientoPublicoResponse` para estudiante y docente, `EquipamientoResponse` para admins |
| `GET /equipamiento/{id}` | Todos | Existente. Misma regla de respuesta por rol. `404 EQUIPAMIENTO_NO_ENCONTRADO` si no está en alcance |
| `GET /categorias` | Todos | Sin cambios |

`EquipamientoPublicoResponse`: datos del ítem (`id`, `codigo`, `nombre`, `marca`, `modelo`, `categoria_id`, `descripcion`, `max_dias_prestamo`, `alta_gama`, `imagen_url`, `video_url`, `reglas_cuidado`), `locker` (si todas las unidades activas de la sede lo comparten) y los campos calculados `cantidad_total`, `cantidad_disponible`, `en_mantenimiento`. Sin lista de unidades.

### 5.2 Stock (PRE-12) — sólo admins

| Método y ruta | Descripción |
| :---- | :---- |
| `GET /equipamiento` (respuesta de admin) | Alimenta la tabla: Nombre, Categoría, Locker, Tipo (`alta_gama` → Especial/Común) y unidades disponibles; las unidades se despliegan desde `unidades` |
| `GET /unidades` | Existente (`sede`, `estado`, `equipamiento_id`). Se agrega `locker` en el filtro opcional si hace falta en la UI |

El **ordenamiento** de columnas se hace en el cliente (el catálogo por sede es pequeño; YAGNI, P10). Si un ítem sin unidades en la sede visible existe, sólo los admins lo ven (comportamiento actual).

### 5.3 Alta, edición y baja (PRE-19, PRE-12)

| Método y ruta | Roles | Códigos | Descripción |
| :---- | :---- | :---- | :---- |
| `POST /equipamiento` | Admins | 201, 401, 403, 409, 422 | Existente. Plazo por defecto según RN-I6 |
| `POST /equipamiento/{id}/unidades` | Admins | 201, 401, 403, 404, 409 | Existente |
| `PATCH /equipamiento/{id}` | Admins | 200, 401, 403, 404, 409, 422 | **Nuevo.** Edita nombre, marca, modelo, categoría, descripción, `max_dias_prestamo`, `alta_gama`, URLs, `reglas_cuidado`. `codigo` es inmutable. Un `ADMIN_LOCAL` sólo edita ítems con al menos una unidad en su sede o sin unidades (el catálogo es global; ver D-06) |
| `PATCH /equipamiento/{id}/estado` | Admins | 200, 401, 403, 404 | **Nuevo.** Body `{activo: bool}`. Baja y reactivación lógica (RN-I5). Desactivar con unidades `prestado` responde `409 EQUIPAMIENTO_CON_PRESTAMOS` |
| `PATCH /unidades/{id}` | Admins | 200, 401, 403, 404, 409, 422 | **Nuevo.** Edita `numero_serie`, `codigo_inventario`, `locker` (1–7). La sede no se modifica (RN-I1) |
| `PATCH /unidades/{id}/estado` | Admins | 200, 401, 403, 404, 409, 422 | Existente. Aplica RN-I3, RN-I8. Transición inválida: `409 TRANSICION_ESTADO_INVALIDA` |

Matriz de transiciones del admin (`PATCH /unidades/{id}/estado`):

| Desde \ Hacia | `disponible` | `mantenimiento` | `baja` | `prestado` |
| :---- | :---- | :---- | :---- | :---- |
| `disponible` | — | Sí | Sí | No (`422`) |
| `mantenimiento` | Sí | — | Sí | No (`422`) |
| `prestado` | `409` | `409` | `409` | — |
| `baja` | `409` | `409` | — | No (`422`) |

Una unidad `prestado` sólo la libera `loans` (devolución, PRE-13). Pasar a `mantenimiento` una unidad con reservas futuras aprobadas no se bloquea en `inventory`: la respuesta incluye `reservas_afectadas: int` si `loans` ofrece la función de lectura (Fase B); la cancelación forzada es PRE-17 (Perfil 3).

### 5.4 Disponibilidad por fechas (PRE-01) — Fase B, diferida

`GET /equipamiento/{id}/disponibilidad?desde=<fecha>&hasta=<fecha>` → por día, `unidades_operativas` (no `mantenimiento`/`baja`), `unidades_ocupadas` y `disponible: bool`. Sin identidad de solicitantes. Rango máximo: parámetro de `config` a definir con Perfil 3 (D-07). Se construye sobre una función de lectura de ocupación por unidad y período que **expone `loans`**; hasta entonces, el catálogo muestra la disponibilidad actual (RN-I4) y el mini-calendario queda oculto.

### 5.5 Historial de usuarios por unidad (PRE-12) — Fase B, diferida

`GET /unidades/{id}/historial` → lista paginada de movimientos (usuario, fechas, estado), sólo admins con jurisdicción sobre la sede de la unidad; el resto responde `404`. Los datos los provee una función de lectura pública de `loans`; `inventory` no importa modelos de `loans`.

## 6. Interfaz de servicio hacia `loans` (DT-20) — propuesta

`app/modules/inventory/service.py` (nuevo, función pública declarada por este módulo, conforme a la enmienda 1.1.1 propuesta):

| Función | Uso por `loans` |
| :---- | :---- |
| `unidades_asignables(db, equipamiento_id, sede) -> list[int]` | Ids de unidades en `disponible` de esa sede, para asignar al aprobar |
| `unidad_es_asignable(db, unidad_id, sede) -> bool` | Validar antes de asignar (excluye `mantenimiento` y `baja`) |
| `marcar_unidad_prestada(db, unidad_id)` / `liberar_unidad(db, unidad_id)` | Entrega y devolución; cambian el estado con `FOR UPDATE` y levantan `AppError(409)` si la transición no es válida |
| `datos_equipamiento_por_ids(db, ids) -> dict[int, DatosEquipamiento]` *(addendum v1.1.0, C8 de SPEC-05, `BORRADOR`)* | Validar plazo por línea y alta gama al crear una orden, y mostrar nombre y código al administrador, sin importar los modelos de `inventory` |

Estas funciones no hacen `commit`: la transacción es de quien llama. **Hasta que Perfil 3 las adopte, nada de `loans` cambia.** Se registra como ítem de coordinación (§10).

### 6.1 Addendum v1.1.0 — `datos_equipamiento_por_ids` (C8 de SPEC-05) · `BORRADOR`

Pedido del Perfil 3 (SPEC-05 §16, C8). Es una función pública de lectura, en el estilo de `users.datos_publicos_por_ids`. Cumple P3.3 (enmienda 1.1.1): `loans` colabora a través de una función del módulo dueño y no importa `Equipamiento`.

- **Firma:** `datos_equipamiento_por_ids(db: AsyncSession, ids: Iterable[int]) -> dict[int, DatosEquipamiento]`.
- **`DatosEquipamiento`** (`dataclass(frozen=True, slots=True)`): `id`, `codigo`, `nombre`, `activo`, `es_notebook`, `alta_gama`, `max_dias_prestamo`.
- **RN-I9 (alcance).** El catálogo es global (`equipamientos` no tiene sede; las unidades sí), así que la función **no filtra por sede ni por estado** y no incluye `sede`. `activo` viaja en el resultado y decide quien llama (un ítem dado de baja no se puede pedir, RN-I5). La autorización es de quien llama.
- **RN-I10 (consulta).** Una sola consulta con los ids en un único parámetro arreglo; ids repetidos se consultan una vez; entrada vacía devuelve `{}` sin consultar la base; los ids inexistentes se omiten.
- **RN-I11 (mínimo dato, P6).** Selecciona sólo las columnas necesarias, no la entidad: no carga unidades, series ni códigos de inventario en la sesión de quien llama.
- **RN-I12 (transacción).** No hace `commit`, `rollback` ni `flush`.
- **Criterio INV-27:** devuelve los siete campos correctos; incluye ítems inactivos y sin unidades; no filtra por sede; omite inexistentes y repetidos; entrada vacía sin consulta; una sola `SELECT` por lote que no toca `unidades_fisicas`; no deja la entidad en la sesión; no hace `flush`; el resultado es inmutable.
- **Fuera de este addendum:** `marcar_unidad_mantenimiento` (C17), confirmar que `bloquear_unidad` es API pública (C14), el comportamiento de `max_dias_prestamo` al cambiar el parámetro (C18) y el frontend "Agregar al pedido" (C11) quedan como preguntas abiertas hasta que el usuario las decida.

## 7. Modelo de datos y migración `0010_inventory_gestion`

Reversible (`upgrade` + `downgrade`), registrada en `alembic/env.py` si hace falta.

| Cambio | Detalle |
| :---- | :---- |
| `equipamientos.activo` | `BOOLEAN NOT NULL DEFAULT true` (RN-I5) |
| `CHECK` locker | Reemplaza `ck_unidades_fisicas_locker_positivo` por `locker IS NULL OR locker BETWEEN 1 AND 7` (DT-23). Si hay filas fuera de rango, la migración **falla** con un mensaje que lista los ids; no corrige datos en silencio |
| `equipamientos.es_notebook` | `BOOLEAN NOT NULL DEFAULT false` (D-05). Si es `true` y `max_dias_prestamo` se omite en el alta, se toma `prestamo.notebook.max_dias`; si no, `prestamo.general.max_dias`. Se expone en `EquipamientoCreate`, `EquipamientoUpdate` y las respuestas |
| `CHECK` `max_dias_prestamo` | Sin cambio (tope 15 fijo, D-05); se avisa al Perfil 1 (§10) |

Sin tablas nuevas. El historial de cambios de estado de unidades no se persiste en esta etapa (D-08).

## 8. Frontend (`src/features/inventory/`)

- `CatalogPage` consume `listarEquipamiento` y `listarCategorias` (`inventoryApi.ts`) por medio de `lib/api.ts`; se eliminan `mockInventory.ts` y sus imports. Sede según `useSede()`/`useAuth()`: estudiante y docente sólo la propia; `SUPERADMIN` con selector.
- Estados de pantalla: cargando, error (`ApiError.detail`), **sin resultados** ("No hay recursos disponibles para el criterio seleccionado"), con `AbortSignal` ante cambios rápidos de filtro y búsqueda con *debounce*.
- Filtros de sede y texto enviados a la API (`sede`, `q`). La **categoría se filtra en la pantalla** (decisión del 2026-10-23): un solo pedido por sede y búsqueda alcanza para mostrar los contadores de todas las categorías. El parámetro `categoria` del backend (INV-04) sigue disponible para otros clientes.
- Tabla de stock para admins (PRE-12): columnas Nombre, Categoría, Locker, Tipo y Disponibles, con flechas de orden asc/desc; fila desplegable con las unidades y acciones de estado (PRE-14) con confirmación.
- Formulario de alta (PRE-19): el selector de sede **no se muestra** a `ADMIN_LOCAL` y es obligatorio para `SUPERADMIN`. Edición y baja lógica según §5.3.
- `types/index.ts` y `mappers.ts` se mantienen como espejo 1:1 de los esquemas; se agregan los DTOs nuevos. Los botones de "Agregar al carrito", pedidos y calendario de disponibilidad no se implementan acá (Perfil 3).

## 9. Criterios de aceptación

Prefijo `INV-` para no colisionar con AC-xx de SPEC-02. Cada uno tendrá al menos un test (`# INV-NN`), con `pytestmark = pytest.mark.integracion` y PostgreSQL real.

| ID | Criterio | Req. |
| :---- | :---- | :---- |
| INV-01 | Todo endpoint del módulo responde `401 NO_AUTENTICADO` sin token | P4.1 |
| INV-02 | Estudiante y docente listan sólo equipamiento con unidades de su sede; pedir otra sede → `403 SEDE_FUERA_DE_ALCANCE` | PRE-01, PRE-02 |
| INV-03 | `SUPERADMIN` sin `sede` ve ambas; con `sede` ve sólo esa | PRE-02 |
| INV-04 | Filtrar por `categoria` y por `q` (nombre, código, marca) devuelve sólo coincidencias; sin coincidencias → `200` y lista vacía | PRE-02 |
| INV-05 | Estudiante y docente reciben `EquipamientoPublicoResponse`: sin `numero_serie`, `codigo_inventario` ni `unidades` | RN-I7 |
| INV-06 | Un ítem desactivado no aparece para estudiante ni docente; los admins lo ven con `incluir_inactivos=true` | RN-I5 |
| INV-07 | `GET /equipamiento/{id}` de un ítem sin unidades en la sede del usuario → `404` | P5 |
| INV-08 | Los campos calculados respetan RN-I4 (con unidades en `baja` y en `mantenimiento`) | PRE-01 |
| INV-09 | `ADMIN_LOCAL` da de alta unidades con sede automática; indicar otra sede → `403` | PRE-19 |
| INV-10 | `SUPERADMIN` sin sede en el alta → `422 SEDE_REQUERIDA`; con sede, la unidad se crea allí | PRE-19 |
| INV-11 | Estudiante y docente reciben `403 PERMISO_INSUFICIENTE` en cualquier alta, edición o cambio de estado | PRE-19 |
| INV-12 | Código, serie o inventario duplicados → `409 INVENTARIO_DUPLICADO`; dos altas concurrentes con la misma serie: una `201` y otra `409` | RN-I8 |
| INV-13 | Plazo por defecto = `prestamo.general.max_dias` (y `prestamo.notebook.max_dias` si `es_notebook = true`, D-05); cambia al editar el parámetro | RN-I6 |
| INV-14 | Locker 0, 8 o negativo → `422`; insertar locker 8 directo en la base falla por `CHECK` | DT-23 |
| INV-15 | `PATCH /equipamiento/{id}` edita campos permitidos y rechaza `codigo`, `sede` u otros desconocidos (`422`) | PRE-12 |
| INV-16 | `PATCH /equipamiento/{id}/estado` desactiva y reactiva; con unidades `prestado` → `409 EQUIPAMIENTO_CON_PRESTAMOS` | RN-I5 |
| INV-17 | `PATCH /unidades/{id}` edita serie, inventario y locker; no cambia la sede | PRE-12 |
| INV-18 | Cambios válidos de estado según la matriz (§5.3); `disponible → mantenimiento` baja `cantidad_disponible` | PRE-14 |
| INV-19 | `prestado` enviado por un admin → `422`; salir de `prestado` o de `baja` → `409 TRANSICION_ESTADO_INVALIDA` | RN-I3 |
| INV-20 | Un `ADMIN_LOCAL` no puede ver ni modificar una unidad de la otra sede (`404`) | P5 |
| INV-21 | Dos cambios de estado concurrentes sobre la misma unidad se serializan; el resultado es consistente | RN-I8 |
| INV-22 | `unidades_asignables` y `unidad_es_asignable` excluyen `mantenimiento`, `baja` y unidades de otra sede | DT-20 |
| INV-23 | Migración `0010`: `upgrade`/`downgrade`/`upgrade` sin errores; con locker fuera de rango, falla con mensaje claro | P7.4 |
| INV-24 | Frontend: el catálogo se carga desde la API (sin mock), muestra el aviso de "sin resultados" y errores de la API; el orden de columnas funciona | PRE-02, PRE-12 |
| INV-25 | Frontend: el selector de sede en el alta no aparece para `ADMIN_LOCAL` y es obligatorio para `SUPERADMIN` | PRE-19 |
| INV-26 *(Fase B)* | Disponibilidad por fechas e historial por unidad según §5.4 y §5.5, sin identidad de otros usuarios para roles no admin | PRE-01, PRE-12 |

Verificación del frontend: `npm run build`, pruebas unitarias de mappers y filtros, y una verificación manual o E2E de INV-24 y INV-25.

## 10. Coordinación con otros perfiles (a registrar en `MEMORY.md` §5 al aprobar)

| Para | Pedido | Motivo |
| :---- | :---- | :---- |
| Perfil 3 (`loans`) | Usar las funciones de §6 en vez de escribir `estado` de la unidad; no asignar unidades en `mantenimiento` o `baja` | DT-20, PRE-14 |
| Perfil 3 (`loans`) | Exponer una función pública de lectura de ocupación por unidad y período, sin identidad | PRE-01 (§5.4) |
| Perfil 3 (`loans`) | Exponer una función pública del historial de movimientos de una unidad (para administradores) y una de reservas futuras aprobadas por unidad | PRE-12 (§5.5), PRE-17 |
| Perfil 3 (`loans`) | Resolver en el spec de `loans` la cancelación forzada (PRE-17) al pasar una unidad a mantenimiento | PRE-17 |
| Perfil 1 (`config`) | Si se aprueba D-07, sembrar el parámetro de ventana máxima del calendario de disponibilidad. Y evaluar quitar el `15` fijo del `CHECK` de `max_dias_prestamo` (D-05) | P8 |
| Perfil 5 | Los endpoints de catálogo y stock que use el asistente son los de §5.1 y §5.2; no hay endpoints especiales para IA | IA-02 |

## 11. Casos de borde

- Equipamiento con unidades en ambas sedes: el admin local ve sólo las de la suya; `cantidad_*` se calcula sobre lo visible.
- Equipamiento recién creado sin unidades: visible sólo para admins; para el resto no existe aún.
- Cambio de estado de una unidad inexistente o de otra sede: `404 UNIDAD_NO_ENCONTRADA`.
- Cambio de estado a su valor actual: `200` idempotente, sin error.
- Editar una unidad con serie o inventario que ya existen en otra: `409 INVENTARIO_DUPLICADO`.
- Categoría inexistente al crear o editar: `422 CATEGORIA_INEXISTENTE`.
- `q` con comodines (`%`, `_`): se escapan para que se busquen literalmente.

## 12. Decisiones abiertas (con recomendación)

| ID | Pregunta | Recomendación |
| :---- | :---- | :---- |
Todas resueltas el 2026-10-23 según la recomendación (columna "Resolución"). D-07 queda pendiente de Fase B.

| ID | Pregunta | Resolución |
| :---- | :---- | :---- |
| D-01 | ¿Numeración SPEC-04 o SPEC-03? | **04** (Perfil 1 reserva el 03) |
| D-02 | ¿El admin puede poner `prestado` a mano? | **No**; sólo `loans` vía §6. Cambia el comportamiento actual de `PATCH /unidades/{id}/estado` |
| D-03 | ¿`baja` es terminal? | **Sí**. Corregir un error se hace con edición; reactivar sería una alta nueva |
| D-04 | ¿Estudiantes y docentes ven números de serie y códigos de inventario? | **No**. Respuesta reducida (RN-I7) |
| D-05 | Plazo por defecto de notebooks y tope 15 del `CHECK` | Se usa `prestamo.notebook.max_dias` para ítems con `es_notebook = true` (campo nuevo, §7). Tope 15 se mantiene y se avisa al Perfil 1 |
| D-06 | `ADMIN_LOCAL` sobre ítems con unidades de la otra sede | Editar datos descriptivos: **sí**. Desactivar: sólo `SUPERADMIN` si hay unidades en ambas sedes (`403 PERMISO_INSUFICIENTE`) |
| D-07 | Ventana máxima del calendario de disponibilidad (Fase B) | Pendiente: se define con Perfil 3; parámetro de `config` |
| D-08 | ¿Historial de cambios de estado de unidades? | **No** ahora (YAGNI). El historial de PRE-12 es de usuarios, vía `loans` |
| D-09 | "Fuera de servicio" del ERS | `mantenimiento` = "En Mantenimiento" (temporal); `baja` = "Fuera de servicio" (definitivo). Dos botones distintos |
| D-10 | Entrega en dos fases | **Sí**: Fase A (conexión, stock, gestión, migración, servicio) y Fase B (disponibilidad e historial, tras `loans`) |

## 13. Trazabilidad

| Requisito | Endpoints (§5) | Criterios |
| :---- | :---- | :---- |
| PRE-01 | `GET /equipamiento`, `GET /equipamiento/{id}`, `GET /equipamiento/{id}/disponibilidad` (B) | INV-02, 05, 07, 08, 24, 26 |
| PRE-02 | `GET /equipamiento`, `GET /categorias` | INV-02, 03, 04, 24 |
| PRE-12 | `GET /equipamiento`, `GET /unidades`, `PATCH /equipamiento/{id}`, `PATCH /equipamiento/{id}/estado`, `PATCH /unidades/{id}`, `GET /unidades/{id}/historial` (B) | INV-06, 15, 16, 17, 20, 24, 26 |
| PRE-14 | `PATCH /unidades/{id}/estado` | INV-18, 19, 21, 22 |
| PRE-19 | `POST /equipamiento`, `POST /equipamiento/{id}/unidades` | INV-09, 10, 11, 12, 13, 25 |
| DT-22 / DT-23 / DT-20 | Frontend §8 / migración `0010` / §6 | INV-24 / INV-14, 23 / INV-22 |

## 14. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.1.0 | 2026-11-06 | **`BORRADOR`** (addendum §6.1, pendiente de aprobación): `datos_equipamiento_por_ids` a pedido del Perfil 3 (C8 de SPEC-05). El código se escribió antes de redactar el addendum, a pedido explícito del usuario; si el addendum no se aprueba, se descarta |
| 1.0.1 | 2026-10-23 | Fase A implementada. §8: la categoría se filtra en la pantalla, no en la API. Se agregan en el frontend el alta y edición de unidades desde la tabla de stock (cubre PRE-12 y PRE-19). Hallazgo en la migración `0010`: `NAMING_CONVENTION` duplica el prefijo de los `CHECK` en bases creadas con Alembic; la migración usa SQL directo y tolera ambos nombres |
| 1.0.0 | 2026-10-23 | Aprobado con todas las recomendaciones de §12. Se agrega `equipamientos.es_notebook` (D-05) y se corrige §3 (los tests existentes cubren AC-40…AC-45) |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
