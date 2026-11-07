# TASKS-04 — Catálogo y existencias (`inventory`)

> **Spec:** `specs/04-inventory-catalogo-existencias/spec.md` v1.2.0 · **Plan:** `specs/04-inventory-catalogo-existencias/plan.md` v2.0.0 · **Estado:** Fase A cerrada; Fases B y C `BORRADOR` · **Fecha:** 2026-11-07 · **Perfil:** 2
> Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo. **Las tareas de las Fases B y C esperan a que el spec v1.2.0 esté `APROBADO`** (salvo P-01 y P-02, que son de documentación).
> Comandos de backend desde `Backend-PrestaMeDios/` (venv con Python 3.12, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Fase A (cerrada)

T-00, B-01…B-14, F-01…F-07 y D-01…D-03 cerradas el 2026-10-23 (detalle en la versión 1.0.0 de este archivo, en el historial de Git). Cobertura: INV-01…INV-25 (matriz al final). Notas de cierre:

- [x] **D-02 · Estado de los documentos.** `docs/perfiles.md` §4–§5 y `AGENTS.md` §3 actualizados por el Perfil 1 el 2026-11-02 (`MEMORY.md` §5, ítem del 2026-10-23 cerrado).
- [x] **D-03 · PR.** Backend PR \#14 y frontend PR \#9, mergeados en `develop` el 2026-10-23.
- [x] **Posteriores:** `datos_equipamiento_por_ids` (C8, INV-27, backend PR \#19), "No disponible" (DT-27, frontend PR \#11) y test de concurrencia (DT-28, backend PR \#20), todos en `develop` el 2026-11-06.

---

## Bloque P — Proceso (antes de programar)

- [ ] **P-01 · Aprobación del spec v1.2.0.** Presentar al Perfil 1 el spec (incluye el addendum §6.1 ya mergeado) y las decisiones D-07, D-11…D-14. Al aprobarse: estado `APROBADO`, versión 1.2.0 y fecha en §14.
  *Verificación:* PR de Docs mergeado con la aprobación registrada.
- [ ] **P-02 · Avisos de coordinación.** En `MEMORY.md` §5: C14 y C17 aceptados (con fecha de entrega prevista), C16 y C18 respondidos, contrato `onAddToCart` (D-12) para el Perfil 3 y el Perfil 1, retiro del pedido de la clave de ventana (D-07).
  *Verificación:* ítems registrados en el mismo PR de Docs que P-01.
- [ ] **P-03 · Línea base.** Ramas `feat/inventory-disponibilidad` (backend) y `feat/inventory-detalle` (frontend) desde `develop` actualizado. Correr `pytest -q`, `npm run typecheck`, `npm run build`, `npm test` y anotar el resultado (si falla `test_datos_publicos_solo_tiene_id_nombre_y_apellido_e_inmutable`, es DT-30 por Python 3.13: cambiar a 3.12).
  *Verificación:* resultados anotados para el PR.

## Bloque B — Fase B, backend

- [ ] **B-15 · `marcar_unidad_mantenimiento` y contrato de `bloquear_unidad` (C17, C14).** En `service.py`: la función de plan §4.2; docstring del módulo con la API pública; docstring de `bloquear_unidad` con las tres reglas de spec §6.2.
  *Verificación:* `tests/inventory/test_service.py` con los casos de plan §4.6. *Cubre:* INV-28.
- [ ] **B-16 · Plazo al cambiar de tipo (C18).** Extraer `_plazo_por_defecto(db, es_notebook)` de `crear_equipamiento` y aplicar RN-I13 en `editar_equipamiento` (plan §4.4).
  *Verificación:* los tests de INV-13 siguen en verde y los nuevos de INV-29 en `test_gestion.py`. *Cubre:* INV-29.
- [ ] **B-17 · Esquemas de disponibilidad.** `DiaDisponibilidad` y `DisponibilidadResponse` en `schemas.py` (plan §4.5), con `Field(..., examples=[...])`.
  *Verificación:* `python -c "from app.main import app; app.openapi()"` sin errores.
- [ ] **B-18 · `disponibilidad.py`.** `MAX_DIAS_DISPONIBILIDAD`, `inicio_del_dia`, `validar_rango`, `contar_libres_por_dia` y `disponibilidad_por_dia` (plan §4.3). Sólo este archivo importa `loans` (RN-I16).
  *Verificación:* `tests/inventory/test_disponibilidad_unit.py` (sin base, casos de plan §4.6) y `python -c "import app.main"` sin error de import circular.
- [ ] **B-19 · Endpoint `GET /equipamiento/{id}/disponibilidad`.** En `router.py`, con el orden de validación de plan §4.4 y la respuesta de §5.4.
  *Verificación:* `tests/inventory/test_disponibilidad.py`. *Cubre:* INV-26, INV-30.
- [ ] **B-20 · Coherencia con `loans` (C16).** Test de integración que compara el calendario con `POST /api/v1/loans/ordenes` sobre los mismos datos (plan §4.6).
  *Verificación:* test en verde. Si falla, **no** se ajusta el test: se detiene la tarea y se revisa RN-I14 con el Perfil 3. *Cubre:* INV-31.
- [ ] **B-21 · Cierre del backend.** `test_exige_sesion` (o el test de INV-01) con la ruta nueva; `pytest -q` completo; `pytest --cov=app/modules/inventory` ≥ 90 %; revisar `/docs`; README del backend (endpoint nuevo, `marcar_unidad_mantenimiento`, `bloquear_unidad` pública).
  *Verificación:* suite y cobertura en verde; INV-26, 28, 29, 30, 31 con test anotado.

## Bloque F — Fase B, frontend

- [ ] **F-08 · Tipos y API.** `DiaDisponibilidadDTO`, `DisponibilidadDTO`, `DiaCalendario` en `types/index.ts`; `obtenerDisponibilidad` en `inventoryApi.ts` (con `construirQuery` o equivalente para `desde`, `hasta`, `sede`).
  *Verificación:* `npm run typecheck` y un caso en `inventoryApi.test.ts` que arma la URL correcta.
- [ ] **F-09 · Lógica pura del calendario y del botón.** `services/calendario.ts` y `services/carrito.ts` (plan §5.1).
  *Verificación:* `calendario.test.ts` y `carrito.test.ts` (casos de plan §5.1). `npm test`.
- [ ] **F-10 · `useDisponibilidad` y `MiniCalendario`.** Hook con `AbortController`; componente con flechas limitadas por `puedeIrA`, grilla, leyenda, carga, error y `aria-label` por día.
  *Verificación:* `npm run build`; recorrido manual contra el backend local (dos meses, un día en rojo). *Cubre:* INV-32 (calendario).
- [ ] **F-11 · `EquipmentDetailModal` y apertura desde el catálogo.** Modal con los datos de spec §8.2 y el calendario; `CatalogPage` con estado `detalle`, sin la prop `onSelect`; tarjeta y fila abren el detalle para todos los roles; selector de sede propio si el `SUPERADMIN` está en "ambas sedes".
  *Verificación:* recorrido manual con estudiante, admin local y `SUPERADMIN`. *Cubre:* INV-32.
- [ ] **F-12 · Botón "Agregar al pedido" y rótulo (C11, C16).** `AgregarAlPedido` en tarjeta, fila y detalle, visible sólo con `onAddToCart` y rol estudiante o docente, deshabilitado con el motivo de `motivoNoAgregable`; "Disponibles" → "Disponibles hoy".
  *Verificación:* tests de F-09 y recorrido manual con un *callback* de prueba local (no se commitea). *Cubre:* INV-33.
- [ ] **F-13 · Cierre del frontend.** `npm run typecheck`, `npm run build`, `npm test`; README del frontend (detalle, calendario y contrato `onAddToCart` para el Perfil 3).
  *Verificación:* los tres comandos en verde.

## Bloque D — Documentación y PR de la Fase B

- [ ] **D-04 · `MEMORY.md`.** Snapshot de `inventory` (Fase B), bitácora, ADR de D-11…D-14 y D-07 (o una entrada en ADR-020), aviso al Perfil 3 de que `marcar_unidad_mantenimiento` está publicada (destraba AC-L59) y de que el botón espera su cableado en `App.tsx`.
  *Verificación:* PR de Docs.
- [ ] **D-05 · Estado de los documentos.** Spec: Fase B `IMPLEMENTADO` en el encabezado y §14; `AGENTS.md` §3 y `docs/perfiles.md` §4 (los mantiene el Perfil 1: se pide en `MEMORY.md` §5).
  *Verificación:* PR de Docs o pedido registrado.
- [ ] **D-06 · PRs de código.** Backend y frontend, con tabla requisito → endpoint → test, resultados de pruebas y el aviso de que `inventory` ahora depende de `loans.ocupacion_de_unidades`. Sin commit, push ni merge salvo pedido explícito.

## Bloque C — Fase C (bloqueada: espera `historial_de_unidad` y `reservas_futuras_de_unidad` de `loans`)

- [ ] **C-01 · Revisar firmas.** Cuando `loans` las publique en `develop`, compararlas con spec §5.3 y §5.5. Si difieren, actualizar el spec (revisión menor) y pedir re-aprobación antes de seguir.
  *Verificación:* spec al día y aprobado.
- [ ] **C-02 · Historial por unidad (backend).** Esquemas `SolicitanteResumen` y `MovimientoUnidadResponse`; `GET /unidades/{id}/historial` (plan §6).
  *Verificación:* `tests/inventory/test_historial.py`. *Cubre:* INV-34.
- [ ] **C-03 · `reservas_afectadas` (backend).** `UnidadEstadoResponse` y el cálculo tras el `commit` en `cambiar_estado_unidad` (plan §6).
  *Verificación:* casos de INV-35 en `test_gestion.py`; los tests de INV-18, 19 y 21 siguen en verde. *Cubre:* INV-35 (backend).
- [ ] **C-04 · Historial y aviso (frontend).** DTOs, `listarHistorialUnidad`, `HistorialUnidadModal`, botón "Historial" en `UnidadesRow` y aviso persistente en el stock.
  *Verificación:* `npm test`, `npm run build` y recorrido manual. *Cubre:* INV-34 (UI), INV-35 (UI).
- [ ] **C-05 · Cierre de la Fase C.** Suites completas, README de ambos repos, `MEMORY.md` y estado del spec (`IMPLEMENTADO` completo); PRs.

## Orden y dependencias

```
P-01 (aprobación) ──► P-03
P-02 puede ir en el mismo PR que P-01

Backend:  P-03 → B-15 → B-16 → B-17 → B-18 → B-19 → B-20 → B-21
                 (B-15 y B-16 son independientes del resto y se pueden hacer primero o en paralelo)
Frontend: B-17 (contrato) ──► F-08 → F-09 → F-10 → F-11 → F-12 → F-13
          F-09 no necesita el backend; F-10 y F-11 sí (backend local con B-19)
Docs:     B-21 + F-13 ──► D-04 → D-05 → D-06

Fase C:   loans publica historial y reservas ──► C-01 → C-02 → C-03 → C-04 → C-05
```

**Para la demo alcanza con P-01…F-13.** B-15 (C17) conviene entregarlo primero, porque destraba la devolución con daño del Perfil 3.

## Matriz de cobertura (criterio → tarea)

| Criterio | Tarea | Criterio | Tarea |
| :---- | :---- | :---- | :---- |
| INV-01 | B-13 (A), B-21 | INV-14 | B-04, B-13 (A) |
| INV-02…08 | B-06 (A) | INV-15 | B-09 (A) |
| INV-09…12 | B-13 (A) | INV-16 | B-10 (A) |
| INV-13 | B-08 (A), B-16 | INV-17 | B-11 (A) |
| INV-18, 19, 21 | B-12 (A) | INV-20 | B-11 (A) |
| INV-22 | B-05 (A) | INV-23 | B-03, B-04 (A) |
| INV-24 | F-03, F-04 (A) | INV-25 | F-05 (A) |
| INV-26 | B-19 | INV-27 | PR \#19 |
| INV-28 | B-15 | INV-29 | B-16 |
| INV-30 | B-19 | INV-31 | B-20 |
| INV-32 | F-10, F-11 | INV-33 | F-09, F-12 |
| INV-34 | C-02, C-04 | INV-35 | C-03, C-04 |

## Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 2.0.0 | 2026-11-07 | `BORRADOR` (Perfil 2, con asistencia de IA): tareas de las Fases B y C (P-01…P-03, B-15…B-21, F-08…F-13, D-04…D-06, C-01…C-05). D-02 y D-03 de la Fase A marcadas como cerradas con sus referencias |
| 1.0.0 | 2026-10-23 | Fase A ejecutada: T-00, B-01…B-14, F-01…F-07 y D-01 cerradas; quedan D-02 (documentos del Perfil 1) y D-03 (PR). Notas: T-00: las ramas se crearon al cierre (`feat/inventory-gestion` `b93017f` y `feat/inventory-catalogo` `128b749`, publicadas); F-03 filtra la categoría en la pantalla; INV-24 e INV-25 verificados a mano en el navegador integrado contra un backend local con base descartable |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
