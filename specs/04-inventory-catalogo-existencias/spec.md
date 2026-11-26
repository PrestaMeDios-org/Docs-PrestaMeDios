# SPEC-04 — Catálogo y existencias (`inventory`)

> **Estado:** Fase A `IMPLEMENTADO` (2026-10-23) · Fase B `IMPLEMENTADO` (aprobada el 2026-11-07, en `develop` desde el 2026-11-08; cierre de los pendientes en B-22: backend PR #46 y frontend PR #33, mergeados el 2026-11-24) · Fase C **`IMPLEMENTADO`** (v1.3.0 y addendum v1.3.1 aprobados el 2026-11-25; backend PR \#50 y frontend PR \#34, en revisión) · **Versión:** 1.3.1 · **Perfil:** 2 (Catálogo y existencias)
> **Requisitos:** PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 · **Deuda que cierra:** DT-22, DT-23 (y la parte de `inventory` de DT-20)
> **Precedencia:** `docs/constitution.md` → `AGENTS.md` → `docs/perfiles.md` → este spec → `MEMORY.md`.
> **Depende de:** SPEC-01 y SPEC-02 (`core`, `config`), SPEC-05 v1.0.2 (`loans.ocupacion_de_unidades`, en `develop` desde el backend PR \#21; `historial_de_unidad` y `reservas_futuras_de_unidad`, en `develop` desde el backend PR \#23, 2026-11-08).
> **Numeración:** 04 (D-01). SPEC-03 es del Perfil 1 y SPEC-05 del Perfil 3.

---

## 1. Alcance

El trabajo se entrega en tres fases (D-10):

| Fase | Contenido | Requisitos | Estado |
| :---- | :---- | :---- | :---- |
| **A** | Catálogo conectado a la API, stock, estados de unidades, altas, ediciones y bajas lógicas, `CHECK` de locker, `service.py` para `loans` | PRE-01 (parcial), PRE-02, PRE-12 (parcial), PRE-14, PRE-19, DT-20, DT-22, DT-23 | Implementada (2026-10-23) |
| **B** | §6.1 (`datos_equipamiento_por_ids`, ya mergeado), §6.2 (C14, C17), RN-I13 (C18), aclaración de RN-I4 (C16), disponibilidad por fechas y mini-calendario en un detalle del equipo (§5.4), botón "Agregar al pedido" (C11) | PRE-01 completo, PRE-03 (lado del catálogo), PRE-14 | Implementada (backend PR \#24, frontend PR \#13 y \#23). Pendientes de cierre (INV-28 completo, INV-31 y READMEs) hechos en B-22 (backend PR #46 y frontend PR #33, mergeados en `develop` el 2026-11-24) |
| **C** | Historial de usuarios por unidad (§5.5) y `reservas_afectadas` al pasar una unidad a mantenimiento o baja (§5.3) | PRE-12 completo, PRE-17 (aviso) | **`IMPLEMENTADO`** (v1.3.0 y v1.3.1, backend PR \#50 y frontend PR \#34, en revisión): las funciones de `loans` están en `develop` (backend PR \#23) y los contratos de §5.3 y §5.5 ya siguen sus firmas reales (tarea C-01) |

**Fuera** (otros perfiles; ver §10):

- Carrito, formulario de pedido y validaciones de la orden (PRE-03…PRE-10): Perfil 3. El catálogo sólo ofrece el botón y avisa con un *callback* (§8.2).
- Cancelación forzada (PRE-17), entrega y devolución (PRE-13): Perfil 3.
- Notificaciones al afectado: Perfil 5.
- **Importación masiva del inventario desde CSV o Excel** (D-15): ningún requisito ni caso de uso del ERS la pide. La carga del inventario real se hace con el alta de PRE-19 (formulario con varias unidades por equipo). Si el piloto la necesita, la pide el Perfil 1 con un requisito y un spec propios.
- Cualquier cambio en `core`, `users`, `config`, `loans`, `spaces` o en el layout del frontend (`App.tsx`, `Navbar.tsx`).

## 2. Actores y permisos

| Actor | Catálogo y disponibilidad (lectura) | Stock, unidades e historial | Altas, ediciones, estados |
| :---- | :---- | :---- | :---- |
| `ESTUDIANTE`, `DOCENTE` | Sí, sólo su sede | No | No |
| `ADMIN_LOCAL` | Sí, su sede | Sí, su sede | Sí, su sede |
| `SUPERADMIN` | Sí, ambas sedes o una elegida (la disponibilidad exige una) | Sí | Sí, sede obligatoria en altas |

Se reutiliza sin cambios: `get_current_user`, `require_roles(ADMIN_LOCAL, SUPERADMIN)`, `resolver_alcance_sede`, `sede_para_alta`, `puede_ver_sede`, `AppError`, `obtener_parametro`, `ahora_lab`, `ZONA_HORARIA_LAB`, `RolUsuario`, `SedeEnum`. No se definen roles, usuarios ni formatos de error propios. Un recurso de otra sede responde `404` (no `403`) para no filtrar su existencia (Constitución §4.2, P4.5).

## 3. Estado actual (verificado en `origin/develop` el 2026-11-23, backend `5243337`, frontend `e0740bc`)

| Elemento | Estado |
| :---- | :---- |
| Backend `inventory` | Fases A y B: lo de la Fase A más `GET /equipamiento/{id}/disponibilidad` (§5.4, sobre `loans.ocupacion_de_unidades`, sólo desde `inventory/disponibilidad.py`) y RN-I13 en `PATCH /equipamiento/{id}` (backend PR \#24). `PATCH /unidades/{id}/estado` todavía responde `UnidadFisicaResponse`, sin `reservas_afectadas`; no existe `GET /unidades/{id}/historial`. Migraciones `0006`, `0010` y `0019_inventory_categorias_base` (§7) |
| `inventory/service.py` | `TRANSICIONES_ADMIN`, `bloquear_unidad` (pública, C14), `validar_transicion_admin`, `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad`, `marcar_unidad_mantenimiento` (C17, PR \#24) y `datos_equipamiento_por_ids` (§6.1, PR \#19) |
| `loans/service.py` (Perfil 3) | Publica `ocupacion_de_unidades` y `unidades_libres` (PR \#21), y `reservas_futuras_de_unidad` e `historial_de_unidad` (PR \#23). Sus firmas reales están en §5.3 y §5.5. Las columnas `entregado_en`, `devuelto_en` y `observacion_devolucion` llegan con la migración `0012` de `loans` (Fase 3 de SPEC-05), que todavía no está en `develop` |
| Frontend `inventory` | Fases A y B: catálogo, detalle del equipo con mini-calendario y "Agregar al pedido" (PR \#13; estilos y modo oscuro en el PR \#23, DT-31 y DT-32), tabla de stock con unidades desplegables. Con SPEC-10 (Perfil 1, aval U1): vista previa en el alta, miniaturas y vista por locker MOMENTÁNEA (M-03), y `Modal` movido a `components/ui` (PR \#29). Sin historial por unidad ni aviso de reservas afectadas |
| Frontend `loans` | Carrito conectado: `App.tsx` pasa `onAddToCart={puedePedir ? carrito.agregar : undefined}` (D-12). La bandeja cruza los ids de `GET /ordenes/{id}/unidades-libres` con el stock de `inventory` para mostrar "CAM-S-01 · locker 3" al aprobar (`loans/services/bandeja.ts`, `etiquetasDelStock`; responde Q1, D-18) |
| Tests | Backend en `develop`: INV-26, INV-29 e INV-30 con test anotado; INV-28 parcial e INV-31 sin test. **B-22 (backend PR #46 y frontend PR #33, mergeados en `develop` el 2026-11-24):** INV-28 completo, INV-31 y READMEs; arregla `bloquear_unidad` para que `liberar_unidad` + `marcar_unidad_mantenimiento` funcione en una transacción sin `flush`. 992 tests en verde, cobertura de `inventory` 99 %. Frontend: `calendario.test.ts`, `botonAgregar.test.ts` y los de SPEC-10 |

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

**Fase C — `reservas_afectadas` (PRE-14, PRE-17).** La respuesta de `PATCH /unidades/{id}/estado` pasa a ser `UnidadEstadoResponse` = `UnidadFisicaResponse` + dos campos:

| Campo | Tipo | Valor |
| :---- | :---- | :---- |
| `reservas_afectadas` | `int \| null` | Cantidad de reservas aprobadas de la unidad que empiezan desde ahora |
| `ordenes_afectadas` | `list[int] \| null` | Ids de las órdenes de esas reservas, sin repetir y en el orden de retiro (D-16) |

- **Fuente.** `loans.reservas_futuras_de_unidad(db, unidad_id, desde=ahora_lab()) -> list[ReservaFutura]` (firma real en `develop`, PR \#23): líneas `reservado` de la unidad con `retiro_pactado >= desde`, ordenadas por retiro, con `orden_id`, `detalle_id`, `retiro` y `devolucion`, sin solicitante ni sede. `reservas_afectadas = len(lista)`; `ordenes_afectadas` = sus `orden_id` sin repetir. Una línea `entregado` ya empezó y no cuenta (el equipo está en manos del solicitante y la unidad está `prestado`, que el admin no puede cambiar).
- **Cuándo.** Sólo si el estado **cambió** a `mantenimiento` o `baja` (también `mantenimiento → baja`). Si el estado nuevo es `disponible`, o el pedido es idempotente (mismo estado), los dos campos valen `null`.
- **Orden.** Se calcula **después** del `commit` del cambio de estado, para que la lectura no alargue el bloqueo `FOR UPDATE` (RN-I8). Si la lectura falla, el cambio de estado ya quedó hecho: el error se propaga como `500` y el admin ve el estado real al recargar (caso no esperado; no se compensa).
- **Privacidad.** Ni nombres ni datos de solicitantes: sólo cantidad e ids de órdenes, que el admin ya ve en la bandeja de su sede (RN-I7, P6). La jurisdicción la valida `inventory` antes (unidad de otra sede → `404`).
- **Alcance de `inventory`.** Sólo informa: la cancelación forzada con motivo y el aviso al afectado son de `loans` (PRE-17, CU-L06 de SPEC-05) y `notifications`.

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

### 5.5 Historial de usuarios por unidad (PRE-12) — Fase C

`GET /unidades/{id}/historial?limit=20&offset=0`

| Aspecto | Contrato |
| :---- | :---- |
| Roles | Admins (`require_roles`); estudiante y docente → `403 PERMISO_INSUFICIENTE` (como el resto de las rutas de gestión, INV-11) |
| Alcance | Unidad inexistente o de otra sede → `404 UNIDAD_NO_ENCONTRADA` (lo valida `inventory` con `puede_ver_sede` antes de llamar a `loans`). Además, `loans` filtra por la sede de la **orden** (`ADMIN_LOCAL`: la suya; `SUPERADMIN`: todas). Las dos coinciden, porque `loans` sólo asigna unidades de la sede de la orden (`unidad_es_asignable`) |
| Datos | `loans.historial_de_unidad(db, unidad_id, actor, *, limit, offset) -> list[MovimientoUnidad]` (firma real en `develop`, PR \#23). Se llama desde el router, como `reservas_futuras_de_unidad` (RN-I16); `inventory` no importa modelos de `loans` |
| Paginación | `limit` 1–100 (por defecto 20) y `offset ≥ 0`, validados con `Query` (fuera de rango → `422`) y pasados tal cual a `loans`, que pagina en la consulta. Sin total: el cliente pide la página siguiente mientras reciba `limit` elementos |
| Orden | Del más reciente al más antiguo por `retiro_pactado` (y por `detalle_id` ante un empate), como lo devuelve `loans` |
| Respuesta | `200` con `list[MovimientoUnidadResponse]`; lista vacía si la unidad nunca se asignó |

`MovimientoUnidadResponse` (espejo de `MovimientoUnidad`):

| Campo | Tipo | Nota |
| :---- | :---- | :---- |
| `orden_id`, `detalle_id` | `int` | La línea de la orden que usó la unidad |
| `solicitante` | `SolicitanteResumen \| null` | `id`, `nombre`, `apellido` (de `users.datos_publicos_por_ids` vía `loans`). `null` si `users` no devuelve al usuario. Nunca DNI, email ni teléfono (P6) |
| `estado` | `str` | Estado de la línea en `loans` (`pendiente`, `reservado`, `entregado`, `devuelto`, `cancelado`, `rechazado`, `no_retirado`), tal como lo define SPEC-05. `inventory` no lo reinterpreta |
| `retiro_pactado`, `devolucion_pactada` | `datetime` | — |
| `entregado_en`, `devuelto_en` | `datetime \| null` | `null` hasta que `loans` sume la migración `0012` (Fase 3 de SPEC-05). El contrato no cambia cuando lleguen |
| `observacion_devolucion` | `str \| null` | Ídem |

Si `loans` cambia la firma, falla `tests/inventory/test_historial.py` (es la alarma buscada) y se ajusta este contrato en una revisión del spec antes de tocar el código (AGENTS.md §4). El historial de **reparaciones** por unidad (requisito futuro, ADR-026 b) no entra acá: si se hace, va en otra ruta (D-17).

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

**Fase B:** sin tablas ni columnas nuevas. **Migración de datos `0019_inventory_categorias_base`** (backend PR \#37, 2026-11-11, a pedido del Perfil 2 para la demo; se registra acá en la v1.3.0 porque se mergeó sin pasar por el spec): carga las cinco categorías base (Audio, Cámaras, Iluminación, Notebooks, Trípodes) con `ON CONFLICT DO NOTHING`, y el `downgrade` borra sólo las que siguen intactas y sin equipos. Cuelga de `0017_config_sedes` (D-22 de SPEC-03).

**Fase C:** sin tablas, columnas ni migraciones. El historial de cambios de estado de unidades no se persiste (D-08); el historial de PRE-12 es el de usuarios, que vive en `loans`.

## 8. Frontend (`src/features/inventory/`)

### 8.1 Fase A (implementada)

Catálogo conectado a la API con carga, error, "sin resultados", *debounce* y `AbortSignal`; categoría filtrada en la pantalla; tabla de stock ordenable con unidades desplegables y acciones de estado con confirmación; formulario de alta y edición con selector de sede oculto para `ADMIN_LOCAL` y obligatorio para `SUPERADMIN`; DTOs espejo y `mappers.ts`.

### 8.2 Fase B

- **Detalle del equipo (PRE-01).** Al hacer clic en una tarjeta o fila del catálogo se abre `EquipmentDetailModal` (de `inventory`, sin pantalla nueva en `App.tsx`): imagen, marca y modelo, descripción técnica, reglas de cuidado, botón de video instructivo (si hay `video_url`), locker, tipo (Especial/Común), plazo máximo, "Disponibles hoy" y el **mini-calendario**. Se abre para todos los roles, incluidos los ítems sin unidades disponibles hoy (el calendario lo muestra todo en 0). La prop `onSelect` de `CatalogPage` se elimina (no tiene consumidores).
- **Mini-calendario.** Vista mensual de lunes a domingo, empezando por el mes actual, con flechas para avanzar y retroceder dentro de la ventana `[hoy, hoy + 61 días]` (D-07). Por mes hace **un solo** pedido a `GET /equipamiento/{id}/disponibilidad` con `desde = max(día 1, hoy)` y `hasta = min(último día, hoy + 61)`, cancelable con `AbortSignal`. Cada día muestra: pasado o fuera de ventana (gris, sin dato), libre (verde con la cantidad `unidades_libres`) o sin unidades libres (rojo). Leyenda debajo, aclarando que es orientativo. Estados de carga y error (`ApiError.detail`). El `SUPERADMIN` envía la sede vista (`useSede()`); si está en "ambas sedes", el calendario pide elegir una.
- **Botón "Agregar al pedido" (C11, D-12).** `inventory` **no importa nada de `loans`**. `CatalogPage` sigue exponiendo `onAddToCart?: (eq: Equipment) => void`; la tarjeta, la fila de la lista y el detalle muestran el botón sólo si se recibió `onAddToCart` y el rol es estudiante o docente. Está **deshabilitado** si el ítem no está activo, está en mantenimiento o `cantidad_disponible = 0` (con RN-I14, sin unidades disponibles hoy no hay ninguna fecha libre), con un `title` que explica el motivo. Al pulsarlo llama a `onAddToCart(eq)` y muestra "Agregado" un par de segundos. Quién conecta el *callback* con el carrito es el Perfil 3, en `App.tsx` (con la conformidad del Perfil 1), por ejemplo `onAddToCart={(eq) => carrito.agregar(eq)}`. Si el pedido falla por fechas sin unidades, el `409 EQUIPAMIENTO_NO_DISPONIBLE` lo muestra la pantalla de `loans` (F1.7 de SPEC-05).
- **Rótulo.** "Disponibles" pasa a "Disponibles hoy" en tarjetas, lista y detalle (C16). La tabla de stock de los admins no cambia.

### 8.3 Fase C

- **Historial por unidad (PRE-12).** En `UnidadesRow` (Control de Stock, vista por equipo), un botón "Historial" por unidad abre `HistorialUnidadModal` (sobre `components/ui/Modal`) con el código de inventario en el título y la lista de §5.5: solicitante ("Nombre Apellido", o "—" si viene `null`), retiro y devolución pactados, entregado y devuelto ("—" mientras `loans` no los complete), estado de la línea como chip y observación de la devolución. Pide 20 por página y muestra "Cargar más" mientras la última página venga completa. Estados de carga, error (`ApiError.detail`) y vacío ("Esta unidad todavía no se prestó"). La vista por locker (M-03 de SPEC-10, MOMENTÁNEA) no suma el botón.
- **Reservas afectadas (PRE-17).** `useGestion.cambiarEstado` lee la respuesta del `PATCH`. Si `reservas_afectadas > 0`, Control de Stock muestra un aviso persistente (se cierra a mano, no desaparece solo) arriba de la tabla: "La unidad CAM-S-01 tenía N reservas aprobadas (órdenes #12, #15). Resolvelas con una cancelación forzada en la Bandeja de Validaciones." Sin enlace hasta que exista la cancelación forzada del Perfil 3 (Fase 3 de SPEC-05). La confirmación previa de mantenimiento y baja (PRE-14) no cambia.
- **Tipos.** `MovimientoUnidadDTO`, `SolicitanteResumenDTO` y `UnidadEstadoDTO` espejo de §5.3 y §5.5; `listarHistorialUnidad(id, {limit, offset}, signal)` en `inventoryApi.ts`. `inventory` no importa nada de `loans` (D-12): el texto de los estados de línea vive en `inventory`.

### 8.4 Unidades fuera de servicio en el stock (addendum v1.3.1, `APROBADO`)

PRE-14 conserva las unidades dadas de baja "para no perder su historial", así que no se borran (D-03, P7.3). Lo que cambia es cómo se muestran en Control de Stock, vista por equipo (`UnidadesRow`), para que no queden mezcladas con las que están en uso (D-19). Es sólo presentación: no cambia la API, los datos ni las reglas de §5.3.

- **Agrupadas aparte.** Al desplegar un equipo, cada sede muestra primero sus unidades en uso (`disponible`, `prestado`, `mantenimiento`). Las unidades en `baja` van debajo, en una línea plegada "Fuera de servicio (N)", **cerrada por defecto**, que se abre y se cierra al tocarla (`aria-expanded`). Abierta, cada unidad muestra el código, la serie, el locker, el chip "Fuera de servicio" y el botón "Historial"; sigue sin acciones de estado (la baja es definitiva).
- **Sin unidades en uso.** Si en una sede todas las unidades están dadas de baja, en lugar de la lista vacía aparece "Ninguna unidad en uso en esta sede", y debajo la línea plegada.
- **Columna "Disponibles" de la tabla.** Si el equipo no tiene ninguna unidad activa (todas en `baja`, `cantidad_total = 0`) pero sí tuvo unidades, muestra "Sin unidades en uso" en lugar de "0 de 0" y sin barra. Un equipo sin ninguna unidad cargada sigue como hoy.
- **Resumen.** La cabecera de las unidades ("6 unidades · 5 disponibles · 1 fuera de servicio") no cambia.
- **Sugerencia al administrador.** Cuando un equipo queda sin unidades en uso, la fila desplegada agrega: "Todas las unidades están fuera de servicio. Si el equipo no vuelve a usarse, dalo de baja con el botón de la papelera para sacarlo del catálogo." Es sólo texto: dar de baja el equipo sigue siendo la acción de RN-I5, con su confirmación.
- **Fuera de alcance.** La vista por locker (M-03 de SPEC-10, MOMENTÁNEA) queda como está.

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

### 9.3 Fase C

| ID | Criterio | Req. |
| :---- | :---- | :---- |
| INV-34 | `GET /unidades/{id}/historial`: admin con jurisdicción → `200` con las líneas de la unidad en cualquier estado, del más reciente al más antiguo, con `orden_id`, `detalle_id`, solicitante (`id`, `nombre`, `apellido`) y `entregado_en`, `devuelto_en`, `observacion_devolucion` en `null`; `limit` y `offset` paginan (sin solapamientos entre páginas); `limit` 0 o 101 → `422`; unidad sin líneas → `200 []`; `ADMIN_LOCAL` de la otra sede o unidad inexistente → `404`; estudiante o docente → `403`; sin token → `401`; ninguna respuesta incluye DNI, email ni teléfono (buscar en `response.text`) | PRE-12, P5, P6 |
| INV-35 | `PATCH /unidades/{id}/estado` a `mantenimiento` o `baja` devuelve `reservas_afectadas` y `ordenes_afectadas` según §5.3: cuenta sólo líneas `reservado` con retiro futuro (no `entregado`, `pendiente`, `cancelado` ni las de retiro pasado); `mantenimiento → baja` vuelve a contarlas; a `disponible` o idempotente → `null`; sin reservas → `0` y `[]`; el cambio de estado queda hecho aunque haya reservas; los tests de INV-18, 19 y 21 siguen en verde | PRE-14, PRE-17 |
| INV-37 | Frontend (addendum v1.3.1, §8.4): al desplegar un equipo, las unidades en `baja` aparecen debajo de las que están en uso, en una línea "Fuera de servicio (N)" cerrada por defecto que se abre y se cierra; abiertas muestran "Historial" y ninguna acción de estado; con todas las unidades en `baja`, la tabla dice "Sin unidades en uso" en lugar de "0 de 0" y la fila desplegada sugiere dar de baja el equipo; un equipo sin unidades cargadas no cambia | PRE-12, PRE-14 |
| INV-36 | Frontend: el botón "Historial" abre el modal con la lista, "Cargar más" pide la página siguiente y se oculta con una página incompleta, muestra "—" en los campos `null` y los errores de la API; el aviso de reservas afectadas aparece sólo con `reservas_afectadas > 0`, nombra las órdenes y queda hasta que el admin lo cierra | PRE-12, PRE-17 |

Verificación del frontend: `npm run typecheck`, `npm run build`, `npm test` (Vitest para las funciones puras) y un recorrido manual de INV-32 e INV-33 contra el backend local.

## 10. Coordinación con otros perfiles

| Para | Pedido | Motivo | Estado |
| :---- | :---- | :---- | :---- |
| Perfil 1 | **Aprobar la v1.3.0** (Fase C: §5.3, §5.5, §8.3, §9.3 y D-15…D-18) | AGENTS.md §4 | Cerrado: aprobada el 2026-11-25, con D-16 (`ordenes_afectadas`) |
| Perfil 1 | Aprobación de la v1.2.0 (Fase B y addendum §6.1) | AGENTS.md §4 | Cerrado (2026-11-07, Docs `0af866d`) |
| Perfil 1 | **Se retira el pedido de la ventana del calendario** (D-07): es un tope técnico de la consulta, no una regla del reglamento | P8 | Cerrado con la v1.2.0; se cierra el ítem del 2026-10-23 de `MEMORY.md` §5 |
| Perfil 1 | Conformidad para que el Perfil 3 pase `onAddToCart` a `CatalogPage` en `App.tsx` (una línea) | C11, D-12 | Cerrado: cableado en `develop` |
| Perfil 1 | El `CHECK` 1–15 de `max_dias_prestamo` sigue fijo (D-05) | P8 | Abierto (sin cambios) |
| Perfil 1 | **Importación desde CSV o Excel descartada** (D-15): no está en el ERS; la carga del piloto usa el alta de PRE-19 | AGENTS.md §4, P10 | Cerrado: confirmado por el Perfil 1 (2026-11-23) |
| Perfil 1 | **Aval U1 de SPEC-10, con dos correcciones** en los cambios locales de la entrega 2: (a) `EquipmentDetailModal` importa `REGLAMENTO_USO` de `loans/components/TerminosPrestamo` (contra D-12) y lo filtra por el comienzo del texto; mover el texto a un lugar compartido o recibirlo por prop; (b) `MiniCalendario` quita la leyenda "Orientativo: la confirmación llega al enviar el pedido", que piden §8.2 y RN-I15 | D-12, RN-I15 | Abierto |
| Perfil 3 | `bloquear_unidad` es API pública con el contrato de §6.2 (C14) y `marcar_unidad_mantenimiento` está en `develop` (C17, PR \#24): destraba AC-L59 | RN-L11, RN-L20 | Cerrado (en `develop` desde el 2026-11-08) |
| Perfil 3 | El carrito recibe un `Equipment` de `inventory` por el *callback* `onAddToCart`; `inventory` no importa `loans` (D-12) | C11 | Cerrado (`App.tsx` en `develop`) |
| Perfil 3 | C16 y C18 respondidos (RN-I4, RN-I13, RN-I14); D-13 explica por qué no se cambia `max_dias_prestamo` a nulo | SPEC-05 §16 | Cerrado con la v1.2.0 |
| Perfil 3 | Publicar `historial_de_unidad` y `reservas_futuras_de_unidad` | PRE-12, PRE-17 | Cerrado (PR \#23); la Fase C las usa con sus firmas reales |
| Perfil 3 | **Q1 respondida** (D-18): alcanza con cruzar los ids de `unidades-libres` con el stock, como ya hace `etiquetasDelStock`; no hace falta `datos_unidades_por_ids`. Cerrar Q1 en el plan de SPEC-05 | SPEC-05 plan §Q1 | Cerrado por el Perfil 2; falta el cierre en SPEC-05 (Perfil 3) |
| Perfil 3 | `ordenes_afectadas` (§5.3) le da a la cancelación forzada (CU-L06) las órdenes a resolver; si su pantalla agrega un enlace por orden, el aviso de §8.3 lo usa | PRE-17 | Informativo |
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
- **Mantenimiento con reservas:** la unidad pasa a `mantenimiento` igual; la entrega de esas reservas fallará con `409` en `loans` hasta que el admin las resuelva (PRE-17). En la Fase C el admin lo ve en `reservas_afectadas` y `ordenes_afectadas`.
- **Reserva con retiro ya vencido y sin entregar** (línea `reservado` con `retiro_pactado` pasado): no cuenta en `reservas_afectadas`, porque `reservas_futuras_de_unidad` sólo trae retiros desde ahora. Su cierre como `no_retirado` es de `loans` (Fase 3 de SPEC-05).
- **Dos reservas de la misma orden sobre la unidad:** no ocurre, porque las líneas de una orden comparten período y el `EXCLUDE` de `loans` impide asignar dos veces la misma unidad en períodos solapados. Igual, `reservas_afectadas` cuenta líneas y `ordenes_afectadas` no repite órdenes.
- **Historial de una unidad dada de baja:** se sigue viendo (P7.3: la unidad se conserva para no perder su historial, PRE-14).
- **Historial de una unidad que cambió de sede:** no puede pasar (la sede de una unidad no se edita, §5.3).

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
| D-15 | ¿Importar el inventario real desde CSV o Excel? | **Fuera de alcance (v1.3.0; decisión del Perfil 2, confirmada por el Perfil 1 el 2026-11-23).** Ningún requisito ni caso de uso del ERS lo pide (PRE-19 describe el alta individual) y sin spec aprobado no se escribe código (AGENTS.md §4). La carga del piloto se hace con el alta existente, que admite varias unidades por equipo. Si el laboratorio lo necesita, el Perfil 1 lo suma al ERS y se especifica aparte |
| D-16 | ¿`reservas_afectadas` sólo cuenta o también identifica las reservas? | **Aprobada con la v1.3.0 (2026-11-25):** cantidad **y** `ordenes_afectadas` (ids de orden), porque el admin necesita saber qué órdenes resolver con la cancelación forzada y esos ids ya los ve en su bandeja (sin datos personales). Alternativa: sólo la cantidad, como decía la v1.2.0; obliga al admin a buscar las órdenes a mano |
| D-17 | ¿El historial de la Fase C cubre las reparaciones (ADR-026 b)? | **No.** `GET /unidades/{id}/historial` es el historial **de usuarios** de PRE-12 y se arma con `loans`. Las reparaciones son un requisito futuro, necesitarían persistir los cambios de estado (hoy no, D-08) e irían en otra ruta (por ejemplo `/unidades/{id}/reparaciones`) y en otra pestaña del mismo modal; nada de esta fase lo impide |
| D-19 | ¿Se pueden borrar las unidades dadas de baja, que "quedan en la nada" en el stock? (observación del Perfil 2 del 2026-11-25 al probar la Fase C) | **No se borran** (PRE-14: la unidad se conserva para no perder su historial; P7.3). **Aprobada con la v1.3.1 (2026-11-25):** mostrarlas plegadas debajo de las unidades en uso y reemplazar "0 de 0" por "Sin unidades en uso" (§8.4). Alternativas descartadas: ocultarlas del todo (se pierde el acceso a su historial desde la pantalla) y un filtro global "Mostrar fuera de servicio" (agrega un control más a la pantalla para algo que se consulta poco) |
| D-18 | Q1 de SPEC-05: ¿función `datos_unidades_por_ids` para mostrar el código de inventario al aprobar? | **No hace falta.** La bandeja del Perfil 3 ya cruza los ids de `unidades-libres` con el stock de admin (`GET /equipamiento`, que trae las unidades con `codigo_inventario` y `locker`), sin consultas extra por unidad. Se reconsidera sólo si el stock de una sede crece tanto que traerlo entero sea lento |

## 13. Trazabilidad

| Requisito | Endpoints (§5) / funciones (§6) | Criterios |
| :---- | :---- | :---- |
| PRE-01 | `GET /equipamiento`, `GET /equipamiento/{id}`, `GET /equipamiento/{id}/disponibilidad` (B) | INV-02, 05, 07, 08, 24, 26, 30, 31, 32, 33 |
| PRE-02 | `GET /equipamiento`, `GET /categorias` | INV-02, 03, 04, 24 |
| PRE-03 (lado del catálogo) | Botón "Agregar al pedido" (B) | INV-31, 33 |
| PRE-12 | `GET /equipamiento`, `GET /unidades`, `PATCH /equipamiento/{id}`, `PATCH /equipamiento/{id}/estado`, `PATCH /unidades/{id}`, `GET /unidades/{id}/historial` (C) | INV-06, 15, 16, 17, 20, 24, 29, 34, 36, 37 |
| PRE-14 | `PATCH /unidades/{id}/estado`, `marcar_unidad_mantenimiento` (B) | INV-18, 19, 21, 22, 28, 35 |
| PRE-17 (aviso al admin) | `reservas_afectadas`, `ordenes_afectadas` (C) | INV-35, 36 |
| PRE-19 | `POST /equipamiento`, `POST /equipamiento/{id}/unidades` | INV-09, 10, 11, 12, 13, 25 |
| DT-20 | §6 | INV-22, 27, 28 |
| DT-22 / DT-23 | Frontend §8.1 / migración `0010` | INV-24 / INV-14, 23 |

## 14. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.3.1 | 2026-11-25 | **`APROBADO`** (OK del Perfil 1, transmitido por el Perfil 2). Fase C implementada el mismo día (backend PR \#50 y frontend PR \#34): INV-34…INV-37 con tests; backend 1041 tests en verde y cobertura de `inventory` 99 %; frontend 278 tests. Redactado por el Perfil 2, con asistencia de IA. Addendum de presentación: §8.4 (unidades fuera de servicio plegadas en el stock y "Sin unidades en uso"), INV-37 y D-19. No cambia la API ni los datos |
| 1.3.0 | 2026-11-25 | **`APROBADO`** para la Fase C (OK del Perfil 1, transmitido por el Perfil 2), con D-15…D-18 tal como están; el cierre de la Fase B (B-22) quedó mergeado el 2026-11-24 (backend PR \#46, frontend PR \#33) |
| 1.3.0 | 2026-11-23 | `BORRADOR` (Perfil 2, con asistencia de IA, Docs PR \#48). Fase C desbloqueada y ajustada a las firmas reales de `loans` (backend PR \#23, tarea C-01): §5.3 con `ordenes_afectadas` (D-16) y reglas de cuándo se calcula; §5.5 con `detalle_id`, paginación en `loans`, doble control de sede y campos `null` hasta la `0012` de `loans`; §8.3 detallado; INV-34 e INV-35 precisados e INV-36 nuevo (frontend). Fase B marcada `IMPLEMENTADO` con tres pendientes de cierre (B-22). §3 al día con `develop`; §7 registra la `0019`; §10 cierra lo resuelto y suma el aval U1 de SPEC-10 con dos correcciones; nuevas D-15 (importación por CSV fuera de alcance), D-17 (reparaciones, ADR-026 b) y D-18 (Q1 de SPEC-05) |
| 1.2.0 | 2026-11-07 | **`APROBADO` para la Fase B** (OK del Perfil 1, Docs `0af866d`); la Fase C quedó en `BORRADOR`. Redactada por el Perfil 2, con asistencia de IA. Planifica todo lo que queda: Fase B (disponibilidad por fechas con `loans.ocupacion_de_unidades`, detalle con mini-calendario, botón "Agregar al pedido", C14, C17, C16, C18) y Fase C (historial y `reservas_afectadas`, bloqueada por `loans`). Somete a aprobación el addendum v1.1.0 (§6.1). Nuevas RN-I13…RN-I16, INV-26 redefinido e INV-28…INV-35, decisiones D-11…D-14 y propuesta para D-07. Limpieza: encabezado y nota de numeración, §3 al día con `develop`, tabla de §12 corregida |
| 1.1.0 | 2026-11-06 | `BORRADOR` (addendum §6.1): `datos_equipamiento_por_ids` a pedido del Perfil 3 (C8 de SPEC-05). El código se escribió antes de redactar el addendum, a pedido explícito del usuario, y se mergeó en `develop` (PR \#19). Queda incluido en la v1.2.0 |
| 1.0.1 | 2026-10-23 | Fase A implementada. §8: la categoría se filtra en la pantalla, no en la API. Se agregan en el frontend el alta y edición de unidades desde la tabla de stock. Hallazgo en la migración `0010`: `NAMING_CONVENTION` duplica el prefijo de los `CHECK` en bases creadas con Alembic; la migración usa SQL directo y tolera ambos nombres (DT-26) |
| 1.0.0 | 2026-10-23 | Aprobado con todas las recomendaciones de §12. Se agrega `equipamientos.es_notebook` (D-05) y se corrige §3 |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
