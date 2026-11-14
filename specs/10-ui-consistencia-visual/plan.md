# PLAN-10 — Plan técnico de la entrega 1 de SPEC-10

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/10-ui-consistencia-visual/spec.md` (v0.22.0, `EN REVISIÓN`) |
| **Estado del plan** | `EN REVISIÓN` — v1.0.0, 2026-11-14 |
| **Perfil** | 1 (transversal al frontend) |
| **Entrega** | Entrega 1: un PR de frontend, uno de backend (sólo M-02) y uno de Docs (§2). La entrega 2 (spec §1.5) tendrá su propio plan |

---

## 1. Punto de partida

| Elemento | Situación | Impacto en el plan |
| --- | --- | --- |
| Frontend | `develop` en `6ae5db4`; la rama `feat/ui-consistencia` sale de ahí y `develop` no avanzó desde entonces | PR directo, sin rebase |
| Backend | `develop` en `1c89c53`, cabeza `0019_inventory_categorias_base` | `0020_notifications_portada` cuelga de `0019`; `alembic heads` da una sola cabeza |
| Docs | `main` en `9a02a9a` | El spec, el plan y las tareas van en `docs/spec-10-ui` |
| Componentes comunes | `components/ui` tenía `Avatar`, `Badge`, `Button`, `Form`, `Input`, `icons` | Se suman `Dialogo`, `DatePicker`, `SelectorHora`, `calendario/GrillaMes` (spec §4.2) |
| Pantallas de otros perfiles | `inventory`, `loans`, `spaces`, `notifications` | Cambios de presentación; cada perfil revisa los suyos en el PR (spec §5) |

---

## 2. Ramas y PR

| Repo | Rama | Base | Contenido | Orden de merge |
| --- | --- | --- | --- | --- |
| Docs | `docs/spec-10-ui` | `main` | `spec.md`, `plan.md`, `tasks.md` | 1 (se revisa primero) |
| Backend | `feat/ui-consistencia` | `develop` | M-02: `0020_notifications_portada.py`, `notifications/portada.py`, `tests/notifications/test_portada.py`, líneas marcadas en `main.py` y `alembic/env.py` | 2 |
| Frontend | `feat/ui-consistencia` | `develop` | Toda la entrega (spec §5) | 3, después del backend: la portada necesita sus endpoints |

**Por qué un PR de frontend y no uno por dominio** (cambia lo que decía el spec §0): los componentes comunes (`Dialogo`, `DatePicker`, `GrillaMes`) los usan casi todos los dominios, y la rama ya los mezcla. Partirla obliga a mergear en cadena y a reconstruir cada paso. En cambio, el PR lista los archivos por dominio (spec §5) para que cada perfil revise sólo los suyos y deje su aval como comentario (U1…U4).

Los PR de frontend y backend **no se mergean** hasta tener el aval de los Perfiles 2 a 5 y la aprobación del spec.

---

## 3. Dependencias nuevas

Ninguna (NFR-U01).

---

## 4. Frontend

| Área | Archivos nuevos | Archivos modificados |
| --- | --- | --- |
| Base común | `components/ui/{Dialogo,DatePicker,SelectorHora}.tsx`, `components/ui/calendario/{GrillaMes.tsx,mes.ts,mes.test.ts}` | `components/ui/icons.tsx` (`clock`), `theme.ts` (`premium`, `premiumBg`), `App.tsx` (`DialogoProvider`, manual), `components/layout/Navbar.tsx` |
| Manual de uso (M-01) | `components/layout/{ManualDeUsoModal.tsx,manualDeUso.ts,manualDeUso.test.ts}` | `App.tsx` (líneas marcadas) |
| `inventory` | `AltaGamaBadge`, `LockerTable` (M-03), `VistaPreviaEquipo`, `services/{stockVista,vistaPrevia}.ts` y sus tests | `AgregarAlPedido`, `EquipmentCard`, `EquipmentDetailModal`, `EquipmentFormModal`, `MiniCalendario`, `Modal`, `StockTable`, `UnidadFormModal`, `UnidadesRow`, `hooks/useGestion.ts`, `CatalogPage`, `StockPage` |
| `loans` | `BandejaTabla`, `TerminosPrestamo` (M-04), `hooks/`, `services/{bandejaVista,calendarioPedido,misSolicitudesVista}.ts` y sus tests | `AprobarOrdenModal`, `CarritoPanel`, `SolicitudForm`, `BandejaPage`, `MisSolicitudesPage` |
| `spaces` | `MisReservas`, `SolicitudesPendientesEspacios`, `services/{motivo,reservasDelDia,pendientesVista}.ts` y sus tests | `CalendarGrid`, `SpacesPage` |
| `notifications` | `BannerComunicado`, `portada/` (M-02), `services/tema.ts` y su test | `ComunicadoForm`, `ComunicadosList`, `NewsPage` |
| `users` | — | `UsersPage`, `ProfilePage`, `types/index.ts` |

No cambian servicios de API existentes salvo `users/types` (dos campos opcionales de filtro que el backend ya acepta) y el cliente nuevo `notifications/portada/portadaApi.ts` (M-02).

---

## 5. Backend (M-02)

Tabla propia `comunicados_portada`, router propio montado antes que el de `notifications`, sin tocar tablas, esquemas ni enums existentes (spec §4.7, RN-U03). Se saca con `alembic downgrade` de `0020` y borrando los archivos marcados (spec §1.4).

---

## 6. Verificación por PR

| PR | Comandos | Resultado al 2026-11-14 |
| --- | --- | --- |
| Frontend | `npm run typecheck`, `npm test`, `npm run build` | En verde: 35 archivos, 257 tests |
| Backend | `pytest -q`, `alembic heads` | En verde: 969 tests; una sola cabeza (`0020`) |
| Manual | Recorrido con estudiante, docente, admin local y superadmin, en claro y oscuro | Hecho a lo largo del relevamiento (spec §13) |

---

## 7. Documentación y coordinación

| Momento | Qué se hace |
| --- | --- |
| Al abrir los PR | Pedir el aval de cada perfil sobre sus archivos (spec §5 y §11, U1…U4) |
| Al aprobar el spec | Registrar en `MEMORY.md` §5 los ítems U1…U7 y lo pendiente de la entrega 2 (spec §1.5) |
| Entrega 2 | Nuevo plan para P-1…P-5 (spec §1.5) |

---

## 8. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| PR de frontend grande, difícil de revisar | Tabla por dominio en la descripción; cada perfil revisa sólo lo suyo |
| Otro PR toca las mismas pantallas antes del merge | Rebase sobre `develop` y volver a correr §6 antes de mergear |
| Otra migración entra antes que `0020` | Ajustar `down_revision` a la nueva cabeza y verificar `alembic heads` |
| Un perfil no avala un cambio | Se saca ese cambio del PR (los MOMENTÁNEOS se sacan según spec §1.4) |

---

## 9. Historial

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 1.0.0 | 2026-11-14 | Perfil 1 (con asistencia de IA) | Plan de la entrega 1 |
