# TASKS-04 — Catálogo y existencias (`inventory`)

> **Spec:** `specs/04-inventory-catalogo-existencias/spec.md` v1.0.0 · **Plan:** `specs/04-inventory-catalogo-existencias/plan.md` v0.1.0 · **Estado:** `BORRADOR` · **Fecha:** 2026-10-23 · **Perfil:** 2
> Alcance: Fase A. Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo.
> Comandos de backend desde `Backend-PrestaMeDios/` (venv activo, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Bloque 0 — Preparación

- [x] **T-00 · Línea base.** Crear ramas `feat/inventory-gestion` (backend) y `feat/inventory-catalogo` (frontend) desde `develop` actualizado. Correr `pytest -q`, `npm run typecheck`, `npm run build`, `npm test` y anotar el resultado inicial (los 257 tests de 2026-10-08 no se volvieron a correr).
  *Verificación:* resultados anotados en el PR; si algo falla de entrada, se informa antes de seguir.

## Bloque 1 — Backend: contratos, modelos y migración (API-First)

- [x] **B-01 · Esquemas.** En `inventory/schemas.py`: `es_notebook` y `activo`, `EquipamientoPublicoResponse` (sin `unidades`, con `locker` y campos calculados), `EquipamientoUpdate` (todo opcional, sin `codigo`, `extra="forbid"`), `EquipamientoEstadoUpdate {activo}`, `UnidadFisicaUpdate` (`numero_serie`, `codigo_inventario`, `locker` 1–7; sin `sede`). `Field(..., examples=[...])` en todos.
  *Verificación:* `python -c "from app.main import app; app.openapi()"` sin errores. *Cubre:* INV-05, INV-15, INV-17.
- [x] **B-02 · Modelos.** `Equipamiento.activo`, `Equipamiento.es_notebook`; `CHECK` `locker_rango` (reemplaza `locker_positivo`).
  *Verificación:* la suite existente sigue en verde (la base de tests usa `create_all`). *Cubre:* INV-14.
- [x] **B-03 · Migración `0010_inventory_gestion`.** `upgrade` con las dos columnas y el reemplazo del `CHECK`, con verificación previa de locker fuera de rango (falla con los ids); `downgrade` reversible.
  *Verificación:* `alembic upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo; probar con un locker 9 insertado a mano (debe fallar con mensaje claro). *Cubre:* INV-23.
- [x] **B-04 · Test de migración.** `tests/inventory/test_migracion_0010.py`: inspección del `CHECK` y de las columnas con el modelo; el módulo de migración se carga como en `test_spaces_migrations.py`.
  *Verificación:* verde. *Cubre:* INV-14 (base), INV-23.

## Bloque 2 — Backend: servicio y reglas

- [x] **B-05 · `service.py`.** `TRANSICIONES_ADMIN`, `bloquear_unidad`, `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad`. Sin `commit`; errores con `AppError`.
  *Verificación:* `tests/inventory/test_service.py` (excluye `mantenimiento`, `baja` y otra sede; transiciones inválidas → `409`). *Cubre:* INV-22.
- [x] **B-06 · Lectura por rol.** En el router: respuesta pública vs. de admin (unión de `response_model`), `incluir_inactivos`, filtro de `activo`, escape de `q`. Verificar la serialización de la unión en el OpenAPI.
  *Verificación:* `tests/inventory/test_catalogo.py`. *Cubre:* INV-02, 03, 04, 05, 06, 07, 08.
- [x] **B-07 · Ajuste de tests existentes por D-04.** Actualizar `test_estudiante_ve_solo_su_sede` y los demás que usen `unidades` con roles no admin (plan §3.4).
  *Verificación:* `pytest tests/inventory -q` en verde, con cada cambio comentado `# INV-05`.
- [x] **B-08 · Alta con plazo por defecto.** `POST /equipamiento` toma `prestamo.notebook.max_dias` si `es_notebook`, si no `prestamo.general.max_dias`.
  *Verificación:* test que cambia el parámetro con `set_parametro` y comprueba ambos caminos. *Cubre:* INV-13.
- [x] **B-09 · Edición de equipamiento.** `PATCH /equipamiento/{id}` con regla de alcance (`404` si el ítem no tiene unidades en la sede del `ADMIN_LOCAL` y sí tiene en otra), `409` por duplicado y `422 CATEGORIA_INEXISTENTE`.
  *Verificación:* `tests/inventory/test_gestion.py`. *Cubre:* INV-15.
- [x] **B-10 · Baja lógica.** `PATCH /equipamiento/{id}/estado` con `409 EQUIPAMIENTO_CON_PRESTAMOS` y `403` para `ADMIN_LOCAL` con unidades en ambas sedes (D-06).
  *Verificación:* tests de desactivar, reactivar, con prestadas y con ambas sedes. *Cubre:* INV-06, INV-16.
- [x] **B-11 · Edición de unidades.** `PATCH /unidades/{id}`: serie, inventario y locker; la sede no cambia; `404` fuera de alcance; `409` por duplicado.
  *Verificación:* tests. *Cubre:* INV-17, INV-20.
- [x] **B-12 · Cambio de estado.** Reescribir `PATCH /unidades/{id}/estado`: `FOR UPDATE`, matriz de transiciones, idempotencia, `422 ESTADO_NO_PERMITIDO` para `prestado`, `409 TRANSICION_ESTADO_INVALIDA`.
  *Verificación:* tests de la matriz completa y de concurrencia (dos `PATCH` simultáneos con `asyncio.gather`, una sesión por request, ADR-013). *Cubre:* INV-18, INV-19, INV-21.
- [x] **B-13 · Altas, seguridad y errores.** Completar tests de altas y de roles que faltan: sede automática y obligatoria, duplicados concurrentes, roles sin permiso en cada ruta de escritura, `test_exige_sesion` con las rutas nuevas.
  *Verificación:* tests. *Cubre:* INV-01, 09, 10, 11, 12, 14 (API: locker 0, 8, −1 → `422`).
- [x] **B-14 · Cierre del backend.** `pytest -q` completo; `pytest --cov=app/modules/inventory` ≥ 90 %; revisar `/docs` (ejemplos, `401/403/404/409/422`, unión de respuestas); actualizar el README del backend.
  *Verificación:* cobertura y suite en verde; matriz INV-01…INV-23 completa con test anotado.

## Bloque 3 — Frontend

- [x] **F-01 · Tipos y API.** DTOs nuevos y `es_notebook`/`activo` en `types/index.ts`; funciones nuevas en `inventoryApi.ts`; `ponerFueraDeServicio` se reemplaza por `ponerEnMantenimiento` y `darDeBaja` (D-09).
  *Verificación:* `npm run typecheck`.
- [x] **F-02 · Mappers y orden.** `toEquipment` con DTO público y de admin, `toUnidad` y `services/ordenar.ts`.
  *Verificación:* `mappers.test.ts` y `ordenar.test.ts` (asc/desc por cada columna, locker nulo al final, comparación con acentos). `npm test`.
- [x] **F-03 · Catálogo conectado.** `hooks/useCatalogo.ts` y `CatalogPage` con carga, error y "sin resultados"; filtros de categoría, sede y texto enviados a la API; borrar `mockInventory.ts` al terminar.
  *Verificación:* `npm run build` y recorrido manual contra el backend local con estudiante, docente y admin. *Cubre:* INV-24 (parte catálogo).
- [x] **F-04 · Tabla de stock (PRE-12).** `StockTable`, `UnidadesRow` y `StockPage`: filtro de sede, flechas de orden, despliegue de unidades, botones "En mantenimiento", "Fuera de servicio" y "Rehabilitar" con confirmación y manejo de `ApiError`.
  *Verificación:* recorrido manual de PRE-12 y PRE-14 (incluyendo `409`). *Cubre:* INV-24 (parte stock).
- [x] **F-05 · Alta y edición.** `EquipmentFormModal`: selector de sede oculto para `ADMIN_LOCAL` y obligatorio para `SUPERADMIN`; `es_notebook`; baja lógica del ítem.
  *Verificación:* recorrido con `ADMIN_LOCAL` y `SUPERADMIN`; prueba unitaria de la lógica de sede si se extrae a una función. *Cubre:* INV-25.
- [x] **F-06 · Integración en `App.tsx`.** Montar `StockPage` en `admin-stock`. **Requiere confirmación previa del Perfil 1** (plan §6).
  *Verificación:* el menú de administrador abre la tabla; el resto de las pantallas no cambia. Si no hay confirmación, se omite y se registra en `MEMORY.md`.
- [x] **F-07 · Cierre del frontend.** `npm run typecheck`, `npm run build`, `npm test`; actualizar el README del frontend; sin referencias al mock.
  *Verificación:* los tres comandos en verde y `grep` sin `mockInventory`.

## Bloque 4 — Documentación y registro

- [x] **D-01 · `MEMORY.md`.** Registrar: ADR de este spec (D-02, D-03, D-04, D-05, D-09), cierre de DT-22 y DT-23, avance de DT-20 (funciones de `service.py` publicadas), snapshot de `inventory`, bitácora, y los ítems de coordinación del spec §10 (hacia Perfiles 1, 3 y 5). Los ítems de coordinación pueden adelantarse hoy.
  *Verificación:* revisión del Perfil 1 (dueño del documento).
- [ ] **D-02 · Estado de los documentos.** Pasar el spec a `IMPLEMENTADO` y actualizar el estado del Perfil 2 en `docs/perfiles.md` y `AGENTS.md` §3 (a pedido del Perfil 1, que los mantiene).
  *Verificación:* PRs de documentación o aprobación del Perfil 1.
- [ ] **D-03 · PR.** Descripción con tabla requisito → endpoint → test, resultados de pruebas y migración, y el aviso del cambio de contrato (D-02, D-04). Sin commit, push ni merge salvo pedido explícito.

## Orden y dependencias

```
T-00
 └─ B-01 → B-02 → B-03 → B-04
              └─ B-05 → B-06 → B-07 → B-08 → B-09 → B-10 → B-11 → B-12 → B-13 → B-14
B-06 (contrato de lectura estable) ──► F-01 → F-02 → F-03 → F-04 → F-05 → F-06 → F-07
B-12 (contrato de estado estable) ───► F-04
D-01 (coordinación) puede adelantarse a cualquier momento; el resto al cierre
```

El frontend puede arrancar cuando B-06 y B-12 estén listos; antes de eso, contra los contratos de OpenAPI ya publicados por B-01.

## Matriz de cobertura (criterio → tarea)

| Criterio | Tarea | Criterio | Tarea |
| :---- | :---- | :---- | :---- |
| INV-01 | B-13 | INV-14 | B-04, B-13 |
| INV-02…08 | B-06 | INV-15 | B-09 |
| INV-09…12 | B-13 | INV-16 | B-10 |
| INV-13 | B-08 | INV-17 | B-11 |
| INV-18, 19, 21 | B-12 | INV-20 | B-11 |
| INV-22 | B-05 | INV-23 | B-03, B-04 |
| INV-24 | F-03, F-04 | INV-25 | F-05 |
| INV-26 | Fase B (fuera) | | |

## Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.0.0 | 2026-10-23 | Fase A ejecutada: T-00, B-01…B-14, F-01…F-07 y D-01 cerradas; quedan D-02 (documentos del Perfil 1) y D-03 (PR). Notas: T-00: las ramas se crearon al cierre (`feat/inventory-gestion` `b93017f` y `feat/inventory-catalogo` `128b749`, publicadas); F-03 filtra la categoría en la pantalla; INV-24 e INV-25 verificados a mano en el navegador integrado contra un backend local con base descartable |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
