# TASKS-05 — Préstamos (`loans`): Fase 1, Solicitar

> **Estado:** `BORRADOR` · **Versión:** 0.2.0 · **Fecha:** 2026-11-06 · **Perfil:** 3
> **Spec:** `specs/05-loans-prestamos/spec.md` v0.3.0 · **Plan:** `specs/05-loans-prestamos/plan.md` v0.2.0
> Cada tarea es chica y verificable. Las tareas que dependen de otros perfiles (C8, `files`, K10) se aíslan para que el resto avance. **No se mergea `POST /ordenes` hasta que la v0.3.0 esté aprobada (V4).**

Leyenda: `[ ]` pendiente · `[~]` bloqueada o en curso · `[x]` hecha

---

## Backend

| ID | Tarea | Criterios | Verificación | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **T1.0** | Verificaciones previas V1…V4 del plan: `core/settings.py` (`ahora_lab`, `ZONA_HORARIA_LAB`), fábricas de tests, estado de C8 y C3, y el spec en `APROBADO` | — | Plan §2. V1…V3 hechas; **V4 pendiente** (v0.3.0 en revisión del Perfil 1) | `[~]` |
| **T1.1** | `ReglasResponse` en `schemas.py`, `service.reglas(db)` y `GET /reglas` (cualquier usuario autenticado), con el **horario global** | AC-L01, AC-L52 | `tests/loans/test_reglas.py`: devuelve los valores sembrados; con `set_parametro` el valor cambia; sin token, `401`. El horario por sede es T1.13 | `[x]` |
| **T1.2** | Funciones puras de fechas en `service.py`: `_a_hora_lab`, `_validar_franja`, `_validar_anticipacion`, `_dias_corridos` | AC-L07, L08, L09; EC-L02, L03, L04 | `tests/loans/test_validaciones.py` (sin base de datos): horas exactas de apertura y cierre válidas; fuera de franja inválidas; anticipación justa válida; zona horaria distinta; mismo día | `[x]` |
| **T1.3** | `_limite_dias(es_notebook, max_general, max_notebook, max_item)` y `_validar_plazo` | AC-L10, L11; EC-L01 | Unitarias: equipo común 4, notebook 15, el menor entre parámetro e ítem; el error trae `equipamiento_id` y `max_dias` | `[x]` |
| **T1.4** | Unidades libres por período: `ids_unidades_libres` (interna, ids por modelo), `unidades_libres` (pública, cantidades, spec §10.2) y `_validar_disponibilidad` (pura, `409 EQUIPAMIENTO_NO_DISPONIBLE`) | AC-L56, L57 | `tests/loans/test_unidades_libres.py` (integración): criterio físico, sede, ítem inactivo, reserva que se solapa y en otras fechas, períodos consecutivos, estados que no ocupan, varios modelos, período inválido, cantidades. `test_validaciones.py`: disponibilidad suficiente, justa, sin unidades, modelo ausente, más líneas que unidades | `[x]` |
| **T1.5** | Adaptador de lectura de equipamiento con interfaz propia: `DatosEquipamiento` y `_datos_items(db, ids)` (plan §4.6). Responde `501` hasta C8 | AC-L12 | Los tests lo reemplazan con `monkeypatch`; sin reemplazo, `POST /ordenes` responde `501 NO_IMPLEMENTADO` | `[x]` |
| **T1.6** | `service.crear_orden` con el orden de validaciones del plan §4.3 (corte §1.1), el handler de `POST /ordenes` y los códigos de `AppError` del spec §6.3 | AC-L02…L13, L15, L56, L57 | `tests/loans/test_crear_orden.py`: estudiante y docente, carrito con repetidos, asignatura, franja, anticipación, plazo (con datos extra del error), notebook, ítem inexistente e inactivo, alta gama, sin unidades libres, reserva en otras fechas, más líneas que unidades, otra sede, dos pendientes sobre el mismo modelo, renovación en `501`. `test_contratos.py`: campos extra, normativa, `SUPERADMIN` y `ADMIN_LOCAL` en `403`. **Sin merge hasta V4** | `[x]` |
| **T1.7** | `service.listar_mis_ordenes` (con `estado`, `limit`, `offset`) y `service.obtener_orden` (solo el dueño) | AC-L16, L18 | `tests/loans/test_consulta.py`: solo las propias, una ajena responde `404`, paginación | `[x]` |
| **T1.8** | Actualizar `tests/loans/test_contratos.py`: los endpoints implementados dejan de esperar `501`; los pendientes lo conservan | AC-L52 | La suite sigue en verde | `[x]` |
| **T1.9** | Cierre: `ruff check`, `ruff format --check`, `pytest -q` completo, revisar `/docs`, actualizar `MEMORY.md` y el estado del spec, abrir el PR | Plan §6 | PR con `base: develop`, después de V4 | `[ ]` |
| **T1.10** | Esquema: `pdf_aval_id: UUID \| None` y `renueva_detalle_id: int \| None` en `OrdenPedidoCreate`; una renovación lleva una sola línea | AC-L04, RN-L24 | `tests/loans/test_schemas.py`: sin aval ni renovación por defecto, UUID válido e inválido, renovación con una y con dos líneas, id no positivo | `[x]` |
| **T1.11** | Conectar `_datos_items` a la función pública de `inventory` | AC-L12 | Depende de **C8**. Se reemplaza el cuerpo del adaptador; los tests de `test_crear_orden.py` no cambian, y el test del `501` sin C8 se borra | `[~]` |
| **T1.12** | Aval de alta gama: `vincular_archivo` en la misma transacción que la orden; con aval válido se crea, sin aval `422 AVAL_REQUERIDO`; los errores de `files` se propagan | AC-L14, L60 | Depende de **`files`** (SPEC-03) en `develop`. Si la creación falla, el archivo no queda vinculado | `[~]` |
| **T1.13** | Horario por sede en `GET /reglas` y en la franja de `crear_orden` (`sede` en `ReglasResponse`, `?sede=` para el `SUPERADMIN`) | AC-L63, RN-L04 | Depende de **K10** (claves por sede en `config`). Cambia solo la lectura de parámetros | `[~]` |
| **T1.14** | Renovación (RN-L24): `renueva_detalle_id` debe ser una línea `entregado` propia de una notebook (si no, `422 RENOVACION_NO_PERMITIDA`), sin anticipación mínima, y la unidad renovada cuenta como libre para esa orden | PRE-11, RN-L24 | **Fuera de este corte.** Necesita su propio diseño de disponibilidad, porque la notebook está `prestado` y `unidades_asignables` no la devuelve | `[ ]` |

**Orden sugerido:** T1.0 → T1.1 → T1.2 → T1.3 → T1.7 → T1.4 → T1.10 → T1.5 → T1.6 → T1.8 → (con V4) T1.9. Después, a medida que se destraben: T1.11 (C8), T1.12 (`files`), T1.13 (K10) y T1.14.

**Commits sugeridos** (Conventional Commits en español):

- `feat(loans): GET /reglas con los parámetros vigentes (SPEC-05, AC-L01)`
- `feat(loans): validaciones puras de franja, anticipación y plazo (SPEC-05)`
- `feat(loans): consulta de órdenes propias (SPEC-05, AC-L16)`
- `feat(loans): cálculo de unidades libres por modelo y período (SPEC-05, RN-L10)`
- `feat(loans): aval y renovación en el esquema de la orden (SPEC-05, RN-L09, RN-L24)`
- `feat(loans): crear orden de pedido con adaptador de inventory (SPEC-05, PRE-03…PRE-09)`

---

## Frontend

Dependen de que el contrato de `POST /ordenes` esté estable (después de T1.6) y de C11.

| ID | Tarea | Requisito | Verificación | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **F1.1** | Estructura `src/features/loans/{components,pages,services,types}` y DTOs `snake_case` espejo de los esquemas, con `mappers.ts` | — | Los tipos compilan con TypeScript estricto | `[ ]` |
| **F1.2** | Servicio `loansApi` sobre `src/lib/api.ts` (`reglas`, `crearOrden`, `misOrdenes`, `obtenerOrden`) con `ApiError {status, code, detail}` | — | Prueba con el servidor local | `[ ]` |
| **F1.3** | Carrito (estado local con provider propio) | PRE-03 | Agregar, quitar y repetir ítems | `[ ]` |
| **F1.4** | Formulario unificado: calendario de retiro y devolución con selectores de hora limitados por `GET /reglas`, asignatura (solo estudiante), casilla de normativa, errores en rojo y botón deshabilitado mientras se envía | PRE-03, 04, 06, 07, 09 | El backend sigue siendo la garantía (P2.2) | `[ ]` |
| **F1.5** | Pantalla "Mis solicitudes" con estados y paginación | USR-06 | Lista las propias y muestra `demorado` | `[ ]` |
| **F1.6** | Botón "Solicitar" en el catálogo de `inventory`, deshabilitado sin unidades libres | PRE-03 | Coordinado con el Perfil 2 (C11, C16) | `[~]` |
| **F1.7** | Manejo de errores del servidor: `409 EQUIPAMIENTO_NO_DISPONIBLE` (volver al carrito), `422` de plazo (resaltar la línea) | PRE-04 | Mensajes en español, según `code` | `[ ]` |

---

## Riesgos

- **C8 no llega a tiempo:** la lógica y los tests de `crear_orden` ya están contra el adaptador (T1.5); solo T1.11 queda bloqueada. Mientras tanto, la API real responde `501` en `POST /ordenes`.
- **El Perfil 2 elige otra firma para C8:** el cambio queda en `_datos_items`, un solo lugar.
- **La v0.3.0 cambia en la revisión:** `crear_orden` es la parte más expuesta; por eso no se mergea antes de V4.
- **Parámetros fuera de rango:** `config` ya valida plazos y horarios coherentes; los tests usan `set_parametro` para probar los bordes.
