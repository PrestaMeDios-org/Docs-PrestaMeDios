# TASKS-10 — Consistencia visual, entrega 1

> **Spec:** `specs/10-ui-consistencia-visual/spec.md` v0.22.0 (`EN REVISIÓN`) · **Plan:** `specs/10-ui-consistencia-visual/plan.md` v1.0.0 · **Estado:** `EN REVISIÓN`
> La entrega 1 se implementó durante el relevamiento, a pedido del Perfil 1 (spec §2.3 y §13). Estas tareas registran lo hecho y lo que falta para integrarlo. Lo pendiente del spec (§1.5) es la entrega 2.

---

## Bloque 0 — Preparación

- [x] **T-00 · Línea base.** Frontend `develop` `6ae5db4`, backend `develop` `1c89c53` (cabeza `0019`), Docs `main` `9a02a9a`; las ramas no quedaron atrás.

## Bloque A — Base común (frontend)

- [x] **A-01 · Diálogo propio** (`Dialogo.tsx`) y reemplazo de `window.confirm`/`window.prompt` en las seis acciones. *Cubre:* V-11, AC-U11.
- [x] **A-02 · Calendario común** (`GrillaMes`, `DatePicker`, `SelectorHora`), con tests de `mes.ts`. *Cubre:* V-01, V-08, AC-U08.
- [x] **A-03 · Tokens `premium`/`premiumBg`** e ícono `clock`. *Cubre:* V-06.
- [x] **A-04 · Manual de uso** (M-01), con `manualDeUso.test.ts`. *Cubre:* V-02, AC-U01…AC-U07.

## Bloque B — Pantallas (frontend)

- [x] **B-01 · `inventory`:** tarjeta y lista del catálogo, detalle del equipo, alta con vista previa, Control de Stock y vista por locker (M-03). *Cubre:* V-04, V-05, V-07, V-15…V-17, AC-U09, AC-U10, AC-U14, AC-U15.
- [x] **B-02 · `loans`:** Solicitar equipos con disponibilidad, Términos y Condiciones (M-04), Bandeja en tabla y Mis Solicitudes con pestañas. *Cubre:* V-14, V-18, V-19, AC-U13, AC-U16, AC-U17.
- [x] **B-03 · `spaces`:** calendario alineado, turnos del día, materia y descripción, y pendientes del admin con filtros y paginación. *Cubre:* V-09, V-12, V-13, V-21, AC-U12, AC-U19.
- [x] **B-04 · `notifications`:** tarjetas de comunicados y portada elegible (M-02, front). *Cubre:* V-10, AC-U20.
- [x] **B-05 · `users`:** directorio con chips por rol y orden. *Cubre:* V-20, AC-U18.

## Bloque C — Backend (M-02)

- [x] **C-01 · Portada de comunicado:** migración `0020`, router `portada.py` y `test_portada.py`. *Verificación:* upgrade → downgrade → upgrade; una sola cabeza. *Cubre:* AC-U20.

## Bloque D — Integración

- [x] **D-01 · Verificación completa.** `npm run typecheck`, `npm test` (257) y `npm run build`; `pytest -q` (969) y `alembic heads`. *Cubre:* AC-U21.
- [x] **D-02 · Spec completo para revisión** (v0.22.0): pendientes en §1.5 con el marcador `PENDIENTE SPEC-10`, plan y tareas.
- [ ] **D-03 · PR de Docs** hacia `main`.
- [ ] **D-04 · PR de backend** hacia `develop`.
- [ ] **D-05 · PR de frontend** hacia `develop`, con la tabla por dominio y el pedido de aval.
- [ ] **D-06 · Avales** de los Perfiles 2, 3, 4 y 5 (U1…U4) y aprobación del spec.
- [ ] **D-07 · Merge** en el orden del plan §2 (Docs, backend, frontend), después de rebasar y repetir D-01 si `develop` avanzó.
- [ ] **D-08 · `MEMORY.md`:** ítems U1…U7 y la entrega 2 (plan §7).
