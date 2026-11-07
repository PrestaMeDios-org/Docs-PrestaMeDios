# PLAN-05 — Préstamos (`loans`): Fase 1, Solicitar

> **Estado:** `BORRADOR` · **Versión:** 0.3.0 · **Fecha:** 2026-11-06 · **Perfil:** 3
> **Spec:** `specs/05-loans-prestamos/spec.md` v1.0.0, `APROBADO` (§14, Fase 1) · **Tareas:** `specs/05-loans-prestamos/tasks.md`
> Este plan define el **cómo** de la Fase 1. Las Fases 2 a 5 se planifican cuando se cierre cada fase anterior.

---

## 1. Alcance de la Fase 1

| Endpoint | Rol | Requisitos | Criterios (SPEC-05 §12) |
| :---- | :---- | :---- | :---- |
| `GET /api/v1/loans/reglas` | todos | PRE-06, PRE-07 | AC-L01 (AC-L63, horario por sede, pendiente de K10) |
| `POST /api/v1/loans/ordenes` | ESTUDIANTE, DOCENTE | PRE-03, 04, 05, 06, 07, 09 | AC-L02…L15, L56, L57 |
| `GET /api/v1/loans/ordenes/mias` | ESTUDIANTE, DOCENTE | USR-06 | AC-L16, L18 |
| `GET /api/v1/loans/ordenes/{orden_id}` | dueño | — | AC-L16 |

`GET /ordenes` (bandeja) y `PATCH /ordenes/{id}/estado` siguen en `501 NO_IMPLEMENTADO` hasta la Fase 2. En esta fase el detalle solo lo ve el dueño; el acceso de administradores y docentes se agrega en las Fases 2 y 4.

Reglas que se implementan: RN-L01…RN-L10 (sede, solicitante, estado inicial, franja, anticipación, plazo, asignatura, normativa, alta gama, unidades libres) y RN-L28, RN-L29.

### 1.1 Corte de esta primera entrega

Mientras se aprueba la v0.3.0 y llega `files` (SPEC-03), `POST /ordenes` se entrega recortado:

| Tema | En este corte | Cuándo se completa |
| :---- | :---- | :---- |
| **Renovación** (RN-L24, `renueva_detalle_id`) | **Fuera de alcance.** El esquema ya acepta el campo, pero el servicio responde `501 NO_IMPLEMENTADO` | Tarea propia (T1.14), con su propio diseño de disponibilidad: la notebook a renovar está `prestado`, no figura en `unidades_asignables` y debe contar como libre para esa orden |
| **Aval** (RN-L09, `pdf_aval_id`) | Toda orden con un ítem de alta gama responde `422 AVAL_REQUERIDO`, traiga o no `pdf_aval_id`, porque todavía no se puede vincular el archivo | Cuando `files` esté en `develop` (T1.12) |
| **Lectura de equipamiento** (C8) | **Resuelto** (2026-11-06): `crear_orden` usa `inventory.datos_equipamiento_por_ids` (PR #19 del backend) | — |
| **Horario por sede** (K10, AC-L63) | Se leen `horario.apertura` y `horario.cierre` globales | Cuando `config` publique las claves por sede (T1.13): cambia la lectura, no la regla |

---

## 2. Verificaciones previas (antes de escribir código)

| # | Qué verificar | Dónde | Resultado (2026-11-06) |
| :---- | :---- | :---- | :---- |
| V1 | `ahora_lab()` y `ZONA_HORARIA_LAB` existen y su firma (S6) | `app/core/settings.py` | Verificado |
| V2 | Cómo crean los tests de `inventory` y `spaces` equipamiento, unidades y usuarios (para armar las fábricas de `loans`) | `tests/inventory/`, `tests/conftest.py` | Verificado: las fábricas de `loans` viven en `tests/conftest.py` |
| V3 | Estado de C8 (lectura de equipamiento en `inventory`) y de C3 (asignaturas) | Respuesta del Perfil 2 y del equipo | C8 resuelto por el Perfil 2 (`datos_equipamiento_por_ids`, PR #19). C3 sin cambios (D-L13) |
| V4 | Que el spec esté `APROBADO` (Constitución P1) | `Docs-PrestaMeDios` | **Aprobado** (v1.0.0, 2026-11-07) |

---

## 3. Archivos

| Archivo | Acción | Contenido |
| :---- | :---- | :---- |
| `app/modules/loans/service.py` | **Crear** | Reglas y orquestación (§4). Todas las funciones públicas reciben `db` y `actor` |
| `app/modules/loans/schemas.py` | Modificar | Agregar `ReglasResponse`; `pdf_aval_id` y `renueva_detalle_id` en `OrdenPedidoCreate` (§4.5) |
| `app/modules/loans/router.py` | Modificar | `GET /reglas`; los cuatro endpoints de la fase delegan en `service`; el resto sigue en `501` |
| `tests/loans/test_validaciones.py` | **Crear** | Pruebas unitarias de las funciones puras (sin base de datos) |
| `tests/loans/test_reglas.py` | **Crear** | Integración de `GET /reglas` |
| `tests/loans/test_unidades_libres.py` | **Crear** | Integración de `ids_unidades_libres` y `unidades_libres` |
| `tests/loans/test_crear_orden.py` | **Crear** | Integración de `POST /ordenes`, contra la base real |
| `tests/loans/test_ocupacion.py` | **Crear** | Integración de `ocupacion_de_unidades` (incluye que use una sola consulta) |
| `tests/loans/test_consulta.py` | **Crear** | Integración de `GET /ordenes/mias` y `GET /ordenes/{id}` |
| `tests/loans/test_schemas.py` | Modificar | Forma de `pdf_aval_id` y `renueva_detalle_id` |
| `tests/conftest.py` | Modificar | Fábricas `crear_equipamiento` y `crear_linea` (según V2) |
| `tests/loans/test_contratos.py` | Modificar | Los endpoints implementados dejan de esperar `501` |

**Sin migraciones ni dependencias nuevas en esta fase.** `resuelto_por_id`, `resuelto_en` y el historial llegan en `0011` (Fase 2). La garantía de no superposición ya existe: es el `EXCLUDE` de `0009` (D-L17 descartada, spec §15.3).

---

## 4. Diseño de `service.py`

### 4.1 Funciones puras (sin base de datos, con pruebas unitarias)

| Función | Regla | Detalle |
| :---- | :---- | :---- |
| `_a_hora_lab(instante)` | RN-L29 | Convierte un `datetime` con zona a la zona del laboratorio |
| `_validar_franja(retiro, devolucion, apertura, cierre)` | RN-L04 | La hora local de ambos extremos está entre apertura y cierre, **inclusive**. Error `FRANJA_FUERA_DE_HORARIO` (422) |
| `_validar_anticipacion(retiro, ahora, horas)` | RN-L05 | `retiro >= ahora + horas`. Error `ANTICIPACION_INSUFICIENTE` (422) |
| `_dias_corridos(retiro, devolucion)` | RN-L06 | `(fecha_local(devolucion) - fecha_local(retiro)).days + 1`, contando ambos extremos |
| `_limite_dias(es_notebook, max_general, max_notebook, max_item)` | RN-L06 | Menor entre el parámetro del tipo y `max_dias_prestamo` del ítem |
| `_validar_plazo(retiro, devolucion, limite, equipamiento_id)` | RN-L06 | Error `LIMITE_DIAS_EXCEDIDO` (422) con `equipamiento_id` y `max_dias` como datos extra |
| `_validar_disponibilidad(solicitadas, libres)` | RN-L10 | `solicitadas`: líneas pedidas por modelo (un `Counter`). `libres`: lo que devuelve `ids_unidades_libres`. Si para algún modelo las líneas superan las unidades libres → `409 EQUIPAMIENTO_NO_DISPONIBLE` con `equipamiento_id`, `solicitadas` y `libres`. Un modelo ausente de `libres` cuenta como sin unidades |

### 4.2 Funciones con base de datos

| Función | Qué hace |
| :---- | :---- |
| `reglas(db)` | Lee con `obtener_parametro` las seis claves y arma `ReglasResponse` (horario global hasta K10) |
| `ids_unidades_libres(db, equipamiento_ids, sede, desde, hasta)` | **Interna de `loans`.** Por modelo, los ids de las unidades libres para el período: `inventory.unidades_asignables(...)` menos las que tienen una línea `reservado` o `entregado` (`ESTADOS_DETALLE_QUE_OCUPAN`) cuyo `periodo` se solapa con `[desde, hasta)` (consulta a `detalles_prestamo` con `&&`). Siempre devuelve una clave por modelo pedido, sin repetidos. Un período vacío o invertido es un `ValueError` (error de programación). La usan `crear_orden` y, en la Fase 2, `GET /ordenes/{id}/unidades-libres` |
| `unidades_libres(db, equipamiento_ids, sede, desde, hasta)` | **API pública** (spec §10.2), para el mini-calendario del Perfil 2 (INV-26, C10, C16). Mismo criterio, pero devuelve solo **cantidades** por modelo, sin identidad de unidades ni de solicitantes |
| `ocupacion_de_unidades(db, unidad_ids, desde, hasta)` | **API pública** (spec §10.2), para el mini-calendario y la disponibilidad por fechas del Perfil 2 (PRE-01, INV-26). Por unidad, los períodos `[retiro_pactado, fin_ocupacion)` de sus líneas `reservado` o `entregado` que se solapan con el rango, en una sola consulta y sin identidad. `inventory` arma el conteo por día |
| `crear_orden(db, actor, payload)` | Orquesta la creación (§4.3) |
| `listar_mis_ordenes(db, actor, estado, limit, offset)` | Filtra por `solicitante_id`, ordena por `fecha_solicitud` descendente |
| `obtener_orden(db, actor, orden_id)` | Solo el dueño; otra persona o inexistente → `404 ORDEN_NO_ENCONTRADA` |

### 4.3 `crear_orden`, orden de las validaciones

1. **Renovación**: en este corte, `renueva_detalle_id` → `501 NO_IMPLEMENTADO` (§1.1).
2. **Sede y solicitante** salen de `actor`. Con estos roles la sede no puede ser nula (lo garantiza el `CHECK sede_segun_rol` de `usuarios`); el servicio lo afirma.
3. **Asignatura** obligatoria para `ESTUDIANTE` → `422 ASIGNATURA_REQUERIDA`. Su existencia no se verifica (D-L13).
4. **Parámetros**: `obtener_parametro` para horario, anticipación y plazos.
5. **Franja y anticipación** (funciones puras).
6. **Datos de los ítems** con `inventory.datos_equipamiento_por_ids` (una sola llamada para todos los modelos): ausente o inactivo → `404 EQUIPAMIENTO_NO_ENCONTRADO` con `equipamiento_id`.
7. **Alta gama** → `422 AVAL_REQUERIDO` si falta `pdf_aval_id`. En este corte se rechaza toda alta gama, con o sin aval (§1.1).
8. **Plazo por línea**: `_limite_dias` y `_validar_plazo`, por cada modelo distinto.
9. **Unidades libres**: `Counter` de las líneas por modelo, `ids_unidades_libres(db, modelos, sede, retiro, devolucion)` y `_validar_disponibilidad`.
10. **Persistencia**: una `OrdenPedido` en estado `pendiente` con una `DetallePrestamo` por línea (`estado=pendiente`, sin unidad, `retiro_pactado`, `devolucion_pactada` y `fin_ocupacion = devolucion`), `commit` y `refresh` (la base pone `fecha_solicitud`). Con `files`, `vincular_archivo` va acá, antes del `commit` y en la misma transacción.

Los pasos 1 a 9 solo leen: un `AppError` en ellos no deja nada que deshacer.

### 4.4 Transacciones y errores

- `get_db` no hace `commit`: el servicio lo hace al final. Si el paso 10 falla (incluido `vincular_archivo`, cuando exista), `rollback` antes de relanzar (patrón de `config`).
- Las líneas `pendiente` no ocupan unidades: **no hay riesgo de concurrencia al crear** (AC-L15). Dos pedidos pendientes del mismo modelo y período se crean ambos. El control de unidades libres es una verificación previa (P7.2); la garantía final es el `EXCLUDE` de `0009` al aprobar (Fase 2).
- Se lanza siempre `AppError`; no se usa `HTTPException`.

### 4.5 Esquema (`OrdenPedidoCreate`)

- `pdf_aval_id: UUID | None`: el id de `archivos` es UUID v4 (SPEC-03 §7).
- `renueva_detalle_id: int | None` (`ge=1`).
- Si viene `renueva_detalle_id`, la orden lleva **una sola línea** (validación del esquema, RN-L24). Que sea una línea `entregado` propia de una notebook lo valida el servicio (`422 RENOVACION_NO_PERMITIDA`, T1.14).

### 4.6 Lectura de equipamiento (C8, resuelto)

`loans` no puede leer los modelos de `inventory` (P3.3). Mientras C8 no existía, `crear_orden` dependía de un adaptador propio (`_datos_items`) que respondía `501`, y los tests lo reemplazaban por uno falso. El 2026-11-06 el Perfil 2 publicó `inventory.datos_equipamiento_por_ids(db, ids) -> dict[int, DatosEquipamiento]` (`id`, `codigo`, `nombre`, `activo`, `es_notebook`, `alta_gama`, `max_dias_prestamo`) con la firma propuesta, así que se borró el adaptador: `crear_orden` la llama directamente y los tests corren contra la base real (T1.11).

---

## 5. Bloqueos y alternativas

| Bloqueo | Afecta | Alternativa mientras se resuelve |
| :---- | :---- | :---- |
| **`files`** (SPEC-03) | Aval de alta gama (RN-L09, AC-L14) | Se rechaza toda alta gama con `422 AVAL_REQUERIDO` |
| **K10** (horario por sede) | AC-L63 | Claves globales de `config` |
| **C3**: catálogo de asignaturas | Verificar `asignatura_id` | D-L13: se exige pero no se verifica su existencia |
| **V4**: spec aprobado | Merge de `POST /ordenes` | Se puede programar y probar; no se mergea hasta la aprobación de la v0.3.0 |

### 5.1 Pregunta abierta

AC-L12 pide `404 EQUIPAMIENTO_NO_ENCONTRADO` también para un modelo **sin unidades en la sede**. `inventory` solo informa unidades `disponible` (`unidades_asignables`), así que hoy ese caso no se distingue de "todas ocupadas" y responde `409 EQUIPAMIENTO_NO_DISPONIBLE`. Opciones: ajustar AC-L12 o sumar a C8 la cantidad de unidades no dadas de baja por sede.

---

## 6. Verificación de la fase

1. `pytest -q` completo y `ruff check` sin errores.
2. `/docs` muestra los cinco endpoints (cuatro implementados) con las respuestas de error de `error_responses`. El `501` transitorio de `POST /ordenes` (renovación) no se declara en OpenAPI porque `error_responses` de `core` no lo admite; queda en el docstring.
3. Cada criterio AC-L01…L16, L18, L56 y L57 tiene al menos un test anotado con `# AC-Lxx` y `pytest.mark.integracion` (los unitarios, sin la marca).
4. `MEMORY.md` actualizado (decisiones, deuda nueva) y el spec en `IMPLEMENTADO` para los criterios de la fase.

---

## 7. Frontend de la fase

Se planifica en `tasks.md` (tareas F1.x). Depende de que el contrato de `POST /ordenes` esté estable y de C11 (botón en el catálogo de `inventory`).

---

## 8. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 0.3.0 | 2026-11-06 | C8 resuelto: `crear_orden` usa `inventory.datos_equipamiento_por_ids` y se borra el adaptador provisorio. Suma `ocupacion_de_unidades` (spec v0.3.1 §10.2) para el Perfil 2 |
| 0.2.0 | 2026-11-06 | Alineado con SPEC-05 v0.3.0: `AVAL_REQUERIDO` en lugar de `AVAL_NO_HABILITADO`; división `ids_unidades_libres` / `unidades_libres` y `_validar_disponibilidad`; adaptador de C8 con función falsa en los tests; cambio de esquema (`pdf_aval_id`, `renueva_detalle_id`); renovación fuera de este corte; horario global hasta K10; garantía final en el `EXCLUDE` de `0009` (D-L17 descartada); nombres de archivo reales; resultado de V1…V4 |
| 0.1.0 | 2026-11-03 | Primera versión, sobre SPEC-05 v0.2.0 |
