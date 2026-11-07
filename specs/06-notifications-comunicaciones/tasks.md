# TASKS-06 — Comunicaciones y notificaciones (`notifications`)

> **Spec:** `specs/06-notifications-comunicaciones/spec.md` v1.0.0 · **Plan:** `specs/06-notifications-comunicaciones/plan.md` v1.0.0 · **Estado:** `APROBADO` (2026-11-07) · **Fecha:** 2026-11-07 · **Perfil:** 5
> Alcance: Fases A y B. Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo.
> Comandos de backend desde `Backend-PrestaMeDios/` (venv con **Python 3.12** activo, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Bloque 0 — Preparación

- [x] **T-00 · Línea base.** Actualizar `develop` en backend y frontend. Crear `feat/notifications-comunicados` en los dos repos. Correr `pytest -q`, `npm run typecheck`, `npm run build` y `npm test`, y anotar el resultado inicial.
  *Verificación:* resultados anotados en el PR; si algo falla de entrada, se informa antes de seguir (la suite completa no se corre desde el 2026-10-23).
  *Cerrada 2026-11-07.* Ramas `feat/notifications-comunicados` creadas desde `develop` (backend `3ffed99`, que ya incluye el PR \#21 de `loans`; frontend `0a5ff37`). Entorno: Python 3.12.10, PostgreSQL 16 en Docker (puerto 5433), migraciones hasta `0010` (sigue siendo la cabeza). **Backend:** 496 pasan, 1 falla: `tests/users/test_datos_publicos.py::test_datos_publicos_solo_tiene_id_nombre_y_apellido_e_inmutable` (DT-30), que **también falla con 3.12.10** (`TypeError: super(type, obj)…`). No es de este módulo; se informa al Perfil 1. **Frontend:** `typecheck` y `build` en verde; `npm test` 52 tests en verde (8 archivos).
- [x] **T-01 · Conformidades.** Pedir al Perfil 1 conformidad para los cambios de `tests/conftest.py` (`_TABLAS` e import) y de `src/App.tsx` (montar `NewsPage`), con el diff exacto (plan §6, C-N03).
  *Verificación:* respuesta registrada en `MEMORY.md` §5. `conftest.py` bloquea B-A04; `App.tsx` bloquea sólo F-A06.
  *Cerrada 2026-11-07:* el Perfil 1 dio conformidad (la informó el Perfil 5). Cubre también los cambios de una línea en `app/main.py` y `alembic/env.py` (plan §6).

## Fase A — Comunicados y portal (NOV-01, NOV-02)

> **Resumen al 2026-11-07.** Backend completo: 54 tests nuevos de `notifications` (cobertura 100 %); suite completa 550 pasan y 1 falla (DT-30, ajeno). Migración `0013` probada con `upgrade` → `downgrade -1` → `upgrade` y una sola cabeza. Frontend: 17 tests nuevos (69 en total), `typecheck` y `build` en verde. Prueba punta a punta contra la API local (login, alta global, listado, horario de `config`, `422 SEDE_REQUERIDA`). Desvío: las fechas de las respuestas se normalizan a la zona del laboratorio (antes salían en UTC o en `-03:00` según de dónde vinieran). Pendiente: recorrido manual en el navegador de NTF-24 y NTF-25 con estudiante, `ADMIN_LOCAL` y `SUPERADMIN`.

### Backend: contratos, modelos y migración (API-First)

- [x] **B-A01 · Enums y esquemas.** `notifications/enums.py` (los tres enums) y, en `schemas.py`, los esquemas de comunicados: `ComunicadoCreate` (con `model_validator` que rechaza sede y global juntos), `ComunicadoUpdate` (al menos un campo; `vence_en` con `model_fields_set`), `ComunicadoEstadoUpdate`, `ComunicadoResponse` y `ComunicadosPage`. `Field(..., examples=[...])` en todos.
  *Verificación:* `python -c "from app.modules.notifications import schemas"` sin errores. *Cubre:* NTF-03 (validación), NTF-10.
- [x] **B-A02 · Modelos.** `Comunicado` y `Notificacion` en `models.py`, con `CHECK` e índices de spec §7.
  *Verificación:* `python -c "from app.modules.notifications import models"`; la suite existente sigue en verde.
- [x] **B-A03 · Migración `0013_notifications_init`.** Las dos tablas, los dos enums, los `CHECK` con SQL directo y los índices (incluido el parcial). `downgrade` reversible que no toca `sede_enum`. Registrar el modelo en `alembic/env.py`.
  *Verificación:* `alembic upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo; `alembic heads` muestra una sola cabeza. *Cubre:* NTF-23.
- [x] **B-A04 · Fixtures y test de migración.** Sumar `notificaciones, comunicados` a `_TABLAS` e importar el modelo en `tests/conftest.py` (requiere T-01). `tests/notifications/test_migracion_0013.py`: estructura de las tablas, índices y `CHECK`, e inserción directa de un comunicado global con sede, que tiene que fallar.
  *Verificación:* verde. *Cubre:* NTF-04, NTF-23.

### Backend: servicio y router

- [x] **B-A05 · Alta.** `sede_para_comunicado` y `POST /comunicados` (plan §3.3, puntos 2 y 6). Montar el router en `app/main.py`.
  *Verificación:* `tests/notifications/test_comunicados.py` con alta de `ADMIN_LOCAL` (propia, otra sede, global) y de `SUPERADMIN` (sin nada, con las dos cosas, con cada una); `vence_en` pasado. *Cubre:* NTF-02, NTF-03, NTF-11.
- [x] **B-A06 · Lectura.** `GET /comunicados` y `GET /comunicados/{id}` con alcance, vigencia, `incluir_archivados`, paginación y `autor` con `datos_publicos_por_ids` (plan §3.3, puntos 3 a 5).
  *Verificación:* tests con comunicados de Ushuaia, Río Grande y globales, vencidos y archivados, para cada rol. *Cubre:* NTF-05, NTF-06, NTF-07, NTF-12.
- [x] **B-A07 · Edición y estado.** `PATCH /comunicados/{id}` y `PATCH /comunicados/{id}/estado` con `FOR UPDATE`, alcance (`404`), idempotencia y `actualizado_en`.
  *Verificación:* tests de edición por otro admin de la misma sede, de la otra sede y de un global; quitar el vencimiento con `null`; archivar y reactivar dos veces. *Cubre:* NTF-09, NTF-10, NTF-11.
- [x] **B-A08 · Seguridad y sesión.** Tests de roles sin permiso en cada ruta de escritura y `401` sin token en todas las rutas de comunicados.
  *Verificación:* tests. *Cubre:* NTF-01 (comunicados), NTF-08.
- [x] **B-A09 · Cierre del backend A.** `pytest -q` completo; `pytest --cov=app/modules/notifications`; revisar `/docs`; sección de `notifications` en el README del backend.
  *Verificación:* suite en verde; NTF-01…12 y 23 con test anotado.

### Frontend

- [x] **F-A01 · Tipos, API y mappers.** `types/index.ts`, las funciones de comunicados en `notificationsApi.ts` y `toComunicado` en `mappers.ts`.
  *Verificación:* `npm run typecheck`; `mappers.test.ts` (alcance "Global" o sede, autor `null` → "Laboratorio", fechas).
- [x] **F-A02 · Reglas del formulario.** `services/alcance.ts` con `mostrarSelectorAlcance` y `validarComunicado`.
  *Verificación:* `alcance.test.ts` (selector oculto para `ADMIN_LOCAL`, obligatorio para `SUPERADMIN`, título y contenido obligatorios, vencimiento pasado). *Cubre:* NTF-25 (lógica).
- [ ] **F-A03 · Lista de comunicados.** `hooks/useComunicados.ts` y `ComunicadosList` con carga, error, "No hay comunicados" y texto con `pre-line`.
  *Verificación:* `npm run build`; recorrido manual con estudiante. *Cubre:* NTF-24 (comunicados).
  *Estado 2026-11-07:* código listo; `typecheck`, `build` y `npm test` en verde, y la API probada punta a punta. **Falta el recorrido manual en el navegador** (ver resumen de la Fase A).
- [ ] **F-A04 · Formulario y acciones de admin.** `ComunicadoForm` (alta y edición) y botones de archivar y reactivar, con confirmación y errores de `ApiError`.
  *Verificación:* recorrido con `ADMIN_LOCAL` y `SUPERADMIN`. *Cubre:* NTF-25.
  *Estado 2026-11-07:* código listo; `typecheck`, `build` y `npm test` en verde, y la API probada punta a punta. **Falta el recorrido manual en el navegador** (ver resumen de la Fase A).
- [ ] **F-A05 · Portal.** `services/portal.ts` y `PortalInfo`, con el horario leído de `config`.
  *Verificación:* cambiar `horario.apertura` desde la pantalla de parámetros y ver el cambio en el portal. *Cubre:* NTF-24 (portal).
  *Estado 2026-11-07:* código listo; `typecheck`, `build` y `npm test` en verde, y la API probada punta a punta. **Falta el recorrido manual en el navegador** (ver resumen de la Fase A).
- [ ] **F-A06 · `NewsPage` e integración.** Pestañas en `NewsPage` y montaje en `App.tsx` (requiere T-01).
  *Verificación:* el ítem "Novedades" del menú abre la pantalla; el resto de las pantallas no cambia. Sin conformidad, se omite y se registra.
  *Estado 2026-11-07:* código listo; `typecheck`, `build` y `npm test` en verde, y la API probada punta a punta. **Falta el recorrido manual en el navegador** (ver resumen de la Fase A).
- [x] **F-A07 · Cierre del frontend A.** `npm run typecheck`, `npm run build`, `npm test`; README del frontend.
  *Verificación:* los tres comandos en verde.

## Fase B — Centro de notificaciones (NOV-04)

> Rama `feat/notifications-campanita`, desde `develop` con la Fase A mergeada (o desde `feat/notifications-comunicados` si todavía no se mergeó).

### Backend

- [ ] **B-B01 · Plantillas.** `plantillas.py` con los 10 tipos de spec §6.2, su severidad y sus claves, y `renderizar`.
  *Verificación:* `tests/notifications/test_plantillas.py`: todos los tipos tienen plantilla y se arman sin variables sueltas; clave faltante o sobrante → `ValueError`; ninguna clave es `dni`, `email`, `telefono` ni `password`; las tres críticas son `CRITICA`. *Cubre:* NTF-14, NTF-15, NTF-16.
- [ ] **B-B02 · Contrato público.** `crear_notificacion` y `crear_notificaciones` en la sección pública de `service.py`, sin `commit` ni `flush`. Esquema `ReferenciaNotificacion`.
  *Verificación:* `tests/notifications/test_service.py`: con `commit` la fila queda; con `rollback` no; ids repetidos → una por destinatario; lista vacía → `[]`; destinatario `SUSPENDIDO`. *Cubre:* NTF-13, NTF-21, NTF-22.
- [ ] **B-B03 · Lectura.** `GET /notificaciones` (orden de plan §3.3, punto 10; `solo_no_leidas`; paginación) y `GET /notificaciones/resumen`.
  *Verificación:* `tests/notifications/test_notificaciones_api.py`: sólo las propias, críticas no leídas primero, conteos correctos. *Cubre:* NTF-17, NTF-18.
- [ ] **B-B04 · Marcado.** `PATCH /notificaciones/{id}/leida` y `POST /notificaciones/leer-todas` (plan §3.3, puntos 12 y 13).
  *Verificación:* tests: dos marcados conservan el primer `leida_en`; una ajena → `404`; `leer-todas` deja las críticas sin leer y devuelve `marcadas`. *Cubre:* NTF-17, NTF-19, NTF-20.
- [ ] **B-B05 · Sesión.** `401` sin token en todas las rutas de notificaciones; verificar en `/docs` que no exista `POST /notificaciones`.
  *Verificación:* tests. *Cubre:* NTF-01 (notificaciones).
- [ ] **B-B06 · Cierre del backend B.** `pytest -q` completo, cobertura de `notifications` ≥ 90 %, README con el contrato de `crear_notificacion` y un ejemplo de uso (spec §6.3).
  *Verificación:* suite en verde; NTF-13…22 con test anotado.

### Frontend

- [ ] **F-B01 · API y mappers.** Funciones de notificaciones en `notificationsApi.ts` y `toNotificacion`.
  *Verificación:* `npm run typecheck`; casos nuevos en `mappers.test.ts`.
- [ ] **F-B02 · Consulta periódica.** `hooks/useResumenNotificaciones.ts` (60 s, pausa con la pestaña oculta, `refrescar()`).
  *Verificación:* `useResumenNotificaciones.test.ts` con timers falsos: consulta al montar, a los 60 s, no consulta con la pestaña oculta y vuelve a consultar al recuperar el foco.
- [ ] **F-B03 · `NotificationBell`.** Número de no leídas, panel con las últimas 20, críticas arriba y destacadas, marcado de las normales al abrir y de las críticas al hacer clic, "Marcar todas como leídas". Sin enlace desde `referencia` (desvío del plan §4.3).
  *Verificación:* recorrido manual con notificaciones creadas desde un script o fixture (normales y críticas). *Cubre:* NTF-26.
- [ ] **F-B04 · Integración en `Navbar.tsx`.** Reemplazar la maqueta (`NOTIFICATIONS_DATA` y su estado) por `<NotificationBell />` (C-N06).
  *Verificación:* `grep NOTIFICATIONS_DATA` sin resultados; el resto del `Navbar` se ve y funciona igual.
- [ ] **F-B05 · Cierre del frontend B.** `npm run typecheck`, `npm run build`, `npm test`; README.
  *Verificación:* los tres comandos en verde.

## Bloque D — Documentación y registro

- [ ] **D-01 · `MEMORY.md`.** Al cerrar cada fase: snapshot de `notifications` (backend y frontend), conteo de tests, bitácora y, en la Fase B, aviso a los Perfiles 3 y 4 de que el contrato ya está en `develop` (C-N01, C-N02).
  *Verificación:* revisión del Perfil 1.
- [ ] **D-02 · Estado de los documentos.** Pasar el spec a `IMPLEMENTADO` (Fases A y B), registrar en su historial el desvío de la navegación desde `referencia` y pedir al Perfil 1 que actualice la fila del Perfil 5 en `AGENTS.md` §3 y `docs/perfiles.md` §4.
  *Verificación:* PR de documentación o aprobación del Perfil 1.
- [ ] **D-03 · PRs.** Un PR por fase y por repo, con la tabla requisito → endpoint → test, el resultado de las pruebas y de la migración, y los puntos de integración tocados (plan §6). Sin commit, push ni merge salvo pedido explícito.

## Orden y dependencias

```
T-00 ─ T-01 (conformidades; en paralelo)
 └─ B-A01 → B-A02 → B-A03 → B-A04 (requiere T-01) → B-A05 → B-A06 → B-A07 → B-A08 → B-A09
B-A01 (contrato estable) ──► F-A01 → F-A02 → F-A03 → F-A04 → F-A05 → F-A06 (requiere T-01) → F-A07
B-A09 ──► B-B01 → B-B02 → B-B03 → B-B04 → B-B05 → B-B06
B-B03 (contrato estable) ──► F-B01 → F-B02 → F-B03 → F-B04 → F-B05
D-01 al cierre de cada fase; D-02 y D-03 al final
```

El frontend de cada fase puede arrancar contra el OpenAPI en cuanto estén los esquemas (B-A01, B-B03).

## Matriz de cobertura (criterio → tarea)

| Criterio | Tarea | Criterio | Tarea |
| :---- | :---- | :---- | :---- |
| NTF-01 | B-A08, B-B05 | NTF-14…16 | B-B01 |
| NTF-02 | B-A05 | NTF-13, 21, 22 | B-B02 |
| NTF-03 | B-A01, B-A05 | NTF-17 | B-B03, B-B04 |
| NTF-04 | B-A04 | NTF-18 | B-B03 |
| NTF-05…07, 12 | B-A06 | NTF-19, 20 | B-B04 |
| NTF-08 | B-A08 | NTF-23 | B-A03, B-A04 |
| NTF-09 | B-A07 | NTF-24 | F-A03, F-A05 |
| NTF-10 | B-A01, B-A07 | NTF-25 | F-A02, F-A04 |
| NTF-11 | B-A05, B-A07 | NTF-26 | F-B03 |

## Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.0.0 | 2026-11-07 | Aprobado por el Perfil 5 |
| 0.1.0 | 2026-11-07 | Borrador inicial (Perfil 5) |
