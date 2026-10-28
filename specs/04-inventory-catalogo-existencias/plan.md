# PLAN-04 — Catálogo y existencias (`inventory`)

> **Spec:** `specs/04-inventory-catalogo-existencias/spec.md` v1.0.0 (`APROBADO`) · **Estado del plan:** `BORRADOR` · **Fecha:** 2026-10-23 · **Perfil:** 2
> **Alcance de este plan:** Fase A completa. La Fase B (INV-26: disponibilidad por fechas e historial) queda fuera hasta que `loans` exponga sus funciones de lectura (§8).
> Tareas: `specs/04-inventory-catalogo-existencias/tasks.md`.

---

## 1. Principios de ejecución

- Sólo se tocan archivos de `inventory` (backend y frontend), más los **puntos de integración mínimos** listados en §6. No se modifican `core`, `users`, `config`, `loans`, `spaces`.
- Orden API-First: contratos (esquemas) → migración y modelos → servicio → router → tests → frontend.
- Cada tarea termina con tests en verde (`pytest -q` con `TEST_DATABASE_URL`) o con `npm run typecheck && npm run build && npm test`.
- Sin commits, push ni merge sin pedido explícito. Ramas sugeridas desde `develop`: `feat/inventory-gestion` (backend) y `feat/inventory-catalogo` (frontend).

## 2. Dependencias nuevas

Ninguna, ni en backend ni en frontend (Constitución §3). El frontend sigue sin librería de estado ni de tablas: se usan hooks de React y ordenamiento en el cliente.

## 3. Backend

### 3.1 Archivos a modificar

| Archivo | Cambio | Spec |
| :---- | :---- | :---- |
| `app/modules/inventory/models.py` | `Equipamiento.activo` (`bool`, default `True`), `Equipamiento.es_notebook` (`bool`, default `False`). `UnidadFisica`: `CheckConstraint("locker IS NULL OR locker BETWEEN 1 AND 7", name="locker_rango")` en lugar de `locker_positivo` | §7, DT-23 |
| `app/modules/inventory/schemas.py` | Nuevos: `EquipamientoPublicoResponse`, `EquipamientoUpdate`, `EquipamientoEstadoUpdate`, `UnidadFisicaUpdate`. `EquipamientoBase`/`Create`/`Response` suman `es_notebook`; `Response` suma `activo`. `UnidadFisicaEstadoUpdate` sin cambios de forma (la restricción de `prestado` se aplica en el router con `AppError`) | §5 |
| `app/modules/inventory/router.py` | Respuesta por rol en `GET /equipamiento` y `/{id}`; `incluir_inactivos`; escape de comodines en `q`; plazo según `es_notebook`; endpoints `PATCH /equipamiento/{id}`, `PATCH /equipamiento/{id}/estado`, `PATCH /unidades/{id}`; `PATCH /unidades/{id}/estado` con matriz de transiciones y `FOR UPDATE` | §5, RN-I1…I8 |
| `app/modules/inventory/enums.py` | Sin cambios | — |
| `tests/inventory/test_inventario.py` | Se actualizan los tests que dependen de D-02 y D-04 (ver 3.4) | §3 del spec |
| `Backend-PrestaMeDios/README.md` | Sección de endpoints de `inventory` (Constitución §6.1) | DoD |

`alembic/env.py` ya importa `inventory.models`; no necesita cambios.

### 3.2 Archivos a crear

| Archivo | Contenido |
| :---- | :---- |
| `app/modules/inventory/service.py` | Funciones públicas de §6 del spec: `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad`; helper interno `bloquear_unidad` (`SELECT … FOR UPDATE`) y la matriz `TRANSICIONES_ADMIN` que usa también el router. Sin `commit` |
| `alembic/versions/0010_inventory_gestion.py` | `down_revision = "0009_loans_init"`. `upgrade`: agrega `activo` y `es_notebook` (`server_default`), verifica locker fuera de rango (consulta previa; si hay filas, `RuntimeError` con los ids) y reemplaza `ck_unidades_fisicas_locker_positivo` por `ck_unidades_fisicas_locker_rango`. `downgrade`: restaura el `CHECK` anterior y borra las dos columnas |
| `tests/inventory/test_catalogo.py` | INV-02…08 |
| `tests/inventory/test_gestion.py` | INV-09…13, 15…21 |
| `tests/inventory/test_service.py` | INV-22 |
| `tests/inventory/test_migracion_0010.py` | INV-14 (parte base) e INV-23 |

### 3.3 Decisiones de diseño

1. **Respuesta por rol.** Los handlers de lectura construyen explícitamente `EquipamientoResponse` (admins) o `EquipamientoPublicoResponse` (estudiante, docente) con `model_validate`. `response_model` se declara como unión (`EquipamientoResponse | EquipamientoPublicoResponse`). La unión de Pydantic v2 en modo inteligente respeta la instancia exacta; se verifica en las pruebas (INV-05) y en el OpenAPI generado. Si la unión da problemas, alternativa: `response_model=None` + `responses={200: …}` documentado a mano.
2. **`locker` en la respuesta pública.** Se calcula sobre unidades activas (no `baja`) de la sede visible; si todas comparten un valor, se devuelve ese; si no, `null`. El mapper del frontend ya hace algo parecido.
3. **Unidades visibles para estudiantes.** El filtro SQL actual (`selectinload` con `sede.in_(sedes)`) se mantiene; sólo cambia la serialización. Las unidades en `baja` siguen excluidas de `cantidad_total`.
4. **Ítems inactivos.** `_stmt_equipamiento_en_alcance` agrega `Equipamiento.activo.is_(True)` salvo que el actor sea admin y pida `incluir_inactivos=true`.
5. **Transiciones y concurrencia.** `cambiar_estado_unidad` hace `select(UnidadFisica).where(id).with_for_update()`, valida alcance (`puede_ver_sede` → `404`), aplica la matriz y hace `commit`. Mismo estado → `200` sin cambios. `prestado` en el body → `AppError(422, "ESTADO_NO_PERMITIDO", …)`. Transición no permitida → `AppError(409, "TRANSICION_ESTADO_INVALIDA", …)`.
6. **Desactivar equipamiento (D-06).** Con unidades `prestado` → `409 EQUIPAMIENTO_CON_PRESTAMOS`. Si hay unidades en ambas sedes y el actor es `ADMIN_LOCAL` → `403 PERMISO_INSUFICIENTE` (con `permiso_insuficiente()` de `core.deps`). Edición descriptiva: `ADMIN_LOCAL` sólo si el ítem tiene al menos una unidad en su sede o ninguna; si no, `404`.
7. **Plazo por defecto.** `max_dias_prestamo` omitido → `prestamo.notebook.max_dias` si `es_notebook`, si no `prestamo.general.max_dias`, siempre con `obtener_parametro`. El `CHECK` de 1–15 de la base no cambia.
8. **Duplicados en edición.** `PATCH` de unidades y equipamiento reutiliza `_commit_inventario` (`409 INVENTARIO_DUPLICADO`).
9. **Búsqueda `q`.** Se escapan `\`, `%` y `_` y se usa `ilike(patron, escape="\\")`.
10. **`service.py` sin dependencia de `loans`.** Las funciones sólo leen y escriben `unidades_fisicas`; `loans` las llamará cuando el Perfil 3 las adopte.

### 3.4 Impacto en tests existentes

| Test | Motivo | Acción |
| :---- | :---- | :---- |
| `TestAlcanceDeLectura.test_estudiante_ve_solo_su_sede` (líneas 55–60) | Asume `unidades` y sede en la respuesta del estudiante (D-04) | Cambiar para verificar `cantidad_total` y la ausencia de `unidades` |
| `TestAlcanceDeLectura.test_otra_sede_y_unidades`, `test_detalle` | Posible uso de `unidades` con rol no admin | Revisar al implementar; ajustar sólo lo que dependa de D-04 |
| `TestEstadoDeUnidades.test_alcance` | Puede enviar `prestado` (D-02) | Revisar; reemplazar por `mantenimiento` |
| `test_exige_sesion` | Rutas nuevas | Agregar `patch /equipamiento/1`, `patch /equipamiento/1/estado`, `patch /unidades/1` |

Cada cambio se anota con el comentario del criterio (`# INV-NN`) y se informa en el PR.

### 3.5 Migración y datos

- Es idempotente respecto del orden: `0010` depende de `0009`.
- Si la base tiene un locker fuera de 1–7 (posible, porque Pydantic ya lo impedía pero la base no), la migración aborta con los ids; el equipo corrige a mano. No se modifica nada en silencio.
- Se valida con `alembic upgrade head` → `downgrade -1` → `upgrade head` sobre una base de desarrollo, y con un test que inspecciona el `CHECK` (la base de tests se crea con `create_all`, no con Alembic: ADR-013).

## 4. Frontend (`src/features/inventory/`)

### 4.1 Archivos a modificar

| Archivo | Cambio |
| :---- | :---- |
| `types/index.ts` | DTOs nuevos: `EquipamientoPublicoDTO`, `EquipamientoUpdateDTO`, `UnidadFisicaUpdateDTO`; `es_notebook` y `activo`; tipo unión `EquipamientoCatalogoDTO`. `Equipment` suma `activo` y `unidades?` |
| `services/inventoryApi.ts` | `editarEquipamiento`, `cambiarEstadoEquipamiento`, `editarUnidad`, `listarUnidades`, `agregarUnidad`, `crearCategoria` (si hace falta); `incluir_inactivos` en filtros; `ponerFueraDeServicio` → `ponerEnMantenimiento` y `darDeBaja` (D-09) |
| `services/mappers.ts` | `toEquipment` soporta DTO público y de admin; `toUnidad`; sin asumir `unidades` |
| `pages/CatalogPage.tsx` | Elimina el mock; usa `useCatalogo` (nuevo); estados de carga, error y vacío; filtros enviados a la API |
| `components/CatalogFilters.tsx`, `components/EquipmentCard.tsx` | Ajustes mínimos: contadores desde la API, aviso de vacío, acciones de admin (editar, desactivar) |
| `src/App.tsx` | **Punto de integración mínimo**: montar `<StockPage />` en la pantalla `admin-stock` (hoy muestra "pendiente de implementación") y agregar `"admin-stock"` a la lista de pantallas renderizadas. No se cambia nada más del layout (ver §6) |
| `Frontend-PrestaMeDios/README.md` | Estructura de `inventory` |

### 4.2 Archivos a crear

| Archivo | Contenido |
| :---- | :---- |
| `hooks/useCatalogo.ts` | Carga con `AbortSignal`, *debounce* de `q` (300 ms), estados `cargando`, `error`, `datos` |
| `pages/StockPage.tsx` | Tabla de stock para admins (PRE-12), filtro de sede, orden asc/desc |
| `components/StockTable.tsx` | Columnas Nombre, Categoría, Locker, Tipo, Disponibles; fila desplegable con unidades |
| `components/UnidadesRow.tsx` | Unidades con acciones "En mantenimiento", "Fuera de servicio (baja)" y "Rehabilitar", con confirmación |
| `components/EquipmentFormModal.tsx` | Alta y edición; selector de sede oculto para `ADMIN_LOCAL`, obligatorio para `SUPERADMIN` (INV-25) |
| `services/ordenar.ts` | Función pura de ordenamiento por columna (testeable) |
| `services/mappers.test.ts`, `services/ordenar.test.ts` | Pruebas unitarias con Vitest |

### 4.3 Eliminación

`services/mockInventory.ts` se borra al terminar la conexión (no tiene otros consumidores: verificado con búsqueda).

### 4.4 Decisiones de diseño

- El rol y la sede salen de `useAuth()` / `useSede()` (no de props simuladas). `CatalogPage` mantiene sus props actuales para no romper `App.tsx`; internamente ignora lo que ya resuelve la sesión.
- Estudiante y docente: el backend ya acota la sede; el front sólo oculta el selector.
- `ApiError.detail` se muestra tal cual (mensajes en español del backend).
- Acciones destructivas (baja, desactivar) piden confirmación; la baja avisa que es irreversible (D-03).
- Las acciones de "Agregar al carrito" y "Detalle" quedan como props opcionales sin lógica propia (Perfil 3).

## 5. Verificación

| Qué | Cómo |
| :---- | :---- |
| Backend | `pytest -q` completo (incluye los 257 existentes) y `pytest --cov=app/modules/inventory`. Meta: ≥ 90 % en `inventory`; cada INV-01…INV-23 con un test anotado |
| Migración | `alembic upgrade head` / `downgrade -1` / `upgrade head` en base de desarrollo; test `test_migracion_0010.py` |
| OpenAPI | Revisar `/docs`: ejemplos, códigos `401/403/404/409/422` y la unión de respuestas |
| Frontend | `npm run typecheck`, `npm run build`, `npm test`; recorrido manual o E2E de INV-24 e INV-25 contra el backend local |
| Trazabilidad | Tabla requisito → endpoint → test en la descripción del PR |

## 6. Puntos de contacto con otros perfiles (sin modificarlos)

| Elemento | Dueño | Tratamiento |
| :---- | :---- | :---- |
| `src/App.tsx` (montar `StockPage`) | Perfil 1 (layout) | Cambio de pocas líneas, confinado al render de `admin-stock`. **Se pide confirmación al Perfil 1 antes de integrar**; si no la hay, se entrega `StockPage` sin montar y se registra el ítem |
| Funciones de `service.py` | Perfil 3 | Se publican y documentan; `loans` las adopta por su cuenta |
| Parámetro de ventana del calendario (D-07) | Perfil 1 (`config`) | Pendiente de Fase B |
| Tope 15 del `CHECK` de `max_dias_prestamo` | Perfil 1 (`config`) | Ítem de aviso en `MEMORY.md` |
| Función de lectura de `loans` (ocupación, historial, reservas futuras) | Perfil 3 | Ítem de coordinación; bloquea Fase B |

## 7. Riesgos

| Riesgo | Mitigación |
| :---- | :---- |
| La unión de `response_model` no serializa bien según el rol | Pruebas de INV-05 temprano (tarea B-05); alternativa documentada en 3.3 |
| Cambio de contrato (D-02, D-04) rompe a consumidores | Hoy sólo lo consume el frontend de `inventory` (no conectado) y no hay `loans` operativo; se avisa a los Perfiles 3 y 5 en `MEMORY.md` |
| Datos de desarrollo con locker fuera de rango | La migración falla con ids y mensaje claro; no corrige en silencio |
| Tests con TRUNCATE no incluyen tablas de `loans` | `TRUNCATE … CASCADE` sobre `unidades_fisicas` ya arrastra las dependientes; sin acción |
| `App.tsx` es del Perfil 1 | §6: confirmación previa |

## 8. Fase B (fuera de este plan)

Se planifica en una revisión de este documento cuando `loans` publique: (a) lectura de ocupación por unidad y período, (b) historial de movimientos por unidad, (c) reservas futuras aprobadas por unidad. Trabajo previsto: `GET /equipamiento/{id}/disponibilidad`, `GET /unidades/{id}/historial`, campo `reservas_afectadas` en el cambio de estado, mini-calendario en el detalle, y la definición de D-07 con el Perfil 1.

## 9. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.0.0 | 2026-10-23 | Plan ejecutado (Fase A). Desviaciones: (1) la categoría se filtra en la pantalla y no en la API (spec §8); (2) la migración `0010` usa SQL directo para los `CHECK` por el prefijo duplicado de `NAMING_CONVENTION`; (3) `UnidadFormModal` agrega alta y edición de unidades desde la tabla de stock; (4) las ramas de T-00 se crearon al cierre, con pedido explícito: `feat/inventory-gestion` (backend, `b93017f`) y `feat/inventory-catalogo` (frontend, `128b749`), publicadas por `Farvi-1986` |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
