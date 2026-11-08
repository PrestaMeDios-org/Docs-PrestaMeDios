# SPEC-04 — Catálogo y existencias (`inventory`)

> **Estado:** Fase A `IMPLEMENTADO` (2026-10-23) · Fase B `APROBADO` (2026-11-07, OK del Perfil 1) · Fase C `BORRADOR` (bloqueada) · **Versión:** 1.2.0 · **Perfil:** 2 (Catálogo y existencias)
> **Requisitos:** PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 · **Deuda que cierra:** DT-22, DT-23 (y la parte de `inventory` de DT-20)
> **Precedencia:** `docs/constitution.md` → `AGENTS.md` → `docs/perfiles.md` → este spec → `MEMORY.md`.
> **Depende de:** SPEC-01 y SPEC-02 (`core`, `config`), SPEC-05 v1.0.0 (`loans.ocupacion_de_unidades`, en `develop` desde el backend PR \#21; `historial_de_unidad` y `reservas_futuras_de_unidad`, todavía sin publicar).
> **Numeración:** 04 (D-01). SPEC-03 es del Perfil 1 y SPEC-05 del Perfil 3.

---

## 1. Alcance

El trabajo se entrega en tres fases (D-10):

| Fase | Contenido | Requisitos | Estado |
| :---- | :---- | :---- | :---- |
| **A** | Catálogo conectado a la API, stock, estados de unidades, altas, ediciones y bajas lógicas, `CHECK` de locker, `service.py` para `loans` | PRE-01 (parcial), PRE-02, PRE-12 (parcial), PRE-14, PRE-19, DT-20, DT-22, DT-23 | Implementada (2026-10-23) |
| **B** | §6.1 (`datos_equipamiento_por_ids`, ya mergeado), §6.2 (C14, C17), RN-I13 (C18), aclaración de RN-I4 (C16), disponibilidad por fechas y mini-calendario en un detalle del equipo (§5.4), botón "Agregar al pedido" (C11) | PRE-01 completo, PRE-03 (lado del catálogo), PRE-14 | **`BORRADOR`**: todo depende sólo de funciones que ya están en `develop` |
| **C** | Historial de usuarios por unidad (§5.5) y `reservas_afectadas` al pasar una unidad a mantenimiento o baja (§5.3) | PRE-12 completo, PRE-17 (aviso) | **`BORRADOR`, bloqueada** hasta que `loans` publique `historial_de_unidad` y `reservas_futuras_de_unidad` (SPEC-05 §10.2, Fases 2–3) |

**Fuera** (otros perfiles; ver §10):

- Carrito, formulario de pedido y validaciones de la orden (PRE-03…PRE-10): Perfil 3. El catálogo sólo ofrece el botón y avisa con un *callback* (§8.2).
- Cancelación forzada (PRE-17), entrega y devolución (PRE-13): Perfil 3.
- Notificaciones al afectado: Perfil 5.
- Cualquier cambio en `core`, `users`, `config`, `loans`, `spaces` o en el layout del frontend (`App.tsx`, `Navbar.tsx`).

## 2. Actores y permisos

| Actor | Catálogo y disponibilidad (lectura) | Stock, unidades e historial | Altas, ediciones, estados |
| :---- | :---- | :---- | :---- |
| `ESTUDIANTE`, `DOCENTE` | Sí, sólo su sede | No | No |
| `ADMIN_LOCAL` | Sí, su sede | Sí, su sede | Sí, su sede |
| `SUPERADMIN` | Sí, ambas sedes o una elegida (la disponibilidad exige una) | Sí | Sí, sede obligatoria en altas |

Se reutiliza sin cambios: `get_current_user`, `require_roles(ADMIN_LOCAL, SUPERADMIN)`, `resolver_alcance_sede`, `sede_para_alta`, `puede_ver_sede`, `AppError`, `obtener_parametro`, `ahora_lab`, `ZONA_HORARIA_LAB`, `RolUsuario`, `SedeEnum`. No se definen roles, usuarios ni formatos de error propios. Un recurso de otra sede responde `404` (no `403`) para no filtrar su existencia (Constitución §4.2, P4.5).

## 3. Estado actual (verificado en `origin/develop`, backend `3ffed99`, frontend `0a5ff37`)

| Elemento | Estado |
| :---- | :---- |
| Backend `inventory` | Fase A completa: `GET/POST /categorias`; `GET /equipamiento` y `/{id}` con vista por rol (RN-I7) e `incluir_inactivos`; `POST /equipamiento`, `POST /equipamiento/{id}/unidades`; `PATCH /equipamiento/{id}` y `/{id}/estado`; `GET /unidades`, `PATCH /unidades/{id}` y `/{id}/estado` con la matriz de §5.3. Migraciones `0006` y `0010` |
| `inventory/service.py` | `TRANSICIONES_ADMIN`, `bloquear_unidad`, `validar_transicion_admin`, `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad` y `datos_equipamiento_por_ids` (§6.1, backend PR \#19) |
| `loans/service.py` (Perfil 3) | Publica `ocupacion_de_unidades(db, unidad_ids, desde, hasta)` y `unidades_libres(db, equipamiento_ids, sede, desde, hasta)` (backend PR \#21). **No** publica todavía `historial_de_unidad` ni `reservas_futuras_de_unidad` |
| Frontend `inventory` | Catálogo conectado, tabla de stock en `admin-stock`, alta, edición, baja lógica, estados y "No disponible" (DT-27). `EquipmentCard` dibuja un botón "Agregar al carrito" que sólo llama a `onAddToCart` si alguien lo pasa; `App.tsx` no lo pasa. **No hay vista de detalle del equipo**: `CatalogPage` acepta `onSelect`, pero nadie la usa |
| Frontend `loans` | Sólo `.gitkeep`. El carrito (provider) es la tarea F1.3 del Perfil 3 |
| Tests | Backend: 320 en verde al 2026-10-23, más los de `loans` (PR \#16 y \#21) y los de `datos_equipamiento_por_ids` y concurrencia (PR \#19 y \#20). Frontend: 47 en verde al 2026-10-23 |

## 4. Reglas de negocio

- **RN-I1 (sede).** Toda lectura de unidades se filtra por sede en la consulta SQL (`resolver_alcance_sede`). Sólo `SUPERADMIN` puede elegir `sede`; pedir otra sede a un rol local responde `403 SEDE_FUERA_DE_ALCANCE`.
- **RN-I2 (alta, PRE-19).** `ADMIN_LOCAL`: sede automática, indicar otra responde `403 SEDE_FUERA_DE_ALCANCE`. `SUPERADMIN`: sede obligatoria (`422 SEDE_REQUERIDA`). La sede nunca se toma de otro lugar que `sede_para_alta`.
- **RN-I3 (estado, PRE-14).** El admin puede llevar una unidad a `disponible`, `mantenimiento` o `baja`. `prestado` lo gestiona sólo `loans` mediante las funciones de §6 (D-02). Una unidad en `baja` no vuelve a otro estado (D-03).
- **RN-I4 (stock lógico).** `cantidad_total` excluye `baja`; `cantidad_disponible` cuenta `disponible`; `en_mantenimiento` es verdadero si todas las unidades activas están en `mantenimiento`. Una unidad en `mantenimiento` o `baja` no se puede asignar a un préstamo. **Aclaración (C16):** `cantidad_disponible` informa el **estado físico de hoy** (cuántas unidades están en el estante), no si hay unidades libres para unas fechas. Eso lo informa la disponibilidad por fechas (§5.4). En la pantalla se rotula "Disponibles hoy".
- **RN-I5 (baja lógica, P7.3).** Equipamiento y unidades no se borran físicamente. Un ítem dado de baja desaparece del catálogo de estudiantes y docentes y sigue visible para administradores (filtro `activo`). Un equipamiento sin unidades activas se muestra "No disponible".
- **RN-I6 (parámetros, P8).** El plazo por defecto sale de `obtener_parametro`: `prestamo.general.max_dias`, o `prestamo.notebook.max_dias` para ítems con `es_notebook = true` (D-05). No se codifican plazos.
- **RN-I7 (privacidad).** Las respuestas para `ESTUDIANTE` y `DOCENTE` no incluyen `numero_serie`, `codigo_inventario` ni el estado individual de cada unidad (D-04). El locker sí se muestra. Ninguna respuesta de este módulo expone identidad de solicitantes a esos roles; la disponibilidad por fechas devuelve sólo cantidades.
- **RN-I8 (concurrencia, P7.2).** La unicidad de `codigo`, `numero_serie` y `codigo_inventario` se garantiza con `UNIQUE` y se traduce a `409 INVENTARIO_DUPLICADO`. Los cambios de estado sobre una misma unidad se serializan con `SELECT ... FOR UPDATE`.
- **RN-I9…RN-I12** (§6.1): alcance, consulta, mínimo dato y transacción de `datos_equipamiento_por_ids`.
- **RN-I13 (plazo al cambiar de tipo, C18).** `max_dias_prestamo` se copia del parámetro vigente al crear el ítem y después sólo cambia si un administrador lo edita. Excepción: si un `PATCH /equipamiento/{id}` cambia `es_notebook` y **no** incluye `max_dias_prestamo`, el plazo se recalcula con el parámetro del tipo nuevo (RN-I6). Si lo incluye, gana el valor enviado. Consecuencia aceptada (D-13): bajar un parámetro se aplica enseguida a todos los pedidos, porque `loans` toma el menor entre el parámetro y el ítem (RN-L06 de SPEC-05); subirlo no alcanza a los ítems ya creados, que el administrador edita si corresponde.
- **RN-I14 (unidad libre en una fecha, D-11).** Para la disponibilidad por fechas se usa **el mismo criterio que `loans` al crear una orden** (RN-L10 de SPEC-05): una unidad cuenta si es asignable hoy (`unidades_asignables`: `disponible`, de la sede, de un ítem activo) y no tiene una línea `reservado` o `entregado` cuyo período se solape con ese día. Las unidades `prestado`, `mantenimiento` y `baja` no cuentan para ninguna fecha. Así el calendario nunca muestra libre un día que `POST /ordenes` rechazaría por falta de unidades.
- **RN-I15 (día libre).** Un día es el intervalo `[00:00, 24:00)` en la zona del laboratorio (`ZONA_HORARIA_LAB`). Una unidad está libre ese día si **ningún** período ocupado se solapa con él (criterio conservador: una devolución a las 12:00 ocupa el día entero). El calendario es orientativo; la garantía es la validación de `POST /ordenes` y el `EXCLUDE` de `loans` (P7.2).
- **RN-I16 (dependencia de `loans`).** `inventory` usa funciones públicas de `loans` sólo desde `inventory/disponibilidad.py` (y en la Fase C desde el router, para historial y reservas). `inventory/service.py` **nunca** importa `loans`, porque `loans/service.py` ya importa `inventory/service.py` y se formaría un ciclo. `inventory` no importa modelos de `loans`.

## 5. Contratos (prefijo `/api/v1/inventory`, todos con sesión)

Errores en formato `{detail, code}` vía `AppError`; validación `422` estándar de FastAPI. Todos los payloads `*Create`/`*Update` usan `extra="forbid"` y `str_strip_whitespace`.

### 5.1 Lectura del catálogo (PRE-01, PRE-02) — Fase A

| Método y ruta | Roles | Contrato |
| :---- | :---- | :---- |
| `GET /equipamiento` | Todos | Filtros `sede`, `categoria`, `q`; `incluir_inactivos: bool = false` (sólo admins; para otros roles se ignora). Respuesta según rol (RN-I7): `EquipamientoPublicoResponse` para estudiante y docente, `EquipamientoResponse` para admins |
| `GET /equipamiento/{id}` | Todos | Misma regla de respuesta por rol. `404 EQUIPAMIENTO_NO_ENCONTRADO` si no está en alcance |
| `GET /categorias` | Todos | Sin cambios |

`EquipamientoPublicoResponse`: datos del ítem (`id`, `codigo`, `nombre`, `marca`, `modelo`, `categoria_id`, `descripcion`, `max_dias_prestamo`, `alta_gama`, `es_notebook`, `imagen_url`, `video_url`, `reglas_cuidado`), `locker` (si todas las unidades activas de la sede lo comparten) y los campos calculados `cantidad_total`, `cantidad_disponible`, `en_mantenimiento`. Sin lista de unidades.

### 5.2 Stock (PRE-12) — sólo admins, Fase A

| Método y ruta | Descripción |
| :---- | :---- |
| `GET /equipamiento` (respuesta de admin) | Alimenta la tabla: Nombre, Categoría, Locker, Tipo (`alta_gama` → Especial/Común) y unidades disponibles; las unidades se despliegan desde `unidades` |
| `GET /unidades` | Filtros `sede`, `estado`, `equipamiento_id` |

El ordenamiento de columnas se hace en el cliente (P10).

### 5.3 Alta, edición, baja y estados (PRE-19, PRE-12, PRE-14)

| Método y ruta | Roles | Códigos | Descripción |
| :---- | :---- | :---- | :---- |
| `POST /equipamiento` | Admins | 201, 401, 403, 409, 422 | Plazo por defecto según RN-I6 |
| `POST /equipamiento/{id}/unidades` | Admins | 201, 401, 403, 404, 409 | — |
| `PATCH /equipamiento/{id}` | Admins | 200, 401, 403, 404, 409, 422 | Edita nombre, marca, modelo, categoría, descripción, `max_dias_prestamo`, `alta_gama`, `es_notebook`, URLs, `reglas_cuidado`. `codigo` es inmutable. **Fase B:** aplica RN-I13 |
| `PATCH /equipamiento/{id}/estado` | Admins | 200, 401, 403, 404, 409 | Body `{activo: bool}` (RN-I5). Con unidades `prestado` → `409 EQUIPAMIENTO_CON_PRESTAMOS` |
| `PATCH /unidades/{id}` | Admins | 200, 401, 403, 404, 409, 422 | Edita `numero_serie`, `codigo_inventario`, `locker` (1–7). La sede no se modifica |
| `PATCH /unidades/{id}/estado` | Admins | 200, 401, 403, 404, 409, 422 | Matriz de abajo, RN-I8. **Fase C:** la respuesta suma `reservas_afectadas` |

Matriz de transiciones del admin (`PATCH /unidades/{id}/estado`):

| Desde \ Hacia | `disponible` | `mantenimiento` | `baja` | `prestado` |
| :---- | :---- | :---- | :---- | :---- |
| `disponible` | — | Sí | Sí | No (`422`) |
| `mantenimiento` | Sí | — | Sí | No (`422`) |
| `prestado` | `409` | `409` | `409` | — |
| `baja` | `409` | `409` | — | No (`422`) |

Una unidad `prestado` sólo la libera `loans` (devolución, PRE-13). Pasar a `mantenimiento` o `baja` una unidad con reservas futuras aprobadas no se bloquea en `inventory`.

**Fase C — `reservas_afectadas`.** La respuesta de `PATCH /unidades/{id}/estado` pasa a ser `UnidadEstadoResponse` = `UnidadFisicaResponse` + `reservas_afectadas: int | null`. Cuando el estado nuevo es `mantenimiento` o `baja`, vale la cantidad de reservas aprobadas de la unidad que empiezan desde ahora (`loans.reservas_futuras_de_unidad(db, unidad_id, desde=ahora_lab())`), calculada **después** del `commit` del cambio de estado (la lectura no debe demorar el bloqueo). En otro caso, o si el cambio es idempotente, vale `null`. `inventory` sólo informa: la cancelación forzada es de `loans` (PRE-17).

### 5.4 Disponibilidad por fechas (PRE-01) — Fase B

`GET /equipamiento/{id}/disponibilidad?desde=<fecha>&hasta=<fecha>[&sede=<sede>]`

| Aspecto | Contrato |
| :---- | :---- |
| Roles | Todos (estudiante, docente y admins) |
| Parámetros | `desde`, `hasta`: `date` (ISO `AAAA-MM-DD`), obligatorios, ambos inclusive, en la zona del laboratorio. `sede`: opcional; sólo `SUPERADMIN` la elige y **para él es obligatoria** |
| Sede | La misma regla que `sede_para_alta`: roles locales → su sede (pedir otra → `403 SEDE_FUERA_DE_ALCANCE`); `SUPERADMIN` sin `sede` → `422 SEDE_REQUERIDA` |
| Rango | `desde ≤ hasta`, `desde ≥ hoy` (zona del laboratorio) y `hasta − desde + 1 ≤ 62` días (D-07). Si no se cumple → `422 RANGO_FECHAS_INVALIDO`, con `detail` que explica cuál de las tres reglas falló |
| Alcance del ítem | Igual que `GET /equipamiento/{id}`: estudiante y docente sólo ven ítems activos con unidades en su sede; si no → `404 EQUIPAMIENTO_NO_ENCONTRADO`. Un admin ve también un ítem inactivo o sin unidades (con todo en 0) |
| Cálculo | `unidades_asignables(db, id, sede)` → `loans.ocupacion_de_unidades(db, esas_ids, inicio(desde), inicio(hasta + 1 día))` → por día, unidades sin períodos solapados (RN-I14, RN-I15). Tres consultas como máximo, sin consultas por día |
| Privacidad | Sólo cantidades: sin ids de unidades, series, órdenes ni solicitantes (RN-I7) |

Respuesta `200` — `DisponibilidadResponse`:

| Campo | Tipo | Descripción |
| :---- | :---- | :---- |
| `equipamiento_id` | `int` | — |
| `sede` | `SedeEnum` | Sede sobre la que se calculó |
| `desde`, `hasta` | `date` | El rango pedido |
| `unidades_asignables` | `int` | Unidades que hoy cuentan (RN-I14); es el máximo de cualquier día |
| `dias` | `list[DiaDisponibilidad]` | Un elemento por día del rango, en orden |

`DiaDisponibilidad`: `fecha: date`, `unidades_libres: int`, `disponible: bool` (`unidades_libres > 0`).

### 5.5 Historial de usuarios por unidad (PRE-12) — Fase C, bloqueada

`GET /unidades/{id}/historial?limit=20&offset=0`

| Aspecto | Contrato |
| :---- | :---- |
| Roles | Admins (`require_roles`); estudiante y docente → `403 PERMISO_INSUFICIENTE` (como el resto de las rutas de gestión, INV-11) |
| Alcance | Unidad inexistente o de otra sede → `404 UNIDAD_NO_ENCONTRADA` (lo valida `inventory` con `puede_ver_sede` antes de llamar a `loans`) |
| Datos | `loans.historial_de_unidad(db, unidad_id, actor)` (SPEC-05 §10.2). `inventory` no importa modelos de `loans` |
| Paginación | `limit` 1–100 (por defecto 20) y `offset ≥ 0`. Si la función de `loans` no pagina, `inventory` recorta la lista |
| Respuesta | `list[MovimientoUnidadResponse]`, del más reciente al más antiguo. Campos **indicativos** hasta que `loans` publique su firma: `orden_id`, `solicitante` (`id`, `nombre`, `apellido`, de `users.datos_publicos_por_ids` vía `loans`), `estado` de la línea, `retiro_pactado`, `devolucion_pactada`, `entregado_en`, `devuelto_en`, `observacion_devolucion`. Nunca DNI, email ni teléfono (P6) |

Si al publicarse la firma de `loans` difiere de esta tabla, se ajusta este contrato en una revisión del spec antes de implementar (AGENTS.md §4).

## 6. Interfaz de servicio hacia `loans` (DT-20)

`app/modules/inventory/service.py`. Ninguna función hace `commit`: la transacción es de quien llama.

| Función | Uso por `loans` | Estado |
| :---- | :---- | :---- |
| `unidades_asignables(db, equipamiento_id, sede) -> list[int]` | Ids de unidades `disponible` de esa sede, de un ítem activo | Fase A |
| `unidad_es_asignable(db, unidad_id, sede) -> bool` | Validar antes de asignar | Fase A |
| `marcar_unidad_prestada(db, unidad_id)` / `liberar_unidad(db, unidad_id)` | Entrega y devolución; bloquean con `FOR UPDATE` y lanzan `409 TRANSICION_ESTADO_INVALIDA` si el estado no corresponde | Fase A |
| `datos_equipamiento_por_ids(db, ids) -> dict[int, DatosEquipamiento]` | Plazo por línea, alta gama y datos para el administrador (§6.1) | Mergeado (PR \#19); se aprueba con esta versión |
| `bloquear_unidad(db, unidad_id) -> UnidadFisica \| None` | Bloquear la unidad al aprobar (RN-L11 de SPEC-05) (§6.2) | Existe; pasa a API pública (C14) |
| `marcar_unidad_mantenimiento(db, unidad_id) -> UnidadFisica` | Devolución con daño en la misma transacción (RN-L20, AC-L59) (§6.2) | **Nueva**, Fase B (C17) |

### 6.1 `datos_equipamiento_por_ids` (C8 de SPEC-05) — addendum v1.1.0

Pedido del Perfil 3 (SPEC-05 §16, C8). Es una función pública de lectura, en el estilo de `users.datos_publicos_por_ids`. Cumple P3.3 (enmienda 1.1.1): `loans` colabora a través de una función del módulo dueño y no importa `Equipamiento`. **El código está en `develop` desde el 2026-11-06 (backend PR \#19); esta versión del spec lo somete a aprobación junto con la Fase B.**

- **Firma:** `datos_equipamiento_por_ids(db: AsyncSession, ids: Iterable[int]) -> dict[int, DatosEquipamiento]`.
- **`DatosEquipamiento`** (`dataclass(frozen=True, slots=True)`): `id`, `codigo`, `nombre`, `activo`, `es_notebook`, `alta_gama`, `max_dias_prestamo`.
- **RN-I9 (alcance).** El catálogo es global (`equipamientos` no tiene sede; las unidades sí), así que la función **no filtra por sede ni por estado** y no incluye `sede`. `activo` viaja en el resultado y decide quien llama. La autorización es de quien llama.
- **RN-I10 (consulta).** Una sola consulta con los ids en un único parámetro arreglo; ids repetidos se consultan una vez; entrada vacía devuelve `{}` sin consultar la base; los ids inexistentes se omiten.
- **RN-I11 (mínimo dato, P6).** Selecciona sólo las columnas necesarias, no la entidad.
- **RN-I12 (transacción).** No hace `commit`, `rollback` ni `flush`.
- **Criterio INV-27:** devuelve los siete campos correctos; incluye ítems inactivos y sin unidades; no filtra por sede; omite inexistentes y repetidos; entrada vacía sin consulta; una sola `SELECT` por lote que no toca `unidades_fisicas`; no deja la entidad en la sesión; no hace `flush`; el resultado es inmutable.

### 6.2 `bloquear_unidad` y `marcar_unidad_mantenimiento` (C14, C17) — Fase B

**`bloquear_unidad(db, unidad_id) -> UnidadFisica | None` (C14).** Se declara API pública con el comportamiento que ya tiene: `SELECT ... FOR UPDATE` con `populate_existing`, devuelve la unidad o `None` si no existe, sin filtrar por sede ni estado y sin `commit`. Contrato para quien llama:

- Puede **leer** `id`, `equipamiento_id`, `sede` y `estado` de la unidad devuelta.
- **No** asigna `estado` ni otro atributo: los cambios de estado pasan por `marcar_unidad_prestada`, `liberar_unidad` o `marcar_unidad_mantenimiento`.
- Si bloquea varias unidades en una transacción, lo hace en **orden ascendente de id** para no provocar interbloqueos (RN-L11 de SPEC-05).

**`marcar_unidad_mantenimiento(db, unidad_id) -> UnidadFisica` (C17).** Pasa una unidad a `mantenimiento` dentro de la transacción de quien llama:

1. `bloquear_unidad`; si no existe → `AppError 404 UNIDAD_NO_ENCONTRADA`.
2. Si ya está en `mantenimiento`, la devuelve sin cambios (idempotente, como el `PATCH` del admin).
3. Si no, `validar_transicion_admin(estado, mantenimiento)`: desde `disponible` se permite; desde `prestado` o `baja` → `409 TRANSICION_ESTADO_INVALIDA`.
4. Asigna `mantenimiento` y devuelve la unidad. Sin `commit` ni `flush`; no valida sede (la autorización es de quien llama, como en el resto de §6).

Uso previsto por `loans` en una devolución con daño: `liberar_unidad` (`prestado` → `disponible`) y enseguida `marcar_unidad_mantenimiento`, en la misma transacción; la unidad nunca queda `disponible` para otra transacción (AC-L59, EC-L15).

## 7. Modelo de datos

**Fase A — migración `0010_inventory_gestion`** (aplicada): `equipamientos.activo` y `equipamientos.es_notebook` (`BOOLEAN NOT NULL`), `CHECK locker IS NULL OR locker BETWEEN 1 AND 7` (DT-23). El `CHECK` 1–15 de `max_dias_prestamo` no cambió (D-05).

**Fases B y C:** sin tablas ni columnas nuevas y **sin migración**, así que no compiten con la numeración de `0011`/`0012` (C19 de SPEC-05). El historial de cambios de estado de unidades no se persiste (D-08); el historial de PRE-12 es el de usuarios, que vive en `loans`.

## 8. Frontend (`src/features/inventory/`)

### 8.1 Fase A (implementada)

Catálogo conectado a la API con carga, error, "sin resultados", *debounce* y `AbortSignal`; categoría filtrada en la pantalla; tabla de stock ordenable con unidades desplegables y acciones de estado con confirmación; formulario de alta y edición con selector de sede oculto para `ADMIN_LOCAL` y obligatorio para `SUPERADMIN`; DTOs espejo y `mappers.ts`.

### 8.2 Fase B

- **Detalle del equipo (PRE-01).** Al hacer clic en una tarjeta o fila del catálogo se abre `EquipmentDetailModal` (de `inventory`, sin pantalla nueva en `App.tsx`): imagen, marca y modelo, descripción técnica, reglas de cuidado, botón de video instructivo (si hay `video_url`), locker, tipo (Especial/Común), plazo máximo, "Disponibles hoy" y el **mini-calendario**. Se abre para todos los roles, incluidos los ítems sin unidades disponibles hoy (el calendario lo muestra todo en 0). La prop `onSelect` de `CatalogPage` se elimina (no tiene consumidores).
- **Mini-calendario.** Vista mensual de lunes a domingo, empezando por el mes actual, con flechas para avanzar y retroceder dentro de la ventana `[hoy, hoy + 61 días]` (D-07). Por mes hace **un solo** pedido a `GET /equipamiento/{id}/disponibilidad` con `desde = max(día 1, hoy)` y `hasta = min(último día, hoy + 61)`, cancelable con `AbortSignal`. Cada día muestra: pasado o fuera de ventana (gris, sin dato), libre (verde con la cantidad `unidades_libres`) o sin unidades libres (rojo). Leyenda debajo, aclarando que es orientativo. Estados de carga y error (`ApiError.detail`). El `SUPERADMIN` envía la sede vista (`useSede()`); si está en "ambas sedes", el calendario pide elegir una.
- **Botón "Agregar al pedido" (C11, D-12).** `inventory` **no importa nada de `loans`**. `CatalogPage` sigue exponiendo `onAddToCart?: (eq: Equipment) => void`; la tarjeta, la fila de la lista y el detalle muestran el botón sólo si se recibió `onAddToCart` y el rol es estudiante o docente. Está **deshabilitado** si el ítem no está activo, está en mantenimiento o `cantidad_disponible = 0` (con RN-I14, sin unidades disponibles hoy no hay ninguna fecha libre), con un `title` que explica el motivo. Al pulsarlo llama a `onAddToCart(eq)` y muestra "Agregado" un par de segundos. Quién conecta el *callback* con el carrito es el Perfil 3, en `App.tsx` (con la conformidad del Perfil 1), por ejemplo `onAddToCart={(eq) => carrito.agregar(eq)}`. Si el pedido falla por fechas sin unidades, el `409 EQUIPAMIENTO_NO_DISPONIBLE` lo muestra la pantalla de `loans` (F1.7 de SPEC-05).
- **Rótulo.** "Disponibles" pasa a "Disponibles hoy" en tarjetas, lista y detalle (C16). La tabla de stock de los admins no cambia.

### 8.3 Fase C (bloqueada)

- **Historial por unidad (PRE-12).** En `UnidadesRow`, un botón "Historial" por unidad abre `HistorialUnidadModal` con la lista paginada de §5.5 (solicitante, fechas pactadas y reales, estado y observación de la devolución) y "Cargar más".
- **Reservas afectadas (PRE-17).** Si `PATCH /unidades/{id}/estado` devuelve `reservas_afectadas > 0`, la tabla de stock muestra un aviso persistente: "Esta unidad tenía N reservas aprobadas. Resolvelas con una cancelación forzada en la bandeja de Préstamos". Sin enlace hasta que exista la pantalla del Perfil 3.

## 9. Criterios de aceptación

Prefijo `INV-` para no colisionar con AC-xx de SPEC-02 ni con AC-Lxx de SPEC-05. Cada uno tendrá al menos un test (`# INV-NN`), con `pytestmark = pytest.mark.integracion` y PostgreSQL real.

### 9.1 Fase A (cubiertos, ver `tasks.md`)

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
| INV-13 | Plazo por defecto = `prestamo.general.max_dias` (y `prestamo.notebook.max_dias` si `es_notebook = true`); cambia al editar el parámetro | RN-I6 |
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
| INV-27 | `datos_equipamiento_por_ids` según §6.1 (cubierto por `tests/inventory/test_datos_equipamiento.py`, PR \#19) | DT-20, C8 |

### 9.2 Fase B

| ID | Criterio | Req. |
| :---- | :---- | :---- |
| INV-26 | `GET /equipamiento/{id}/disponibilidad` devuelve un día por fecha del rango y `unidades_libres` según RN-I14 y RN-I15: (a) las líneas `reservado` y `entregado` ocupan los días que tocan, también si empiezan antes del rango o terminan después; (b) `pendiente`, `devuelto`, `cancelado`, `rechazado` y `no_retirado` no ocupan; (c) las unidades `prestado`, `mantenimiento` y `baja`, las de otra sede y las de un ítem inactivo no cuentan; (d) una línea que termina a las 12:00 ocupa ese día; (e) `unidades_asignables` coincide con `unidades_asignables()`; (f) la respuesta no contiene ids de unidades, series, órdenes ni solicitantes | PRE-01, RN-I7 |
| INV-28 | `marcar_unidad_mantenimiento`: `disponible` → `mantenimiento`; idempotente si ya está en `mantenimiento`; desde `prestado` o `baja` → `409 TRANSICION_ESTADO_INVALIDA`; inexistente → `404 UNIDAD_NO_ENCONTRADA`; no hace `commit` ni `flush` (un `rollback` posterior deja la unidad como estaba); `liberar_unidad` seguido de `marcar_unidad_mantenimiento` en una transacción deja la unidad en `mantenimiento` y otra sesión nunca la lee `disponible` | PRE-14, C17 |
| INV-29 | `PATCH /equipamiento/{id}` con `es_notebook` cambiado y sin `max_dias_prestamo` toma el parámetro del tipo nuevo; con `max_dias_prestamo` gana el enviado; sin cambiar `es_notebook` el plazo no se toca (RN-I13) | RN-I6, C18 |
| INV-30 | Validaciones de disponibilidad: sin token → `401`; `hasta < desde`, `desde` anterior a hoy o más de 62 días → `422 RANGO_FECHAS_INVALIDO`; `SUPERADMIN` sin `sede` → `422 SEDE_REQUERIDA`; rol local con otra sede → `403 SEDE_FUERA_DE_ALCANCE`; estudiante con un ítem inactivo o sin unidades en su sede → `404`; un admin con un ítem inactivo → `200` con todo en 0 | PRE-01, P4, P5 |
| INV-31 | Coherencia con `loans` (C16): con los mismos datos, un día que el calendario informa con `unidades_libres = 0` hace que `POST /api/v1/loans/ordenes` para ese día responda `409 EQUIPAMIENTO_NO_DISPONIBLE`, y un día con `unidades_libres ≥ 1` permite crear la orden de una línea | PRE-01, PRE-03 |
| INV-32 | Frontend: el detalle del equipo muestra descripción, reglas, video, locker y el mini-calendario; hace un pedido por mes con el rango recortado a la ventana; pinta días libres, sin unidades y fuera de ventana; no deja navegar fuera de la ventana; muestra errores de la API | PRE-01 |
| INV-33 | Frontend: el botón "Agregar al pedido" sólo aparece con `onAddToCart` y rol estudiante o docente; se deshabilita con ítem inactivo, en mantenimiento o sin disponibles hoy; al pulsarlo llama a `onAddToCart` con el equipo; el rótulo dice "Disponibles hoy" | PRE-01, PRE-03, C11, C16 |

### 9.3 Fase C (bloqueada)

| ID | Criterio | Req. |
| :---- | :---- | :---- |
| INV-34 | `GET /unidades/{id}/historial`: admin con jurisdicción → `200` paginado y ordenado del más reciente al más antiguo; `ADMIN_LOCAL` de la otra sede o unidad inexistente → `404`; estudiante o docente → `403`; sin token → `401`; ninguna respuesta incluye DNI, email ni teléfono | PRE-12, P6 |
| INV-35 | `PATCH /unidades/{id}/estado` a `mantenimiento` o `baja` devuelve `reservas_afectadas` igual a la cantidad de reservas aprobadas futuras de la unidad; a `disponible` o idempotente devuelve `null`; frontend: aviso persistente si es mayor que 0 | PRE-14, PRE-17 |

Verificación del frontend: `npm run typecheck`, `npm run build`, `npm test` (Vitest para las funciones puras) y un recorrido manual de INV-32 e INV-33 contra el backend local.

## 10. Coordinación con otros perfiles

| Para | Pedido | Motivo | Estado |
| :---- | :---- | :---- | :---- |
| Perfil 1 | Aprobar esta versión (incluye el addendum §6.1 que ya está mergeado) | AGENTS.md §4 | Abierto |
| Perfil 1 | **Se retira el pedido de la ventana del calendario** (D-07): es un tope técnico de la consulta, no una regla del reglamento | P8 | Al aprobar, cerrar el ítem de `MEMORY.md` §5 |
| Perfil 1 | Conformidad para que el Perfil 3 pase `onAddToCart` a `CatalogPage` en `App.tsx` (una línea) | C11, D-12 | Abierto |
| Perfil 1 | El `CHECK` 1–15 de `max_dias_prestamo` sigue fijo (D-05) | P8 | Abierto (sin cambios) |
| Perfil 3 | `bloquear_unidad` es API pública con el contrato de §6.2 (C14) y `marcar_unidad_mantenimiento` queda disponible al mergear la Fase B (C17): destraba AC-L59 | RN-L11, RN-L20 | Se avisa al mergear |
| Perfil 3 | El carrito (F1.3) recibe un `Equipment` de `inventory` por el *callback* `onAddToCart` que el Perfil 3 conecta en `App.tsx`; `inventory` no importa `loans` (D-12) | C11 | Abierto |
| Perfil 3 | C16 y C18 respondidos (RN-I4, RN-I13, RN-I14); D-13 explica por qué no se cambia `max_dias_prestamo` a nulo | SPEC-05 §16 | Se avisa al aprobar |
| Perfil 3 | Publicar `historial_de_unidad` y `reservas_futuras_de_unidad` (SPEC-05 §10.2, Fases 2–3) con su firma definitiva; desbloquean la Fase C | PRE-12, PRE-17 | Abierto |
| Perfil 5 | El asistente puede usar `GET /equipamiento/{id}/disponibilidad` para responder "¿hay X libre el jueves?"; no hay endpoints especiales para IA | IA-02 | Informativo |

## 11. Casos de borde

- Equipamiento con unidades en ambas sedes: el admin local ve sólo las de la suya; `cantidad_*` y la disponibilidad se calculan sobre esa sede.
- Equipamiento recién creado sin unidades: visible sólo para admins; su disponibilidad es todo 0.
- Cambio de estado de una unidad inexistente o de otra sede: `404 UNIDAD_NO_ENCONTRADA`.
- Cambio de estado a su valor actual: `200` idempotente, sin error.
- Editar una unidad con serie o inventario que ya existen en otra: `409 INVENTARIO_DUPLICADO`.
- Categoría inexistente al crear o editar: `422 CATEGORIA_INEXISTENTE`.
- `q` con comodines (`%`, `_`): se escapan para que se busquen literalmente.
- **Disponibilidad:** una unidad hoy `prestado` y con devolución pactada la semana próxima **no** aparece libre después de esa fecha (RN-I14, D-L16 de SPEC-05): recién cuenta cuando se registra la devolución.
- **Disponibilidad:** dos unidades libres en días alternados dan `unidades_libres = 1` todos los días, aunque ninguna esté libre el rango entero; el `409` de `POST /ordenes` cubre ese caso (RN-I15).
- **Disponibilidad:** el cambio de horario de verano no aplica en Argentina, pero los límites del día se calculan con `ZONA_HORARIA_LAB` igual.
- **Mantenimiento con reservas:** la unidad pasa a `mantenimiento` igual; la entrega de esas reservas fallará con `409` en `loans` hasta que el admin las resuelva (PRE-17). En la Fase C el admin lo ve en `reservas_afectadas`.

## 12. Decisiones

| ID | Pregunta | Resolución |
| :---- | :---- | :---- |
| D-01 | ¿Numeración SPEC-04 o SPEC-03? | **04** (Perfil 1 reserva el 03) |
| D-02 | ¿El admin puede poner `prestado` a mano? | **No**; sólo `loans` vía §6 |
| D-03 | ¿`baja` es terminal? | **Sí**. Corregir un error se hace con edición; reactivar sería una alta nueva |
| D-04 | ¿Estudiantes y docentes ven números de serie y códigos de inventario? | **No**. Respuesta reducida (RN-I7) |
| D-05 | Plazo por defecto de notebooks y tope 15 del `CHECK` | `prestamo.notebook.max_dias` para ítems con `es_notebook = true`. Tope 15 se mantiene y se avisa al Perfil 1 |
| D-06 | `ADMIN_LOCAL` sobre ítems con unidades de la otra sede | Editar datos descriptivos: **sí**. Desactivar: sólo `SUPERADMIN` si hay unidades en ambas sedes |
| D-07 | Ventana máxima del calendario de disponibilidad | **Propuesta v1.2.0:** tope técnico fijo de **62 días** (dos meses) en `inventory/disponibilidad.py`, como el `limit` de una paginación: acota el costo de la consulta y no es una regla del reglamento, así que P8 no exige un parámetro. Si el equipo quiere que sea configurable, el Perfil 1 agrega la clave y se cambia una línea. La ventana de reserva a futuro de los préstamos (pregunta 6 de SPEC-05 §15.2) es una regla de `loans`, no de este calendario |
| D-08 | ¿Historial de cambios de estado de unidades? | **No** ahora (YAGNI). El historial de PRE-12 es de usuarios, vía `loans` |
| D-09 | "Fuera de servicio" del ERS | `mantenimiento` = "En Mantenimiento" (temporal); `baja` = "Fuera de servicio" (definitivo) |
| D-10 | Entrega por fases | **A** (implementada), **B** (lo que ya se puede hacer con `develop`) y **C** (espera funciones de `loans`) |
| D-11 | ¿Qué unidades cuentan en el calendario? | **Propuesta v1.2.0:** el criterio de `loans` (RN-I14): sólo las asignables hoy. Alternativa descartada: contar también las `prestado` y mostrarlas libres después de su devolución pactada; sería más optimista, pero `POST /ordenes` rechazaría esas fechas (SPEC-05 D-L16), y el calendario prometería lo que el pedido no permite |
| D-12 | ¿Cómo se conecta el botón del catálogo con el carrito? | **Propuesta v1.2.0:** por el *callback* `onAddToCart` que ya existe. `inventory` no importa `loans` y el Perfil 3 hace el cableado en `App.tsx`. Alternativa descartada: que `inventory` llame a `useCarrito()` de `loans`, que acopla las dos *features* y obliga a montar el provider antes de que el catálogo funcione |
| D-13 | C18: ¿`max_dias_prestamo` debería "seguir" al parámetro? | **Propuesta v1.2.0:** no por ahora. Se mantiene la copia al crear, más RN-I13. Alternativa para más adelante: columna nula = "usa el parámetro del tipo" (`loans._limite_dias` ya acepta `None`); cambia el contrato de `DatosEquipamiento`, el `CHECK` y las respuestas, y necesita migración, así que se evalúa después de la demo |
| D-14 | Granularidad del calendario | **Propuesta v1.2.0:** por día (RN-I15), sin horas: es lo que pide PRE-01 ("mini-calendario") y alcanza para elegir fechas; las horas las valida el formulario de `loans` |

## 13. Trazabilidad

| Requisito | Endpoints (§5) / funciones (§6) | Criterios |
| :---- | :---- | :---- |
| PRE-01 | `GET /equipamiento`, `GET /equipamiento/{id}`, `GET /equipamiento/{id}/disponibilidad` (B) | INV-02, 05, 07, 08, 24, 26, 30, 31, 32, 33 |
| PRE-02 | `GET /equipamiento`, `GET /categorias` | INV-02, 03, 04, 24 |
| PRE-03 (lado del catálogo) | Botón "Agregar al pedido" (B) | INV-31, 33 |
| PRE-12 | `GET /equipamiento`, `GET /unidades`, `PATCH /equipamiento/{id}`, `PATCH /equipamiento/{id}/estado`, `PATCH /unidades/{id}`, `GET /unidades/{id}/historial` (C) | INV-06, 15, 16, 17, 20, 24, 29, 34 |
| PRE-14 | `PATCH /unidades/{id}/estado`, `marcar_unidad_mantenimiento` (B) | INV-18, 19, 21, 22, 28, 35 |
| PRE-17 (aviso al admin) | `reservas_afectadas` (C) | INV-35 |
| PRE-19 | `POST /equipamiento`, `POST /equipamiento/{id}/unidades` | INV-09, 10, 11, 12, 13, 25 |
| DT-20 | §6 | INV-22, 27, 28 |
| DT-22 / DT-23 | Frontend §8.1 / migración `0010` | INV-24 / INV-14, 23 |

## 14. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.2.0 | 2026-11-07 | **`BORRADOR`** (Perfil 2, con asistencia de IA). Planifica todo lo que queda: Fase B (disponibilidad por fechas con `loans.ocupacion_de_unidades`, detalle con mini-calendario, botón "Agregar al pedido", C14, C17, C16, C18) y Fase C (historial y `reservas_afectadas`, bloqueada por `loans`). Somete a aprobación el addendum v1.1.0 (§6.1). Nuevas RN-I13…RN-I16, INV-26 redefinido e INV-28…INV-35, decisiones D-11…D-14 y propuesta para D-07. Limpieza: encabezado y nota de numeración, §3 al día con `develop`, tabla de §12 corregida |
| 1.1.0 | 2026-11-06 | `BORRADOR` (addendum §6.1): `datos_equipamiento_por_ids` a pedido del Perfil 3 (C8 de SPEC-05). El código se escribió antes de redactar el addendum, a pedido explícito del usuario, y se mergeó en `develop` (PR \#19). Queda incluido en la v1.2.0 |
| 1.0.1 | 2026-10-23 | Fase A implementada. §8: la categoría se filtra en la pantalla, no en la API. Se agregan en el frontend el alta y edición de unidades desde la tabla de stock. Hallazgo en la migración `0010`: `NAMING_CONVENTION` duplica el prefijo de los `CHECK` en bases creadas con Alembic; la migración usa SQL directo y tolera ambos nombres (DT-26) |
| 1.0.0 | 2026-10-23 | Aprobado con todas las recomendaciones de §12. Se agrega `equipamientos.es_notebook` (D-05) y se corrige §3 |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
