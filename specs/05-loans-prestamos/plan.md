# PLAN-05 — Préstamos (`loans`): Fases 1 y 2

> **Estado:** `BORRADOR` · **Versión:** 0.4.4 · **Fecha:** 2026-11-11 · **Perfil:** 3
> **Spec:** `specs/05-loans-prestamos/spec.md` v1.0.2 (`APROBADO` v1.0.0; la v1.0.1 corrige EC-L10 y la v1.0.2 agrega el aval) (§14, Fases 1 y 2) · **Tareas:** `specs/05-loans-prestamos/tasks.md`
> Este plan define el **cómo** de la Fase 1, Solicitar (§1…§7, implementada en el backend PR #21), y de la Fase 2, Validar (§8, implementada en el backend PR #23 y #28, salvo las notificaciones). Las Fases 3 a 5 se planifican cuando se cierre cada fase anterior.

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
| **Aval** (RN-L09, `pdf_aval_id`) | **En curso** (T1.12, en `feat/loans-aval`, sin PR hasta el OK de la v1.0.2): se vincula con `files.vincular_archivo` en la misma transacción, la orden guarda `aval_archivo_id` (migración `0016`) y `GET /ordenes/{id}/aval` lo sirve al dueño y a los administradores con jurisdicción | — |
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

## 8. Fase 2, Validar

> La Fase 1 está implementada y mergeada en `develop` (backend PR #21). Esta sección define el **cómo** de la Fase 2. Rama del backend: `feat/loans-validar`.

### 8.1 Alcance

| Endpoint o función | Rol | Requisitos | Criterios (SPEC-05 §12) |
| :---- | :---- | :---- | :---- |
| `GET /api/v1/loans/ordenes` (bandeja) | ADMIN_LOCAL, SUPERADMIN | PRE-15 | AC-L17, L18, L61 |
| `GET /api/v1/loans/ordenes/{orden_id}` | dueño y administradores con jurisdicción | PRE-10 | AC-L16, L29 |
| `GET /api/v1/loans/ordenes/{orden_id}/unidades-libres` | ADMIN_LOCAL, SUPERADMIN | PRE-10 | AC-L47, L58 |
| `PATCH /api/v1/loans/ordenes/{orden_id}/estado` | ver §8.5.4 | PRE-10, PRE-18 | AC-L19…L34, L53, L55 |
| `reservas_futuras_de_unidad` (pública, §10.2) | — (la llama `inventory`) | PRE-17 (aviso) | Desbloquea la Fase C de SPEC-04 (`reservas_afectadas`) |
| `historial_de_unidad` (pública, §10.2) | — (la llama `inventory`) | PRE-12 | Desbloquea la Fase C de SPEC-04 (`GET /unidades/{id}/historial`) |
| Migración `0011_loans_resolucion` | — | P7.3, USR-08 | AC-L54 |

Reglas que se implementan: RN-L11…RN-L16, RN-L18, RN-L26, RN-L27, RN-L31 y, para la cancelación de una orden aprobada, RN-L30.

**Fuera de la Fase 2:**

| Tema | Por qué | Cuándo |
| :---- | :---- | :---- |
| Aprobar una renovación (PRE-11, AC-L41…L44) | Depende de crear la orden de renovación (T1.14), que quedó fuera del corte de la Fase 1 | Después de la demo, junto con T1.14 |
| Cancelación forzada por línea (PRE-17, AC-L35) | Usa `PATCH …/detalles/{id}/estado`, el endpoint de la Fase 3 | Fase 3 |
| Notificaciones de cada transición (§10.3) | `notifications.crear_notificacion` es de la Fase B de SPEC-06 y todavía no está en `develop` | T2.13, cuando llegue (C12, C-N01) |
| Panel docente y observación (PRE-20) | Depende de C3 (asignaturas) | Fase 4 |

### 8.2 Prioridad para la demo

El plan de la demo del Perfil 1 (`plan-demo-perfil-3.md`, paso 4) pide llegar a aprobar. Las tareas se ordenan en tres bloques:

1. **Demo:** migración, bandeja, detalle para administradores, unidades libres por línea, aprobar, rechazar y cancelar la propia (T2.1…T2.8).
2. **Si queda tiempo antes de la demo:** cancelar una orden aprobada (T2.9) y el ajuste horario al aprobar (T2.10, PRE-18).
3. **Para el Perfil 2 (Fase C de SPEC-04):** `reservas_futuras_de_unidad` y `historial_de_unidad` (T2.11, T2.12). No son de la demo, pero son chicas y destraban su trabajo.

### 8.3 Verificaciones previas

| # | Qué verificar | Resultado (2026-11-07) |
| :---- | :---- | :---- |
| V5 | **Numeración de `0011` (C19).** `develop` termina en `0010_inventory_gestion`. La Fase A de SPEC-06 trae `0013_notifications_init`, también con `down_revision = "0010_inventory_gestion"` (backend PR #22, abierto) | Si las dos llegan a `develop` con la misma base, Alembic queda con dos cabezas. Regla: **la que se mergea segunda apunta su `down_revision` a la cabeza de `develop`** al abrir su PR (Alembic encadena por id, no por número). **Resuelto (2026-11-08):** entró primero el #22, y la `0011` pasó a colgar de `0013_notifications_init` (backend PR #23): `0010 → 0013 → 0011`, una sola cabeza, upgrade → downgrade → upgrade sin errores |
| V6 | **`bloquear_unidad` como API pública (C14).** RN-L11 la usa para bloquear cada unidad al aprobar | Está en `develop`; SPEC-04 v1.2.0 (Fase B, rama `docs/spec-04-fase-b`) la declara pública |
| V7 | `users.datos_publicos_por_ids` para el resumen del solicitante | En `develop` (backend PR #18) |
| V8 | `inventory.marcar_unidad_mantenimiento` (C17) | Implementada en `feat/inventory-disponibilidad` (sin mergear). La usa la Fase 3, no esta |

### 8.4 Archivos

| Archivo | Acción | Contenido |
| :---- | :---- | :---- |
| `alembic/versions/0011_loans_resolucion.py` | **Crear** | `ordenes_pedido.resuelto_por_id` (FK `usuarios`, `SET NULL`) y `resuelto_en` (`timestamptz`); tabla `ordenes_historial_estado` (`id` `BigInteger` `Identity`, `orden_id` FK `CASCADE`, `estado_anterior` nulo, `estado_nuevo`, `motivo` `String(500)` nulo, `actor_id` FK `SET NULL`, `created_at`) e índice `(orden_id, created_at)`. Reusa `estado_orden_enum` sin crearlo. `downgrade` completo |
| `app/modules/loans/models.py` | Modificar | Columnas nuevas y modelo `OrdenHistorialEstado` |
| `app/modules/loans/schemas.py` | Modificar | En `OrdenPedidoResponse`: `resuelto_en`, `situacion` (derivada, RN-L31) y `solicitante: SolicitanteResumen \| None` (`id`, `nombre`, `apellido`). `LineaUnidadesLibresResponse` (`detalle_id`, `equipamiento_id`, `unidades: list[int]`) |
| `app/modules/loans/service.py` | Modificar | §8.5. Además, reemplaza el `assert sede is not None` de `crear_orden` por un `AppError` (observación O2 del Perfil 1) |
| `app/modules/loans/router.py` | Modificar | Bandeja, `unidades-libres` y `PATCH …/estado` delegan en `service`. Se declara `/ordenes/{orden_id}/unidades-libres` |
| `tests/loans/test_migracion_0011.py` | **Crear** | Upgrade → downgrade → upgrade (AC-L54), como `tests/test_spaces_migrations.py` |
| `tests/loans/test_bandeja.py` | **Crear** | Bandeja y detalle para administradores |
| `tests/loans/test_aprobar.py` | **Crear** | Aprobación, asignaciones, unidades libres por línea y ajuste horario |
| `tests/loans/test_rechazar_cancelar.py` | **Crear** | Rechazo, cancelación propia y cancelación por el administrador |
| `tests/loans/test_concurrencia.py` | **Crear** | AC-L23, AC-L24 y EC-L10 con sesiones independientes (AC-L55) |
| `tests/loans/test_lecturas_inventory.py` | **Crear** | `reservas_futuras_de_unidad` y `historial_de_unidad` |
| `tests/loans/test_contratos.py` | Modificar | La bandeja y el `PATCH` dejan de esperar `501` |

### 8.5 Diseño de `service.py`

#### 8.5.1 Alcance y bloqueo de la orden

`_orden_con_alcance(db, actor, orden_id, *, bloquear=False)` concentra la regla de visibilidad: la ve el dueño, el `ADMIN_LOCAL` de la sede de la orden y el `SUPERADMIN` (`core.deps.puede_ver_sede`). Cualquier otro caso responde `404 ORDEN_NO_ENCONTRADA`, nunca `403` (RN-L25, RN-L26). Con `bloquear=True` lee la fila con `SELECT … FOR UPDATE` (RN-L14). `obtener_orden` pasa a usarla, así que el detalle queda disponible para los administradores con jurisdicción.

#### 8.5.2 Bandeja (`listar_bandeja`)

- Sedes con `core.deps.resolver_alcance_sede(actor, sede)`: el `ADMIN_LOCAL` siempre la suya (pedir otra responde `403 SEDE_FUERA_DE_ALCANCE`); el `SUPERADMIN`, la indicada o ambas. El filtro va en el `WHERE` (RN-L26).
- `estado` por defecto `pendiente`; `limit` y `offset` (AC-L18).
- Orden: `fecha_solicitud` **ascendente**, para atender primero lo más viejo.
- Solicitante: una sola llamada a `users.datos_publicos_por_ids` con los ids de la página. Nunca DNI, email ni teléfono (P6).

#### 8.5.3 Respuesta de la orden

`OrdenPedidoResponse` suma `resuelto_en`, `situacion` y `solicitante`. `situacion` se deriva de las líneas: `en_curso` si alguna está `pendiente`, `reservado` o `entregado`; si no, `finalizada` (RN-L31, AC-L61). `solicitante` se completa solo para administradores; el dueño recibe `null`. Que la orden tenga el retiro vencido (EC-L05) lo calcula la interfaz a partir de `retiro_pactado`.

#### 8.5.4 `PATCH /ordenes/{orden_id}/estado` (`cambiar_estado_orden`)

Orden de los controles: (1) permiso por rol, que no depende de la orden (403); (2) leer y bloquear la orden con alcance (404); (3) transición válida desde el estado actual (409); (4) datos del pedido (422); (5) aplicar.

| Estado pedido | Quién | Estado actual | Efecto | Errores propios |
| :---- | :---- | :---- | :---- | :---- |
| `aprobada` | Administrador con jurisdicción | `pendiente` | §8.5.5 | `RETIRO_VENCIDO`, `ASIGNACIONES_INVALIDAS`, `UNIDAD_NO_ASIGNABLE` (422); `UNIDAD_NO_DISPONIBLE` (409) |
| `rechazada` | Administrador con jurisdicción | `pendiente` | Líneas `rechazado`; `motivo_resolucion` = motivo | `MOTIVO_REQUERIDO` (422) |
| `cancelada` | Dueño | `pendiente` | Líneas `cancelado`; motivo opcional | Si está `aprobada`: `403 CANCELACION_NO_PERMITIDA` (AC-L32) |
| `cancelada` | Administrador con jurisdicción | `aprobada`, sin líneas `entregado` | Líneas `reservado` → `cancelado` (las unidades se liberan, AC-L33); `motivo_resolucion` = motivo | `MOTIVO_REQUERIDO` (422); con una línea `entregado`, `409 TRANSICION_INVALIDA` (AC-L34) |

- Un estudiante o docente que pide `aprobada` o `rechazada` recibe `403 ROL_NO_AUTORIZADO` en el paso 1, sea o no el dueño (AC-L29): el control depende solo del rol, así que no revela si la orden existe. Para `cancelada`, quien no es dueño ni administrador con jurisdicción recibe `404` en el paso 2.
- Cualquier otra combinación (por ejemplo, aprobar una orden ya `aprobada`, o que el administrador cancele una `pendiente` en lugar de rechazarla) responde `409 TRANSICION_INVALIDA` (AC-L28).
- Toda transición registra quién y cuándo resolvió (`resuelto_por_id`, `resuelto_en`) y agrega una fila a `ordenes_historial_estado` (D-L10).
- Ante cualquier `AppError` después de bloquear, `rollback` antes de propagar (RN-L14).

#### 8.5.5 Aprobar

1. **Retiro vencido (RN-L27):** sin ajuste horario, si el retiro de la orden ya pasó (`<= ahora_lab()`), `422 RETIRO_VENCIDO`. Aprobar **no** revalida plazos ni franja (EC-L11).
2. **Ajuste horario (RN-L18, T2.10):** si vienen `nuevo_retiro` y `nueva_devolucion`, se validan la franja y el plazo de cada línea (con `datos_equipamiento_por_ids`) y que el retiro nuevo sea futuro; no se exige la anticipación mínima. Se aplica a todas las líneas y `fin_ocupacion` queda igual a la devolución nueva.
3. **Asignaciones (RN-L11):** exactamente una por línea de la orden, sin líneas ajenas ni unidades repetidas entre líneas; si no, `422 ASIGNACIONES_INVALIDAS` (AC-L22). El esquema ya rechaza dos asignaciones para la misma línea.
4. **Unidades, en orden ascendente de id (RN-L14):** `inventory.bloquear_unidad`. Si la unidad no existe, es de otra sede o de otro modelo, no está `disponible` o su ítem no está activo (`unidad_es_asignable`) → `422 UNIDAD_NO_ASIGNABLE` con `detalle_id` y `unidad_fisica_id` (AC-L20, L21, L26; EC-L08).
5. **Aplicar:** líneas `reservado` con su unidad, orden `aprobada`, resolución e historial.
6. **`commit`:** si la base rechaza el solapamiento (`IntegrityError` con SQLSTATE `23P01`, del `EXCLUDE`), `rollback` y `409 UNIDAD_NO_DISPONIBLE` (AC-L23, AC-L47). Cualquier otra violación de base hace `rollback` y se propaga como 500 (AC-L53). Es todo o nada (RN-L13).

`bloquear_unidad` devuelve la entidad `UnidadFisica` de `inventory`. `loans` solo lee sus atributos (`sede`, `equipamiento_id`, `estado`), nunca la modifica: el estado de la unidad sigue siendo de `inventory` (DT-20).

#### 8.5.6 Unidades libres por línea (`unidades_libres_de_orden`)

Para cada línea, las unidades del modelo en la sede de la orden que están `disponible` y sin otra línea ocupante que se solape con el período de la línea (AC-L58). Usa `ids_unidades_libres` con una sola llamada (todas las líneas comparten el período). Devuelve solo ids. Para mostrar el código de inventario de cada unidad, la interfaz los cruza con el stock de `inventory` (ver §8.7, pregunta Q1).

#### 8.5.7 Funciones públicas para `inventory` (Fase C de SPEC-04)

Ninguna hace `commit`. Las dos devuelven dataclasses inmutables, en el estilo de `ocupacion_de_unidades`.

| Función | Devuelve | Notas |
| :---- | :---- | :---- |
| `reservas_futuras_de_unidad(db, unidad_id, desde) -> list[ReservaFutura]` | Líneas `reservado` de la unidad con `retiro_pactado >= desde`, ordenadas por retiro. `ReservaFutura`: `orden_id`, `detalle_id`, `retiro`, `devolucion` | Sin identidad del solicitante. La jurisdicción la valida `inventory` antes de llamar (SPEC-04 §5.3). `reservas_afectadas` es `len(...)` |
| `historial_de_unidad(db, unidad_id, actor, *, limit=20, offset=0) -> list[MovimientoUnidad]` | Líneas de la unidad, de la más reciente a la más antigua por `retiro_pactado`. `MovimientoUnidad`: `orden_id`, `detalle_id`, `solicitante` (`id`, `nombre`, `apellido`), `estado`, `retiro_pactado`, `devolucion_pactada`, `entregado_en`, `devuelto_en`, `observacion_devolucion` | Coincide con los campos indicativos de SPEC-04 §5.5. `entregado_en`, `devuelto_en` y `observacion_devolucion` valen `None` hasta la migración `0012` (Fase 3): la firma ya los incluye para que el contrato no cambie. `actor`: el `ADMIN_LOCAL` solo ve líneas de órdenes de su sede; el `SUPERADMIN`, todas; otro rol, lista vacía. Dos consultas: las líneas y `datos_publicos_por_ids` |

#### 8.5.8 Notificaciones (T2.13)

Cuando `notifications.crear_notificacion` llegue a `develop` (SPEC-06 Fase B), cada transición la llama **dentro de la misma transacción**, antes del `commit`: `ORDEN_APROBADA`, `ORDEN_RECHAZADA`, `ORDEN_CANCELADA` y, con ajuste horario, `ORDEN_HORARIO_AJUSTADO` (crítica). Las fechas se formatean en la zona del laboratorio (`"12/11 10:00"`), como pide SPEC-06 §6.2. No bloquea el resto de la fase.

### 8.6 Concurrencia

- El orden de bloqueo es siempre la orden primero y después las unidades por id ascendente (RN-L14), así dos aprobaciones no se interbloquean.
- Los tests de AC-L23, AC-L24 y EC-L10 lanzan dos pedidos HTTP en paralelo con sesiones independientes (ADR-013, AC-L55), como `tests/inventory/test_gestion.py::test_cambios_concurrentes_de_estado` (DT-28).

### 8.7 Bloqueos, coordinación y preguntas

| # | Con | Qué | Afecta |
| :---- | :---- | :---- | :---- |
| C19 | Perfiles 1 y 5 | Numeración y cadena de `0011` frente a `0013` (V5) | T2.1 y el merge |
| C12 / C-N01 | Perfil 5 | `crear_notificacion` en `develop` | T2.13 |
| O1 | Perfil 1 y equipo | Lista provisoria de asignaturas para el formulario (C3, D-L13). No afecta al backend de esta fase, pero bloquea la demo para estudiantes | Frontend de la Fase 1 |
| Q1 | Perfil 2 | Para elegir la unidad al aprobar, el administrador necesita ver el código de inventario. ¿Alcanza con que la interfaz cruce los ids con el stock de `inventory`, o conviene una función pública `datos_unidades_por_ids`? | Frontend de la Fase 2 |

### 8.8 Riesgos

- **Dos cabezas de Alembic** si `0011` y `0013` se mergean con la misma base: se resuelve con la regla de V5 y se verifica con `alembic heads` antes de cada merge.
- **Tests de concurrencia inestables:** se usan sesiones independientes y aserciones sobre el resultado (uno gana y el otro recibe el código esperado), no sobre el orden.
- **Cambia la firma esperada por el Perfil 2** para el historial: los campos siguen la tabla indicativa de SPEC-04 §5.5; si difieren, se ajusta antes de mergear (AGENTS §4).

### 8.9 Verificación de la fase

1. `pytest -q` completo y `ruff check` sin errores; `alembic upgrade head`, `downgrade -1` y `upgrade head` contra una base local.
2. `/docs` muestra la bandeja, `unidades-libres` y el `PATCH` con sus respuestas de error.
3. Cada criterio AC-L17…L34, L47, L53…L55, L58 y L61 tiene al menos un test anotado.
4. `MEMORY.md`, `tasks.md` y el spec al día; PR de `feat/loans-validar` contra `develop`.

### 8.10 Frontend de la fase

Se planifica en `tasks.md` (tareas F2.x): bandeja del administrador, detalle con selector de unidades, rechazo con motivo y cancelación de la propia en "Mis solicitudes". Depende de F1.1 y F1.2 (tipos y `loansApi`).

---

## 9. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 0.4.4 | 2026-11-11 | Revisión del Perfil 1 al PR #26 de Docs: T1.12 queda en curso (no mergeada) en lugar de hecha |
| 0.4.3 | 2026-11-10 | T1.12 (aval) programada en `feat/loans-aval`, según la spec v1.0.2. Sin PR hasta que el Perfil 1 apruebe esa versión |
| 0.4.2 | 2026-11-10 | La Fase 2 queda implementada en `develop` (backend PR #23 y #28), salvo T2.13 (espera `crear_notificacion`). `files` ya está en `develop`, así que T1.12 (aval) se desbloquea |
| 0.4.1 | 2026-11-08 | Registra el resultado de V5 (C19: la `0011` cuelga de `0013_notifications_init`) y referencia la v1.0.1 del spec (EC-L10). El avance de la fase está en `tasks.md` |
| 0.4.0 | 2026-11-07 | Agrega la Fase 2, Validar (§8): alcance, prioridad para la demo, verificaciones V5…V8 (cadena de `0011` frente a `0013`), diseño de la bandeja, el `PATCH …/estado`, las unidades libres por línea y las funciones `reservas_futuras_de_unidad` e `historial_de_unidad` para la Fase C de SPEC-04. La Fase 1 queda implementada (backend PR #21) |
| 0.3.0 | 2026-11-06 | C8 resuelto: `crear_orden` usa `inventory.datos_equipamiento_por_ids` y se borra el adaptador provisorio. Suma `ocupacion_de_unidades` (spec v0.3.1 §10.2) para el Perfil 2 |
| 0.2.0 | 2026-11-06 | Alineado con SPEC-05 v0.3.0: `AVAL_REQUERIDO` en lugar de `AVAL_NO_HABILITADO`; división `ids_unidades_libres` / `unidades_libres` y `_validar_disponibilidad`; adaptador de C8 con función falsa en los tests; cambio de esquema (`pdf_aval_id`, `renueva_detalle_id`); renovación fuera de este corte; horario global hasta K10; garantía final en el `EXCLUDE` de `0009` (D-L17 descartada); nombres de archivo reales; resultado de V1…V4 |
| 0.1.0 | 2026-11-03 | Primera versión, sobre SPEC-05 v0.2.0 |
