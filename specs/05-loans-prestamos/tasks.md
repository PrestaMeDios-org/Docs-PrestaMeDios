# TASKS-05 — Préstamos (`loans`): Fases 1 y 2

> **Estado:** `BORRADOR` · **Versión:** 0.4.2 · **Fecha:** 2026-11-10 · **Perfil:** 3
> **Spec:** `specs/05-loans-prestamos/spec.md` v1.0.1 (`APROBADO` v1.0.0; la v1.0.1 corrige EC-L10) · **Plan:** `specs/05-loans-prestamos/plan.md` v0.4.2
> Cada tarea es chica y verificable. Las tareas que dependen de otros perfiles (`files`, K10) se aíslan para que el resto avance.

Leyenda: `[ ]` pendiente · `[~]` bloqueada o en curso · `[x]` hecha

---

## Fase 1, Solicitar — Backend

Implementada y mergeada en `develop` (backend PR #21).

| ID | Tarea | Criterios | Verificación | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **T1.0** | Verificaciones previas V1…V4 del plan: `core/settings.py` (`ahora_lab`, `ZONA_HORARIA_LAB`), fábricas de tests, estado de C8 y C3, y el spec en `APROBADO` | — | Plan §2. V1…V4 hechas (spec aprobada el 2026-11-07) | `[x]` |
| **T1.1** | `ReglasResponse` en `schemas.py`, `service.reglas(db)` y `GET /reglas` (cualquier usuario autenticado), con el **horario global** | AC-L01, AC-L52 | `tests/loans/test_reglas.py`: devuelve los valores sembrados; con `set_parametro` el valor cambia; sin token, `401`. El horario por sede es T1.13 | `[x]` |
| **T1.2** | Funciones puras de fechas en `service.py`: `_a_hora_lab`, `_validar_franja`, `_validar_anticipacion`, `_dias_corridos` | AC-L07, L08, L09; EC-L02, L03, L04 | `tests/loans/test_validaciones.py` (sin base de datos): horas exactas de apertura y cierre válidas; fuera de franja inválidas; anticipación justa válida; zona horaria distinta; mismo día | `[x]` |
| **T1.3** | `_limite_dias(es_notebook, max_general, max_notebook, max_item)` y `_validar_plazo` | AC-L10, L11; EC-L01 | Unitarias: equipo común 4, notebook 15, el menor entre parámetro e ítem; el error trae `equipamiento_id` y `max_dias` | `[x]` |
| **T1.4** | Unidades libres por período: `ids_unidades_libres` (interna, ids por modelo), `unidades_libres` (pública, cantidades, spec §10.2) y `_validar_disponibilidad` (pura, `409 EQUIPAMIENTO_NO_DISPONIBLE`) | AC-L56, L57 | `tests/loans/test_unidades_libres.py` (integración): criterio físico, sede, ítem inactivo, reserva que se solapa y en otras fechas, períodos consecutivos, estados que no ocupan, varios modelos, período inválido, cantidades. `test_validaciones.py`: disponibilidad suficiente, justa, sin unidades, modelo ausente, más líneas que unidades | `[x]` |
| **T1.5** | Adaptador provisorio de lectura de equipamiento (`DatosEquipamiento` y `_datos_items`, plan §4.6), que respondía `501` mientras faltaba C8 | AC-L12 | Reemplazado por la función de `inventory` en T1.11 | `[x]` |
| **T1.6** | `service.crear_orden` con el orden de validaciones del plan §4.3 (corte §1.1), el handler de `POST /ordenes` y los códigos de `AppError` del spec §6.3 | AC-L02…L13, L15, L56, L57 | `tests/loans/test_crear_orden.py`: estudiante y docente, carrito con repetidos, asignatura, franja, anticipación, plazo (con datos extra del error), notebook, ítem inexistente e inactivo, alta gama, sin unidades libres, reserva en otras fechas, más líneas que unidades, otra sede, dos pendientes sobre el mismo modelo, renovación en `501`. `test_contratos.py`: campos extra, normativa, `SUPERADMIN` y `ADMIN_LOCAL` en `403`. **Sin merge hasta V4** | `[x]` |
| **T1.7** | `service.listar_mis_ordenes` (con `estado`, `limit`, `offset`) y `service.obtener_orden` (solo el dueño) | AC-L16, L18 | `tests/loans/test_consulta.py`: solo las propias, una ajena responde `404`, paginación | `[x]` |
| **T1.8** | Actualizar `tests/loans/test_contratos.py`: los endpoints implementados dejan de esperar `501`; los pendientes lo conservan | AC-L52 | La suite sigue en verde | `[x]` |
| **T1.9** | Cierre: `ruff check`, `pytest -q` completo, revisar `/docs`, actualizar `MEMORY.md` y el estado del spec, abrir el PR | Plan §6 | Backend PR #21 mergeado en `develop` (151 tests de `loans`; 496 en la suite, con la DT-30 de `users` como único fallo) | `[x]` |
| **T1.10** | Esquema: `pdf_aval_id: UUID \| None` y `renueva_detalle_id: int \| None` en `OrdenPedidoCreate`; una renovación lleva una sola línea | AC-L04, RN-L24 | `tests/loans/test_schemas.py`: sin aval ni renovación por defecto, UUID válido e inválido, renovación con una y con dos líneas, id no positivo | `[x]` |
| **T1.11** | Usar `inventory.datos_equipamiento_por_ids` (C8) en `crear_orden` y borrar el adaptador provisorio | AC-L12 | `test_crear_orden.py` corre contra la base real, sin la función falsa; se borra el test del `501` sin C8 | `[x]` |
| **T1.12** | Aval de alta gama: `vincular_archivo` en la misma transacción que la orden; con aval válido se crea, sin aval `422 AVAL_REQUERIDO`; los errores de `files` se propagan | AC-L14, L60 | **Desbloqueada** el 2026-11-08: `files` está en `develop` (backend PR #26; ver K3 en `MEMORY.md` §5). Si la creación falla, el archivo no queda vinculado | `[ ]` |
| **T1.13** | Horario por sede en `GET /reglas` y en la franja de `crear_orden` (`sede` en `ReglasResponse`, `?sede=` para el `SUPERADMIN`) | AC-L63, RN-L04 | Depende de **K10** (claves por sede en `config`). Cambia solo la lectura de parámetros | `[~]` |
| **T1.14** | Renovación (RN-L24): `renueva_detalle_id` debe ser una línea `entregado` propia de una notebook (si no, `422 RENOVACION_NO_PERMITIDA`), sin anticipación mínima, y la unidad renovada cuenta como libre para esa orden | PRE-11, RN-L24 | **Fuera de este corte.** Necesita su propio diseño de disponibilidad, porque la notebook está `prestado` y `unidades_asignables` no la devuelve | `[ ]` |
| **T1.15** | `ocupacion_de_unidades(db, unidad_ids, desde, hasta)` (spec §10.2): por unidad, los períodos ocupados que se solapan con el rango, en una sola consulta y sin identidad, para el mini-calendario del Perfil 2 | PRE-01, INV-26 | `tests/loans/test_ocupacion.py`: períodos por unidad ordenados, estados que no ocupan, solapamiento semiabierto sin recorte, entrada vacía sin consulta, una sola consulta, repetidos, unidad inexistente, período inválido, resultado inmutable y sin identidad | `[x]` |

**Orden sugerido:** T1.0 → T1.1 → T1.2 → T1.3 → T1.7 → T1.4 → T1.10 → T1.5 → T1.6 → T1.8 → (con V4) T1.9. T1.11 y T1.15 se hicieron al llegar C8. Quedan, a medida que se destraben: T1.12 (`files`), T1.13 (K10) y T1.14.

**Commits** (rama `feat/loans-solicitudes`, Conventional Commits en español):

- `feat(loans): GET /reglas y consulta de órdenes propias (SPEC-05, AC-L01, AC-L16)`
- `feat(loans): validaciones puras de franja, anticipación y plazo (SPEC-05)`
- `feat(loans): unidades libres por modelo y período (SPEC-05, RN-L10)`
- `feat(loans): aval y renovación en el esquema de la orden (SPEC-05, RN-L09, RN-L24)`
- `feat(loans): crear orden de pedido (SPEC-05, PRE-03…PRE-09)`
- `feat(loans): ocupación de unidades por período para inventory (SPEC-05 §10.2, PRE-01)`

---

## Fase 1, Solicitar — Frontend

Dependen de que el contrato de `POST /ordenes` esté estable (después de T1.6) y de C11.

| ID | Tarea | Requisito | Verificación | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **F1.1** | Estructura `src/features/loans/{components,pages,services,types}` y DTOs `snake_case` espejo de los esquemas, con `mappers.ts` | — | Frontend PR #18 | `[x]` |
| **F1.2** | Servicio `loansApi` sobre `src/lib/api.ts` (`reglas`, `crearOrden`, `misOrdenes`, `obtenerOrden`) con `ApiError {status, code, detail}` | — | Frontend PR #18 | `[x]` |
| **F1.3** | Carrito (estado local con provider propio) | PRE-03 | Frontend PR #18: `CarritoContext` exportable, para el botón del catálogo | `[x]` |
| **F1.4** | Formulario unificado: calendario de retiro y devolución con selectores de hora limitados por `GET /reglas`, asignatura (solo estudiante), casilla de normativa, errores en rojo y botón deshabilitado mientras se envía | PRE-03, 04, 06, 07, 09 | El backend sigue siendo la garantía (P2.2) | `[ ]` |
| **F1.5** | Pantalla "Mis solicitudes" con estados y paginación | USR-06 | Lista las propias y muestra `demorado` | `[ ]` |
| **F1.6** | Botón "Solicitar" en el catálogo de `inventory`, deshabilitado sin unidades libres | PRE-03 | Frontend PR #18: carrito conectado al catálogo (C11) | `[x]` |
| **F1.7** | Manejo de errores del servidor: `409 EQUIPAMIENTO_NO_DISPONIBLE` (volver al carrito), `422` de plazo (resaltar la línea) | PRE-04 | Mensajes en español, según `code` | `[ ]` |

---

## Fase 2, Validar — Backend

Plan §8. Rama `feat/loans-validar`. Las tareas T2.1…T2.8 son las de la demo; T2.9 y T2.10, si queda tiempo; T2.11 y T2.12 destraban la Fase C del Perfil 2.

| ID | Tarea | Criterios | Verificación | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **T2.0** | Verificaciones V5…V8 del plan §8.3; acordar la cadena de `0011` con los Perfiles 1 y 5 (C19) | — | Notas en el PR. C19 resuelto: la `0011` cuelga de `0013_notifications_init` (backend PR #23) | `[x]` |
| **T2.1** | Migración `0011_loans_resolucion` y modelos: `resuelto_por_id`, `resuelto_en` y `ordenes_historial_estado` | AC-L54 | `tests/loans/test_migracion_0011.py`: upgrade → downgrade → upgrade; `alembic heads` con una sola cabeza | `[x]` |
| **T2.2** | `OrdenPedidoResponse` con `resuelto_en`, `situacion` (RN-L31) y `solicitante` (solo para administradores) | AC-L61 | `test_schemas.py`: `situacion` según los estados de las líneas | `[x]` |
| **T2.3** | `_orden_con_alcance` (con `FOR UPDATE` opcional) y `GET /ordenes/{id}` para administradores con jurisdicción, con el resumen del solicitante; reemplazar el `assert` de `crear_orden` por un `AppError` (O2) | AC-L16, L29 | `test_bandeja.py`: el admin de la sede lo ve con nombre y apellido; el de otra sede y otro estudiante reciben `404`; nunca DNI, email ni teléfono | `[x]` |
| **T2.4** | Bandeja `GET /ordenes`: alcance de sede con `resolver_alcance_sede`, `estado` (por defecto `pendiente`), `limit` y `offset`, de la más vieja a la más nueva, solicitante en una sola llamada | AC-L17, L18 | `test_bandeja.py`: sede propia, `SUPERADMIN` con y sin `?sede=`, `ADMIN_LOCAL` pidiendo otra sede (`403`), filtro por estado, paginación, estudiante y docente en `403` | `[x]` |
| **T2.5** | `GET /ordenes/{id}/unidades-libres` con `ids_unidades_libres` | AC-L47, L58 | `test_aprobar.py`: solo unidades del modelo y la sede, `disponible` y sin solapamiento; una reserva en otras fechas sí aparece; fuera de alcance `404` | `[x]` |
| **T2.6** | `PATCH …/estado`: rechazar con motivo y cancelar la propia `pendiente`; historial de estados en cada transición | AC-L27, L28, L31, L32 | `test_rechazar_cancelar.py`: sin motivo `422`; líneas `rechazado` o `cancelado`; dueño que cancela una `aprobada` `403 CANCELACION_NO_PERMITIDA`; dueño que intenta aprobar `403`; transición inválida `409`; fila en `ordenes_historial_estado` | `[x]` |
| **T2.7** | `PATCH …/estado`: aprobar con asignaciones (plan §8.5.5), bloqueo de la orden y de las unidades en orden, traducción de `23P01` | AC-L19…L22, L26, L30, L47, L53 | `test_aprobar.py`: aprobación válida con `resuelto_*`; unidad `prestado`, en `mantenimiento` o `baja`, de otra sede o de otro modelo `422 UNIDAD_NO_ASIGNABLE`; asignaciones incompletas, repetidas o ajenas `422`; retiro vencido `422`; unidad con reserva solapada `409 UNIDAD_NO_DISPONIBLE` sin cambios parciales | `[x]` |
| **T2.8** | Concurrencia: dos aprobaciones sobre la misma unidad, dos acciones sobre la misma orden y cancelación simultánea con aprobación | AC-L23, L24, L55; EC-L10 | `test_concurrencia.py` con pedidos en paralelo y sesiones independientes | `[x]` |
| **T2.9** | Cancelar una orden `aprobada` (administrador): motivo obligatorio, sin líneas `entregado`, unidades liberadas | AC-L33, L34 | Backend PR #28 (`test_rechazar_cancelar.py`) | `[x]` |
| **T2.10** | Ajuste horario al aprobar (PRE-18): franja y plazo por línea, retiro futuro, todas las líneas, `fin_ocupacion` igual a la nueva devolución | AC-L25, AC-L30 | Backend PR #28 (`test_aprobar.py`) | `[x]` |
| **T2.11** | `reservas_futuras_de_unidad(db, unidad_id, desde)` (spec §10.2) | PRE-17 | `test_lecturas_inventory.py`: solo `reservado` con retiro desde la fecha, ordenadas; sin identidad; una consulta | `[x]` |
| **T2.12** | `historial_de_unidad(db, unidad_id, actor, *, limit, offset)` (spec §10.2) con los campos de SPEC-04 §5.5 (`entregado_en`, `devuelto_en` y `observacion_devolucion` en `None` hasta `0012`) | PRE-12 | `test_lecturas_inventory.py`: orden por retiro descendente, alcance del `ADMIN_LOCAL`, solicitante con nombre y apellido, paginación | `[x]` |
| **T2.13** | Notificaciones `ORDEN_APROBADA`, `ORDEN_RECHAZADA`, `ORDEN_CANCELADA` y `ORDEN_HORARIO_AJUSTADO` dentro de la transacción (plan §8.5.8) | §10.3, C-N01 | Depende de `crear_notificacion` (SPEC-06 Fase B) en `develop` | `[~]` |
| **T2.14** | Cierre: `test_contratos.py` sin `501` para la bandeja y el `PATCH`; `ruff check`, `pytest -q` completo, `/docs`, `MEMORY.md`, este archivo y el PR | Plan §8.9 | Backend PR #23 y #28 mergeados en `develop`; suite completa en verde (895 tests al 2026-11-10) | `[x]` |

**Avance (2026-11-08):** T2.0…T2.8, T2.11 y T2.12 hechas en el backend PR #23 (`feat/loans-validar`), con 255 tests en `tests/loans/`. T2.9 y T2.10 responden `501` y van en un PR aparte, después del merge del #23. T2.13 sigue esperando `crear_notificacion`.

**Orden sugerido:** T2.0 → T2.1 → T2.2 → T2.3 → T2.4 → T2.6 → T2.5 → T2.7 → T2.8 → (si queda tiempo) T2.9 → T2.10 → T2.11 → T2.12 → T2.14. T2.13 cuando llegue `crear_notificacion`.

**Commits sugeridos** (Conventional Commits en español):

- `feat(loans): migración 0011 con resolución e historial de estados (SPEC-05, D-L10)`
- `feat(loans): bandeja y detalle para administradores (SPEC-05, AC-L17, AC-L29)`
- `feat(loans): rechazar y cancelar órdenes pendientes (SPEC-05, AC-L27, AC-L31)`
- `feat(loans): aprobar con asignación de unidades (SPEC-05, PRE-10, AC-L19)`
- `test(loans): concurrencia de aprobaciones y cancelaciones (SPEC-05, AC-L23, AC-L24)`
- `feat(loans): cancelar órdenes aprobadas y ajuste horario (SPEC-05, PRE-18)`
- `feat(loans): reservas futuras e historial por unidad para inventory (SPEC-05 §10.2)`

## Fase 2, Validar — Frontend

Dependen de F1.1 y F1.2 (tipos y `loansApi`) y del contrato de la Fase 2 en `develop`.

| ID | Tarea | Requisito | Verificación | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **F2.1** | Bandeja del administrador: pendientes de su sede (el `SUPERADMIN` filtra por sede), paginación, solicitante con nombre y apellido, marca de retiro vencido | PRE-15 | Prueba con el servidor local | `[ ]` |
| **F2.2** | Detalle para aprobar: una unidad por línea elegida de `GET …/unidades-libres` (con el código de inventario, ver Q1 del plan) | PRE-10 | Errores `UNIDAD_NO_ASIGNABLE` y `UNIDAD_NO_DISPONIBLE` en rojo, en la línea | `[ ]` |
| **F2.3** | Rechazar con motivo obligatorio y, si entra T2.9, cancelar una aprobada | PRE-10 | El botón se habilita con el motivo escrito | `[ ]` |
| **F2.4** | "Mis solicitudes": cancelar una orden propia `pendiente` | CU-L03 | La orden pasa a `cancelada` en la lista | `[ ]` |
| **F2.5** | Ajuste horario al aprobar, si entra T2.10 | PRE-18 | Selectores de hora limitados por `GET /reglas` | `[ ]` |

---

## Riesgos

- **Dos cabezas de Alembic:** `0011` (esta fase) y `0013` (SPEC-06) parten de `0010`. La que se mergea segunda reapunta su `down_revision` (plan §8.3, V5).
- **Concurrencia:** los tests de AC-L23, AC-L24 y EC-L10 verifican el resultado (uno gana, el otro recibe el código esperado), no el orden.
- **Parámetros fuera de rango:** `config` ya valida plazos y horarios coherentes; los tests usan `set_parametro` para probar los bordes.
