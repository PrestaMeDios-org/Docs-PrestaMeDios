# SPEC-05 — Préstamos de equipamiento y notebooks (`loans`)

> **Estado:** `APROBADO` (v1.0.0); las v1.0.1 (EC-L10) y v1.0.2 (aval) esperan el OK del Perfil 1 · **Versión:** 1.0.2 · **Fecha:** 2026-11-10 · **Perfil:** 3 (Préstamos y concurrencia)
> **Requisitos:** PRE-03…PRE-11, PRE-13, PRE-15…PRE-18, PRE-20 (`docs/ERS.md` del repo `Docs-PrestaMeDios`, Subsistema 2, módulos 2, 3 y 4, incluida la Iteración 5)
> **Depende de:** SPEC-01 (`core`, autenticación), SPEC-02 (alcance de sede, `config`), SPEC-03 (`users.datos_publicos_por_ids`, `files` para el aval, horario por sede K10) y SPEC-04 (`inventory/service.py`)
> **Constitución:** v1.1.0, con la enmienda 1.1.1 propuesta (ADR-019) · **Plan y tareas:** `plan.md` y `tasks.md` en esta misma carpeta (Fase 1)


---

## 0. Supuestos a verificar antes de aprobar

Este spec se redactó leyendo `constitution.md`, `AGENTS.md`, `perfiles.md`, `MEMORY.md`, `docs/ERS.md` y el código de `origin/develop`. Los supuestos quedaron verificados contra el código:

| # | Supuesto | Fuente | Dónde se confirma |
| :---- | :---- | :---- | :---- |
| S1 | **Verificado** en `app/core/deps.py`: `get_current_user`, `require_roles(RolUsuario...)` (devuelve el `Usuario`), `resolver_alcance_sede(...)` y `sede_para_alta(...)` | `app/core/deps.py` | — |
| S2 | **Verificado** en `app/core/errors.py`: `AppError(status_code, code, detail, *, headers=None, **extra)` responde `{detail, code, ...extra}`; `ErrorNegocio` es el esquema OpenAPI y `error_responses(*codes)` declara las respuestas para `responses=` (admite 401, 403, 404, 409 y 422) | `app/core/errors.py` | — |
| S3 | **Verificado** en `config/service.py`: `obtener_parametro(db, clave) -> int | float | bool | str | time` (`HORA` se devuelve como `datetime.time`); una clave inexistente responde `500 PARAMETRO_NO_CONFIGURADO`. Las claves `horario.apertura`, `horario.cierre`, `prestamo.general.max_dias`, `prestamo.notebook.max_dias`, `solicitud.anticipacion_min_horas` y `prestamo.tolerancia_retiro_horas` figuran en `config/seed.py`. `config` valida que el plazo general no supere el de notebooks y que apertura sea anterior a cierre | `config/service.py`, `config/seed.py` | —. El horario pasa a ser **por sede** (ADR-022 a): las claves de `config` van a cambiar (SPEC-03 K10) |
| S4 | **Verificado** en `inventory/service.py` de `origin/develop` (73fb4b9): `unidades_asignables(db, equipamiento_id, sede) -> list[int]`, `unidad_es_asignable(db, unidad_id, sede) -> bool`, `marcar_unidad_prestada(db, unidad_id)` y `liberar_unidad(db, unidad_id)`. Ninguna hace `commit`. Las dos primeras solo consideran unidades `disponible` **hoy** de ítems activos, que es el criterio buscado: una unidad `prestado` no se promete hasta que se devuelva (ver §10.1) | `inventory/service.py` | — |
| S5 | **Verificado** en `inventory/models.py`: `Equipamiento` tiene `es_notebook`, `alta_gama`, `max_dias_prestamo` y `activo` | `inventory/models.py` | — |
| S6 | **Verificado** en `app/core/settings.py`: `ahora_lab()` y `ZONA_HORARIA_LAB` (ambas sedes comparten zona) | `app/core/settings.py` | — |
| S7 | Los tests de integración crean el esquema con `create_all` y una sesión por request (ADR-013); la migración se valida aparte | `MEMORY.md` ADR-013 | `tests/conftest.py` |

> **Nota de nombres (inventory):** `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada` y `liberar_unidad` están confirmadas por el código de `origin/develop` (73fb4b9) y por `MEMORY.md` (2026-10-23, Perfil 2 → Perfil 3, SPEC-04 §6); `bloquear_unidad` también figura en el servicio. Los nombres `unidades_disponibles` y `marcar_unidad_devuelta` que se citaron después no existen. Según SPEC-04 D-02, un administrador ya no puede poner `prestado` por la API: solo `loans`, mediante `marcar_unidad_prestada`.

---

## 1. Alcance

### 1.1 Incluye

1. **Orden de pedido unificada**, simple (un ítem desde el catálogo) o por carrito, con fechas y horas de retiro y devolución, asignatura y aceptación de la normativa (PRE-03, PRE-04, PRE-06, PRE-07, PRE-09).
2. **Validación de plazos** (4 días general, 15 notebooks), de la franja operativa y de la anticipación mínima, leídas de `config` (PRE-06, PRE-07, P8).
3. **Bandeja administrativa** con jurisdicción por sede, **aprobación con asignación de unidad**, rechazo y ajuste horario (PRE-10, PRE-15, PRE-18).
4. **Cancelación** por el solicitante (pendiente) y por el administrador (aprobada), y **cancelación forzada** por línea (PRE-17).
5. **Entrega y devolución** en mostrador, con observaciones del estado físico y alerta de demora (PRE-13).
6. **Renovación de notebooks** como nueva solicitud emitida en el mostrador (PRE-11, ADR-022 h).
7. **Cancelación automática por no retiro** (PRE-08).
8. **Calendario maestro** de operaciones (PRE-16) y **panel de observación docente** (PRE-20).
9. **Funciones públicas de lectura** que necesitan otros perfiles (§10.2).
10. **Saneamiento de la deuda** DT-16…DT-20 (§3).
11. **Frontend** de `loans` (§11).

### 1.2 No incluye

- Catálogo y stock (PRE-01, PRE-02, PRE-12, PRE-14, PRE-19): Perfil 2. `loans` consume su servicio y publica funciones de lectura para su Fase B.
- Usuarios, sanciones y chips de comportamiento (USR-09): Perfil 1.
- Notificaciones (NOV-xx): Perfil 5. Este spec define los eventos que `loans` emite (§10.3), no el módulo.
- Catálogo de asignaturas: no tiene dueño definido (§16, C3). Bloquea parcialmente PRE-03 y PRE-20. El almacenamiento de archivos para el aval lo provee SPEC-03 (C4).
- Reasignación de unidad de una línea ya aprobada (se anota en EC-L06 como trabajo futuro).

---

## 2. Estado actual del módulo (en `develop`)

| Artefacto | Contenido | Observación |
| :---- | :---- | :---- |
| `loans/enums.py` | `EstadoOrdenEnum` (`pendiente`, `aprobada`, `rechazada`, `cancelada`), `EstadoDetalleEnum` (`pendiente`, `reservado`, `entregado`, `devuelto`, `rechazado`, `no_retirado`, `cancelado`), `ESTADOS_DETALLE_QUE_OCUPAN` | Valores en minúsculas, como `inventory` (DT-19) |
| `loans/schemas.py` | `OrdenPedidoCreate` (`asignatura_id` opcional, `retiro`, `devolucion`, `items[{equipamiento_id}]`, `acepta_normativa: Literal[True]`), `OrdenPedidoResponse` (con `demorado` derivado), `DetallePrestamoCreate/Response`, `AsignacionUnidad` y `OrdenPedidoEstadoUpdate` (reemplaza a `OrdenPedidoResolucion` y `OrdenPedidoCancelacion`) | Se eliminaron `ErrorConflictoReserva` y `ErrorLimiteDias` (DT-18). `OrdenPedidoCreate` no valida franja ni tope de días: pasan al servicio (P8) |
| `loans/models.py` | `OrdenPedido` y `DetallePrestamo`; columna generada `periodo = tstzrange(retiro_pactado, fin_ocupacion, '[)')`; `ExcludeConstraint` sobre `(unidad_fisica_id, periodo)` para `reservado` y `entregado`; tres `CHECK` | FK real a `usuarios`, `equipamientos` y `unidades_fisicas` |
| Migración `0009_loans_init` | Crea las dos tablas, los enums `estado_orden_enum` y `estado_detalle_enum`, la extensión `btree_gist` y la restricción | Los `CHECK` usan nombres cortos, así que el nombre final es igual con Alembic y con `create_all` (relevante para DT-26) |
| `loans/router.py` | Cinco rutas en `/api/v1/loans`: `POST /ordenes`, `GET /ordenes/mias`, `GET /ordenes`, `GET /ordenes/{id}` y `PATCH /ordenes/{id}/estado` | Exigen sesión y rol (`get_current_user`, `require_roles`), documentan errores con `error_responses` y responden `501 NO_IMPLEMENTADO` (PR #16). Montado en `main.py` con tag "Préstamos y Solicitudes" |
| `loans/dependencies.py` | **Eliminado** en el PR #16 | Resuelve DT-17 |
| `loans/service.py`, frontend | **No existen** (el frontend es un `.gitkeep`) | |
| `tests/loans/` | Contrato HTTP (401, 403 por rol, 501) y esquemas Pydantic (PR #16); la suite completa quedó en 370 tests en verde | |

**Garantía de integridad ya vigente y probada en una base real:** dos líneas `reservado` o `entregado` de la misma unidad con períodos solapados no pueden coexistir; una línea `pendiente` no ocupa; devolver y retirar en el mismo instante no choca; una línea que ocupa debe tener unidad asignada. Es la garantía definitiva de no superposición (D-L17 descartada, §15.3).

---

## 3. Deuda técnica que resuelve este spec

| ID | Descripción (`MEMORY.md` §4) | Resolución |
| :---- | :---- | :---- |
| **DT-16** | `loans` está en `develop` sin spec | Este documento. Pasa a `APROBADO` antes de escribir código de aplicación |
| **DT-17** | `dependencies.py` es un placeholder, define un `RolEnum` propio y los endpoints responden 500 sin exigir sesión | Se **elimina** `loans/dependencies.py`. Todos los endpoints usan `Depends(get_current_user)` o `Depends(require_roles(RolUsuario...))`; la jurisdicción usa `resolver_alcance_sede`. Los roles son `RolUsuario` (`SUPERADMIN`, `ADMIN_LOCAL`, `DOCENTE`, `ESTUDIANTE`). El solicitante y la sede salen siempre del token. **Fase 0:** hasta que exista el servicio, los endpoints exigen sesión y responden `501 NO_IMPLEMENTADO` mediante `AppError` (D-L14) **Hecho en el PR #16.** |
| **DT-18** | Errores como `{codigo, detalle}` con `HTTPException` | Todos los errores de negocio usan `AppError(status, "CODIGO", "mensaje")` → `{detail, code}` (§6.3). Se eliminan `ErrorConflictoReserva` y `ErrorLimiteDias`. Los errores de validación de Pydantic conservan el 422 estándar. La documentación OpenAPI usa `error_responses(...)` y `ErrorNegocio` de `core.errors`, sin esquemas de error propios **Hecho en el PR #16.** |
| **DT-19** | Tres estilos de valores de enum | **No se unifica en este spec** (requiere decisión del equipo). `loans` mantiene minúsculas, como `inventory`. Los enums están aislados en `enums.py`, de modo que una unificación futura es una migración acotada (D-L11) |
| **DT-20** | Estado de la unidad duplicado entre `inventory` (`prestado`) y `loans` (`entregado`) | `loans` **no escribe** el estado de la unidad: usa `inventory/service.py` (§10.1). Reparto: la **ocupación por fechas** es de `loans` (estado de la línea y `EXCLUDE`); la **condición física** es de `inventory`. `prestado` es un reflejo que `loans` fija al entregar y libera al devolver, en la misma transacción. `loans` solo asigna unidades `disponible` (una unidad `prestado` no se promete ni se entrega hasta que se devuelva). Responde al ítem abierto del 2026-10-23 (Perfil 2 → Perfil 3) de `MEMORY.md` |
| DT-24 (parcial) | `main.py` y el README no describen `loans` | Se actualiza la descripción de `app/main.py` en la Fase 0; el README lo ajusta el Perfil 1 (C6) |
| DT-26 (informativo) | `NAMING_CONVENTION` duplica el prefijo de los `CHECK` en migraciones | `0009` ya usa nombres cortos; las migraciones `0011` y `0012` seguirán el mismo criterio |

---

## 4. Actores y permisos

| Acción | `ESTUDIANTE` | `DOCENTE` | `ADMIN_LOCAL` | `SUPERADMIN` |
| :---- | :---- | :---- | :---- | :---- |
| Consultar reglas operativas | Sí | Sí | Sí | Sí |
| Crear orden | Sí | Sí (uso de cátedra) | No | No (D-L06) |
| Ver sus órdenes | Sí | Sí | — | — |
| Cancelar orden propia `pendiente` | Sí | Sí | — | — |
| Bandeja y detalle de órdenes de la sede | No | No | Sí (su sede) | Sí (ambas) |
| Aprobar, rechazar, ajustar horario | No | No | Sí (su sede) | Sí |
| Cancelar orden `aprobada` y cancelación forzada | No | No | Sí (su sede) | Sí |
| Entregar, devolver y aprobar renovaciones | No | No | Sí (su sede) | Sí |
| Calendario maestro | No | No | Sí (su sede) | Sí |
| Panel docente y observación | No | Sí (sus asignaturas) | No | No |

Todos los endpoints requieren sesión (P4.1). Fuera de alcance de sede o de propiedad responde `404` (§4.2 de la Constitución), nunca `403`, para no revelar existencia.

---

## 5. Casos de uso

| ID | Caso de uso | Actor | Requisitos | Resumen del flujo |
| :---- | :---- | :---- | :---- | :---- |
| CU-L01 | Solicitar equipamiento | Estudiante, Docente | PRE-03, 04, 06, 07, 09 | Elige ítems (uno o carrito), fecha y hora de retiro y devolución dentro de la franja, asignatura (estudiante), acepta la normativa y envía. La orden queda `pendiente` |
| CU-L02 | Solicitar con alta gama | Estudiante, Docente | PRE-05 | Igual que CU-L01 con aval PDF obligatorio, subido con `files` (SPEC-03) |
| CU-L03 | Cancelar solicitud propia | Estudiante, Docente | — | Cancela una orden `pendiente` |
| CU-L04 | Validar solicitud | Admin | PRE-10, 15, 18 | Abre la bandeja de su sede, revisa (con la observación del docente), opcionalmente ajusta horarios, asigna una unidad por línea y aprueba, o rechaza con motivo |
| CU-L05 | Cancelar orden aprobada | Admin | — | Libera las unidades y registra el motivo |
| CU-L06 | Cancelación forzada | Admin | PRE-17 | Cancela una línea afectada por la baja de una unidad, con motivo obligatorio y aviso al usuario |
| CU-L07 | Entregar | Admin | PRE-13 | Confirma la entrega presencial: línea `entregado` y unidad `prestado` |
| CU-L08 | Recibir devolución | Admin | PRE-13 | Registra la devolución con observaciones: línea `devuelto` y unidad liberada |
| CU-L09 | Renovar notebook | Estudiante (en el mostrador), Admin | PRE-11 | El estudiante presenta la notebook y emite desde la app una nueva solicitud de renovación; el administrador la aprueba o rechaza (ADR-022 h) |
| CU-L10 | Observar solicitudes de mi cátedra | Docente | PRE-20 | Lista de solo lectura de solicitudes de sus asignaturas y comentario |
| CU-L11 | Ver calendario maestro | Admin | PRE-16 | Recursos agrupados en "En Uso" y "En Reserva" |
| CU-L12 | Procesos automáticos | Sistema | PRE-08 | No retiro dentro de la tolerancia (RN-L23) |

---

## 6. Contratos de la API

Base: `/api/v1/loans` · tag "Préstamos y Solicitudes" · todos exigen `Authorization`.

### 6.1 Endpoints

| Método y ruta | Roles | Descripción | Éxito | Errores |
| :---- | :---- | :---- | :---- | :---- |
| `GET /reglas` | todos | Reglas operativas efectivas para el formulario (D-L07) | 200 | 401 |
| `POST /ordenes` | ESTUDIANTE, DOCENTE | Crea la orden `pendiente` con sus líneas | 201 | 401, 403, 404, 409, 422 |
| `GET /ordenes/mias` | ESTUDIANTE, DOCENTE | Órdenes propias (`estado`, `limit`, `offset`) | 200 | 401, 403 |
| `GET /ordenes/docente` | DOCENTE | Panel de observación docente | 200 | 401, 403 |
| `GET /ordenes` | ADMIN_LOCAL, SUPERADMIN | Bandeja (`estado`=`pendiente` por defecto, `sede` solo SUPERADMIN, `limit`, `offset`) | 200 | 401, 403 |
| `GET /ordenes/{orden_id}` | dueño, admin con alcance, docente de la asignatura | Detalle | 200 | 401, 404 |
| `GET /ordenes/{orden_id}/aval` | dueño, admin con alcance | El PDF de aval de la orden (PRE-05), servido con `files.abrir_archivo` y `respuesta_descarga` (RN-61 de SPEC-03). Cualquier otro usuario, incluido el docente de la asignatura, recibe `404` (RN-60 de SPEC-03). Una orden sin aval responde `404 ARCHIVO_NO_ENCONTRADO` | 200 | 401, 404 |
| `PATCH /ordenes/{orden_id}/estado` | ver §4 | Aprobar, rechazar o cancelar | 200 | 401, 403, 404, 409, 422 |
| `GET /ordenes/{orden_id}/unidades-libres` | ADMIN_LOCAL, SUPERADMIN | Por cada línea de la orden, las unidades del modelo en la sede que están `disponible` y sin otra línea `reservado` o `entregado` que se solape con su período, para asignar al aprobar (RN-L10, RN-L12) | 200 | 401, 403, 404 |
| `PATCH /ordenes/{orden_id}/detalles/{detalle_id}/estado` | ADMIN_LOCAL, SUPERADMIN | Entregar, devolver o cancelación forzada | 200 | 401, 403, 404, 409, 422 |
| `PUT /ordenes/{orden_id}/observacion-docente` | DOCENTE | Comentario del docente | 200 | 401, 403, 404, 409, 422 |
| `GET /calendario` | ADMIN_LOCAL, SUPERADMIN | Calendario maestro (`desde`, `hasta`, `sede` solo SUPERADMIN) | 200 | 401, 403, 422 |

Los cambios de estado usan `PATCH /<recurso>/{id}/estado` (Constitución §4.2). Esto **renombra** los actuales `/resolucion` y `/cancelacion` (D-L02); como hoy no responden de forma útil, el cambio no afecta a ningún consumidor. En el router, `/ordenes/mias` y `/ordenes/docente` se declaran **antes** de `/ordenes/{orden_id}`.

### 6.2 Esquemas

| Esquema | Campos | Reglas |
| :---- | :---- | :---- |
| `OrdenPedidoCreate` | `asignatura_id?`, `retiro`, `devolucion`, `items[1..20]{equipamiento_id}`, `acepta_normativa`, `pdf_aval_id?` (alta gama, PRE-05), `renueva_detalle_id?` (renovación, PRE-11) | `extra="forbid"`; `acepta_normativa` debe ser `true`; `devolucion > retiro`. No incluye `solicitante_id`, `sede` ni `estado` |
| `OrdenPedidoEstadoUpdate` | `estado` ∈ {`aprobada`, `rechazada`, `cancelada`}, `motivo?`, `asignaciones[]`, `nuevo_retiro?`, `nueva_devolucion?` | `rechazada` exige `motivo` y no admite asignaciones; `aprobada` exige una asignación por línea y admite el ajuste horario (ambas fechas juntas); `cancelada` por administrador exige `motivo` (lo valida el servicio, depende del rol). Reemplaza a `OrdenPedidoResolucion` y `OrdenPedidoCancelacion` |
| `DetalleEstadoUpdate` | `estado` ∈ {`entregado`, `devuelto`, `cancelado`}, `observacion?` (solo `devuelto`, ≤ 500), `motivo?`, `a_mantenimiento?` (solo `devuelto`) | `cancelado` (forzada) exige `motivo` |
| `ObservacionDocenteUpdate` | `observacion` (1..500) | |
| `ReglasResponse` | `sede`, `horario_apertura`, `horario_cierre`, `anticipacion_min_horas`, `max_dias_general`, `max_dias_notebook`, `tolerancia_retiro_horas` | Valores vigentes de `config` para la **sede del solicitante**; `SUPERADMIN` la indica con `?sede=` (ADR-022 a, K10) |
| `OrdenPedidoResponse` / `DetallePrestamoResponse` | Los actuales, más `entregado_en`, `devuelto_en`, `observacion_devolucion`, `motivo_cancelacion` en el detalle; `resuelto_en`, `situacion` (derivada, RN-L31) y `aval_archivo_id` (el PDF de aval, K3 de SPEC-03; se descarga con `GET /ordenes/{id}/aval`) en la orden. Para administradores y docentes, un resumen del solicitante obtenido con `users.datos_publicos_por_ids` (`id`, `nombre`, `apellido`); **nunca** DNI, email ni teléfono (P6) | `demorado` y `situacion` son derivados |

Todos los campos llevan `Field(..., examples=[...])` y las respuestas de error se documentan en OpenAPI (Constitución §9).

### 6.3 Errores (`AppError` → `{detail, code}`)

| `code` | HTTP | Cuándo |
| :---- | :---- | :---- |
| `NO_IMPLEMENTADO` | 501 | Solo en la Fase 0 |
| `ORDEN_NO_ENCONTRADA` | 404 | Inexistente o fuera de alcance |
| `EQUIPAMIENTO_NO_ENCONTRADO` | 404 | Inexistente, inactivo o sin unidades en la sede |
| `ROL_NO_AUTORIZADO` | 403 | Rol sin permiso para la acción |
| `CANCELACION_NO_PERMITIDA` | 403 | El solicitante intenta cancelar una orden `aprobada` |
| `ASIGNATURA_REQUERIDA` | 422 | Estudiante sin asignatura |
| `FRANJA_FUERA_DE_HORARIO` | 422 | Hora de retiro o devolución fuera del horario de la sede del solicitante |
| `ANTICIPACION_INSUFICIENTE` | 422 | Retiro antes de `ahora + solicitud.anticipacion_min_horas` |
| `LIMITE_DIAS_EXCEDIDO` | 422 | Rango mayor al máximo de alguna línea (incluye `equipamiento_id` y el máximo en el mensaje) |
| `AVAL_REQUERIDO` | 422 | Orden con ítems de alta gama sin `pdf_aval_id` |
| `ARCHIVO_INVALIDO` | 422 | De `files.vincular_archivo`: el aval no existe, es de otro usuario, tiene otro propósito o ya está vinculado a otra orden (un solo código, D-19 de SPEC-03). No se crea la orden |
| `ARCHIVO_NO_ENCONTRADO` | 404 | `GET /ordenes/{id}/aval` de una orden sin aval |
| `RETIRO_VENCIDO` | 422 | Aprobar una orden cuyo retiro ya pasó, sin ajuste horario |
| `ASIGNACIONES_INVALIDAS` | 422 | Faltan, sobran, se repiten o no pertenecen a la orden |
| `UNIDAD_NO_ASIGNABLE` | 422 | Unidad de otra sede o modelo, o en `mantenimiento`/`baja` |
| `MOTIVO_REQUERIDO` | 422 | Rechazo, cancelación por administrador o cancelación forzada sin motivo |
| `RENOVACION_NO_PERMITIDA` | 422 | `renueva_detalle_id` no es una línea `entregado` de una notebook del solicitante |
| `TRANSICION_INVALIDA` | 409 | El estado actual no admite la acción |
| `UNIDAD_NO_DISPONIBLE` | 409 | La base rechazó la asignación: la unidad ya tiene otra línea `reservado` o `entregado` con un período que se solapa (SQLSTATE `23P01` del `EXCLUDE`) |
| `EQUIPAMIENTO_NO_DISPONIBLE` | 409 | No hay unidades libres del modelo en la sede para el período pedido, o el pedido tiene más líneas del modelo que unidades libres |

Los datos adicionales de un error viajan como `**extra` de `AppError` (por ejemplo `equipamiento_id` y `max_dias` en `LIMITE_DIAS_EXCEDIDO`). Las respuestas se declaran en cada ruta con `error_responses(...)`.

Los `401` y `403` por rol los produce `require_roles` con los códigos que defina `core`; `ROL_NO_AUTORIZADO` solo se usa cuando la decisión la toma el servicio.

**Traducción de errores de base:** solo la violación de exclusión (`23P01`) se convierte en `409 UNIDAD_NO_DISPONIBLE`. Las violaciones de `CHECK` (`23514`), de unicidad (`23505`) o de clave foránea (`23503`) no se enmascaran como conflicto: indican un defecto y devuelven 500. No se reutiliza `_commit_or_409` de `inventory`, porque traduce cualquier `IntegrityError` a un mensaje único. Tras el error se hace `rollback`.

---

## 7. Modelo de datos

### 7.1 Existente (migración `0009`)

`ordenes_pedido` (`id`, `solicitante_id` FK `usuarios`, `sede` (`sede_enum`), `asignatura_id`, `estado`, `fecha_solicitud`, `observacion_docente`, `motivo_resolucion`, `es_renovado`) y `detalles_prestamo` (`id`, `orden_id`, `equipamiento_id`, `unidad_fisica_id` nullable, `estado`, `retiro_pactado`, `devolucion_pactada`, `fin_ocupacion`, `periodo` generada), con `ex_detalles_prestamo_sin_solapamiento` y los `CHECK` `rango_pactado`, `fin_ocupacion_valido` y `unidad_si_ocupa`.

### 7.2 Cambios propuestos (migraciones `0011` y `0012`)

| Tabla | Cambio | Motivo |
| :---- | :---- | :---- |
| `ordenes_pedido` | `resuelto_por_id` (FK `usuarios`, `SET NULL`), `resuelto_en` (`timestamptz`) | Quién y cuándo resolvió (aprobó, rechazó o canceló); auditoría (USR-08) |
| `ordenes_pedido` | `aval_archivo_id` (`UUID`, FK `archivos`, `RESTRICT`, nulo) | Qué PDF de `files` es el aval de la orden (RN-L09, AC-L60). `files` solo marca el archivo como vinculado; sin esta columna la orden no podría servir su aval |
| `detalles_prestamo` | `entregado_en`, `devuelto_en` (`timestamptz`, nulos) | Registro de entrega y devolución (PRE-13) |
| `detalles_prestamo` | `observacion_devolucion` (`String(500)`, nula) | Estado físico al devolver; alimenta el historial de la unidad (PRE-12, PRE-13) |
| `detalles_prestamo` | `motivo_cancelacion` (`String(500)`, nula) | Cancelación forzada (PRE-17) |
| `detalles_prestamo` | `CHECK` `entrega_registrada` (`estado <> 'entregado' OR entregado_en IS NOT NULL`) y `devolucion_registrada` (`estado <> 'devuelto' OR (entregado_en IS NOT NULL AND devuelto_en IS NOT NULL)`) | Coherencia en la base (P7.1) |
| `ordenes_historial_estado` (nueva) | `id` (`BigInteger`, `Identity`), `orden_id` (FK, `CASCADE`), `estado_anterior?`, `estado_nuevo`, `motivo?`, `actor_id` (FK `usuarios`, `SET NULL`), `created_at`; índice `(orden_id, created_at)` | Traza inmutable de transiciones, igual que `usuarios_historial_estado` (P7.3, D-L10) |

Reparto: `0011_loans_resolucion` (Fase 2) lleva `resuelto_por_id`, `resuelto_en` y `ordenes_historial_estado`; `0012_loans_ciclo_entrega` (Fase 3) lleva las columnas y los `CHECK` de entrega, devolución y cancelación forzada. `0016_loans_aval` (T1.12) lleva `aval_archivo_id`: no entró en la `0011` porque `files` llegó después de mergearla. Cadena vigente: `0010` → `0013` (SPEC-06) → `0011` → `0014`, `0015` (SPEC-03) → `0016` (C19). **La numeración se acuerda con el Perfil 1 antes de abrir cada PR**. Los `CHECK` usan nombres cortos. Cada migración tiene `downgrade` y se valida con upgrade → downgrade → upgrade (P7.4).

---

## 8. Estados y transiciones

### 8.1 Orden

| Desde | Hacia | Quién | Efecto sobre las líneas |
| :---- | :---- | :---- | :---- |
| `pendiente` | `aprobada` | ADMIN_LOCAL (su sede), SUPERADMIN | `pendiente` → `reservado`, con unidad asignada |
| `pendiente` | `rechazada` | ADMIN_LOCAL, SUPERADMIN | → `rechazado` |
| `pendiente` | `cancelada` | Solicitante (dueño) | → `cancelado` |
| `aprobada` | `cancelada` | ADMIN_LOCAL, SUPERADMIN (sin líneas `entregado`) | `reservado` → `cancelado` |
| `aprobada` | `cancelada` | Sistema (RN-L23) | Todas en `no_retirado` |
| `rechazada`, `cancelada` | — | — | Estados finales |

Una orden `aprobada` no tiene estado final propio: el avance lo muestran las líneas.

### 8.2 Línea

| Desde | Hacia | Quién / cuándo |
| :---- | :---- | :---- |
| `pendiente` | `reservado` / `rechazado` / `cancelado` | Con la orden (§8.1) |
| `reservado` | `entregado` | Administrador, en el mostrador |
| `reservado` | `cancelado` | Cancelación de la orden o forzada (PRE-17) |
| `reservado` | `no_retirado` | Sistema, vencida la tolerancia |
| `entregado` | `devuelto` | Administrador, al recibir |

### 8.3 Ocupación de la unidad

| Estado de la línea | Ocupa la unidad (entra en el `EXCLUDE`) |
| :---- | :---- |
| `reservado`, `entregado` | **Sí** |
| `pendiente`, `devuelto`, `rechazado`, `no_retirado`, `cancelado` | No |

---

## 9. Reglas de negocio

| ID | Regla |
| :---- | :---- |
| RN-L01 | La orden pertenece a la sede del solicitante, tomada de la sesión (P5). Nunca se acepta sede ni solicitante en el body |
| RN-L02 | Solo `ESTUDIANTE` y `DOCENTE` crean órdenes: el `SUPERADMIN` no tiene sede (D-L06) y el `ADMIN_LOCAL` no solicita equipamiento, solo valida |
| RN-L03 | La orden nace `pendiente`, con líneas `pendiente` y sin unidad. **Una línea pendiente no ocupa ninguna unidad**, así que varias órdenes pendientes pueden pedir el mismo modelo y período |
| RN-L04 | Franja operativa: la hora de retiro y la de devolución están entre la apertura y el cierre **de la sede del solicitante** (inclusive), en la zona horaria del laboratorio (PRE-06, R4, ADR-022 a). Hoy se leen `horario.apertura` y `horario.cierre` globales; cuando `config` publique las claves por sede (SPEC-03 K10) se cambia la lectura, no la regla |
| RN-L05 | Anticipación: `retiro ≥ ahora_lab() + solicitud.anticipacion_min_horas` (ADR-011) |
| RN-L06 | Plazo máximo por línea = el menor entre el parámetro del tipo (`prestamo.notebook.max_dias` si `es_notebook`, si no `prestamo.general.max_dias`) y `max_dias_prestamo` del ítem. Se cuenta en días corridos incluyendo el día de retiro y el de devolución. La orden debe cumplir el límite de **cada** línea (D-L03, D-L04). Ver C18 sobre cómo `inventory` fija `max_dias_prestamo` |
| RN-L07 | Asignatura obligatoria para `ESTUDIANTE`; el `DOCENTE` solicita para uso de cátedra (PRE-03, PRE-09) |
| RN-L08 | Debe aceptarse la normativa (PRE-03) |
| RN-L09 | Los ítems de alta gama requieren aval PDF (PRE-05). Lo suben estudiantes y docentes con `POST /api/v1/files/archivos` (`proposito=AVAL_PRESTAMO`) y la orden lo referencia con `pdf_aval_id`. El servicio llama a `vincular_archivo(db, archivo_id, *, propietario_id, proposito)` sin `commit`, **en la misma transacción** que crea la orden. La orden guarda el id en `aval_archivo_id`; si la creación falla, el archivo no queda vinculado. Lo descargan el solicitante y los administradores con jurisdicción con `GET /ordenes/{id}/aval`, no el docente de la asignatura (SPEC-03 RN-60, D-18). Sin aval: `422 AVAL_REQUERIDO`. Si la orden no tiene ítems de alta gama, `pdf_aval_id` se ignora: no se vincula ni se guarda, y `files` limpia el archivo huérfano |
| RN-L10 | Cada `equipamiento_id` debe existir, estar activo y tener, **para el período pedido**, al menos una unidad libre en la sede del solicitante. Unidad libre = figura en `unidades_asignables(db, equipamiento_id, sede)` (`disponible` en el estante: una unidad prestada no se promete hasta que vuelva) **y** no tiene ninguna línea `reservado` o `entregado` cuyo período se solape con `[retiro, devolucion)`. Si el pedido trae varias líneas del mismo modelo, las unidades libres deben alcanzar. Si no, `409 EQUIPAMIENTO_NO_DISPONIBLE`. Las líneas `pendiente` no cuentan. Es una verificación previa (P7.2): la garantía final es el `EXCLUDE` al aprobar. El solicitante no elige unidades |
| RN-L11 | Toda aprobación es manual (R1). Se asigna **una unidad por línea**, que debe ser de la sede, del modelo pedido y asignable según `inventory` (`disponible`: una unidad `prestado` no se asigna hasta que se devuelva). La pertenencia al modelo se verifica con la lista de unidades que `inventory` devuelve para ese `equipamiento_id`, porque `unidad_es_asignable` no recibe el modelo. Que la unidad no tenga otra línea activa con un período solapado lo garantiza el `EXCLUDE`. Al asignar, `loans` bloquea cada unidad con `inventory.bloquear_unidad` (en orden ascendente de id) y verifica sede, modelo (`equipamiento_id` de la unidad devuelta) y estado `disponible`; el ítem activo se comprueba con `unidad_es_asignable` |
| RN-L12 | Solo `reservado` y `entregado` ocupan. **Una unidad no puede tener dos líneas ocupantes con períodos que se solapan**: lo garantiza el `EXCLUDE` sobre `(unidad_fisica_id, periodo)` de `0009`, y su violación (`23P01`) se traduce a `409`. Dos reservas de la misma unidad en fechas distintas pueden convivir (ERS PRE-11 y PRE-17). El servicio puede consultar antes para dar un error específico, pero nunca reemplaza a la restricción (P7.2). Una unidad se libera cuando su línea pasa a `devuelto`, `cancelado` o `no_retirado` |
| RN-L13 | Aprobar es **atómico**: orden, líneas y unidades en una transacción. Si una línea choca, ninguna se aprueba |
| RN-L14 | Las transiciones de una orden se serializan con `SELECT ... FOR UPDATE` sobre la fila de la orden, de modo que dos acciones simultáneas sobre la misma orden no se pisan. Para evitar interbloqueos, el orden de bloqueo es siempre: primero la orden y después las unidades, en orden ascendente de id. Como en `config`, ante un `AppError` se hace `rollback` antes de propagarlo |
| RN-L15 | Rechazar exige `motivo` |
| RN-L16 | Cancelación: el solicitante solo cancela su orden `pendiente`; el administrador solo cancela una orden `aprobada` de su sede, sin líneas `entregado`, y con motivo obligatorio |
| RN-L17 | Cancelación forzada (PRE-17): por línea, solo `reservado`, con motivo obligatorio; el cierre de la orden sigue RN-L30; se emite un aviso al solicitante |
| RN-L18 | Ajuste horario al aprobar (PRE-18): cumple RN-L04 y RN-L06, se aplica a todas las líneas, `fin_ocupacion` queda igual a la nueva devolución y se avisa al solicitante |
| RN-L19 | Entrega: solo una línea `reservado` de una orden `aprobada`. Llama a `inventory.marcar_unidad_prestada` en la misma transacción y registra `entregado_en`. No hay restricción horaria: el control es presencial |
| RN-L20 | Devolución: solo una línea `entregado`. Llama a `inventory.liberar_unidad`, registra `devuelto_en` y la observación del estado físico. Si la unidad vuelve dañada (`a_mantenimiento = true`), pasa a `mantenimiento` en la misma transacción, para que no quede asignable entre la devolución y el cambio de estado (C17) |
| RN-L21 | `demorado` es **derivado**, no se guarda: línea `entregado` y `ahora_lab() > devolucion_pactada`. La interfaz lo muestra en rojo. Las consecuencias de una devolución demorada (llamados de atención y faltas, ADR-022 d, USR-09) dependen de C20: hasta resolverlo, `loans` no registra sanciones |
| RN-L22 | Mora: una unidad que no se devolvió sigue `prestado` en `inventory`, así que no puede asignarse a pedidos nuevos (RN-L11) ni entregarse (`marcar_unidad_prestada` exige `disponible`) hasta que el administrador registre la devolución. Si ya tenía una reserva aprobada para después, la entrega de esa reserva falla con `409 TRANSICION_ESTADO_INVALIDA` y el administrador la resuelve con una cancelación forzada (PRE-17) o, a futuro, reasignando la unidad. `fin_ocupacion` no se extiende por demora: solo cambia por ajuste horario o renovación (D-L16) |
| RN-L23 | No retiro (PRE-08): una línea `reservado` cuyo retiro superó `prestamo.tolerancia_retiro_horas` pasa a `no_retirado` y libera la unidad, **salvo** que su unidad siga `prestado` por la demora de otra línea: en ese caso no se la marca (el solicitante no tiene la culpa) y se informa al administrador para que resuelva (RN-L22); el cierre de la orden sigue RN-L30. Si un no retiro cuenta como llamado de atención se define en C20 (ver también la pregunta 7 de §15.2) |
| RN-L24 | Renovación (PRE-11, ADR-022 h): el estudiante presenta la notebook en el mostrador y emite desde la app una nueva orden con `renueva_detalle_id` (una línea `entregado` suya, de un ítem `es_notebook`) y una sola línea del mismo modelo. Se valida como cualquier pedido (franja, plazo, asignatura), **sin anticipación mínima**, y la unidad renovada cuenta como libre para esa orden. Al aprobarla, el administrador asigna la misma unidad y, en una sola transacción, **primero** la línea anterior pasa a `devuelto` (así deja de ocupar y el `EXCLUDE` no la compara) (sin llamar a `inventory`: la unidad sigue `prestado`) y la nueva a `entregado`; se marca `es_renovado`. Si la unidad tiene otra reserva aprobada que se solapa, la base lo rechaza con `409 UNIDAD_NO_DISPONIBLE` y el administrador asigna otra notebook libre o rechaza |
| RN-L25 | Privacidad (P6): el estudiante solo ve lo propio; el docente solo ve órdenes de sus asignaturas, en lectura y observación, sin DNI, email ni teléfono; ningún rol ve solicitantes de otra sede |
| RN-L26 | Jurisdicción (P5): el `ADMIN_LOCAL` opera solo en su sede y el filtro se aplica en el `WHERE` de la consulta, no en la interfaz |
| RN-L27 | Aprobar exige `retiro_pactado > ahora_lab()`, salvo que se ajuste el horario (`RETIRO_VENCIDO`) |
| RN-L28 | Ningún valor operativo (plazos, horario, anticipación, tolerancia) se escribe fijo en el código: se leen con `obtener_parametro` (P8) |
| RN-L29 | Las fechas se comparan con `ahora_lab()` y se persisten como `timestamptz` (UTC) |
| RN-L30 | Cierre de la orden: después de una cancelación forzada o de un no retiro, si ninguna línea queda `reservado`, `entregado` o `devuelto`, la orden pasa a `cancelada`; si no, sigue `aprobada` (unifica RN-L17 y RN-L23) |
| RN-L31 | `situacion` (derivada, no se guarda): `en_curso` si la orden tiene alguna línea `pendiente`, `reservado` o `entregado`; `finalizada` en otro caso. Permite separar en la bandeja y en el historial (USR-06) las órdenes `aprobada` terminadas de las que siguen en curso, sin agregar un estado |

---

## 10. Integraciones entre módulos

### 10.1 `loans` consume (sin modificar esos módulos)

| De | Qué | Uso |
| :---- | :---- | :---- |
| `core` | `get_current_user`, `require_roles`, `resolver_alcance_sede`, `AppError`, `RolUsuario`, `SedeEnum`, `enum_values`, `ahora_lab` | Autenticación, alcance, errores y tiempo |
| `config` | `obtener_parametro(db, clave)` | RN-L04…L06, L23, §6.2 `ReglasResponse` |
| `inventory` | `unidades_asignables` y `unidad_es_asignable` (**verificadas**): solo cuentan unidades `disponible` hoy y de ítems activos. Es el criterio buscado: una unidad `prestado` no se promete hasta que se devuelva | Creación (RN-L10) y aprobación (RN-L11) |
| `inventory` | `marcar_unidad_prestada` y `liberar_unidad` (**verificadas**): no hacen `commit`, bloquean la unidad con `FOR UPDATE` y lanzan `AppError 409 TRANSICION_ESTADO_INVALIDA` si el estado no corresponde (`disponible` → `prestado` y `prestado` → `disponible`). `loans` hace `rollback` antes de propagar el error | Entrega y devolución (RN-L19, RN-L20) |
| `inventory` | `datos_equipamiento_por_ids(db, ids) -> dict[int, DatosEquipamiento]` (**publicada**, C8, SPEC-04 addendum v1.1.0): `id`, `codigo`, `nombre`, `activo`, `es_notebook`, `alta_gama`, `max_dias_prestamo`, en una sola consulta y sin `commit`. No incluye `sede`: el catálogo es global y las unidades sí tienen sede (RN-I9 de SPEC-04). `activo` lo evalúa `loans` | RN-L06, RN-L09, RN-L10, RN-L24 y respuestas para el administrador |
| `users` | `datos_publicos_por_ids(db, ids) -> dict[int, DatosPublicosUsuario]` (`id`, `nombre`, `apellido`; SPEC-03 Fase A). El vínculo docente–asignatura sigue sin publicar (SPEC-03 D-04, C3) | Resumen del solicitante y panel docente |
| `files` | `vincular_archivo(db, archivo_id, *, propietario_id, proposito)` sin `commit` (SPEC-03) | Aval de alta gama (RN-L09) |

### 10.2 `loans` publica (en `loans/service.py`, documentadas como API pública)

| Función (firma indicativa) | Para | Requisito |
| :---- | :---- | :---- |
| `unidades_libres(db, equipamiento_ids, sede, desde, hasta)` → por modelo, la cantidad de unidades libres para ese período (criterio de RN-L10), **sin identidad de solicitantes**. Sirve para saber si un modelo se puede pedir en las fechas elegidas (botón del catálogo, C16) | Perfil 2 | PRE-01, PRE-03 |
| `ocupacion_de_unidades(db, unidad_ids, desde, hasta) -> dict[int, list[PeriodoOcupado]]` → por unidad, los períodos `[retiro_pactado, fin_ocupacion)` de sus líneas `reservado` o `entregado` que se solapan con el rango, ordenados por inicio. Una sola consulta, sin identidad (P6: ni orden ni solicitante), sin filtro de sede y sin `commit`. Una clave por unidad pedida (lista vacía si está libre). `inventory` pasa las unidades operativas de un modelo y arma el conteo por día del mini-calendario y de la disponibilidad por fechas. Reemplaza las llamadas día por día a `unidades_libres`, con el aval del Perfil 2 (2026-11-06) | Perfil 2 (INV-26) | PRE-01 |
| `historial_de_unidad(db, unidad_id, actor)` → movimientos, solo con jurisdicción | Perfil 2 | PRE-12 |
| `reservas_futuras_de_unidad(db, unidad_id, desde)` → reservas aprobadas, solo con jurisdicción | Perfil 2 | PRE-17 |
| `ordenes_de_usuario(db, usuario_id, ...)` | Perfil 1 | USR-06, USR-07, USR-08 |

### 10.3 Eventos hacia `notifications` (Perfil 5)

Orden aprobada, rechazada o cancelada; horario ajustado (PRE-18); cancelación forzada (PRE-17); no retiro (PRE-08); demora; aviso de vencimiento (`notificacion.aviso_vencimiento_horas`). Mientras `notifications` no exista no se notifica; los eventos quedan especificados para cuando publique su función (C12).

---

## 11. Frontend (`src/features/loans/{components,pages,services,types}`)

- DTOs `snake_case` espejo 1:1 de los esquemas, `mappers.ts` hacia modelos de vista, y `src/lib/api.ts` para todas las llamadas (token y `ApiError {status, code, detail}`).
- Sesión y sede con `useAuth()` / `useSede()`; ningún selector de rol simulado.
- El frontend valida para mejorar la experiencia (campos obligatorios en rojo, PRE-04); la garantía es siempre el backend (P2.2).

| Pantalla | Rol | Requisito | Notas |
| :---- | :---- | :---- | :---- |
| Carrito (estado local con provider propio) y botón "Agregar al pedido" | Estudiante, Docente | PRE-03 | El botón vive en el catálogo de `inventory` (C11) y se deshabilita si no hay unidades libres (el ítem sigue visible con 0 disponibles) |
| **Formulario unificado de préstamo** | Estudiante, Docente | PRE-03, 04, 06, 07, 09 | Ítems, calendario de retiro y devolución con selectores de hora limitados a la franja, selector de asignatura (solo estudiante), casilla de normativa, bloqueo del envío con errores en rojo y botón deshabilitado mientras se envía. Lee `GET /reglas` |
| Mis solicitudes | Estudiante, Docente | USR-06 | Estados y cancelación de las pendientes |
| Bandeja de validación | Admin | PRE-15 | Filtro por estado, detalle con observación del docente |
| Aprobación | Admin | PRE-10, 18 | Asignación de unidad (lista de `GET /ordenes/{id}/unidades-libres`) y ajuste horario |
| Mostrador (entrega, devolución y aprobación de renovaciones) | Admin | PRE-11, 13 | Alerta roja de demora y campo de observaciones |
| Calendario maestro | Admin | PRE-16 | "En Uso" y "En Reserva" |
| Panel docente | Docente | PRE-20 | Solo lectura y comentario |

El formulario sube el aval con `POST /api/v1/files/archivos` (`proposito=AVAL_PRESTAMO`) y envía su id en `pdf_aval_id` (PRE-05). La renovación (PRE-11) es el mismo formulario precargado con la notebook a renovar.

---

## 12. Criterios de aceptación

Cada criterio tendrá al menos un test automatizado, anotado con `# AC-Lxx`, marcado con `pytest.mark.integracion` y ejecutado contra PostgreSQL real (P9).

**Reglas y creación**

| ID | Criterio |
| :---- | :---- |
| AC-L01 | `GET /reglas` devuelve los valores vigentes de `config`; al cambiar un parámetro, cambia la respuesta |
| AC-L02 | Un estudiante crea una orden de un ítem con asignatura: `201`, estado `pendiente`, línea `pendiente` sin unidad, sede y solicitante tomados del token |
| AC-L03 | Un carrito de varias líneas (incluso del mismo modelo repetido) genera una sola orden |
| AC-L04 | Un body con `solicitante_id`, `sede` o `estado` u otro campo desconocido responde `422` |
| AC-L05 | Un estudiante sin asignatura recibe `422 ASIGNATURA_REQUERIDA`; un docente sin asignatura crea la orden |
| AC-L06 | `acepta_normativa` distinto de `true` responde `422` |
| AC-L07 | Una hora de retiro o de devolución fuera de la franja responde `422 FRANJA_FUERA_DE_HORARIO`; las horas exactas de apertura y de cierre son válidas |
| AC-L08 | Un retiro con menos anticipación que la configurada responde `422 ANTICIPACION_INSUFICIENTE` |
| AC-L09 | Una devolución anterior o igual al retiro responde `422` |
| AC-L10 | Un rango que supera el máximo de alguna línea responde `422 LIMITE_DIAS_EXCEDIDO` e identifica el ítem |
| AC-L11 | Un equipo común admite hasta 4 días y una notebook hasta 15, según los parámetros vigentes |
| AC-L12 | Un `equipamiento_id` inexistente, inactivo o sin unidades en la sede responde `404 EQUIPAMIENTO_NO_ENCONTRADO` |
| AC-L13 | `SUPERADMIN` y `ADMIN_LOCAL` reciben `403` al crear; sin token, `401` |
| AC-L14 | Una orden con un ítem de alta gama sin `pdf_aval_id` responde `422 AVAL_REQUERIDO`; con un aval válido se crea y el archivo queda vinculado en la misma transacción (si la creación falla, el archivo no queda vinculado) |
| AC-L15 | Dos órdenes pendientes concurrentes por el mismo modelo y período se crean ambas |
| AC-L56 | Un modelo sin unidades libres para el período (ninguna `disponible` en la sede, o todas con una línea `reservado` o `entregado` que se solapa) responde `409 EQUIPAMIENTO_NO_DISPONIBLE`; si la única reserva es en otras fechas, el pedido se crea |
| AC-L57 | Un pedido con más líneas del mismo modelo que unidades libres para el período responde `409 EQUIPAMIENTO_NO_DISPONIBLE` |
| AC-L58 | `GET .../unidades-libres` devuelve, por línea, solo unidades del modelo y la sede que estén `disponible` y sin otra línea `reservado` o `entregado` que se solape con su período |
| AC-L59 | Devolver con `a_mantenimiento = true` deja la línea `devuelto` y la unidad en `mantenimiento` en una sola transacción, sin pasar por un estado asignable **Bloqueado por C17.** |
| AC-L60 | El aval lo descargan el solicitante y los administradores con jurisdicción; el docente de la asignatura recibe `404` (SPEC-03 RN-60) |
| AC-L61 | `situacion` es `en_curso` mientras haya líneas `pendiente`, `reservado` o `entregado`, y `finalizada` en otro caso |
| AC-L62 | Tras una cancelación forzada y un no retiro sobre las dos líneas de una orden sin entregas, la orden queda `cancelada` (RN-L30) |
| AC-L63 | `GET /reglas` devuelve el horario de la sede del solicitante; el `SUPERADMIN` lo pide con `?sede=` |

**Consulta**

| ID | Criterio |
| :---- | :---- |
| AC-L16 | `GET /ordenes/mias` devuelve solo las propias; el `GET` de una orden ajena responde `404` |
| AC-L17 | La bandeja del `ADMIN_LOCAL` muestra solo su sede y, por defecto, las pendientes; el `SUPERADMIN` ve ambas y puede filtrar; estudiantes y docentes reciben `403` |
| AC-L18 | La bandeja admite paginación con `limit` y `offset` |

**Aprobación y rechazo**

| ID | Criterio |
| :---- | :---- |
| AC-L19 | Aprobar con una asignación válida por línea deja la orden `aprobada` y las líneas `reservado` con unidad, y registra quién y cuándo resolvió |
| AC-L20 | Una unidad que no está `disponible` (`prestado`, `mantenimiento` o `baja`) responde `422 UNIDAD_NO_ASIGNABLE` y no cambia nada |
| AC-L21 | Una unidad de otra sede o de otro modelo responde `422 UNIDAD_NO_ASIGNABLE` |
| AC-L22 | Asignaciones incompletas, repetidas o de líneas ajenas responden `422 ASIGNACIONES_INVALIDAS` |
| AC-L23 | Dos aprobaciones concurrentes de órdenes distintas sobre la misma unidad con períodos que se solapan: una responde `200` y la otra `409 UNIDAD_NO_DISPONIBLE`, y la perdedora queda `pendiente` sin cambios parciales. Con períodos que no se solapan, ambas se aprueban |
| AC-L24 | Dos acciones concurrentes sobre la misma orden: una prospera y la otra responde `409 TRANSICION_INVALIDA` |
| AC-L25 | El ajuste horario valida franja y plazos, actualiza todas las líneas y deja `fin_ocupacion` igual a la nueva devolución |
| AC-L26 | Asignar una unidad que sigue `prestado` (devolución pendiente, aunque esté vencida) responde `422 UNIDAD_NO_ASIGNABLE` |
| AC-L27 | Rechazar sin motivo responde `422 MOTIVO_REQUERIDO`; con motivo deja la orden `rechazada` y las líneas `rechazado` |
| AC-L28 | Una transición no permitida responde `409 TRANSICION_INVALIDA` |
| AC-L29 | Un `ADMIN_LOCAL` de otra sede recibe `404`; un estudiante o docente, `403` |
| AC-L30 | Aprobar una orden cuyo retiro ya pasó responde `422 RETIRO_VENCIDO`, salvo que se ajuste el horario |

**Cancelación**

| ID | Criterio |
| :---- | :---- |
| AC-L31 | El solicitante cancela su orden `pendiente`: queda `cancelada` y las líneas `cancelado` |
| AC-L32 | El solicitante que intenta cancelar una orden `aprobada` recibe `403 CANCELACION_NO_PERMITIDA` |
| AC-L33 | El administrador cancela una orden `aprobada` con motivo y la unidad queda libre: un pedido nuevo puede asignarse esa unidad |
| AC-L34 | El administrador sin motivo recibe `422 MOTIVO_REQUERIDO`; con una línea `entregado`, `409 TRANSICION_INVALIDA` |
| AC-L35 | La cancelación forzada de una línea exige motivo; si era la última vigente, la orden pasa a `cancelada` |

**Entrega, devolución y renovación**

| ID | Criterio |
| :---- | :---- |
| AC-L36 | Entregar una línea `reservado` la deja `entregado`, registra `entregado_en` y la unidad queda `prestado` en `inventory`, en la misma transacción |
| AC-L37 | Si `inventory` rechaza la entrega (la unidad ya no está `disponible`), responde `409 TRANSICION_ESTADO_INVALIDA` (código de `inventory`) y no cambia nada |
| AC-L38 | Devolver una línea `entregado` la deja `devuelto`, registra `devuelto_en` y la observación, y libera la unidad |
| AC-L39 | Entregar o devolver fuera del estado correspondiente responde `409 TRANSICION_INVALIDA` |
| AC-L40 | `demorado` es `true` solo para órdenes con línea `entregado` y devolución pactada vencida |
| AC-L41 | Aprobar una renovación asigna la misma unidad; en una transacción la línea anterior queda `devuelto`, la nueva `entregado`, la unidad sigue `prestado` y la orden queda con `es_renovado` |
| AC-L42 | Un `renueva_detalle_id` que no es una notebook `entregado` responde `422 RENOVACION_NO_PERMITIDA`; uno de otro solicitante responde `404` |
| AC-L43 | La solicitud de renovación no exige la anticipación mínima, pero sí la franja de la sede y el plazo de notebooks |
| AC-L44 | Si la unidad tiene otra reserva aprobada que se solapa, aprobar la renovación responde `409 UNIDAD_NO_DISPONIBLE` y no cambia nada |

**Procesos automáticos, calendario y panel docente**

| ID | Criterio |
| :---- | :---- |
| AC-L45 | `procesar_vencimientos` pasa a `no_retirado` las líneas `reservado` que superaron la tolerancia y libera la unidad |
| AC-L46 | Si todas las líneas de una orden quedan `no_retirado`, la orden pasa a `cancelada`; si alguna fue entregada, sigue `aprobada` |
| AC-L47 | Una unidad con una línea `reservado` o `entregado` que se solapa con el período no aparece en `unidades-libres` y asignarla responde `409 UNIDAD_NO_DISPONIBLE`; con una reserva en otras fechas sí aparece |
| AC-L48 | El proceso es idempotente: ejecutarlo dos veces seguidas no cambia el resultado |
| AC-L49 | El calendario maestro agrupa los recursos "En Uso" y "En Reserva" y respeta la sede del administrador |
| AC-L50 | El docente ve solo órdenes de sus asignaturas, sin DNI, email ni teléfono del solicitante, y no puede resolverlas (`403`) |
| AC-L51 | El docente registra su observación en una orden `pendiente` de su asignatura; en una ajena, `404` |

**Transversales**

| ID | Criterio |
| :---- | :---- |
| AC-L52 | Todos los endpoints responden `401` sin token |
| AC-L53 | Los errores de negocio responden `{detail, code}`; solo la violación de exclusión (`23P01`) se traduce a `409 UNIDAD_NO_DISPONIBLE`; las de `CHECK`, unicidad o clave foránea no se enmascaran como conflicto (§6.3) |
| AC-L54 | Cada migración de `loans` (`0011` y `0012`) se valida con upgrade → downgrade → upgrade |
| AC-L55 | Las pruebas de concurrencia (AC-L23, AC-L24 y EC-L10) usan sesiones independientes, como en producción (ADR-013) |

---

## 13. Casos de borde

| ID | Caso | Comportamiento |
| :---- | :---- | :---- |
| EC-L01 | Orden con notebook y equipo común | Se valida cada línea; el error identifica la línea que excede |
| EC-L02 | Retiro y devolución el mismo día | Válido si la devolución es posterior al retiro y ambas están en la franja |
| EC-L03 | Horas exactas de apertura o cierre | Válidas (intervalo cerrado) |
| EC-L04 | Cliente en otra zona horaria | Los instantes se convierten a la zona del laboratorio antes de validar la franja |
| EC-L05 | Orden pendiente cuyo retiro ya pasó | Sigue `pendiente`; la bandeja la marca y solo puede rechazarse o aprobarse con ajuste horario (RN-L27) |
| EC-L06 | Una unidad reservada pasa a `mantenimiento` o `baja` | La entrega falla (AC-L37) y se resuelve con cancelación forzada. Reasignar la unidad sería mejor, pero queda **fuera de este spec** |
| EC-L07 | La unidad reservada para B sigue `prestado` por la demora de A | La entrega a B falla (`TRANSICION_ESTADO_INVALIDA`) y B conserva su reserva: el proceso de no retiro no la marca `no_retirado` (RN-L23). El administrador espera la devolución, reasigna o hace una cancelación forzada (PRE-17) |
| EC-L08 | Equipo dado de baja lógica con órdenes pendientes | Al aprobar, la unidad no es asignable (`UNIDAD_NO_ASIGNABLE`) |
| EC-L09 | Doble envío del formulario | El backend no deduplica: crea dos órdenes pendientes; la interfaz deshabilita el botón al enviar |
| EC-L10 | Cancelación del solicitante simultánea con la aprobación | `FOR UPDATE` serializa: una prospera y la otra recibe el error que corresponde al estado que dejó la primera. Si ganó la cancelación, aprobar responde `409 TRANSICION_INVALIDA`; si ganó la aprobación, cancelar responde `403 CANCELACION_NO_PERMITIDA` (AC-L32) |
| EC-L11 | Parámetros cambiados entre el pedido y la aprobación | Aprobar no revalida plazos ni franja (la solicitud se hizo con las reglas vigentes); solo el ajuste horario las revalida |
| EC-L12 | Solicitante suspendido con órdenes vigentes | Sus órdenes no se cancelan solas; la sanción la define el Perfil 1 (USR-09). Los llamados de atención que originan las demoras y los no retiros se coordinan en C20 |
| EC-L13 | Aprobación parcial por concurrencia | No existe: aprobar es todo o nada (RN-L13) |
| EC-L14 | Un modelo sin unidades libres para las fechas pedidas | No se puede solicitar para esas fechas (`409 EQUIPAMIENTO_NO_DISPONIBLE`), pero sí para otras. El ítem **sigue visible** en el catálogo (RN-I5 de SPEC-04: solo desaparece si `activo = false`), y el mini-calendario muestra en qué fechas hay unidades libres |
| EC-L15 | La unidad vuelve rota | Al devolverla con `a_mantenimiento = true`, `loans` la libera y la pasa a `mantenimiento` en la misma transacción. Sin eso quedaría `disponible` y asignable hasta que el administrador cambie el estado en otra solicitud (C17) |

---

## 14. Fases de entrega

| Fase | Contenido | Requisitos | Bloqueos |
| :---- | :---- | :---- | :---- |
| **0. Saneamiento** | Eliminar `dependencies.py`, autenticar y autorizar los endpoints, `AppError`, rutas `/estado`, `501 NO_IMPLEMENTADO`, descripción de `main.py` | DT-16, 17, 18 | Implementada (PR #16) |
| **1. Solicitar** | `GET /reglas`, `POST /ordenes` (con aval y renovación), consultas propias, reglas RN-L01…L10; formulario y carrito | PRE-03, 04, 05, 06, 07, 09 | C3 (asignaturas), C8 (lectura de `inventory`), SPEC-03 (`files`, K10), B2 |
| **2. Validar** | Bandeja, unidades libres por línea, aprobar, rechazar, cancelar, ajuste horario, uso de `inventory/service.py`; funciones de lectura para el Perfil 2; migración `0011` | PRE-10, 11, 15, 18, DT-20 | C8 |
| **3. Mostrador** | Entrega, devolución, cancelación forzada; migración `0012` | PRE-13, 17 | C17 |
| **4. Procesos y paneles** | `procesar_vencimientos` (no retiro), calendario maestro, panel docente | PRE-08, 16, 20 | C2, C3, C5 |
| **5. Avisos** | Notificaciones | Eventos §10.3 | C12 |

El frontend avanza una fase detrás del backend de cada una.

---

## 15. Decisiones y preguntas abiertas

### 15.1 Decisiones propuestas (a aprobar)

| ID | Decisión | Recomendación |
| :---- | :---- | :---- |
| D-L01 | Numeración del spec | **Resuelto:** SPEC-05 (SPEC-03 existe) |
| D-L02 | Cambios de estado como `PATCH .../estado` (Constitución §4.2), reemplazando `/resolucion` y `/cancelacion` | Adoptar |
| D-L03 | Plazo máximo por línea = el menor entre el parámetro del tipo y `max_dias_prestamo` del ítem | Adoptar; resuelve las tres fuentes del límite. Requiere la conformidad del Perfil 2 |
| D-L04 | Los días se cuentan corridos, incluyendo el día de retiro y el de devolución | Adoptar; confirmar con la referente |
| D-L05 | Las líneas pendientes no ocupan y la unidad se asigna al aprobar | Adoptar (ya implementado en `0009`) |
| D-L06 | Solo `ESTUDIANTE` y `DOCENTE` crean órdenes; el `SUPERADMIN` no tiene sede y el `ADMIN_LOCAL` solo valida | Adoptar |
| D-L07 | `GET /api/v1/loans/reglas` para que el formulario conozca las reglas sin tocar `config` | Adoptar |
| D-L08 | Los procesos automáticos son una función idempotente más un comando de consola (`python -m app.modules.loans.cli procesar-vencimientos`); la periodicidad la resuelve el despliegue. No se agrega un planificador al servidor | Adoptar; coordinar con el Perfil 1 (C5) |
| D-L09 | Una orden sin líneas `reservado`, `entregado` ni `devuelto` pasa a `cancelada` (RN-L30) | Adoptar |
| D-L10 | Tabla `ordenes_historial_estado` | Adoptar |
| D-L11 | Los enums de `loans` siguen en minúsculas hasta que el equipo decida DT-19 | Adoptar |
| D-L12 | El aval de alta gama usa el almacenamiento de SPEC-03 y se vincula en la transacción que crea la orden (reemplaza el rechazo con `AVAL_NO_HABILITADO`) | Adoptar |
| D-L13 | Hasta que exista el catálogo de asignaturas, `asignatura_id` no tiene FK y no se verifica su existencia | Adoptar como transitoria |
| D-L14 | Fase 0: el router se mantiene montado con `501` en lugar de desmontarlo | Adoptar; permite generar tipos del frontend y del agente |
| D-L15 | Mientras no se aclare, los límites de plazo y la anticipación se aplican también a los docentes | Adoptar como transitoria |
| D-L16 | La mora se resuelve con el estado de la unidad en `inventory` (una unidad `prestado` no se promete ni se entrega hasta devolverse) y no extendiendo `fin_ocupacion` | Adoptar; confirmar con el equipo |
| D-L17 | Una unidad con una línea ocupante no se asigna a otro pedido, sin importar las fechas | **Descartada** (2026-11-06, revisión del Perfil 1, B2): se vuelve al criterio por fechas (§15.3, opción B) |
| D-L18 | La renovación es una nueva solicitud emitida en el mostrador, aprobada por un administrador, que conserva la misma unidad (RN-L24) | Adoptar (pedido de la referente, ADR-022 h) |
| D-L19 | La orden `aprobada` no tiene estado final; `situacion` derivada distingue en curso de finalizada (RN-L31) | Adoptar |

### 15.3 D-L17: decisión tomada (B2 de la revisión)

Se eligió la **opción B: criterio por fechas, solo unidades `disponible`**. Una unidad no puede tener dos líneas ocupantes con períodos solapados (`EXCLUDE` de `0009`), y solo se asignan unidades físicamente presentes (`unidades_asignables`). Motivos: no inmoviliza equipos durante la ventana de reserva a futuro, permite la renovación del mismo equipo (RN-L24), coincide con el ERS (PRE-01, PRE-11, PRE-17) y mantiene cubierto el caso de una unidad que está afuera y vuelve rota. El riesgo residual (una unidad del estante, reservada a futuro, que se presta antes y vuelve rota) se resuelve con la cancelación forzada (PRE-17).

### 15.2 Preguntas para la referente (Natalia Ader)

1. ¿El laboratorio atiende sábados y domingos? Hoy no existe una regla de días hábiles.
2. ¿El límite de 4 días y la anticipación de 24 h aplican también a los docentes? (ya figura en `MEMORY.md` §6, pregunta 3).
3. ¿Una renovación tiene tope de días o de cantidad de veces?
4. ¿La tolerancia de retiro se mide desde la hora de retiro pactada?
5. ¿El docente debe ver nombre y apellido del estudiante?
6. ¿La ventana de reserva a futuro de 120 días (ERS, Iteración 5) aplica también a los préstamos de equipamiento? Hoy el parámetro existente es `reserva_espacio.anticipacion_max_dias`, solo para espacios.
7. Si el solicitante no puede ir a retirar, ¿puede cancelar una orden `aprobada` antes del retiro? Hoy solo puede el administrador, y el no retiro automático podría contarle como falta (ADR-022 d).

---

## 16. Ítems de coordinación (no se modifica ningún otro módulo)

| ID | De → Para | Pedido |
| :---- | :---- | :---- |
| C1 | Perfil 3 → Perfil 1 | Confirmar que las claves de `config` existentes alcanzan (no se piden claves nuevas) |
| C2 | Perfil 3 → Perfil 1 | **Parcialmente resuelto:** SPEC-03 Fase A publica `datos_publicos_por_ids(db, ids)`. Sigue abierto el vínculo docente–asignatura (SPEC-03 D-04, C3) |
| C3 | Perfil 3 → Perfil 1 / equipo | Definir quién implementa el **catálogo de asignaturas** y el vínculo docente–asignatura. Bloquea PRE-20 y la verificación de PRE-03. Lo decide el equipo, no el Perfil 3 solo (SPEC-03 D-04 también lo dejó abierto); D-L13 es la solución transitoria |
| C4 | Perfil 3 → Perfil 1 | **Resuelto por SPEC-03:** `POST /api/v1/files/archivos` (`proposito=AVAL_PRESTAMO`) y `vincular_archivo(db, archivo_id, *, propietario_id, proposito)` sin `commit`. Falta acordar el detalle de K3 (cómo se expone el aval en la orden) |
| C5 | Perfil 3 → Perfil 1 | Cómo se programa la ejecución periódica de `procesar-vencimientos` (cron, contenedor, CI/despliegue). Depende del despliegue, que es del Perfil 1 (ADR-018), y afecta a PRE-08 y, más adelante, a NOV-03; mientras tanto alcanza D-L08 |
| C6 | Perfil 3 → Perfil 1 | Actualizar el README: `loans` está montado en `/api/v1/loans` (DT-24) |
| C7 | Perfil 3 → Perfil 1 | `loans` publica `ordenes_de_usuario` para USR-06, 07 y 08 (§10.2) |
| C8 | Perfil 3 → Perfil 2 | **Resuelto** (2026-11-06, backend PR #19): `inventory.datos_equipamiento_por_ids(db, ids)`, sin `sede` porque el catálogo es global (RN-I9 de SPEC-04). `crear_orden` ya la usa |
| C9 | Perfil 3 → Perfil 2 | **Resuelto:** `marcar_unidad_prestada` y `liberar_unidad` no hacen `commit` (confirmado en el código), por lo que `loans` opera en una sola transacción |
| C10 | Perfil 3 → Perfil 2 | `loans` publica `unidades_libres`, `historial_de_unidad` y `reservas_futuras_de_unidad` (§10.2) y desbloquea la Fase B de SPEC-04. El flujo PRE-17 queda cubierto por RN-L17 |
| C11 | Perfil 3 → Perfil 2 | Frontend: botón "Agregar al pedido" y "Solicitar" en el catálogo, que usan el carrito de `loans` |
| C12 | Perfil 3 → Perfil 5 | Función pública de `notifications` y eventos de §10.3 |
| C13 | Perfil 3 → equipo | Ratificar la enmienda 1.1.1 y decidir DT-19 |
| C14 | — | **Descartado:** `unidades_asignables` y `unidad_es_asignable` alcanzan, porque solo se asignan unidades `disponible`. `bloquear_unidad(db, unidad_id)` figura en `inventory/service.py`; confirmar con SPEC-04 §6 que es API pública, para bloquear la unidad al aprobar |
| C15 | — | **Descartado:** con D-L17 descartada, el ERS no cambia. Sigue vigente el texto propuesto de P7.2 (enmienda 1.1.1) |
| C16 | Perfil 3 → Perfil 2 | El contador `cantidad_disponible` del catálogo (RN-I4) informa unidades `disponible` **ahora**, lo que es correcto para el estado físico. Pero si una unidad está reservada para las fechas que el usuario elige, `loans` rechazará el pedido con `409`. El mini-calendario (PRE-01, Fase B) debe usar `loans.unidades_libres(db, ids, sede, desde, hasta)` para mostrar en qué fechas hay unidades libres. Resolver antes de cerrar la Fase 2 |
| C17 | Perfil 3 → Perfil 2 | Función pública para pasar una unidad a `mantenimiento` dentro de la transacción del llamador (por ejemplo `marcar_unidad_mantenimiento(db, unidad_id)`, usando `bloquear_unidad` y `validar_transicion_admin`), para registrar devoluciones con daño sin una ventana en la que la unidad esté `disponible` y asignable |
| C18 | Perfil 3 → Perfil 2 | `inventory` copia el parámetro vigente en `max_dias_prestamo` al crear el ítem (acotado por `CHECK 1..15`). Con RN-L06, bajar el parámetro se aplica enseguida, pero subirlo no alcanza a los ítems existentes, y cambiar `es_notebook` después del alta no actualiza el tope. Confirmar si es el comportamiento esperado |
| C19 | Perfil 3 → Perfil 1 | Claves de horario por sede en `config` (SPEC-03 K10) y numeración de las migraciones `0011` y `0012` frente a las de SPEC-03 |
| C20 | Perfil 3 → Perfil 1 | **Sanciones (ADR-022 d, USR-09).** Acordar quién registra el llamado de atención cuando `loans` registra una devolución demorada (RN-L21) o un no retiro (RN-L23): (a) una función pública de `users`, sin `commit`, que `loans` llama en la misma transacción (por ejemplo `registrar_llamado_de_atencion(db, usuario_id, *, motivo, orden_id)`), o (b) un evento que `users` consume. Propuesta del Perfil 3: (a), por coherencia con `vincular_archivo` y `datos_publicos_por_ids`. Definir también si el no retiro cuenta como llamado, junto con la pregunta 7 de §15.2. Hasta resolverlo, `loans` no registra sanciones. Conviene cerrarlo antes de aprobar |

---

## 17. Trazabilidad

| Requisito | Casos de uso | Endpoint | Criterios | Fase |
| :---- | :---- | :---- | :---- | :---- |
| PRE-03 | CU-L01 | `POST /ordenes`, `GET /reglas` | AC-L02…L06, L12, L13, L56, L57, L63 | 1 |
| PRE-04 | CU-L01 | `POST /ordenes` (y validación de la interfaz) | AC-L04…L06 | 1 |
| PRE-05 | CU-L02 | `POST /ordenes` (con `pdf_aval_id`), `GET /ordenes/{id}/aval` | AC-L14, L60 | 1 |
| PRE-06 | CU-L01 | `POST /ordenes` | AC-L07…L09 | 1 |
| PRE-07 | CU-L01 | `POST /ordenes` | AC-L10, L11 | 1 |
| PRE-08 | CU-L12 | `procesar-vencimientos` | AC-L45…L48 | 4 |
| PRE-09 | CU-L01 | `POST /ordenes` | AC-L05 | 1 |
| PRE-10 | CU-L04 | `PATCH /ordenes/{id}/estado`, `GET /ordenes/{id}/unidades-libres` | AC-L19…L24, L27, L28, L58, L61 | 2 |
| PRE-11 | CU-L09 | `POST /ordenes` (con `renueva_detalle_id`) y `PATCH /ordenes/{id}/estado` | AC-L41…L44 | 2 |
| PRE-13 | CU-L07, CU-L08 | `PATCH .../detalles/{id}/estado` | AC-L36…L40, L59 (bloqueado por C17) | 3 |
| PRE-15 | CU-L04 | `GET /ordenes` | AC-L17, L18 | 2 |
| PRE-16 | CU-L11 | `GET /calendario` | AC-L49 | 4 |
| PRE-17 | CU-L05, CU-L06 | `PATCH .../estado` (orden y línea) | AC-L33…L35, L62 | 2–3 |
| PRE-18 | CU-L04 | `PATCH /ordenes/{id}/estado` | AC-L25, L30 | 2 |
| PRE-20 | CU-L10 | `GET /ordenes/docente`, `PUT .../observacion-docente` | AC-L50, L51 | 4 |
| DT-16…DT-20 | — | — | AC-L52, L53 y Fase 0 | 0 |

---

## 18. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.0.2 | 2026-11-10 | **Pendiente del OK del Perfil 1.** Aval de alta gama (T1.12, K3 de SPEC-03): `ordenes_pedido.aval_archivo_id` en la migración `0016_loans_aval` (§7.2), porque `files` no guarda a qué orden pertenece el PDF; `GET /ordenes/{id}/aval` (§6.1); `aval_archivo_id` en la respuesta (§6.2); errores `ARCHIVO_INVALIDO` y `ARCHIVO_NO_ENCONTRADO` (§6.3); RN-L09 aclara que sin alta gama `pdf_aval_id` se ignora |
| 1.0.1 | 2026-11-08 | **Pendiente del OK del Perfil 1.** Corrige EC-L10, que contradecía a AC-L32: si la aprobación gana la carrera, la cancelación del solicitante choca con una orden `aprobada` y responde `403 CANCELACION_NO_PERMITIDA`, no `409`. Lo encontró `test_concurrencia.py` (T2.8). Sin otros cambios de contrato |
| 1.0.0 | 2026-11-07 | **Aprobado** por el Perfil 1 (PR #7 y #10 de `Docs-PrestaMeDios`). Corrige §10.1 y C8, que todavía decían que la lectura de equipamiento no estaba publicada (revisión de seguimiento del Perfil 1, 2026-11-07). Sin cambios de contrato respecto de la v0.3.1. Siguen abiertos como coordinación C19 (horario por sede y numeración de migraciones) y C20 (sanciones) |
| 0.3.1 | 2026-11-06 | §10.2: agrega `ocupacion_de_unidades` (ocupación por unidad y período en una sola consulta, para el mini-calendario del Perfil 2, con su aval) y precisa el uso de `unidades_libres`. C8 resuelto por `inventory.datos_equipamiento_por_ids` (PR #19 del backend) |
| 0.3.0 | 2026-11-06 | Responde a la revisión del Perfil 1: incorpora la Iteración 5 y SPEC-03 (renovación como nueva solicitud, horario por sede, aval con `files`, `datos_publicos_por_ids`), unifica el cierre de la orden (RN-L30), agrega `situacion` derivada (RN-L31), corrige AC-L53, AC-L55 y la trazabilidad, actualiza §0, registra la relación con las sanciones (C20) y deja C3 y C5 como decisiones del equipo y del Perfil 1, y descarta D-L17: vuelve al criterio por fechas (§15.3, opción B) con su ajuste en cascada. Pasa a `EN_REVISION` |
| 0.2.0 | 2026-11-03 | Fase 0 implementada (PR #16). Verifica contra `develop` las firmas de `core.errors`, `config` e `inventory` (S2…S4). Adopta la unidad exclusiva (D-L17: índice único parcial, `unidades-libres`, `unidades_libres`), simplifica la mora (D-L16), agrega `a_mantenimiento` (C17), los pedidos C14…C17 y la pregunta 6 para la referente |
| 0.1.0 | 2026-10-23 | Borrador inicial. Documenta lo existente en `develop`, define lo pendiente y resuelve DT-16…DT-20 |