# SPEC-05 — Préstamos de equipamiento y notebooks (`loans`)

> **Estado:** `BORRADOR` · **Versión:** 0.1.0 · **Fecha:** 2026-10-23 · **Perfil:** 3 (Préstamos y concurrencia)
> **Requisitos:** PRE-03…PRE-11, PRE-13, PRE-15…PRE-18, PRE-20 (ERS, Subsistema 2, módulos 2, 3 y 4)
> **Depende de:** SPEC-01 (`core`, autenticación), SPEC-02 (alcance de sede, `config`) y SPEC-04 (`inventory/service.py`)
> **Constitución:** v1.1.0, con la enmienda 1.1.1 propuesta (ADR-019) · **Plan y tareas:** `specs/05-loans-prestamos/plan.md` y `specs/05-loans-prestamos/tasks.md` (se redactan tras la aprobación)

> **Numeración:** tomé SPEC-05 porque existen 01, 02 y 04, y entiendo que el 03 quedó reservado para el próximo spec del Perfil 1. Confirmar (D-L01).

---

## 0. Supuestos a verificar antes de aprobar

Este spec se redactó leyendo `constitution.md`, `AGENTS.md`, `perfiles.md`, `MEMORY.md`, `requisitos.md` y el código de `loans` ya conocido. **No se leyeron** `app/core/deps.py`, `app/core/errors.py`, `app/modules/config/service.py`, `app/modules/inventory/service.py` ni los specs 01, 02 y 04, así que lo siguiente se toma de `AGENTS.md` y `MEMORY.md` y debe confirmarse contra el código:

| # | Supuesto | Fuente | Dónde se confirma |
| :---- | :---- | :---- | :---- |
| S1 | `get_current_user`, `require_roles(RolUsuario...)`, `resolver_alcance_sede(...)` y `sede_para_alta(...)` existen en `app/core/deps.py` con la semántica de `AGENTS.md` §6 | `AGENTS.md` | `app/core/deps.py` |
| S2 | `AppError(status, "CODIGO", "mensaje")` produce `{detail, code}` | `AGENTS.md`, Constitución §4.2 | `app/core/errors.py` |
| S3 | `obtener_parametro(db, "<clave>")` devuelve el valor tipado (la firma y el tipo de retorno no se leyeron). Las claves `horario.apertura`, `horario.cierre` (tipo `HORA`), `prestamo.general.max_dias`, `prestamo.notebook.max_dias`, `solicitud.anticipacion_min_horas` y `prestamo.tolerancia_retiro_horas` **sí figuran** en `config/seed.py` | `AGENTS.md` y `config/seed.py` | `config/service.py` |
| S4 | `inventory/service.py` publica `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada` y `liberar_unidad` | `MEMORY.md` DT-20 y §5 | `inventory/service.py` (firmas, uso de la sesión del llamador, si hacen `commit`) |
| S5 | `Equipamiento` tiene `es_notebook`, `alta_gama` y `max_dias_prestamo` | ADR-020 (D-05), migración `0010` | `inventory/models.py` |
| S6 | `ahora_lab()` y `ZONA_HORARIA_LAB` están en `app/core/settings.py` | `perfiles.md` §2 | `core/settings.py` |
| S7 | Los tests de integración crean el esquema con `create_all` y una sesión por request (ADR-013); la migración se valida aparte | `MEMORY.md` ADR-013 | `tests/conftest.py` |

---

## 1. Alcance

### 1.1 Incluye

1. **Orden de pedido unificada**, simple (un ítem desde el catálogo) o por carrito, con fechas y horas de retiro y devolución, asignatura y aceptación de la normativa (PRE-03, PRE-04, PRE-06, PRE-07, PRE-09).
2. **Validación de plazos** (4 días general, 15 notebooks), de la franja operativa y de la anticipación mínima, leídas de `config` (PRE-06, PRE-07, P8).
3. **Bandeja administrativa** con jurisdicción por sede, **aprobación con asignación de unidad**, rechazo y ajuste horario (PRE-10, PRE-15, PRE-18).
4. **Cancelación** por el solicitante (pendiente) y por el administrador (aprobada), y **cancelación forzada** por línea (PRE-17).
5. **Entrega y devolución** en mostrador, con observaciones del estado físico y alerta de demora (PRE-13).
6. **Renovación de notebooks**, solo presencial (PRE-11).
7. **Cancelación automática por no retiro** y extensión de la ocupación por demora (PRE-08).
8. **Calendario maestro** de operaciones (PRE-16) y **panel de observación docente** (PRE-20).
9. **Funciones públicas de lectura** que necesitan otros perfiles (§10.2).
10. **Saneamiento de la deuda** DT-16…DT-20 (§3).
11. **Frontend** de `loans` (§11).

### 1.2 No incluye

- Catálogo y stock (PRE-01, PRE-02, PRE-12, PRE-14, PRE-19): Perfil 2. `loans` consume su servicio y publica funciones de lectura para su Fase B.
- Usuarios, sanciones y chips de comportamiento (USR-09): Perfil 1.
- Notificaciones (NOV-xx): Perfil 5. Este spec define los eventos que `loans` emite (§10.3), no el módulo.
- Catálogo de asignaturas y almacenamiento de archivos: no tienen dueño definido (§16, C3 y C4). Bloquean parcialmente PRE-03, PRE-05 y PRE-20.
- Reasignación de unidad de una línea ya aprobada (se anota en EC-L06 como trabajo futuro).

---

## 2. Estado actual del módulo (en `develop`)

| Artefacto | Contenido | Observación |
| :---- | :---- | :---- |
| `loans/enums.py` | `EstadoOrdenEnum` (`pendiente`, `aprobada`, `rechazada`, `cancelada`), `EstadoDetalleEnum` (`pendiente`, `reservado`, `entregado`, `devuelto`, `rechazado`, `no_retirado`, `cancelado`), `ESTADOS_DETALLE_QUE_OCUPAN` | Valores en minúsculas, como `inventory` (DT-19) |
| `loans/schemas.py` | `OrdenPedidoCreate` (`asignatura_id` opcional, `retiro`, `devolucion`, `items[{equipamiento_id}]`, `acepta_normativa: Literal[True]`), `OrdenPedidoResponse` (con `demorado` derivado), `DetallePrestamoCreate/Response`, `AsignacionUnidad`, `OrdenPedidoResolucion`, `OrdenPedidoCancelacion`, `ErrorConflictoReserva`, `ErrorLimiteDias` | `OrdenPedidoCreate` ya no valida franja ni tope de días: pasan al servicio (P8) |
| `loans/models.py` | `OrdenPedido` y `DetallePrestamo`; columna generada `periodo = tstzrange(retiro_pactado, fin_ocupacion, '[)')`; `ExcludeConstraint` sobre `(unidad_fisica_id, periodo)` para `reservado` y `entregado`; tres `CHECK` | FK real a `usuarios`, `equipamientos` y `unidades_fisicas` |
| Migración `0009_loans_init` | Crea las dos tablas, los enums `estado_orden_enum` y `estado_detalle_enum`, la extensión `btree_gist` y la restricción | Los `CHECK` usan nombres cortos, así que el nombre final es igual con Alembic y con `create_all` (relevante para DT-26) |
| `loans/router.py` | Seis firmas en `/api/v1/loans`: `POST /ordenes`, `GET /ordenes/mias`, `PATCH /ordenes/{id}/cancelacion`, `GET /ordenes`, `GET /ordenes/{id}`, `PATCH /ordenes/{id}/resolucion` | Montado en `main.py` con tag "Préstamos y Solicitudes" |
| `loans/dependencies.py` | Placeholder con `RolEnum`, `UsuarioActual` y `get_usuario_actual` que lanza `NotImplementedError` | Los endpoints responden 500 y no exigen sesión (DT-17) |
| `loans/service.py`, tests, frontend | **No existen** (el frontend es un `.gitkeep`) | |

**Garantía de integridad ya vigente y probada en una base real:** dos líneas `reservado` o `entregado` de la misma unidad con períodos solapados no pueden coexistir; una línea `pendiente` no ocupa; devolver y retirar en el mismo instante no choca; una línea que ocupa debe tener unidad asignada.

---

## 3. Deuda técnica que resuelve este spec

| ID | Descripción (`MEMORY.md` §4) | Resolución |
| :---- | :---- | :---- |
| **DT-16** | `loans` está en `develop` sin spec | Este documento. Pasa a `APROBADO` antes de escribir código de aplicación |
| **DT-17** | `dependencies.py` es un placeholder, define un `RolEnum` propio y los endpoints responden 500 sin exigir sesión | Se **elimina** `loans/dependencies.py`. Todos los endpoints usan `Depends(get_current_user)` o `Depends(require_roles(RolUsuario...))`; la jurisdicción usa `resolver_alcance_sede`. Los roles son `RolUsuario` (`SUPERADMIN`, `ADMIN_LOCAL`, `DOCENTE`, `ESTUDIANTE`). El solicitante y la sede salen siempre del token. **Fase 0:** hasta que exista el servicio, los endpoints exigen sesión y responden `501 NO_IMPLEMENTADO` mediante `AppError` (D-L14) |
| **DT-18** | Errores como `{codigo, detalle}` con `HTTPException` | Todos los errores de negocio usan `AppError(status, "CODIGO", "mensaje")` → `{detail, code}` (§6.3). Se eliminan `ErrorConflictoReserva` y `ErrorLimiteDias`. Los errores de validación de Pydantic conservan el 422 estándar |
| **DT-19** | Tres estilos de valores de enum | **No se unifica en este spec** (requiere decisión del equipo). `loans` mantiene minúsculas, como `inventory`. Los enums están aislados en `enums.py`, de modo que una unificación futura es una migración acotada (D-L11) |
| **DT-20** | Estado de la unidad duplicado entre `inventory` (`prestado`) y `loans` (`entregado`) | `loans` **no escribe** el estado de la unidad: usa `inventory/service.py` (§10.1). Reparto: la **ocupación por fechas** es de `loans` (estado de la línea y `EXCLUDE`); la **condición física** es de `inventory`. `prestado` es un reflejo que `loans` fija al entregar y libera al devolver, en la misma transacción. `loans` no asigna unidades en `mantenimiento` o `baja` |
| DT-24 (parcial) | `main.py` y el README no describen `loans` | Se actualiza la descripción de `app/main.py` en la Fase 0; el README lo ajusta el Perfil 1 (C6) |
| DT-26 (informativo) | `NAMING_CONVENTION` duplica el prefijo de los `CHECK` en migraciones | `0009` ya usa nombres cortos; la migración `0011` seguirá el mismo criterio |

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
| Entregar, devolver, renovar | No | No | Sí (su sede) | Sí |
| Calendario maestro | No | No | Sí (su sede) | Sí |
| Panel docente y observación | No | Sí (sus asignaturas) | No | No |

Todos los endpoints requieren sesión (P4.1). Fuera de alcance de sede o de propiedad responde `404` (§4.2 de la Constitución), nunca `403`, para no revelar existencia.

---

## 5. Casos de uso

| ID | Caso de uso | Actor | Requisitos | Resumen del flujo |
| :---- | :---- | :---- | :---- | :---- |
| CU-L01 | Solicitar equipamiento | Estudiante, Docente | PRE-03, 04, 06, 07, 09 | Elige ítems (uno o carrito), fecha y hora de retiro y devolución dentro de la franja, asignatura (estudiante), acepta la normativa y envía. La orden queda `pendiente` |
| CU-L02 | Solicitar con alta gama | Estudiante, Docente | PRE-05 | Igual que CU-L01 con aval PDF obligatorio. **Diferido** (D-L12) |
| CU-L03 | Cancelar solicitud propia | Estudiante, Docente | — | Cancela una orden `pendiente` |
| CU-L04 | Validar solicitud | Admin | PRE-10, 15, 18 | Abre la bandeja de su sede, revisa (con la observación del docente), opcionalmente ajusta horarios, asigna una unidad por línea y aprueba, o rechaza con motivo |
| CU-L05 | Cancelar orden aprobada | Admin | — | Libera las unidades y registra el motivo |
| CU-L06 | Cancelación forzada | Admin | PRE-17 | Cancela una línea afectada por la baja de una unidad, con motivo obligatorio y aviso al usuario |
| CU-L07 | Entregar | Admin | PRE-13 | Confirma la entrega presencial: línea `entregado` y unidad `prestado` |
| CU-L08 | Recibir devolución | Admin | PRE-13 | Registra la devolución con observaciones: línea `devuelto` y unidad liberada |
| CU-L09 | Renovar notebook | Admin | PRE-11 | Extiende la devolución de una notebook entregada; se rechaza si choca con otra reserva |
| CU-L10 | Observar solicitudes de mi cátedra | Docente | PRE-20 | Lista de solo lectura de solicitudes de sus asignaturas y comentario |
| CU-L11 | Ver calendario maestro | Admin | PRE-16 | Recursos agrupados en "En Uso" y "En Reserva" |
| CU-L12 | Procesos automáticos | Sistema | PRE-08 | No retiro dentro de la tolerancia y demoras (RN-L22, RN-L23) |

---

## 6. Contratos de la API

Base: `/api/v1/loans` · tag "Préstamos y Solicitudes" · todos exigen `Authorization`.

### 6.1 Endpoints

| Método y ruta | Roles | Descripción | Éxito | Errores |
| :---- | :---- | :---- | :---- | :---- |
| `GET /reglas` | todos | Reglas operativas efectivas para el formulario (D-L07) | 200 | 401 |
| `POST /ordenes` | ESTUDIANTE, DOCENTE | Crea la orden `pendiente` con sus líneas | 201 | 401, 403, 404, 422 |
| `GET /ordenes/mias` | ESTUDIANTE, DOCENTE | Órdenes propias (`estado`, `limit`, `offset`) | 200 | 401, 403 |
| `GET /ordenes/docente` | DOCENTE | Panel de observación docente | 200 | 401, 403 |
| `GET /ordenes` | ADMIN_LOCAL, SUPERADMIN | Bandeja (`estado`=`pendiente` por defecto, `sede` solo SUPERADMIN, `limit`, `offset`) | 200 | 401, 403 |
| `GET /ordenes/{orden_id}` | dueño, admin con alcance, docente de la asignatura | Detalle | 200 | 401, 404 |
| `PATCH /ordenes/{orden_id}/estado` | ver §4 | Aprobar, rechazar o cancelar | 200 | 401, 403, 404, 409, 422 |
| `PATCH /ordenes/{orden_id}/detalles/{detalle_id}/estado` | ADMIN_LOCAL, SUPERADMIN | Entregar, devolver o cancelación forzada | 200 | 401, 403, 404, 409, 422 |
| `PATCH /ordenes/{orden_id}/detalles/{detalle_id}/renovacion` | ADMIN_LOCAL, SUPERADMIN | Renovar notebook | 200 | 401, 403, 404, 409, 422 |
| `PUT /ordenes/{orden_id}/observacion-docente` | DOCENTE | Comentario del docente | 200 | 401, 403, 404, 409, 422 |
| `GET /calendario` | ADMIN_LOCAL, SUPERADMIN | Calendario maestro (`desde`, `hasta`, `sede` solo SUPERADMIN) | 200 | 401, 403, 422 |

Los cambios de estado usan `PATCH /<recurso>/{id}/estado` (Constitución §4.2). Esto **renombra** los actuales `/resolucion` y `/cancelacion` (D-L02); como hoy no responden de forma útil, el cambio no afecta a ningún consumidor. En el router, `/ordenes/mias` y `/ordenes/docente` se declaran **antes** de `/ordenes/{orden_id}`.

### 6.2 Esquemas

| Esquema | Campos | Reglas |
| :---- | :---- | :---- |
| `OrdenPedidoCreate` | `asignatura_id?`, `retiro`, `devolucion`, `items[1..20]{equipamiento_id}`, `acepta_normativa` | `extra="forbid"`; `acepta_normativa` debe ser `true`; `devolucion > retiro`. No incluye `solicitante_id`, `sede` ni `estado` |
| `OrdenPedidoEstadoUpdate` | `estado` ∈ {`aprobada`, `rechazada`, `cancelada`}, `motivo?`, `asignaciones[]`, `nuevo_retiro?`, `nueva_devolucion?` | `rechazada` exige `motivo` y no admite asignaciones; `aprobada` exige una asignación por línea y admite el ajuste horario (ambas fechas juntas); `cancelada` por administrador exige `motivo` (lo valida el servicio, depende del rol). Reemplaza a `OrdenPedidoResolucion` y `OrdenPedidoCancelacion` |
| `DetalleEstadoUpdate` | `estado` ∈ {`entregado`, `devuelto`, `cancelado`}, `observacion?` (solo `devuelto`, ≤ 500), `motivo?` | `cancelado` (forzada) exige `motivo` |
| `RenovacionCreate` | `nueva_devolucion` | Fecha y hora con zona |
| `ObservacionDocenteUpdate` | `observacion` (1..500) | |
| `ReglasResponse` | `horario_apertura`, `horario_cierre`, `anticipacion_min_horas`, `max_dias_general`, `max_dias_notebook`, `tolerancia_retiro_horas` | Solo lectura, valores vigentes de `config` |
| `OrdenPedidoResponse` / `DetallePrestamoResponse` | Los actuales, más `entregado_en`, `devuelto_en`, `observacion_devolucion`, `motivo_cancelacion` en el detalle; `resuelto_en` en la orden. Para administradores y docentes, un resumen del solicitante (`id`, `nombre`, `apellido`); **nunca** DNI, email ni teléfono (P6) | `demorado` sigue siendo derivado (RN-L21) |

Todos los campos llevan `Field(..., examples=[...])` y las respuestas de error se documentan en OpenAPI (Constitución §9).

### 6.3 Errores (`AppError` → `{detail, code}`)

| `code` | HTTP | Cuándo |
| :---- | :---- | :---- |
| `NO_IMPLEMENTADO` | 501 | Solo en la Fase 0 |
| `ORDEN_NO_ENCONTRADA` | 404 | Inexistente o fuera de alcance |
| `EQUIPAMIENTO_NO_ENCONTRADO` | 404 | Inexistente o sin unidades asignables en la sede |
| `ROL_NO_AUTORIZADO` | 403 | Rol sin permiso para la acción |
| `CANCELACION_NO_PERMITIDA` | 403 | El solicitante intenta cancelar una orden `aprobada` |
| `ASIGNATURA_REQUERIDA` | 422 | Estudiante sin asignatura |
| `FRANJA_FUERA_DE_HORARIO` | 422 | Hora de retiro o devolución fuera de `horario.apertura`–`horario.cierre` |
| `ANTICIPACION_INSUFICIENTE` | 422 | Retiro antes de `ahora + solicitud.anticipacion_min_horas` |
| `LIMITE_DIAS_EXCEDIDO` | 422 | Rango mayor al máximo de alguna línea (incluye `equipamiento_id` y el máximo en el mensaje) |
| `AVAL_NO_HABILITADO` | 422 | Orden con ítems de alta gama mientras no exista PRE-05 |
| `RETIRO_VENCIDO` | 422 | Aprobar una orden cuyo retiro ya pasó, sin ajuste horario |
| `ASIGNACIONES_INVALIDAS` | 422 | Faltan, sobran, se repiten o no pertenecen a la orden |
| `UNIDAD_NO_ASIGNABLE` | 422 | Unidad de otra sede o modelo, o en `mantenimiento`/`baja` |
| `MOTIVO_REQUERIDO` | 422 | Rechazo, cancelación por administrador o cancelación forzada sin motivo |
| `RENOVACION_NO_PERMITIDA` | 422 | La línea no es notebook o no está `entregado` |
| `TRANSICION_INVALIDA` | 409 | El estado actual no admite la acción |
| `UNIDAD_NO_DISPONIBLE` | 409 | La base rechazó un solapamiento (SQLSTATE `23P01`) |
| `UNIDAD_EN_MORA` | 409 | La unidad tiene una línea `entregado` vencida |
| `RENOVACION_SOLAPADA` | 409 | La extensión choca con otra reserva (SQLSTATE `23P01`) |

Los `401` y `403` por rol los produce `require_roles` con los códigos que defina `core`; `ROL_NO_AUTORIZADO` solo se usa cuando la decisión la toma el servicio.

**Traducción de errores de base:** solo `23P01` (violación de exclusión) se convierte en `409`. Las violaciones de `CHECK` (`23514`) o de clave foránea (`23503`) no se enmascaran como conflicto: indican un defecto y devuelven 500. No se reutiliza `_commit_or_409` de `inventory`, porque traduce cualquier `IntegrityError` a un mensaje único. Tras `23P01` se hace `rollback`.

---

## 7. Modelo de datos

### 7.1 Existente (migración `0009`)

`ordenes_pedido` (`id`, `solicitante_id` FK `usuarios`, `sede` (`sede_enum`), `asignatura_id`, `estado`, `fecha_solicitud`, `observacion_docente`, `motivo_resolucion`, `es_renovado`) y `detalles_prestamo` (`id`, `orden_id`, `equipamiento_id`, `unidad_fisica_id` nullable, `estado`, `retiro_pactado`, `devolucion_pactada`, `fin_ocupacion`, `periodo` generada), con `ex_detalles_prestamo_sin_solapamiento` y los `CHECK` `rango_pactado`, `fin_ocupacion_valido` y `unidad_si_ocupa`.

### 7.2 Cambios propuestos (migración `0011_loans_ciclo_entrega`)

| Tabla | Cambio | Motivo |
| :---- | :---- | :---- |
| `ordenes_pedido` | `resuelto_por_id` (FK `usuarios`, `SET NULL`), `resuelto_en` (`timestamptz`) | Quién y cuándo resolvió (aprobó, rechazó o canceló); auditoría (USR-08) |
| `detalles_prestamo` | `entregado_en`, `devuelto_en` (`timestamptz`, nulos) | Registro de entrega y devolución (PRE-13) |
| `detalles_prestamo` | `observacion_devolucion` (`String(500)`, nula) | Estado físico al devolver; alimenta el historial de la unidad (PRE-12, PRE-13) |
| `detalles_prestamo` | `motivo_cancelacion` (`String(500)`, nula) | Cancelación forzada (PRE-17) |
| `detalles_prestamo` | `CHECK` `entrega_registrada` (`estado <> 'entregado' OR entregado_en IS NOT NULL`) y `devolucion_registrada` (`estado <> 'devuelto' OR (entregado_en IS NOT NULL AND devuelto_en IS NOT NULL)`) | Coherencia en la base (P7.1) |
| `ordenes_historial_estado` (nueva) | `id` (`BigInteger`, `Identity`), `orden_id` (FK, `CASCADE`), `estado_anterior?`, `estado_nuevo`, `motivo?`, `actor_id` (FK `usuarios`, `SET NULL`), `created_at`; índice `(orden_id, created_at)` | Traza inmutable de transiciones, igual que `usuarios_historial_estado` (P7.3, D-L10) |

Los `CHECK` de la `0011` usan nombres cortos. La migración tiene `downgrade` y se valida con upgrade → downgrade → upgrade (P7.4). Una migración posterior (`0012`) agregará `pdf_aval_id` cuando exista el almacenamiento de archivos (C4).

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
| RN-L04 | Franja operativa: la hora de retiro y la de devolución están entre `horario.apertura` y `horario.cierre` (inclusive), en la zona horaria del laboratorio (PRE-06, R4) |
| RN-L05 | Anticipación: `retiro ≥ ahora_lab() + solicitud.anticipacion_min_horas` (ADR-011) |
| RN-L06 | Plazo máximo por línea = el menor entre el parámetro del tipo (`prestamo.notebook.max_dias` si `es_notebook`, si no `prestamo.general.max_dias`) y `max_dias_prestamo` del ítem. Se cuenta en días corridos incluyendo el día de retiro y el de devolución. La orden debe cumplir el límite de **cada** línea (D-L03, D-L04) |
| RN-L07 | Asignatura obligatoria para `ESTUDIANTE`; el `DOCENTE` solicita para uso de cátedra (PRE-03, PRE-09) |
| RN-L08 | Debe aceptarse la normativa (PRE-03) |
| RN-L09 | Los ítems de alta gama requieren aval PDF (PRE-05). Mientras no exista el almacenamiento se rechazan con `AVAL_NO_HABILITADO` (D-L12) |
| RN-L10 | Cada `equipamiento_id` debe existir y tener unidades asignables en la sede del solicitante. El solicitante no elige unidades |
| RN-L11 | Toda aprobación es manual (R1). Se asigna **una unidad por línea**, que debe ser de la sede, del modelo pedido y asignable según `inventory` (no `mantenimiento` ni `baja`) |
| RN-L12 | Solo `reservado` y `entregado` ocupan. La no superposición la garantiza `EXCLUDE USING gist` y su violación (`23P01`) se traduce a `409`. El servicio puede consultar antes para dar un error específico, pero nunca reemplaza a la restricción (P7.2) |
| RN-L13 | Aprobar es **atómico**: orden, líneas y unidades en una transacción. Si una línea choca, ninguna se aprueba |
| RN-L14 | Las transiciones de una orden se serializan con `SELECT ... FOR UPDATE` sobre la fila de la orden, de modo que dos acciones simultáneas sobre la misma orden no se pisan |
| RN-L15 | Rechazar exige `motivo` |
| RN-L16 | Cancelación: el solicitante solo cancela su orden `pendiente`; el administrador solo cancela una orden `aprobada` de su sede, sin líneas `entregado`, y con motivo obligatorio |
| RN-L17 | Cancelación forzada (PRE-17): por línea, solo `reservado`, con motivo obligatorio; si no quedan líneas vigentes, la orden pasa a `cancelada`; se emite un aviso al solicitante |
| RN-L18 | Ajuste horario al aprobar (PRE-18): cumple RN-L04 y RN-L06, se aplica a todas las líneas, `fin_ocupacion` queda igual a la nueva devolución y se avisa al solicitante |
| RN-L19 | Entrega: solo una línea `reservado` de una orden `aprobada`. Llama a `inventory.marcar_unidad_prestada` en la misma transacción y registra `entregado_en`. No hay restricción horaria: el control es presencial |
| RN-L20 | Devolución: solo una línea `entregado`. Llama a `inventory.liberar_unidad`, registra `devuelto_en` y la observación del estado físico |
| RN-L21 | `demorado` es **derivado**, no se guarda: línea `entregado` y `ahora_lab() > devolucion_pactada`. La interfaz lo muestra en rojo |
| RN-L22 | Mora: el proceso `procesar_vencimientos` extiende `fin_ocupacion` de las líneas `entregado` vencidas hasta la devolución, sin tocar `devolucion_pactada`. Hasta que corra, aprobar una unidad con una línea `entregado` vencida se rechaza con `UNIDAD_EN_MORA` |
| RN-L23 | No retiro (PRE-08): una línea `reservado` cuyo retiro superó `prestamo.tolerancia_retiro_horas` pasa a `no_retirado` y libera la unidad. Si todas las líneas de la orden quedan así, la orden pasa a `cancelada`; si alguna fue entregada, la orden sigue `aprobada` (D-L09) |
| RN-L24 | Renovación (PRE-11): solo notebooks (`es_notebook`), línea `entregado`, la hace un administrador, la nueva devolución es posterior a la actual y cumple RN-L04. Si choca con otra reserva se rechaza (`RENOVACION_SOLAPADA`). Marca `es_renovado` |
| RN-L25 | Privacidad (P6): el estudiante solo ve lo propio; el docente solo ve órdenes de sus asignaturas, en lectura y observación, sin DNI, email ni teléfono; ningún rol ve solicitantes de otra sede |
| RN-L26 | Jurisdicción (P5): el `ADMIN_LOCAL` opera solo en su sede y el filtro se aplica en el `WHERE` de la consulta, no en la interfaz |
| RN-L27 | Aprobar exige `retiro_pactado > ahora_lab()`, salvo que se ajuste el horario (`RETIRO_VENCIDO`) |
| RN-L28 | Ningún valor operativo (plazos, horario, anticipación, tolerancia) se escribe fijo en el código: se leen con `obtener_parametro` (P8) |
| RN-L29 | Las fechas se comparan con `ahora_lab()` y se persisten como `timestamptz` (UTC) |

---

## 10. Integraciones entre módulos

### 10.1 `loans` consume (sin modificar esos módulos)

| De | Qué | Uso |
| :---- | :---- | :---- |
| `core` | `get_current_user`, `require_roles`, `resolver_alcance_sede`, `AppError`, `RolUsuario`, `SedeEnum`, `enum_values`, `ahora_lab` | Autenticación, alcance, errores y tiempo |
| `config` | `obtener_parametro(db, clave)` | RN-L04…L06, L23, §6.2 `ReglasResponse` |
| `inventory` | `unidades_asignables`, `unidad_es_asignable` | Aprobación (RN-L11) |
| `inventory` | `marcar_unidad_prestada`, `liberar_unidad` | Entrega y devolución (RN-L19, RN-L20), con la sesión del llamador |
| `inventory` | Lectura de datos de equipamiento y unidades (`es_notebook`, `alta_gama`, `max_dias_prestamo`, nombre, código): **no publicada hoy** (C8) | RN-L06, RN-L09, RN-L24 y respuestas para el administrador |
| `users` | Nombre y apellido por id; pertenencia docente–asignatura: **no publicados hoy** (C2) | Resumen del solicitante y panel docente |

### 10.2 `loans` publica (en `loans/service.py`, documentadas como API pública)

| Función (firma indicativa) | Para | Requisito |
| :---- | :---- | :---- |
| `ocupacion_por_unidad(db, unidad_ids, desde, hasta)` → intervalos `{unidad_id, desde, hasta, estado}` **sin identidad de solicitantes** | Perfil 2 (INV-26) | PRE-01 |
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
| Carrito (estado local con provider propio) y botón "Agregar al pedido" | Estudiante, Docente | PRE-03 | El botón vive en el catálogo de `inventory` (C11) |
| **Formulario unificado de préstamo** | Estudiante, Docente | PRE-03, 04, 06, 07, 09 | Ítems, calendario de retiro y devolución con selectores de hora limitados a la franja, selector de asignatura (solo estudiante), casilla de normativa, bloqueo del envío con errores en rojo y botón deshabilitado mientras se envía. Lee `GET /reglas` |
| Mis solicitudes | Estudiante, Docente | USR-06 | Estados y cancelación de las pendientes |
| Bandeja de validación | Admin | PRE-15 | Filtro por estado, detalle con observación del docente |
| Aprobación | Admin | PRE-10, 18 | Asignación de unidad (lista de `unidades_asignables`) y ajuste horario |
| Mostrador (entrega, devolución, renovación) | Admin | PRE-11, 13 | Alerta roja de demora y campo de observaciones |
| Calendario maestro | Admin | PRE-16 | "En Uso" y "En Reserva" |
| Panel docente | Docente | PRE-20 | Solo lectura y comentario |

El campo de aval PDF (PRE-05) se incorpora cuando exista el almacenamiento (C4).

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
| AC-L12 | Un `equipamiento_id` inexistente o sin unidades asignables en la sede responde `404 EQUIPAMIENTO_NO_ENCONTRADO` |
| AC-L13 | `SUPERADMIN` y `ADMIN_LOCAL` reciben `403` al crear; sin token, `401` |
| AC-L14 | Una orden con un ítem de alta gama responde `422 AVAL_NO_HABILITADO` mientras no exista PRE-05 |
| AC-L15 | Dos órdenes pendientes concurrentes por el mismo modelo y período se crean ambas |

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
| AC-L20 | Una unidad en `mantenimiento` o `baja` responde `422 UNIDAD_NO_ASIGNABLE` y no cambia nada |
| AC-L21 | Una unidad de otra sede o de otro modelo responde `422 UNIDAD_NO_ASIGNABLE` |
| AC-L22 | Asignaciones incompletas, repetidas o de líneas ajenas responden `422 ASIGNACIONES_INVALIDAS` |
| AC-L23 | Dos aprobaciones concurrentes de órdenes distintas sobre la misma unidad y períodos solapados: una responde `200` y la otra `409 UNIDAD_NO_DISPONIBLE`, y la perdedora queda `pendiente` sin cambios parciales |
| AC-L24 | Dos acciones concurrentes sobre la misma orden: una prospera y la otra responde `409 TRANSICION_INVALIDA` |
| AC-L25 | El ajuste horario valida franja y plazos, actualiza todas las líneas y deja `fin_ocupacion` igual a la nueva devolución |
| AC-L26 | Asignar una unidad con una línea `entregado` vencida responde `409 UNIDAD_EN_MORA` |
| AC-L27 | Rechazar sin motivo responde `422 MOTIVO_REQUERIDO`; con motivo deja la orden `rechazada` y las líneas `rechazado` |
| AC-L28 | Una transición no permitida responde `409 TRANSICION_INVALIDA` |
| AC-L29 | Un `ADMIN_LOCAL` de otra sede recibe `404`; un estudiante o docente, `403` |
| AC-L30 | Aprobar una orden cuyo retiro ya pasó responde `422 RETIRO_VENCIDO`, salvo que se ajuste el horario |

**Cancelación**

| ID | Criterio |
| :---- | :---- |
| AC-L31 | El solicitante cancela su orden `pendiente`: queda `cancelada` y las líneas `cancelado` |
| AC-L32 | El solicitante que intenta cancelar una orden `aprobada` recibe `403 CANCELACION_NO_PERMITIDA` |
| AC-L33 | El administrador cancela una orden `aprobada` con motivo y la unidad queda libre: un pedido nuevo sobre la misma unidad y período se aprueba |
| AC-L34 | El administrador sin motivo recibe `422 MOTIVO_REQUERIDO`; con una línea `entregado`, `409 TRANSICION_INVALIDA` |
| AC-L35 | La cancelación forzada de una línea exige motivo; si era la última vigente, la orden pasa a `cancelada` |

**Entrega, devolución y renovación**

| ID | Criterio |
| :---- | :---- |
| AC-L36 | Entregar una línea `reservado` la deja `entregado`, registra `entregado_en` y la unidad queda `prestado` en `inventory`, en la misma transacción |
| AC-L37 | Si `inventory` rechaza la entrega (unidad pasó a `mantenimiento`), responde `409` y no cambia nada |
| AC-L38 | Devolver una línea `entregado` la deja `devuelto`, registra `devuelto_en` y la observación, y libera la unidad |
| AC-L39 | Entregar o devolver fuera del estado correspondiente responde `409 TRANSICION_INVALIDA` |
| AC-L40 | `demorado` es `true` solo para órdenes con línea `entregado` y devolución pactada vencida |
| AC-L41 | Renovar una notebook `entregado` extiende su devolución y marca `es_renovado` |
| AC-L42 | Renovar un ítem que no es notebook responde `422 RENOVACION_NO_PERMITIDA` |
| AC-L43 | Una renovación que solapa otra reserva responde `409 RENOVACION_SOLAPADA` y no cambia nada |
| AC-L44 | Una nueva devolución anterior o igual a la actual, o fuera de franja, responde `422` |

**Procesos automáticos, calendario y panel docente**

| ID | Criterio |
| :---- | :---- |
| AC-L45 | `procesar_vencimientos` pasa a `no_retirado` las líneas `reservado` que superaron la tolerancia y libera la unidad |
| AC-L46 | Si todas las líneas de una orden quedan `no_retirado`, la orden pasa a `cancelada`; si alguna fue entregada, sigue `aprobada` |
| AC-L47 | El proceso extiende `fin_ocupacion` de las líneas `entregado` vencidas; si choca con otra reserva aprobada no falla: registra el conflicto y lo informa |
| AC-L48 | El proceso es idempotente: ejecutarlo dos veces seguidas no cambia el resultado |
| AC-L49 | El calendario maestro agrupa los recursos "En Uso" y "En Reserva" y respeta la sede del administrador |
| AC-L50 | El docente ve solo órdenes de sus asignaturas, sin DNI, email ni teléfono del solicitante, y no puede resolverlas (`403`) |
| AC-L51 | El docente registra su observación en una orden `pendiente` de su asignatura; en una ajena, `404` |

**Transversales**

| ID | Criterio |
| :---- | :---- |
| AC-L52 | Todos los endpoints responden `401` sin token |
| AC-L53 | Los errores de negocio responden `{detail, code}`; solo `23P01` se traduce a `409` y otras violaciones de base no se enmascaran como conflicto |
| AC-L54 | La migración `0011` se valida con upgrade → downgrade → upgrade |
| AC-L55 | Las pruebas de concurrencia (AC-L23, AC-L24, AC-L43) usan sesiones independientes, como en producción (ADR-013) |

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
| EC-L07 | El proceso de mora choca con una reserva ya aprobada | La base rechaza la extensión (`23P01`); el proceso informa el conflicto para que el administrador reasigne o cancele |
| EC-L08 | Equipo dado de baja lógica con órdenes pendientes | Al aprobar, la unidad no es asignable (`UNIDAD_NO_ASIGNABLE`) |
| EC-L09 | Doble envío del formulario | El backend no deduplica: crea dos órdenes pendientes; la interfaz deshabilita el botón al enviar |
| EC-L10 | Cancelación del solicitante simultánea con la aprobación | `FOR UPDATE` serializa: una prospera y la otra recibe `409 TRANSICION_INVALIDA` |
| EC-L11 | Parámetros cambiados entre el pedido y la aprobación | Aprobar no revalida plazos ni franja (la solicitud se hizo con las reglas vigentes); solo el ajuste horario las revalida |
| EC-L12 | Solicitante suspendido con órdenes vigentes | Sus órdenes no se cancelan solas; la sanción la define el Perfil 1 (USR-09) |
| EC-L13 | Aprobación parcial por concurrencia | No existe: aprobar es todo o nada (RN-L13) |

---

## 14. Fases de entrega

| Fase | Contenido | Requisitos | Bloqueos |
| :---- | :---- | :---- | :---- |
| **0. Saneamiento** | Eliminar `dependencies.py`, autenticar y autorizar los endpoints, `AppError`, rutas `/estado`, `501 NO_IMPLEMENTADO`, descripción de `main.py` | DT-16, 17, 18 | Aprobación del spec |
| **1. Solicitar** | `GET /reglas`, `POST /ordenes`, consultas propias, reglas RN-L01…L10; formulario y carrito | PRE-03, 04, 06, 07, 09 | C3 (asignaturas), C8 (lectura de `inventory`) |
| **2. Validar** | Bandeja, aprobar, rechazar, cancelar, ajuste horario, uso de `inventory/service.py`; funciones de lectura para el Perfil 2 | PRE-10, 15, 18, DT-20 | C8, C9 |
| **3. Mostrador** | Entrega, devolución, renovación, cancelación forzada; migración `0011` | PRE-11, 13, 17 | — |
| **4. Procesos y paneles** | `procesar_vencimientos` (no retiro y mora), calendario maestro, panel docente | PRE-08, 16, 20 | C2, C3, C5 |
| **5. Aval y avisos** | PDF de aval y notificaciones | PRE-05, eventos §10.3 | C4, C12 |

El frontend avanza una fase detrás del backend de cada una.

---

## 15. Decisiones y preguntas abiertas

### 15.1 Decisiones propuestas (a aprobar)

| ID | Decisión | Recomendación |
| :---- | :---- | :---- |
| D-L01 | Numeración del spec | SPEC-05 |
| D-L02 | Cambios de estado como `PATCH .../estado` (Constitución §4.2), reemplazando `/resolucion` y `/cancelacion` | Adoptar |
| D-L03 | Plazo máximo por línea = el menor entre el parámetro del tipo y `max_dias_prestamo` del ítem | Adoptar; resuelve las tres fuentes del límite. Requiere la conformidad del Perfil 2 |
| D-L04 | Los días se cuentan corridos, incluyendo el día de retiro y el de devolución | Adoptar; confirmar con la referente |
| D-L05 | Las líneas pendientes no ocupan y la unidad se asigna al aprobar | Adoptar (ya implementado en `0009`) |
| D-L06 | Solo `ESTUDIANTE` y `DOCENTE` crean órdenes; el `SUPERADMIN` no tiene sede y el `ADMIN_LOCAL` solo valida | Adoptar |
| D-L07 | `GET /api/v1/loans/reglas` para que el formulario conozca las reglas sin tocar `config` | Adoptar |
| D-L08 | Los procesos automáticos son una función idempotente más un comando de consola (`python -m app.modules.loans.cli procesar-vencimientos`); la periodicidad la resuelve el despliegue. No se agrega un planificador al servidor | Adoptar; coordinar con el Perfil 1 (C5) |
| D-L09 | Una orden cuyas líneas quedan todas `no_retirado` pasa a `cancelada` | Adoptar |
| D-L10 | Tabla `ordenes_historial_estado` | Adoptar |
| D-L11 | Los enums de `loans` siguen en minúsculas hasta que el equipo decida DT-19 | Adoptar |
| D-L12 | Sin almacenamiento de archivos, las órdenes con alta gama se rechazan (`AVAL_NO_HABILITADO`) | Adoptar |
| D-L13 | Hasta que exista el catálogo de asignaturas, `asignatura_id` no tiene FK y no se verifica su existencia | Adoptar como transitoria |
| D-L14 | Fase 0: el router se mantiene montado con `501` en lugar de desmontarlo | Adoptar; permite generar tipos del frontend y del agente |
| D-L15 | Mientras no se aclare, los límites de plazo y la anticipación se aplican también a los docentes | Adoptar como transitoria |

### 15.2 Preguntas para la referente (Natalia Ader)

1. ¿El laboratorio atiende sábados y domingos? Hoy no existe una regla de días hábiles.
2. ¿El límite de 4 días y la anticipación de 24 h aplican también a los docentes? (ya figura en `MEMORY.md` §6, pregunta 3).
3. ¿Una renovación tiene tope de días o de cantidad de veces?
4. ¿La tolerancia de retiro se mide desde la hora de retiro pactada?
5. ¿El docente debe ver nombre y apellido del estudiante?

---

## 16. Ítems de coordinación (no se modifica ningún otro módulo)

| ID | De → Para | Pedido |
| :---- | :---- | :---- |
| C1 | Perfil 3 → Perfil 1 | Confirmar que las claves de `config` existentes alcanzan (no se piden claves nuevas) |
| C2 | Perfil 3 → Perfil 1 | `users`: función pública para obtener nombre y apellido por ids y para saber si un docente está vinculado a una asignatura |
| C3 | Perfil 3 → Perfil 1 / equipo | Definir quién implementa el **catálogo de asignaturas** y el vínculo docente–asignatura. Bloquea PRE-20 y la verificación de PRE-03 |
| C4 | Perfil 3 → Perfil 1 | Almacenamiento de archivos para el aval PDF (PRE-05), previsto en el próximo spec del Perfil 1. Interfaz propuesta: subir el archivo, recibir un id y enviarlo en `OrdenPedidoCreate` como `pdf_aval_id` |
| C5 | Perfil 3 → Perfil 1 | Cómo se programa la ejecución periódica de `procesar-vencimientos` (cron, contenedor, CI/despliegue) |
| C6 | Perfil 3 → Perfil 1 | Actualizar el README: `loans` está montado en `/api/v1/loans` (DT-24) |
| C7 | Perfil 3 → Perfil 1 | `loans` publica `ordenes_de_usuario` para USR-06, 07 y 08 (§10.2) |
| C8 | Perfil 3 → Perfil 2 | Función pública de lectura de equipamiento y unidades (`es_notebook`, `alta_gama`, `max_dias_prestamo`, nombre, código, sede), para validar plazos y mostrar datos al administrador |
| C9 | Perfil 3 → Perfil 2 | Confirmar que `marcar_unidad_prestada` y `liberar_unidad` usan la sesión del llamador y no hacen `commit`, para operar en una sola transacción |
| C10 | Perfil 3 → Perfil 2 | `loans` publica `ocupacion_por_unidad`, `historial_de_unidad` y `reservas_futuras_de_unidad` (§10.2) y desbloquea la Fase B de SPEC-04. El flujo PRE-17 queda cubierto por RN-L17 |
| C11 | Perfil 3 → Perfil 2 | Frontend: botón "Agregar al pedido" y "Solicitar" en el catálogo, que usan el carrito de `loans` |
| C12 | Perfil 3 → Perfil 5 | Función pública de `notifications` y eventos de §10.3 |
| C13 | Perfil 3 → equipo | Ratificar la enmienda 1.1.1 y decidir DT-19 |

---

## 17. Trazabilidad

| Requisito | Casos de uso | Endpoint | Criterios | Fase |
| :---- | :---- | :---- | :---- | :---- |
| PRE-03 | CU-L01 | `POST /ordenes`, `GET /reglas` | AC-L02…L06, L12, L13 | 1 |
| PRE-04 | CU-L01 | `POST /ordenes` (y validación de la interfaz) | AC-L04…L06 | 1 |
| PRE-05 | CU-L02 | `POST /ordenes` | AC-L14 (hasta PRE-05) | 5 |
| PRE-06 | CU-L01 | `POST /ordenes` | AC-L07…L09 | 1 |
| PRE-07 | CU-L01 | `POST /ordenes` | AC-L10, L11 | 1 |
| PRE-08 | CU-L12 | `procesar-vencimientos` | AC-L45…L48 | 4 |
| PRE-09 | CU-L01 | `POST /ordenes` | AC-L05 | 1 |
| PRE-10 | CU-L04 | `PATCH /ordenes/{id}/estado` | AC-L19…L24, L27, L28 | 2 |
| PRE-11 | CU-L09 | `PATCH .../renovacion` | AC-L41…L44 | 3 |
| PRE-13 | CU-L07, CU-L08 | `PATCH .../detalles/{id}/estado` | AC-L36…L40 | 3 |
| PRE-15 | CU-L04 | `GET /ordenes` | AC-L17, L18 | 2 |
| PRE-16 | CU-L11 | `GET /calendario` | AC-L49 | 4 |
| PRE-17 | CU-L05, CU-L06 | `PATCH .../estado` (orden y línea) | AC-L33…L35 | 2–3 |
| PRE-18 | CU-L04 | `PATCH /ordenes/{id}/estado` | AC-L25, L30 | 2 |
| PRE-20 | CU-L10 | `GET /ordenes/docente`, `PUT .../observacion-docente` | AC-L50, L51 | 4 |
| DT-16…DT-20 | — | — | AC-L52, L53 y Fase 0 | 0 |

---

## 18. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 0.1.0 | 2026-10-23 | Borrador inicial. Documenta lo existente en `develop`, define lo pendiente y resuelve DT-16…DT-20 |
