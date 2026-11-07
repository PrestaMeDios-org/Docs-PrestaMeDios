# PLAN-06 — Comunicaciones y notificaciones (`notifications`)

> **Spec:** `specs/06-notifications-comunicaciones/spec.md` v1.0.0 (`APROBADO`) · **Estado del plan:** `APROBADO` (2026-11-07) · **Fecha:** 2026-11-07 · **Perfil:** 5
> **Alcance de este plan:** Fases A (comunicados y portal) y B (campanita y `crear_notificacion`). La Fase C (NOV-03 y correo) queda fuera hasta que existan `loans`, `app/core/email.py` y la ejecución periódica (§8).
> Tareas: `specs/06-notifications-comunicaciones/tasks.md`.

---

## 1. Principios de ejecución

- Sólo se tocan archivos de `notifications` (backend y frontend), más los **puntos de integración mínimos** de §6. No se modifican `core`, `users`, `config`, `inventory`, `loans` ni `spaces`.
- Orden API-First: contratos (esquemas) → migración y modelos → servicio → router → tests → frontend.
- Cada tarea termina con tests en verde (`pytest -q` con `TEST_DATABASE_URL`) o con `npm run typecheck && npm run build && npm test`.
- Sin commits, push ni merge sin pedido explícito. Ramas desde `develop` en los dos repos: `feat/notifications-comunicados` (Fase A) y `feat/notifications-campanita` (Fase B, creada desde la de la Fase A o desde `develop` después de mergearla).
- **Python 3.12** para correr la suite (versión validada del proyecto). Un test de `users` (DT-30) falla también con 3.12.10; no es de este módulo y se ignora en las verificaciones de este plan hasta que el Perfil 1 lo corrija.

## 2. Dependencias nuevas

Ninguna, ni en backend ni en frontend (Constitución §3). Las plantillas usan `string.Template` de la biblioteca estándar, como SPEC-03 RN-71. La consulta periódica de la campanita usa `setInterval` y `visibilitychange`, sin librerías de datos.

## 3. Backend (`app/modules/notifications/`)

### 3.1 Archivos a crear

| Archivo | Contenido | Spec |
| :---- | :---- | :---- |
| `__init__.py` | Vacío | — |
| `enums.py` | `EstadoComunicado` (`PUBLICADO`, `ARCHIVADO`), `Severidad` (`NORMAL`, `CRITICA`), `TipoNotificacion` (los 10 tipos de §6.2). `StrEnum`, valores en mayúsculas | §6.2, §7 |
| `models.py` | `Comunicado` y `Notificacion`, con los `CHECK` `alcance_coherente`, `vence_despues_de_publicar` y `referencia_completa`, y los índices de §7. `sede_enum` compartido con `create_type=False`, como en `users/models.py` | §7 |
| `schemas.py` | `ComunicadoCreate`, `ComunicadoUpdate`, `ComunicadoEstadoUpdate`, `ComunicadoResponse`, `ComunicadosPage`, `ReferenciaNotificacion`, `NotificacionResponse`, `NotificacionesPage`, `ResumenNotificaciones`, `LeerTodasResponse`. `_INPUT_CONFIG` en los de entrada; `Field(..., examples=[...])` en todos | §5 |
| `plantillas.py` | Registro `PLANTILLAS: dict[TipoNotificacion, Plantilla]`, con `Plantilla(severidad, claves: frozenset[str], titulo: Template, mensaje: Template)`, y `renderizar(tipo, datos) -> (severidad, titulo, mensaje)`, que lanza `ValueError` si falta o sobra una clave | RN-N7, RN-N8, RN-N9 |
| `service.py` | **Sección pública** (marcada como contrato, igual que `users/service.py`): `crear_notificacion` y `crear_notificaciones`. **Sección interna:** `sede_para_comunicado`, consultas de comunicados por alcance, alta, edición y estado, y lectura, resumen y marcado de notificaciones | §6.1, RN-N1…N14 |
| `router.py` | Un `router` con las rutas `/comunicados…` y `/notificaciones…`. `get_current_user` en todas; `require_roles(ADMIN_LOCAL, SUPERADMIN)` en las de escritura de comunicados; `responses=error_responses(...)` | §5 |
| `alembic/versions/0013_notifications_init.py` | Tablas `comunicados` y `notificaciones`, enums `estado_comunicado_enum` y `severidad_notificacion_enum`, `CHECK` e índices (incluido el parcial). `downgrade` reversible. `down_revision` = la cabeza de `develop` al implementar (ver 3.4) | §7 |
| `tests/notifications/__init__.py` | Vacío | — |
| `tests/notifications/test_comunicados.py` | NTF-01 (rutas de comunicados), NTF-02, 03, 05…12 | Fase A |
| `tests/notifications/test_migracion_0013.py` | NTF-04 (el `CHECK` en la base) y NTF-23 (inspección de tablas, índices y `CHECK`), con el módulo de migración cargado como en `test_spaces_migrations.py` | Fase A |
| `tests/notifications/test_plantillas.py` | NTF-14, NTF-15, NTF-16 (sin base de datos) | Fase B |
| `tests/notifications/test_service.py` | NTF-13, NTF-21, NTF-22 | Fase B |
| `tests/notifications/test_notificaciones_api.py` | NTF-01 (rutas de notificaciones), NTF-17…20 | Fase B |

### 3.2 Archivos a modificar (puntos de integración, §6)

| Archivo | Cambio |
| :---- | :---- |
| `app/main.py` | `app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Comunicaciones y notificaciones"])` |
| `alembic/env.py` | `from app.modules.notifications import models as _notifications_models  # noqa: F401` |
| `tests/conftest.py` | Importar `notifications.models` y sumar `notificaciones, comunicados` al principio de `_TABLAS` |
| `Backend-PrestaMeDios/README.md` | Sección de endpoints de `notifications` y del contrato de `crear_notificacion` (Constitución §6.1) |

### 3.3 Decisiones de diseño

1. **Una sola migración con las dos tablas.** El spec define una migración (`§7`). Se crea en la Fase A con `comunicados` y `notificaciones`. Así la Fase B no necesita otra migración y el contrato de §6 tiene su tabla desde el primer merge. El modelo `Notificacion` entra en la Fase A; su servicio y su router, en la B.
2. **Alcance de un comunicado.** `sede_para_comunicado(usuario, sede, es_global) -> tuple[SedeEnum | None, bool]` es interna del módulo y aplica RN-N2: `ADMIN_LOCAL` → su sede (otra o global → `403 SEDE_FUERA_DE_ALCANCE`); `SUPERADMIN` → exactamente una de las dos (ninguna → `422 SEDE_REQUERIDA`). Que estén las dos se rechaza antes, en un `model_validator` de `ComunicadoCreate` (`422`). No se reutiliza `sede_para_alta` porque no admite "global".
3. **Lectura por alcance (RN-N3).** `sedes = resolver_alcance_sede(usuario, sede)` y `WHERE (sede = ANY(:sedes) OR es_global)`. Para estudiantes y docentes se suma `estado = 'PUBLICADO' AND (vence_en IS NULL OR vence_en > now())`. Los admins ven los archivados sólo con `incluir_archivados=true`, y los vencidos siempre, marcados con `vigente = false`. Orden: `publicado_en DESC, id DESC`. El `total` sale de un `count` con el mismo filtro.
4. **Detalle y edición fuera de alcance → `404`.** `GET`, `PATCH` y `PATCH …/estado` cargan el comunicado con el mismo filtro de alcance. Para editar, además: un `ADMIN_LOCAL` no puede tocar uno global (`404`, RN-N5). La edición usa `SELECT … FOR UPDATE` para que dos ediciones simultáneas no se pisen.
5. **`autor`.** Se resuelve con `users.service.datos_publicos_por_ids` en **una** consulta por página, con los `autor_id` de los ítems. Si el autor no aparece (no debería, porque no hay borrado físico), queda `null`.
6. **`vence_en`.** Un `field_validator` exige zona horaria. Que sea futura se valida en el servicio contra `ahora_lab()` (`core.settings`) y responde `422 VENCIMIENTO_INVALIDO`. En `ComunicadoUpdate` se distingue "no enviado" de "`null`" con `model_fields_set`: enviar `vence_en: null` quita el vencimiento. Un `model_validator` exige al menos un campo.
7. **`actualizado_en`.** Lo actualiza el servicio en cada `PATCH` (`func.now()`), sin trigger.
8. **Plantillas.** `PLANTILLAS` cubre todos los valores de `TipoNotificacion`; un test lo verifica (NTF-15). `renderizar` usa `Template.substitute`, que falla si falta una variable. Antes compara `set(datos)` con `plantilla.claves` en las dos direcciones, para cumplir RN-N7. Otro test recorre las claves de todos los tipos y verifica que ninguna sea `dni`, `email`, `telefono` ni `password` (RN-N8).
9. **`crear_notificacion` sin `commit` ni `flush` (RN-N10).** Llama a `renderizar` y después a `db.add(Notificacion(...))`. `crear_notificaciones` deduplica con `dict.fromkeys(usuario_ids)` (conserva el orden), valida una sola vez y hace `db.add_all`.
10. **Orden de la lista de notificaciones.** `ORDER BY (leida_en IS NULL AND severidad = 'CRITICA') DESC, creada_en DESC, id DESC` (§5.2).
11. **Resumen en una consulta.** `SELECT count(*), count(*) FILTER (WHERE severidad = 'CRITICA') FROM notificaciones WHERE usuario_id = :yo AND leida_en IS NULL`. Usa el índice parcial `ix_notificaciones_no_leidas`.
12. **Marcar como leída sin carreras.** `UPDATE notificaciones SET leida_en = coalesce(leida_en, now()) WHERE id = :id AND usuario_id = :yo RETURNING *`. Si no devuelve filas → `404 NOTIFICACION_NO_ENCONTRADA`. Es idempotente y conserva la primera lectura (RN-N11).
13. **Leer todas.** Un `UPDATE … WHERE usuario_id = :yo AND leida_en IS NULL AND severidad = 'NORMAL'`; `marcadas` es `rowcount` (RN-N14).
14. **Paginación.** `limit: int = Query(20, ge=1, le=100)`, `offset: int = Query(0, ge=0)`, igual en las dos listas.

### 3.4 Migración

- Es la `0013` si las de `loans` (`0011`, `0012`) ya están en `develop` al implementar. Si no, `down_revision` apunta a la cabeza real (hoy `0010_inventory_gestion`) y **antes de mergear** se verifica con `alembic heads` que haya una sola cabeza; si hay dos, se ajusta `down_revision` y, si hace falta, el número. Se avisa al Perfil 1 (C19 de SPEC-05 ya trata la numeración).
- Los `CHECK` se crean con SQL directo y con el nombre final, como en la `0010`, por el prefijo duplicado de `NAMING_CONVENTION` en bases creadas con Alembic (hallazgo de SPEC-04).
- Los enums se crean con `CREATE TYPE` dentro de la migración y se borran en el `downgrade`; `sede_enum` no se toca (es compartido).
- Se valida con `alembic upgrade head` → `downgrade -1` → `upgrade head` en una base de desarrollo. La base de tests se arma con `create_all` (ADR-013), por eso además hay un test que inspecciona la estructura.

### 3.5 Pruebas de la Fase B sin `loans` ni `spaces`

Los tests de la API crean notificaciones llamando a `crear_notificacion` desde el fixture `db` y confirmando la transacción. No hace falta que otro módulo esté conectado. NTF-13 prueba los dos caminos (`commit` y `rollback`) con una sesión propia.

## 4. Frontend (`src/features/notifications/`)

### 4.1 Archivos a crear

| Archivo | Contenido | Fase |
| :---- | :---- | :---- |
| `types/index.ts` | DTOs `snake_case` (`ComunicadoDTO`, `ComunicadoCreateDTO`, `ComunicadoUpdateDTO`, `NotificacionDTO`, `ResumenDTO`, páginas) y view models (`Comunicado`, `Notificacion`) | A, B |
| `services/notificationsApi.ts` | Sobre `apiRequest` de `src/lib/api.ts`, ruta `/api/v1/notifications`: `listarComunicados`, `obtenerComunicado`, `crearComunicado`, `editarComunicado`, `cambiarEstadoComunicado`, `listarNotificaciones`, `obtenerResumen`, `marcarLeida`, `leerTodas` | A, B |
| `services/mappers.ts` | `toComunicado` (alcance "Global" o la sede, fechas legibles, autor o "Laboratorio") y `toNotificacion` | A, B |
| `services/alcance.ts` | Funciones puras: `mostrarSelectorAlcance(rol)` y `validarComunicado(form, rol)`, que devuelve los errores de campo (PRE-04) | A |
| `services/portal.ts` | Contenido fijo del portal: normativa (Res. CICSE N° 056/2023), direcciones de las sedes (Yrigoyen 879 y Thorne 302) y contacto (D-N02) | A |
| `hooks/useComunicados.ts` | Carga con `AbortSignal`, estados `cargando`, `error` y `datos`, paginación | A |
| `hooks/useResumenNotificaciones.ts` | Pide `/resumen` al montar y cada 60 s; se pausa con `document.visibilityState === "hidden"` y vuelve a pedir al recuperar el foco (D-N04). Expone `refrescar()` | B |
| `pages/NewsPage.tsx` | Pestañas "Comunicados" e "Información del laboratorio" | A |
| `components/ComunicadosList.tsx` | Lista con alcance, fecha y vencimiento; "No hay comunicados"; errores con `mensajeDeError`; acciones de admin (editar, archivar o reactivar) | A |
| `components/ComunicadoForm.tsx` | Alta y edición; selector de alcance sólo para `SUPERADMIN` y obligatorio; campos obligatorios en rojo | A |
| `components/PortalInfo.tsx` | Muestra `portal.ts` y el horario leído de `GET /api/v1/config/horario.apertura` y `horario.cierre` | A |
| `components/NotificationBell.tsx` | Botón con el número de no leídas, panel con las últimas 20, críticas arriba y destacadas, "Marcar todas como leídas" | B |
| `services/mappers.test.ts`, `services/alcance.test.ts`, `hooks/useResumenNotificaciones.test.ts` | Vitest: mapeos, reglas del formulario y la pausa de la consulta periódica (con timers falsos) | A, B |

Los comunicados se muestran como texto con `white-space: pre-line`, nunca con `dangerouslySetInnerHTML` (D-N07).

### 4.2 Archivos a modificar (puntos de integración, §6)

| Archivo | Cambio | Fase |
| :---- | :---- | :---- |
| `src/App.tsx` | Montar `{visible === "news" && <NewsPage />}` y agregar `"news"` a la lista de pantallas implementadas (línea 145). Nada más | A |
| `src/components/layout/Navbar.tsx` | Borrar `NOTIFICATIONS_DATA`, los estados `notifOpen`/`notifs` y el bloque de la campanita, y poner `<NotificationBell />` en su lugar. El resto del `Navbar` no cambia | B |
| `Frontend-PrestaMeDios/README.md` | Estructura de `notifications` | A, B |

### 4.3 Decisiones de diseño

- **Rol y sede** salen de `useAuth()` y `useSede()`. Para `SUPERADMIN`, la lista de comunicados usa la sede vista del selector global (`sedeVista`); con "Ambas" no se manda `sede`.
- **Marcar al abrir.** Al abrir la campanita se marcan como leídas, una por una, sólo las `NORMAL` visibles; las críticas se marcan al hacer clic (RN-N9). Después se llama a `refrescar()`.
- **Navegación desde `referencia` (desvío del spec §8).** Hoy no existen las pantallas de destino (solicitudes de `loans`; "Mis Solicitudes" es un marcador) y `Navbar` no recibe una función de navegación genérica. Por eso en esta versión la notificación muestra su texto **sin enlace**, y `referencia` queda disponible en el view model. El enlace se agrega cuando existan las pantallas, con una prop `onAbrirReferencia` que pase por `MainLayout`; se coordina en ese momento. Se registra en el historial del spec al cerrar la Fase B.
- **Errores de la campanita.** Si `/resumen` falla, el número no se muestra y se reintenta en la siguiente vuelta, sin carteles que tapen la pantalla. Un `401` lo maneja `lib/api.ts`, que cierra la sesión.

## 5. Verificación

| Qué | Cómo |
| :---- | :---- |
| Backend | `pytest -q` completo y `pytest --cov=app/modules/notifications` (meta: ≥ 90 %). Cada NTF-01…NTF-23 con un test anotado `# NTF-NN` |
| Migración | `alembic upgrade head` / `downgrade -1` / `upgrade head` en base de desarrollo; `alembic heads` con una sola cabeza; `test_migracion_0013.py` |
| OpenAPI | Revisar `/docs`: ejemplos, códigos `401/403/404/422` y que no exista `POST /notificaciones` |
| Frontend | `npm run typecheck`, `npm run build`, `npm test`; recorrido manual de NTF-24…NTF-26 contra el backend local con estudiante, `ADMIN_LOCAL` y `SUPERADMIN` de las dos sedes |
| Trazabilidad | Tabla requisito → endpoint → test en la descripción de cada PR |

## 6. Puntos de contacto con otros perfiles (sin modificarlos)

| Elemento | Dueño | Tratamiento |
| :---- | :---- | :---- |
| `app/main.py`, `alembic/env.py` | Perfil 1 (kernel) | Una línea cada uno, igual que los demás módulos. Se informa en el PR |
| `tests/conftest.py` (`_TABLAS` e import del modelo) | Perfil 1 | Cambio de dos líneas. **Se pide conformidad** (C-N03); sin ella, los tests de `notifications` no pueden limpiar sus tablas |
| `src/App.tsx` (montar `NewsPage`) | Perfil 1 (layout) | Dos líneas, como SPEC-04 F-06. **Se pide conformidad** antes de integrar; si no la hay, se entrega `NewsPage` sin montar y se registra |
| `src/components/layout/Navbar.tsx` | Compartido | Sólo se reemplaza la campanita (C-N06). Se avisa al equipo en el PR |
| `users.service.datos_publicos_por_ids` | Perfil 1 | Se usa tal cual (contrato público de SPEC-03) |
| `GET /api/v1/config/{clave}` | Perfil 1 | Se usa tal cual; cuando cambien las claves de horario por sede (C-N05), se ajusta `PortalInfo` |
| Llamadas a `crear_notificacion` | Perfiles 3 y 4 | Las hacen ellos (C-N01, C-N02); este plan no toca sus módulos |

## 7. Riesgos

| Riesgo | Mitigación |
| :---- | :---- |
| Dos cabezas de Alembic si `loans` mergea `0011`/`0012` en paralelo | `alembic heads` antes de mergear; ajustar `down_revision` (3.4) |
| `Navbar.tsx` cambia en otra rama al mismo tiempo | El cambio se limita al bloque de la campanita; rebase sobre `develop` antes del PR |
| Muchas pestañas abiertas multiplican las consultas a `/resumen` | Pausa con la pestaña oculta; la consulta usa un índice parcial y devuelve dos números |
| Los otros perfiles arman `datos` con claves distintas a las de §6.2 | `renderizar` falla en el momento con un mensaje que lista las claves esperadas; los tests de ellos lo detectan |
| Suite con Python 3.13 o superior | Usar 3.12 (DT-30); el fallo de `users` no es de este módulo |
| El Perfil 1 no da conformidad a tiempo para `conftest.py` o `App.tsx` | Se avisa al pedirla con el diff exacto; `App.tsx` puede esperar, `conftest.py` no (sin él no hay tests) |

## 8. Fase C (fuera de este plan)

Se planifica en una revisión de este documento cuando estén: `loans` implementado (SPEC-05), `app/core/email.py` (SPEC-03 B1) y la ejecución periódica (C5). Trabajo previsto: tipos `PRESTAMO_POR_VENCER`, `LLAMADO_ATENCION` y `SANCION`; parámetro `por_correo` en `crear_notificacion`; columnas `correo_pendiente`, `correo_enviado_en` y `correo_error` (migración nueva); comando `python -m app.modules.notifications.cli enviar-correos`, idempotente; y la versión 0.2.0 del spec con sus criterios.

## 9. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.0.0 | 2026-11-07 | Aprobado por el Perfil 5 |
| 0.1.0 | 2026-11-07 | Borrador inicial (Perfil 5) |
