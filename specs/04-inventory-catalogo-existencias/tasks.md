# TASKS-04 — Catálogo y existencias (`inventory`)

> **Spec:** `specs/04-inventory-catalogo-existencias/spec.md` v1.3.0 · **Plan:** `specs/04-inventory-catalogo-existencias/plan.md` v2.1.0 · **Estado:** Fases A y B ejecutadas (cierre de B en B-22: backend PR #46, frontend PR #33); Fase C `BORRADOR` · **Fecha:** 2026-11-23 · **Perfil:** 2
> Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo. **Las tareas C-02…C-05 esperan a que el spec v1.3.0 esté `APROBADO`.** B-22 y U-01 ya tienen spec aprobado.
> Comandos de backend desde `Backend-PrestaMeDios/` (venv con Python 3.12, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Fase A (cerrada)

T-00, B-01…B-14, F-01…F-07 y D-01…D-03 cerradas el 2026-10-23 (detalle en la versión 1.0.0 de este archivo, en el historial de Git). Cobertura: INV-01…INV-25 (matriz al final). Notas de cierre:

- [x] **D-02 · Estado de los documentos.** `docs/perfiles.md` §4–§5 y `AGENTS.md` §3 actualizados por el Perfil 1 el 2026-11-02 (`MEMORY.md` §5, ítem del 2026-10-23 cerrado).
- [x] **D-03 · PR.** Backend PR \#14 y frontend PR \#9, mergeados en `develop` el 2026-10-23.
- [x] **Posteriores:** `datos_equipamiento_por_ids` (C8, INV-27, backend PR \#19), "No disponible" (DT-27, frontend PR \#11) y test de concurrencia (DT-28, backend PR \#20), todos en `develop` el 2026-11-06. Categorías base con la migración `0019` (backend PR \#37, 2026-11-11), registrada en spec §7 con la v1.3.0.

---

## Fase B (ejecutada; verificado en `develop` el 2026-11-23)

### Bloque P — Proceso

- [x] **P-01 · Aprobación del spec v1.2.0.** Fase B aprobada por el Perfil 1 el 2026-11-07 (Docs `0af866d`).
- [x] **P-02 · Avisos de coordinación.** Registrados en `MEMORY.md` §5 el 2026-11-07 (C14, C17, C16, C18, D-12, D-07).
- [x] **P-03 · Línea base y ramas.** `feat/inventory-disponibilidad` (backend) y la rama del frontend del PR \#13.

### Bloque B — Backend (PR \#24, mergeado el 2026-11-08)

- [x] **B-15 · `marcar_unidad_mantenimiento` y contrato de `bloquear_unidad` (C17, C14).** En `service.py`. *Test:* `test_service.py::test_mantenimiento_desde_disponible` cubre transición, idempotencia y `404`, sin anotar `# INV-28`. **El resto de INV-28 queda en B-22.**
- [x] **B-16 · Plazo al cambiar de tipo (C18).** *Test:* `test_plazo_tipo.py` (INV-29).
- [x] **B-17 · Esquemas de disponibilidad.**
- [x] **B-18 · `disponibilidad.py`.** Único archivo que importa `loans` (RN-I16).
- [x] **B-19 · Endpoint `GET /equipamiento/{id}/disponibilidad`.** *Test:* `test_disponibilidad.py` (INV-26, INV-30).
- [x] **B-20 · Coherencia con `loans` (C16, INV-31).** Sin test en `develop`; hecho en B-22.
- [x] **B-21 · Cierre del backend.** README y cobertura hechos en B-22.

### Bloque F — Frontend (PR \#13; estilos y modo oscuro en el PR \#23)

- [x] **F-08 · Tipos y API.** `obtenerDisponibilidad` (con test en `inventoryApi.test.ts`).
- [x] **F-09 · Lógica pura.** `services/calendario.ts` y `services/botonAgregar.ts` (renombrado desde `carrito.ts` en el PR \#29), con sus tests.
- [x] **F-10 · `useDisponibilidad` y `MiniCalendario`** (INV-32). Con SPEC-10 se dibuja con `GrillaMes`.
- [x] **F-11 · `EquipmentDetailModal` y apertura desde el catálogo** (INV-32).
- [x] **F-12 · "Agregar al pedido" y "Disponibles hoy"** (INV-33). El Perfil 3 conectó `onAddToCart` en `App.tsx`.
- [x] **F-13 · Cierre del frontend.** README hecho en B-22.

### Bloque D — Documentación y PR

- [x] **D-04 · `MEMORY.md`.** Snapshot de la Fase B registrado (2026-11-10/11).
- [x] **D-05 · Estado de los documentos.** Spec con Fase B `IMPLEMENTADO` en la v1.3.0 (este PR de Docs).
- [x] **D-06 · PRs de código.** Backend PR \#24 y frontend PR \#13.

### Pendiente de cierre (spec aprobado: se puede programar ya)

- [x] **B-22 · Cierre de la Fase B.** Hecho el 2026-11-23 en la rama `fix/inventory-cierre-fase-b` de backend y frontend: backend PR #46 y frontend PR #33, en revisión.
  - (a) INV-28 en `test_service.py` (cuatro tests anotados): desde `prestado` y `baja` → `409`; sin `commit` ni `flush` (el cambio queda en `sesion.dirty` y otra sesión sigue leyendo `disponible`); devolución con daño (`liberar_unidad` + `marcar_unidad_mantenimiento`): otra sesión lee `prestado` hasta el `commit` y después `mantenimiento`. **Hallazgo:** con `autoflush=False` esa secuencia respondía `409`, porque `bloquear_unidad` usaba `populate_existing` y descartaba el `disponible` pendiente. Se corrigió en `bloquear_unidad`: no refresca la unidad si la sesión ya tiene un cambio pendiente sobre ella (la bloqueó esta misma transacción). Sin cambio de contrato (§6.2).
  - (b) INV-31 en `test_disponibilidad.py`: con una reserva de los días +4 a +6, el calendario da 0 el día +5 y `POST /api/v1/loans/ordenes` responde `409 EQUIPAMIENTO_NO_DISPONIBLE`; el día +10 da 1 y la orden se crea (`201`). Coinciden sin ajustar RN-I14.
  - (c) READMEs: backend (ruta de disponibilidad y API pública de `inventory/service.py`) y frontend (fila de `inventory`: ficha, calendario y contrato `onAddToCart`).
  - *Verificación:* `pytest -q` completo **992 en verde** (9 min 50 s, PostgreSQL local); `pytest --cov=app/modules/inventory` **99 %** (`service.py` 99 %, `router.py` 97 %). Frontend: sólo cambia el README, sin código. *Cubre:* INV-28, INV-31.

---

## Bloque U — Aval de SPEC-10

- [ ] **U-01 · Aval U1 de la entrega 2.** Revisado el 2026-11-23 sobre los cambios locales del Perfil 1 en `inventory` (`EquipmentDetailModal`, `MiniCalendario`). Se da con dos correcciones (spec §10): (a) no importar `REGLAMENTO_USO` desde `loans` (D-12) ni filtrarlo por el comienzo del texto; (b) mantener la leyenda "Orientativo: la confirmación llega al enviar el pedido" (§8.2, RN-I15). Lo demás (tarjetas, ficha, stock, vista por locker MOMENTÁNEA) tiene aval.
  *Verificación:* aval registrado en SPEC-10 §11 (U1) por el Perfil 1 cuando lleguen las correcciones.

---

## Fase C (spec v1.3.0 `BORRADOR`)

- [ ] **P-04 · Aprobación del spec v1.3.0.** Presentar al Perfil 1 §5.3, §5.5, §8.3, §9.3 y D-15…D-18 (en especial D-16: `ordenes_afectadas`). Al aprobarse: estado `APROBADO` en el encabezado y §14.
  *Verificación:* PR de Docs mergeado con la aprobación registrada.
- [x] **C-01 · Revisar firmas.** Hecho el 2026-11-23: `reservas_futuras_de_unidad` coincide con §5.3; `historial_de_unidad` suma `detalle_id`, pagina en `loans`, filtra por sede de la orden y deja tres campos en `null` hasta la `0012` de `loans`. El spec v1.3.0 ya lo refleja.
- [ ] **C-02 · Historial por unidad (backend).** Esquemas `SolicitanteResumen` y `MovimientoUnidadResponse`; `GET /unidades/{id}/historial` (plan §6.1).
  *Verificación:* `tests/inventory/test_historial.py`. *Cubre:* INV-34.
- [ ] **C-03 · `reservas_afectadas` y `ordenes_afectadas` (backend).** `UnidadEstadoResponse` y el cálculo tras el `commit` en `cambiar_estado_unidad` (plan §6.1).
  *Verificación:* casos de INV-35 en `test_gestion.py`; INV-18, 19 y 21 siguen en verde. *Cubre:* INV-35.
- [ ] **C-04 · Historial y aviso (frontend).** Tipos, `listarHistorialUnidad`, `services/historial.ts`, `HistorialUnidadModal`, botón en `UnidadesRow`, aviso en `useGestion` y `StockPage` (plan §6.2). Antes, confirmar con el Perfil 1 que la entrega 2 de SPEC-10 no toca esos archivos.
  *Verificación:* `npm test` (incluye `historial.test.ts`), `npm run build` y recorrido manual. *Cubre:* INV-36.
- [ ] **C-05 · Cierre de la Fase C.** Suites completas, READMEs, `MEMORY.md` (snapshot y aviso al Perfil 3 de `ordenes_afectadas`), spec con la Fase C `IMPLEMENTADO` y PRs (sin commit, push ni merge salvo pedido explícito).

**Fuera de alcance:** importación del inventario desde CSV o Excel (spec D-15): no está en el ERS.

## Orden y dependencias

```
Ya:        B-22 hecha (backend PR #46, frontend PR #33) · U-01 (aval) · P-04 (presentar la v1.3.0)
Fase C:    P-04 aprobado ──► C-02 → C-03 → C-04 → C-05
           C-02 y C-03 son independientes entre sí; C-04 necesita los dos en un backend local
```

Con B-22 y C-05 cerrados, SPEC-04 queda `IMPLEMENTADO` completo y el Perfil 2 cubre PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 y su parte de PRE-17.

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
| INV-34 | C-02 | INV-35 | C-03 |
| INV-36 | C-04 | INV-28, INV-31 (cierre) | B-22 |

## Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 2.1.0 | 2026-11-23 | Perfil 2, con asistencia de IA. Fase B marcada según `develop` (PR \#24, \#13, \#23): B-20, B-21 y F-13 quedan abiertas y se juntan en B-22 (INV-28 completo, INV-31, READMEs). Bloque U (aval de SPEC-10). Fase C según el spec v1.3.0: P-04, C-01 hecha, C-02…C-05 con INV-36. Importación por CSV fuera de alcance (D-15) |
| 2.0.0 | 2026-11-07 | `BORRADOR` (Perfil 2, con asistencia de IA): tareas de las Fases B y C (P-01…P-03, B-15…B-21, F-08…F-13, D-04…D-06, C-01…C-05). D-02 y D-03 de la Fase A marcadas como cerradas con sus referencias |
| 1.0.0 | 2026-10-23 | Fase A ejecutada: T-00, B-01…B-14, F-01…F-07 y D-01 cerradas; quedan D-02 (documentos del Perfil 1) y D-03 (PR). Notas: T-00: las ramas se crearon al cierre (`feat/inventory-gestion` `b93017f` y `feat/inventory-catalogo` `128b749`, publicadas); F-03 filtra la categoría en la pantalla; INV-24 e INV-25 verificados a mano en el navegador integrado contra un backend local con base descartable |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
