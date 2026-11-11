# SPEC-08 — Espacios y reservas (`spaces`)

> **Estado:** Línea base IMPLEMENTADO (retroactivo, aprobado por el Perfil 1 el 2026-11-11) · Fases 1–5 BORRADOR · **Versión:** 1.0.0 · **Fecha:** 2026-11-11 · **Perfil:** 4 (Espacios)
> **Tipo:** documentación retrospectiva del módulo existente y especificación de las brechas pendientes.
> **Requisitos:** RES-01…RES-05, GLO-02 y GLO-04.
> **Dependencias:** SPEC-01, SPEC-02, `config`, `users` (SPEC-03: `datos_publicos_por_ids`), y SPEC-06 (interfaz para eventos S7).
> **Fuentes funcionales:** `docs/ERS.md`; las referencias a rutas y líneas de código describen `origin/develop`, no autorizan cambios de aplicación.

## 0. Estado y precedencia

Este spec registra retrospectivamente la funcionalidad ya implementada en `spaces` y explicita las brechas que aún requieren trabajo. La línea base está aprobada; las Fases 1–5 siguen en `BORRADOR` y requieren aprobación antes de implementar los cambios pendientes. No reemplaza ni modifica el ERS. Las reglas funcionales siguen la precedencia de `docs/constitution.md` §6 y `AGENTS.md` §4.

La asignación del Perfil 4 comprende espacios físicos, calendario, reservas y bloqueos, no infraestructura de despliegue (docs/perfiles.md §4, Perfil 4). La matriz clasifica como implementados modelos, contratos, restricciones de solapamiento, validaciones, transiciones y pantallas; registra como pendientes DT-09, la reversión de bloqueos GLO-04 y la Isla de Digitalización (docs/perfiles.md §4, Perfil 4).

## 1. Alcance

### 1.1 Incluye

1. **Vigente:** calendario y disponibilidad del Aula-Estudio y la Isla de Edición por sede (RES-01). Evidencia: `SpacesPage.tsx:69-112`, `availability.py:16-69`; `tests/spaces/test_espacios_reservas.py::test_aislamiento_de_espacios`, `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance`.
2. **Vigente:** solicitudes de turnos en estado `Pendiente`, permitiendo solicitudes concurrentes de distintos usuarios para la misma franja (RES-02). Evidencia: `service.py:183-246`; `tests/spaces/test_espacios_reservas.py::test_reserva_pertenece_al_usuario_del_token`, `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia`.
3. **Vigente:** cancelación por el solicitante antes del inicio, tanto de solicitudes pendientes como aprobadas (RES-03). Evidencia: `service.py:307-327`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_cancela`, `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_cancela_pasada`.
4. **Vigente:** creación de bloqueos administrativos por día completo o intervalo, con motivo, aplicados al calendario (RES-04, GLO-02). Evidencia: `service.py:375-405`, `SpacesPage.tsx:608-681`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_alcance_y_roles`, `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_no_pisa_reservas_activas`. **Pendiente (Fase 3):** reversión GLO-04.
5. **Vigente:** aprobación y rechazo manual por un administrador con jurisdicción; la aprobación adjudica una reserva y rechaza solicitudes pendientes que se superponen (RES-05). Evidencia: `service.py:329-367`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_descarta_pendientes_y_ciclo_de_uso`.
6. **Vigente parcialmente:** anticipación mínima configurable y horario global obtenido de `config`. Evidencia: `service.py:99-104,183-213`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_fuera_de_horario_y_horario_configurable`, `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_minima`. **Pendiente (Fase 2/K10):** consumir horario por sede y mostrar el correo de contacto usando `config.service.datos_de_sede(db, espacio.sede)` (SPEC-09 §4.4) o `GET /api/v1/config/sedes` (§4.5), conforme al pedido H1.
7. **Vigente:** privacidad de reservas propias y de disponibilidad, sin exponer identidad a otros solicitantes. Evidencia: `service.py:253-280,433-517`; `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`, `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance`. **Pendiente (Fase 1/K1):** nombre del solicitante en vistas administrativas (P6).
8. **Pendiente (Fase 4/C-N02):** eventos de notificación de aprobación, rechazo y cancelación administrativa mediante la interfaz pública de SPEC-06.

### 1.2 Fuera de alcance

- Implementar o modificar `core`, `users`, `config` o `notifications`, que pertenecen a otros perfiles. Las dependencias se coordinan con sus responsables.
- Inventario y préstamos de equipamiento, comunicados y asistente de IA.
- La futura Isla de Digitalización de Archivos Físicos, todavía no incluida en el catálogo actual (ERS, requisito futuro de espacios).
- Cambios de código en esta tarea documental.

### 1.3 Línea base verificada

La auditoría de Backend corresponde a `origin/develop` (`3e85feb`). En ese ref existen los modelos, schemas, router, servicio, cálculo de disponibilidad y tests de `spaces` (`Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`; `Backend-PrestaMeDios/app/modules/spaces/schemas.py:36-189`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:99-121,183-246,253-280,307-405,433-517`; `Backend-PrestaMeDios/app/modules/spaces/availability.py:16-69`; `Backend-PrestaMeDios/tests/spaces/test_contratos.py:35-120`; `Backend-PrestaMeDios/tests/spaces/test_espacios_reservas.py:50-417`).

La API actual ofrece `GET/POST /espacios`, `POST/GET /reservas`, `PATCH /reservas/{id_reserva}/estado`, `POST/GET /bloqueos` y `GET /disponibilidad` bajo `/api/v1/spaces`; no existe operación para revertir un bloqueo (`Backend-PrestaMeDios/README.md:41`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`). `ReservaEspacioResponse` no incluye `solicitante`; `BloqueoEspacio` no tiene estado de reversión; el servicio usa `horario.apertura`/`horario.cierre` globales, no claves por sede; y el servicio no invoca `notifications` (`Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99,121-156`; `Backend-PrestaMeDios/app/modules/spaces/models.py:96-112`; `Backend-PrestaMeDios/app/modules/spaces/service.py:99-104,183-213,307-405`).

El frontend auditado está en `origin/develop` (`03ce339`). Tiene calendario, selector de sede/espacio, solicitud y cancelación del usuario, bandeja administrativa y creación de bloqueos; no ofrece control para revertirlos (`Frontend-PrestaMeDios/src/App.tsx:22-25,95-111,133-135`; `Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,212-238,240-281,287-327,437-477,482-606,608-681`). La grilla presenta turnos de una hora y permite navegar por mes hasta el mes actual más cuatro; el backend sólo exige que la hora final sea posterior a la inicial, valida contra horario y aplica una ventana configurable que el ERS fija en 120 días (`Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:21-33,437-477`; `Frontend-PrestaMeDios/src/features/spaces/components/CalendarGrid.tsx:14-58,131-165`; `Backend-PrestaMeDios/app/modules/spaces/schemas.py:77-83`; `Backend-PrestaMeDios/app/modules/spaces/service.py:183-213`; ERS GLO-03).

**Validación de pruebas:** en Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, `pytest -q tests/spaces tests/test_spaces_migrations.py` dio **58 passed** en 22.39 s. Una primera corrida falló porque el rol local de PostgreSQL no tenía permisos para crear la base de tests y la extensión `btree_gist`; se corrigió el entorno local, sin cambios de código.

En Frontend `develop`, commit `8cbc76a5ccee77211abb1ca9dacfd1d5e551beb6`, `npm run build` terminó correctamente y `npm test` reportó **16 archivos, 126 passed, 0 failed, 0 skipped**. Estos resultados de build/tests son independientes del `npm audit`; no se ejecutaron arreglos de dependencias.

## 2. Actores y permisos

| Acción | ESTUDIANTE | DOCENTE | ADMIN_LOCAL | SUPERADMIN | Evidencia |
| --- | --- | --- | --- | --- | --- |
| Consultar calendario/disponibilidad (**vigente**) | Sí, sede propia | Sí, sede propia | Sí, sede propia | Ambas sedes | `availability.py:16-69`; `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance`, `tests/spaces/test_espacios_reservas.py::test_aislamiento_de_espacios`. |
| Crear una solicitud (**vigente**) | Sí | Sí | No | No | `service.py:183-246`; `tests/spaces/test_espacios_reservas.py::test_reserva_pertenece_al_usuario_del_token`. |
| Consultar/cancelar reservas propias antes del inicio (**vigente**) | Sí | Sí | No aplica | No aplica | `service.py:253-327`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_cancela`. |
| Ver bandeja y resolver solicitudes (**vigente**) | No | No | Sí, su sede | Sí | `service.py:253-280`, `SpacesPage.tsx:482-606`; `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`, `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_descarta_pendientes_y_ciclo_de_uso`. |
| Crear bloqueos (**vigente**) | No | No | Sí, su sede | Sí | `service.py:375-405`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_alcance_y_roles`. |
| Revertir bloqueos (**pendiente, Fase 3**) | No | No | Por definir | Por definir | No hay contrato de reversión ni test. |
| Crear espacios (**vigente**) | No | No | Sí, su sede | Sí, eligiendo sede | `router.py:53-66`; SPEC-02 AC-33; `tests/spaces/test_espacios_reservas.py::test_alta_de_espacio_pre19`. |
| Ver identidad propia (**vigente**) / identidad de solicitantes en bandeja (**pendiente, Fase 1/K1**) | Propia | Propia | Pendiente | Pendiente | Dueño: `service.py:253-280`; `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`. Nombre administrativo: sin campo ni test. |

El filtrado por sede debe aplicarse en las consultas de datos, no sólo en la interfaz (Constitución P5.2-P5.4). Toda ruta requiere autenticación y autorización del lado del servidor salvo excepción explícita en el spec (P4.1-P4.5). Los recursos ajenos o fuera de jurisdicción no deben revelar su existencia (Constitución §4.2, P4.5).

Evidencia de operaciones vigentes: calendario/consulta `SpacesPage.tsx:69-122`, `availability.py:16-69`; `tests/spaces/test_espacios_reservas.py::test_aislamiento_de_espacios`, `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance`; reserva/cancelación `service.py:183-246,307-327`; `tests/spaces/test_espacios_reservas.py::test_reserva_pertenece_al_usuario_del_token`, `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_cancela`; bandeja `SpacesPage.tsx:482-606`; bloqueos/alta `service.py:375-405`, `router.py:53-66,129-156`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_alcance_y_roles`. Las referencias corresponden al código auditado en `origin/develop` (`3e85feb` Backend; `03ce339` Frontend); no hay test automatizado de la UI de espacios en la evidencia revisada.

## 3. Reglas de negocio

- **RN-S01 — Disponibilidad (vigente):** el calendario presenta espacios, franjas operativas, ocupaciones adjudicadas y bloqueos, sin identificar a otros solicitantes (RES-01; SPEC-02 AC-36). Evidencia: `availability.py:16-69`; `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance`, `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`.
- **RN-S02 — Solicitud pendiente y concurrencia (vigente):** una solicitud nueva se guarda como `Pendiente`; solicitudes pendientes de otras personas pueden coexistir y no bloquean por sí solas (RES-02). Evidencia: `service.py:183-246`; `tests/spaces/test_espacios_reservas.py::test_reserva_pertenece_al_usuario_del_token`, `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia`.
- **RN-S03 — Adjudicación única (vigente):** sólo un administrador con alcance puede aprobar; la aprobación adjudica y rechaza solicitudes pendientes solapadas (RES-05). Evidencia: `service.py:329-367`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_descarta_pendientes_y_ciclo_de_uso`.
- **RN-S04 — Integridad temporal (vigente):** reservas aprobadas/en uso no se superponen para el mismo espacio; pendientes no participan de la exclusión (Constitución P7.1-P7.2; ADR-004). Evidencia: `models.py:42-75`; `tests/test_spaces_migrations.py::test_modelo_excluye_solapamientos_en_reservas_aprobadas_y_en_uso`, `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobaciones_concurrentes_solapadas`.
- **RN-S05 — Cancelación del solicitante (vigente):** el dueño puede cancelar su reserva pendiente o aprobada sólo antes del inicio (RES-03). Evidencia: `service.py:307-327`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_cancela`, `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_cancela_pasada`.
- **RN-S06 — Horario por sede (vigente parcial; K10/Fase 2 pendiente):** hoy se valida contra parámetros globales de `config`; el cambio a `config.service.datos_de_sede(db, espacio.sede)` está pendiente (SPEC-09 §4.4, H1; GLO-02/GLO-03; P8). Evidencia vigente: `service.py:99-104,183-213`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_fuera_de_horario_y_horario_configurable`.
- **RN-S07 — Anticipación (vigente parcial; aviso de correo pendiente, Fase 2):** se aplica el mínimo configurable y se rechazan solicitudes anticipadas insuficientemente; falta mostrar el correo por sede (ADR-011; SPEC-09 §4.4-§4.5, H1). Evidencia vigente: `service.py:190-213`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_minima`, `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_en_hora_local_del_laboratorio`.
- **RN-S08 — Ventana máxima (vigente):** se rechaza una reserva fuera de la ventana configurada (120 días según el ERS; SPEC-02 V5). Evidencia: `service.py:190-213`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_ventana_maxima`.
- **RN-S09 — Bloqueo (creación vigente; motivo/reversión pendientes, Fase 3):** un bloqueo puede abarcar días completos o intervalos, exige motivo y afecta nuevas solicitudes; la UI no muestra el motivo ni permite revertirlo. Evidencia de creación: `service.py:375-405`, `SpacesPage.tsx:608-681`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_alcance_y_roles`, `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_franja_fuera_de_horario`, `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_no_pisa_reservas_activas`. Motivo en calendario y reversión: sin test; no hay operación de reversión.
- **RN-S10 — Privacidad del solicitante (vigente parcial; K1/Fase 1 pendiente):** listado propio/jurisdiccional y disponibilidad anónima vigentes; nombre/apellido para administradores todavía no se retorna (Constitución P6; SPEC-02 AC-36). Evidencia: `service.py:253-280,433-517`; `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`, `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance`. Nombre administrativo: sin test/campo ausente.
- **RN-S11 — Rechazo (vigente parcial):** el administrador debe ingresar un motivo al rechazar; consulta del motivo por el solicitante está en el contrato de reserva, pero no se identificó un test específico de su visualización (RES-05; SPEC-02 AC-37; Iteración 5). Evidencia: `schemas.py:101-115`; `tests/spaces/test_contratos.py::TestReservaEspacioUpdateStatus::test_rechazada_requiere_motivo`; lectura visual: sin test identificado.
- **RN-S12 — Notificaciones (pendiente, Fase 4/C-N02):** se integrarán en la transacción según SPEC-06 §6.1-§6.2 y C-N02; actualmente `spaces` no las emite. Evidencia de ausencia: `service.py:307-405`; tests de integración: **SIN TEST**.
- **RN-S13 — Bloqueo y reservas ya aprobadas (vigente):** crear un bloqueo no cancela reservas adjudicadas implícitamente; resolución/cancelación de una reserva existente es explícita (RES-03/RES-05, GLO-04). Evidencia: `service.py:375-405`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_no_pisa_reservas_activas`.
- **RN-S14 — Reversión de bloqueos (pendiente de decisión, SPEC-08 v1.1.0):** no se fija si será baja lógica o DELETE físico, ni la política para bloqueos generales; resolver junto con Backend #32 y Frontend #20, contrastando P7.3 antes de aprobar el diseño. Evidencia de brecha: `router.py:129-156`, `models.py:96-112`; sin test porque no está implementado.

## 4. Casos de uso

| ID | Caso | Actor | Requisitos | Resultado |
| --- | --- | --- | --- | --- |
| CU-S01 | Consultar disponibilidad | Cualquier usuario autenticado | RES-01, GLO-02 | Ve calendario de espacios de su sede; SUPERADMIN puede elegir sede. |
| CU-S02 | Solicitar turno | ESTUDIANTE, DOCENTE | RES-02, GLO-02 | Se registra la solicitud pendiente si horario, anticipación, ventana y bloqueos lo permiten. |
| CU-S03 | Cancelar solicitud propia | ESTUDIANTE, DOCENTE | RES-03 | Se cancela sólo antes del inicio y se libera la franja. |
| CU-S04 | Resolver solicitudes | ADMIN_LOCAL, SUPERADMIN | RES-05 | Aprueba o rechaza manualmente; rechazo requiere motivo; aprobación rechaza las solicitudes pendientes superpuestas. |
| CU-S05 | Bloquear calendario | ADMIN_LOCAL, SUPERADMIN | RES-04, GLO-02, GLO-04 | Registra bloqueo con motivo para un día o intervalo y evita nuevas solicitudes en ese rango. |
| CU-S06 | Revertir bloqueo | ADMIN_LOCAL, SUPERADMIN | GLO-04 | Libera el rango conforme a la política de reversión que se decidirá en SPEC-08 v1.1.0; esta versión no determina si se conserva o elimina el registro. |
| CU-S07 | Consultar bandeja administrativa | ADMIN_LOCAL, SUPERADMIN | RES-05 | Ve sólo las reservas de su jurisdicción e identidad pública mínima del solicitante. |

## 5. Contratos actuales

La base de rutas existente es `/api/v1/spaces`; SPEC-02 §3.2 describe `GET /espacios`, `POST /espacios`, `GET /disponibilidad`, `POST /reservas`, `GET /reservas`, `PATCH /reservas/{id}/estado` y `POST/GET /bloqueos`.

Los siguientes contratos son el estado verificado en Backend `origin/develop` (`3e85feb`), no el diseño futuro. Todas las rutas cuelgan de `/api/v1/spaces` (`Backend-PrestaMeDios/README.md:41`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`). `AppError.code` se devuelve con `detail`; los errores Pydantic `422` no tienen `AppError.code` (`Backend-PrestaMeDios/app/core/errors.py:1-6,36-40`). En §5-7, las referencias abreviadas a `router.py`, `service.py`, `schemas.py`, `models.py`, `deps.py` y `alembic/versions/` corresponden a `Backend-PrestaMeDios`.

| Método y ruta | Roles y alcance | Query / path | Body | Respuesta | HTTP y `AppError.code` |
| --- | --- | --- | --- | --- | --- |
| `GET /espacios` | Cualquier usuario autenticado; cada rol queda limitado a su sede; SUPERADMIN puede filtrar sede. | `sede?` | — | `list[EspacioResponse]` | `200`, `401`, `403`; `SEDE_FUERA_DE_ALCANCE` (`router.py:38-50`; `service.py:163-168`; `deps.py:99-114`). |
| `POST /espacios` | ADMIN_LOCAL, SUPERADMIN. ADMIN_LOCAL se asigna a su sede; SUPERADMIN debe indicar sede. | — | `EspacioCreate`: `nombre`, `tipo?`, `sede?`. | `EspacioResponse` (`201`) | `201`, `401`, `403`, `422`; `PERMISO_INSUFICIENTE`, `SEDE_FUERA_DE_ALCANCE`, `SEDE_REQUERIDA` (`router.py:53-66`; `schemas.py:44-60`; `deps.py:83-96,117-132`). |
| `POST /reservas` | ESTUDIANTE, DOCENTE; espacio dentro del alcance del actor; dueño se infiere del token. | — | `ReservaEspacioCreate`: `id_espacio`, `fecha_reserva`, `hora_inicio`, `hora_fin`, `motivo?`; no admite `id_usuario`, `estado` ni `sede`. | `ReservaEspacioResponse` (`201`) | `201`, `401`, `403`, `404`, `409`, `422`; `PERMISO_INSUFICIENTE`, `ESPACIO_NO_ENCONTRADO`, `FUERA_DE_HORARIO`, `ANTICIPACION_INSUFICIENTE`, `FUERA_DE_VENTANA`, `ESPACIO_BLOQUEADO`, `FRANJA_OCUPADA`, `RESERVA_DUPLICADA` (`router.py:72-85`; `schemas.py:66-99`; `service.py:71-80,183-246`). |
| `GET /reservas` | Cualquier usuario autenticado; ESTUDIANTE/DOCENTE ven las propias; admins sólo su jurisdicción; SUPERADMIN puede filtrar sede. | `id_espacio?`, `fecha?`, `estado?`, `id_usuario?` (sólo admin), `sede?` (sólo admin). | — | `list[ReservaEspacioResponse]` | `200`, `401`, `403`; `SEDE_FUERA_DE_ALCANCE` (`router.py:88-107`; `service.py:253-280`; `deps.py:99-114`). |
| `PATCH /reservas/{id_reserva}/estado` | Dueño ESTUDIANTE/DOCENTE sólo cancela; ADMIN_LOCAL/SUPERADMIN resuelven según jurisdicción. | `id_reserva` en path. | `ReservaEspacioUpdateStatus`: `nuevo_estado`, `motivo_rechazo?`; requerido para rechazar por esquema y para cancelar administrativamente por servicio. | `ReservaEspacioResponse` (`200`) | `200`, `401`, `403`, `404`, `409`, `422`; `PERMISO_INSUFICIENTE`, `RESERVA_NO_ENCONTRADA`, `TRANSICION_INVALIDA`, `FRANJA_OCUPADA`, `ESPACIO_BLOQUEADO`, `MOTIVO_REQUERIDO` (`router.py:110-123`; `schemas.py:101-115`; `service.py:283-369`). |
| `POST /bloqueos` | ADMIN_LOCAL/SUPERADMIN, con alcance de sede. | — | `BloqueoEspacioCreate`: `id_espacio`, `fecha_inicio`, `fecha_fin`, `hora_inicio?`, `hora_fin?`, `motivo`; las dos horas se omiten juntas para un bloqueo de día completo. | `BloqueoEspacioResponse` (`201`) | `201`, `401`, `403`, `404`, `409`, `422`; `PERMISO_INSUFICIENTE`, `ESPACIO_NO_ENCONTRADO`, `FUERA_DE_HORARIO`, `BLOQUEO_CON_RESERVAS` (`router.py:129-141`; `schemas.py:121-156`; `service.py:375-405`). |
| `GET /bloqueos` | Cualquier usuario autenticado; lista sólo bloqueos de su alcance (SUPERADMIN puede ver ambas sedes). | `id_espacio?`, `fecha?` | — | `list[BloqueoEspacioResponse]` | `200`, `401`; el router no declara otros errores y el servicio sólo resuelve alcance implícito (`router.py:144-156`; `service.py:415-427`). |
| `GET /disponibilidad` | Cualquier usuario autenticado; aplica alcance por rol y sede. | `fecha` requerida, `sede?`, `id_espacio?` | — | `DisponibilidadResponse`: fecha, sede/espacio, horario, franjas ocupadas anonimizadas, bloqueos e intervalos libres. | `200`, `401`, `403`; `SEDE_FUERA_DE_ALCANCE` (`router.py:162-176`; `schemas.py:162-189`; `service.py:433-448`; `deps.py:99-114`). |

### 5.1 Brechas futuras, no contratos existentes

| Brecha | Diferencia verificada | Propuesta a aprobar; no implementada |
| --- | --- | --- |
| GLO-04, reversión de bloqueos | Sólo existen `POST/GET /bloqueos`; el modelo no tiene estado de reversión ni ruta `DELETE/PATCH` (`router.py:129-156`; `models.py:96-112`). | En SPEC-08 v1.1.0, decidir baja lógica vs. DELETE físico y política de bloqueos generales, coordinando Backend #32/Frontend #20; no fijar aquí la conservación del historial. |
| K1, identidad pública | `ReservaEspacioResponse` expone `id_usuario`, pero no `solicitante`; no se usa `users.datos_publicos_por_ids` desde `spaces` (`schemas.py:85-99`; `service.py:253-280`). | Extender sólo las respuestas administrativas con `id/nombre/apellido`, respetando P6 y jurisdicción. |
| K10, configuración por sede | `horario()` consulta las claves globales `horario.apertura` y `horario.cierre` (`service.py:99-104`). | Cuando la Fase A de SPEC-09 esté en Backend `develop`, consumir `config.service.datos_de_sede(db, espacio.sede)` en validación/disponibilidad y `GET /api/v1/config/sedes` para el aviso de contacto, conforme a SPEC-09 §4.4-§4.5 y H1. |
| C-N02/S7, notificaciones | La aprobación y el rechazo automático por solapamiento no invocan la interfaz de `notifications` (`service.py:329-367`). | Integrar eventos en la transacción según SPEC-06 cuando la función esté disponible. |
| DT-09, estado persistido | El API usa `EstadoReserva`, pero la columna de base es `String(20)` (`schemas.py:22-33`; `models.py:87-90`). | Resolver la decisión de migración antes de adoptar un `ENUM` PostgreSQL. |

## 6. Datos, estados y migraciones

### 6.1 Columnas y restricciones vigentes

Modelo y migraciones se contrastaron columna por columna en `origin/develop` (`3e85feb`). Los campos de respuesta no agregan columnas persistidas.

| Tabla / columna | Tipo, nulabilidad y default vigentes | Restricción o índice | Origen de migración / modelo |
| --- | --- | --- | --- |
| `espacios.id_espacio` | `INTEGER NOT NULL`, autoincremental | PK | `0002_espacios.py:20-27`; `models.py:26-31`. |
| `espacios.nombre` | `VARCHAR(100) NOT NULL` | Sin unicidad declarada | `0002_espacios.py:20-27`; `models.py:32`. |
| `espacios.sede` | `sede_enum NOT NULL` (`Ushuaia`, `Río Grande`) | Índice `ix_espacios_sede`; reemplaza `id_sede INTEGER NOT NULL`, índice `ix_espacios_id_sede` y FK `sedes.id_sede ON DELETE CASCADE` | `0002_espacios.py:20-45`; conversión y renombre en `0007_spaces_sede_y_usuario.py:27-54`; `models.py:33`. |
| `espacios.tipo` | `VARCHAR(100) NULL` | — | `0002_espacios.py:20-27`; `models.py:34`. |
| `reservas_espacios.id_reserva` | `INTEGER NOT NULL`, autoincremental | PK | `0001_spaces_init.py:36-48`; `models.py:77`. |
| `reservas_espacios.id_usuario` | `INTEGER NOT NULL` | Índice; FK `usuarios.id ON DELETE RESTRICT`, agregada en `0007` | Índice `0001_spaces_init.py:36-50`; FK `0007_spaces_sede_y_usuario.py:71-78`; `models.py:78-80`. |
| `reservas_espacios.id_espacio` | `INTEGER NOT NULL` | Índice; FK `espacios.id_espacio ON DELETE CASCADE`, agregada en `0002` | `0001_spaces_init.py:36-50`; `0002_espacios.py:30-45`; `models.py:81-83`. |
| `reservas_espacios.fecha_reserva` | `DATE NOT NULL` | — | `0001_spaces_init.py:36-48`; `models.py:84`. |
| `reservas_espacios.hora_inicio`, `hora_fin` | `TIME WITHOUT TIME ZONE NOT NULL` | No hay `CHECK` para que fin sea posterior al inicio | `0001_spaces_init.py:36-48`; `models.py:85-86`; validación de entrada en `schemas.py:77-82`. |
| `reservas_espacios.estado_reserva` | `VARCHAR(20) NOT NULL DEFAULT 'Pendiente'` | No es `ENUM` PostgreSQL | `0001_spaces_init.py:36-48`; `models.py:87-89`; valores API en `schemas.py:22-33`. |
| `reservas_espacios.motivo` | `TEXT NULL` | — | `0001_spaces_init.py:36-48`; `models.py:90`. |
| `reservas_espacios.created_at` | `TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()` | — | `0001_spaces_init.py:36-48`; `models.py:91-93`. |
| `bloqueos_espacios.id_bloqueo` | `INTEGER NOT NULL`, autoincremental | PK | `0001_spaces_init.py:23-33`; `models.py:101`. |
| `bloqueos_espacios.id_espacio` | `INTEGER NOT NULL` | Índice; FK `espacios.id_espacio ON DELETE CASCADE`, agregada en `0002` | `0001_spaces_init.py:23-35`; `0002_espacios.py:38-45`; `models.py:102-104`. |
| `bloqueos_espacios.fecha_inicio`, `fecha_fin` | `DATE NOT NULL` | No hay `CHECK` para orden de fechas | `0001_spaces_init.py:23-33`; `models.py:105-106`; validación de entrada en `schemas.py:133-143`. |
| `bloqueos_espacios.hora_inicio`, `hora_fin` | `TIME WITHOUT TIME ZONE NULL` | La API requiere ambas o ninguna y fin posterior; no hay `CHECK` en DB | `0001_spaces_init.py:23-33`; `models.py:107-108`; `schemas.py:133-143`. |
| `bloqueos_espacios.motivo` | `TEXT NOT NULL` | — | `0001_spaces_init.py:23-33`; `models.py:109`. |
| `bloqueos_espacios.created_at` | `TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()` | Incorporada después de la tabla inicial | `0004_bloqueos_created_at.py:19-27`; `models.py:110-112`. |

La integridad temporal de las reservas adjudicadas usa `btree_gist` y la restricción `excl_reserva_aprobada_sin_solapamiento`, que compara igualdad de `id_espacio` con intersección de `tsrange(fecha_reserva + hora_inicio, fecha_reserva + hora_fin)`. `0001_spaces_init.py:19-21,52-66` sólo restringía `Aprobada`; `0003_reserva_en_uso.py:18-33` amplió la condición a `Aprobada` y `En_Uso`; el modelo vigente coincide (`models.py:42-75`). No hay restricciones `CHECK` en las migraciones para rangos de fecha/hora; esas reglas viven en Pydantic/servicio y requieren evaluar una migración, no asumir que ya están garantizadas en PostgreSQL (Constitución P7; AGENTS.md §6, Integridad temporal).

La migración `0007_spaces_sede_y_usuario.py:30-78` aborta ante valores de sede distintos de 1/2, convierte `id_sede` a `sede_enum` y elimina reservas cuyo `id_usuario` no existe antes de añadir la FK `RESTRICT`. El `downgrade` vuelve a crear `id_sede` (`0007_spaces_sede_y_usuario.py:81-90`) pero no recupera las reservas eliminadas, tal como advierten los comentarios de la migración (`0007_spaces_sede_y_usuario.py:5-9`).

### 6.2 Máquina de estados actual

| Estado actual | Estado siguiente | Actor autorizado | Condición verificada |
| --- | --- | --- | --- |
| `Pendiente` | `Aprobada` | ADMIN_LOCAL de la sede o SUPERADMIN | Sin otra reserva activa ni bloqueo en la franja. Al aprobar, pendientes superpuestas se rechazan con motivo automático. |
| `Pendiente` | `Rechazada` | ADMIN_LOCAL de la sede o SUPERADMIN | `motivo_rechazo` obligatorio; queda registrado en `motivo`. |
| `Pendiente` | `Rechazada` | Sistema, dentro de la aprobación administrativa | Rechazo automático de toda solicitud pendiente superpuesta; motivo automático persistido. |
| `Pendiente` | `Cancelada` | Dueño (ESTUDIANTE/DOCENTE) o administrador con jurisdicción | Dueño sólo antes del inicio; cancelación administrativa requiere motivo. |
| `Aprobada` | `En_Uso` | ADMIN_LOCAL de la sede o SUPERADMIN | Sin conflicto activo ni bloqueo. |
| `Aprobada` | `Cancelada` | Dueño (ESTUDIANTE/DOCENTE) o administrador con jurisdicción | Dueño sólo antes del inicio; cancelación administrativa requiere motivo. |
| `En_Uso` | `Finalizada` | ADMIN_LOCAL de la sede o SUPERADMIN | Transición administrativa permitida. |
| `Rechazada`, `Cancelada`, `Finalizada` | — | — | Estados terminales: sin transiciones salientes. |

El dueño no puede aprobar ni actuar sobre una reserva ajena; recursos ajenos o de otra jurisdicción responden como no encontrados. Implementación: `service.py:51-60,283-369`; motivos: `schemas.py:101-115`; cobertura de transición y concurrencia: `tests/spaces/test_espacios_reservas.py:266-365`.

El campo `solicitante` aún debe incorporarse a la respuesta administrativa de reserva mediante `users.datos_publicos_por_ids`; hoy no existe en el schema y no se agrega a disponibilidad. La interfaz se encuentra publicada y el pendiente se registra como K1 (K1 de SPEC-03; docs/perfiles.md §5; `schemas.py:85-99`).

## 7. Hallazgos de conformidad

Esta tabla registra diferencias verificadas entre el comportamiento implementado y las fuentes de requisitos/convenciones. Son propuestas para decisión o trabajo futuro; **no se corrigieron en esta entrega documental**.

| Fuente | Hallazgo verificado en el código | Propuesta (sin implementación) |
| --- | --- | --- |
| ERS RES-05 / SPEC-06 C-N02 | El servicio rechaza automáticamente solicitudes pendientes superpuestas al aprobar, pero no llama a `notifications` ni notifica a sus dueños (`service.py:351-364`; ERS RES-05; SPEC-06 §6.2/C-N02). | Integrar eventos en la transacción según el contrato de SPEC-06 §6.1 cuando esté disponible. |
| ERS GLO-02/GLO-03 / ADR-022 | El servicio consulta horario global (`horario.apertura`/`horario.cierre`) y el error de anticipación no añade correo de contacto (`service.py:99-104,183-213`). | Consumir el contrato de SPEC-09 §4.4-§4.5, pedido H1; no introducir claves ni fallback propios. |
| ERS GLO-04 | El ERS contempla el fin de contingencia; el router sólo expone `POST/GET /bloqueos` y la entidad no tiene estado de reversión (`router.py:129-156`; `models.py:96-112`). | En SPEC-08 v1.1.0, resolver baja lógica vs. DELETE físico y política de bloqueos generales con `PrestaMeDios-org/Backend-PrestaMeDios#32` y `PrestaMeDios-org/Frontend-PrestaMeDios#20`; aún no decidir ruta/migración. |
| ERS GLO-03 / calendario | El servidor usa ventana configurable (120 días en ERS), mientras UI permite navegar hasta mes actual más cuatro; el rango visible puede superar la ventana (`service.py:209-213`; `Frontend-PrestaMeDios/src/features/spaces/components/CalendarGrid.tsx:14-58,131-165`). | Alinear calendario a la ventana servida y manejar el límite como error no confirmado. |
| ERS RES-05 / estados | ERS denomina “Ocupado” a la adjudicación; contrato/almacenamiento trabajan con `Aprobada` y `En_Uso` (`schemas.py:22-33`; `models.py:87-90`). | Acordar etiqueta de UI sin cambiar silenciosamente valores persistidos. |
| SPEC-02 AC-39 / migración 0007 | AC-39 cubre la conversión y eliminación de reservas huérfanas; `upgrade` las borra y `downgrade` no las restaura (`0007_spaces_sede_y_usuario.py:5-9,56-90`). Es una pérdida documentada, no una reversión completa de datos. | Mantener aviso de migración y exigir copia/conciliación previa si hay reservas huérfanas. |
| SPEC-03 K1 / P6 | El listado mantiene privacidad por dueño/jurisdicción, pero `ReservaEspacioResponse` no incluye `solicitante` ni llama a `users.datos_publicos_por_ids` (`schemas.py:85-99`; `service.py:253-280`; docs/perfiles.md §5). | Completar K1 sólo para contexto administrativo autorizado, sin DNI, teléfono o email. |
| Constitución P7 / AGENTS §6 | La exclusión GIST protege solapamientos activos, pero rangos invertidos/pares incompletos sólo se rechazan en Pydantic; no hay `CHECK` persistido (`models.py:42-75,96-112`; `schemas.py:77-82,133-143`). | Evaluar `CHECK` PostgreSQL reversible para invariantes de rango; mantener validación API. |
| AGENTS §6, enums | El dominio define `EstadoReserva`, pero persiste `estado_reserva` como `String(20)`, no como `SAEnum`; DT-09 está pendiente (`models.py:87-89`; `schemas.py:22-33`; AGENTS.md §6). | No cambiarlo dentro de SPEC-08 sin decisión de migración y compatibilidad. |
| AGENTS §6, tests | La guía pide anotar cada test con AC/EC; el test de aprobaciones concurrentes no lleva etiqueta en su definición (`tests/spaces/test_espacios_reservas.py:346-365`). | Añadir trazabilidad al editar esos tests; no se modifican aquí. |

## 8. Criterios de aceptación

Los criterios AC-31…AC-39 de SPEC-02 siguen vigentes para autenticación, jurisdicción, creación, propiedad, validaciones, privacidad, transiciones y bloqueos iniciales. Cada criterio nuevo indica la prueba existente más directa; `SIN TEST` marca explícitamente un requisito todavía no cubierto por una prueba de Backend/Frontend.

| ID | Criterio verificable | ERS / SPEC-02 | Test existente |
| --- | --- | --- | --- |
| AC-S01 | ESTUDIANTE/DOCENTE no listan espacios, reservas o disponibilidad de otra sede; SUPERADMIN puede consultar ambas o filtrar sede. | GLO-01, RES-01; SPEC-02 AC-32, AC-36 | `tests/spaces/test_espacios_reservas.py::test_aislamiento_de_espacios`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_listado_con_alcance` |
| AC-S02 | Crear una reserva válida produce `Pendiente`, con el dueño derivado de la sesión; solicitudes distintas pueden coexistir en una franja mientras estén pendientes. | RES-02; SPEC-02 AC-34, AC-35 | `tests/spaces/test_espacios_reservas.py::test_reserva_pertenece_al_usuario_del_token`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia` |
| AC-S03 | Horario, anticipación mínima, ventana futura, bloqueo, reserva activa y duplicado se rechazan con sus códigos HTTP/AppError documentados; el horario y límites provienen de `config`. | GLO-02, GLO-03, RES-04; SPEC-02 AC-35 | `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_fuera_de_horario_y_horario_configurable`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_minima`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_en_hora_local_del_laboratorio`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_ventana_maxima`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_bloqueos_de_dia_y_de_franja`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia` |
| AC-S04 | Al aprobar, sólo una solicitud queda adjudicada y las pendientes que se solapan se rechazan automáticamente. | RES-05; SPEC-02 AC-37 | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_descarta_pendientes_y_ciclo_de_uso`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_rechaza_si_hay_bloqueo` |
| AC-S05 | El rechazo requiere motivo y la cancelación administrativa también; el motivo queda consultable por el solicitante. | RES-05; SPEC-02 AC-37 (transiciones/cancelación) | `tests/spaces/test_contratos.py::TestReservaEspacioUpdateStatus::test_rechazada_requiere_motivo`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_cancelacion_admin_exige_motivo`; lectura visible del motivo: **SIN TEST** |
| AC-S06 | El dueño puede cancelar una solicitud pendiente o aprobada futura; no puede cancelarla después del inicio ni cambiarla a otro estado. | RES-03; SPEC-02 AC-37 | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_cancela`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_aprueba_y_terceros_no_ven`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_cancela_pasada` |
| AC-S07 | ADMIN_LOCAL/SUPERADMIN pueden crear bloqueos completos o parciales dentro de alcance; se rechazan bloqueos fuera de horario o sobre reservas activas. | RES-04, GLO-02; SPEC-02 AC-38 | `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_alcance_y_roles`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_franja_fuera_de_horario`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_no_pisa_reservas_activas`; `tests/spaces/test_contratos.py::TestBloqueoEspacioCreate::test_dia_completo` |
| AC-S11 | La UI de una hora y navegación de cinco meses debe respetar la ventana configurada por servidor (120 días según el ERS) y no confirmar solicitudes rechazadas. | GLO-03; SPEC-02 AC-35 (límite servidor) | Backend: `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_ventana_maxima`; UI/límite combinado: **SIN TEST**. |
| AC-S12 | Disponibilidad no expone identidad ni IDs de reservas de otros; las consultas aplican alcance de sede. | P6; SPEC-02 AC-36 | `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`; `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance` |
| AC-S13 | Dos aprobaciones concurrentes no pueden dejar reservas activas solapadas; GIST es la garantía final en PostgreSQL. | P7.2; SPEC-02 AC-37 (transición) | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobaciones_concurrentes_solapadas`; migración/modelo: `tests/test_spaces_migrations.py::test_modelo_excluye_solapamientos_en_reservas_aprobadas_y_en_uso` |

### 8.1 Criterios pendientes

Estos criterios no describen capacidades vigentes. Se mantienen pendientes para las fases indicadas y no se usan como evidencia de implementación.

| ID | Criterio pendiente | ERS / dependencia | Test existente |
| --- | --- | --- | --- |
| AC-S08 | Mostrar el motivo del bloqueo en el calendario y habilitar la reversión conforme al diseño aún pendiente; la operación no alterará reservas activas de forma implícita. | GLO-04; decisión de baja lógica vs. DELETE físico y bloqueo general para SPEC-08 v1.1.0, coordinada con Backend #32 y Frontend #20 | **SIN TEST** (no existe el contrato de reversión ni test de UI del motivo). |
| AC-S09 | Añadir nombre/apellido del solicitante sólo a respuestas/vistas administrativas con jurisdicción; disponibilidad y respuestas a otros solicitantes no divulgarán identidad. | P6, K1; privacidad vigente cubierta por SPEC-02 AC-36 | **SIN TEST** para nombre administrativo (campo ausente); privacidad vigente: `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`. |
| AC-S10 | Aprobación, rechazo por solapamiento y cancelación por contingencia generan notificaciones en la transacción, sin `commit` independiente. | RES-05/NOV-04; SPEC-06 §6.1-§6.2/C-N02 | **SIN TEST** (integración con `notifications` no implementada en `spaces`). |

## 9. Casos de borde (EC)

| ID | Caso | Test existente |
| --- | --- | --- |
| EC-S01 | Dos usuarios distintos mantienen solicitudes pendientes superpuestas; la adjudicación de una rechaza las pendientes conflictivas. | `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_descarta_pendientes_y_ciclo_de_uso` |
| EC-S02 | Una solicitud no puede solaparse con reserva `Aprobada`/`En_Uso`, incluso ante aprobaciones concurrentes. | `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobaciones_concurrentes_solapadas` |
| EC-S03 | Un usuario no puede duplicar su solicitud pendiente para el mismo intervalo. | `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia` |
| EC-S04 | El dueño intenta cancelar después del inicio o intenta aprobar su propia reserva. | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_cancela_pasada`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_aprueba_y_terceros_no_ven` |
| EC-S05 | Un bloqueo parcial cruza varios días, exige ambas horas y respeta bordes contiguos sin falso solapamiento. | `tests/spaces/test_contratos.py::TestBloqueoEspacioCreate::test_parcial_requiere_ambas_horas`; `tests/spaces/test_contratos.py::test_bloqueo_parcial_aplica_en_cada_fecha_y_bordes_contiguos` |
| EC-S06 | Revertir un bloqueo no elimina su historial ni cambia reservas ya existentes. | **SIN TEST** (reversión no implementada). |
| EC-S07 | Al cambiar sede/espacio, la UI debe descartar disponibilidad de la selección anterior. | **SIN TEST** (no se identificó un test frontend correspondiente). |
| EC-S08 | Una fecha dentro de los meses visibles puede exceder la ventana configurada por el backend (120 días según el ERS). | Servidor: `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_ventana_maxima`; UI/comportamiento ante error: **SIN TEST**. |

## 10. Decisiones y dependencias abiertas

| ID | Tema | Estado y tratamiento |
| --- | --- | --- |
| K1 | Nombre y apellido del solicitante en respuestas administrativas. | `users.datos_publicos_por_ids` está publicado; falta conectarlo a `spaces` sólo para consultas administrativas con jurisdicción (K1 de SPEC-03; docs/perfiles.md §5). El schema actual no incluye el campo (`Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99`). |
| K10 | Parámetros de horario por sede y correo de contacto del laboratorio. | Cuando la Fase A de SPEC-09 esté en Backend `develop`, consumir `config.service.datos_de_sede(db, espacio.sede)` y `GET /api/v1/config/sedes` conforme a SPEC-09 §4.4-§4.5 y H1; no requiere acordar claves nuevas con Perfil 1. |
| GLO-04 | Reversión de bloqueos. | Pendiente para SPEC-08 v1.1.0: decidir baja lógica frente a DELETE físico y política de bloqueos generales, coordinando con `PrestaMeDios-org/Backend-PrestaMeDios#32` y `PrestaMeDios-org/Frontend-PrestaMeDios#20`. No se asume preservación ni eliminación del historial hasta esa decisión; hoy el router sólo ofrece `POST/GET /bloqueos` y el modelo no registra reversión (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`; `Backend-PrestaMeDios/app/modules/spaces/models.py:96-112`). |
| C-N02 / S7 | Notificaciones al resolver solicitudes y al cancelar por bloqueo administrativo. | `spaces` no invoca la interfaz; integrar el contrato transaccional de SPEC-06 §6.1-§6.2/C-N02 cuando la dependencia esté disponible. |
| DT-09 | Estados persistidos como `String` frente a `ENUM` de PostgreSQL. | Deuda pendiente; no se unifica en este spec sin decisión de migración (DT-09; `Backend-PrestaMeDios/app/modules/spaces/models.py:87-90`). |
| Isla de Digitalización | Nuevo espacio físico futuro. | Excluido de esta entrega; es requisito futuro de espacios en el ERS. |

## 11. Trazabilidad

| Requisito | Caso de uso | Criterios | Evidencia previa |
| --- | --- | --- | --- |
| RES-01 | CU-S01 | AC-S01, AC-S11, AC-S12 | ERS RES-01; SPEC-02 AC-36 |
| RES-02 | CU-S02 | AC-S02, AC-S03 | ERS RES-02; SPEC-02 AC-34, AC-35 |
| RES-03 | CU-S03 | AC-S06 | ERS RES-03; SPEC-02 AC-37 |
| RES-04 | CU-S05, CU-S06 | AC-S07, AC-S08 | ERS RES-04/GLO-04; SPEC-02 AC-38 |
| RES-05 | CU-S04, CU-S07 | AC-S04, AC-S05, AC-S10 | ERS RES-05; SPEC-06 C-N02 |
| GLO-02 | CU-S01, CU-S02, CU-S05 | AC-S01, AC-S03, AC-S07 | ERS GLO-02 |
| GLO-04 | CU-S05, CU-S06 | AC-S07, AC-S08 | ERS GLO-04 |

## 12. Fuentes verificadas

- `docs/constitution.md`: P3-P9 y §8 (gobierno de specs).
- `AGENTS.md`: §4 (SDD), §6 (convenciones y pruebas), §7 (reglas para agentes).
- `docs/perfiles.md`: §4 (responsabilidad/estado de Perfil 4) y §5/K1 (interfaz de datos públicos).
- `docs/ERS.md`: RES-01…RES-05, GLO-02…GLO-04, CU de reserva/administración y actualización de Iteración 5.
- `specs/02-integracion-seguridad-cuenta/spec.md`: §3.2 y AC-31…AC-39.
- `specs/06-notifications-comunicaciones/spec.md`: §6.1-§6.2 y C-N02.
- `specs/09-config-sedes-telefono/spec.md`: §4.4-§4.5, H1; incorporado en `origin/main` (`a2347eb3154ab345391219c64477f16b24a1ea3e`, Docs PR #27).
- Backend auditado sobre `origin/develop` (`3e85feb`): `Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`; `Backend-PrestaMeDios/app/modules/spaces/schemas.py:22-189`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:51-60,71-80,99-121,135-177,183-246,253-280,283-405,415-427,433-517`; `Backend-PrestaMeDios/app/core/deps.py:83-132`; `Backend-PrestaMeDios/app/core/errors.py:1-65`; `Backend-PrestaMeDios/app/modules/spaces/availability.py:16-69`; `Backend-PrestaMeDios/alembic/versions/0001_spaces_init.py:19-75`; `Backend-PrestaMeDios/alembic/versions/0002_espacios.py:19-52`; `Backend-PrestaMeDios/alembic/versions/0003_reserva_en_uso.py:18-51`; `Backend-PrestaMeDios/alembic/versions/0004_bloqueos_created_at.py:19-27`; `Backend-PrestaMeDios/alembic/versions/0007_spaces_sede_y_usuario.py:27-90`; `Backend-PrestaMeDios/tests/spaces/test_contratos.py:35-120`; `Backend-PrestaMeDios/tests/spaces/test_espacios_reservas.py:50-417`; `Backend-PrestaMeDios/tests/test_spaces_migrations.py:13-37`. Se revisó que `Backend-PrestaMeDios/app/modules/spaces/enums.py` no existe en ese ref; los estados se declaran en `Backend-PrestaMeDios/app/modules/spaces/schemas.py:22-33`.
- Frontend auditado sobre `origin/develop` (`03ce339`): `Frontend-PrestaMeDios/src/App.tsx:22-25,95-111,133-135`; `Frontend-PrestaMeDios/src/features/auth/roles.ts:5-11`; `Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,212-238,240-281,287-327,437-477,482-606,608-681`; `Frontend-PrestaMeDios/src/features/spaces/components/CalendarGrid.tsx:14-58,131-165`; `Frontend-PrestaMeDios/src/features/spaces/services/spacesApi.ts:7-13,82-153`; `Frontend-PrestaMeDios/src/features/spaces/types/index.ts:3-43`.
- Historial verificado con `git log --oneline origin/develop -- app/modules/spaces`: Backend `98b2e70`, `6a65a9a`, `b4c742a`, `cf8e084`; commits de Frontend indicados en la tabla de bloques implementados de `tasks.md`.
- **Resultado real de pruebas Backend:** `pytest -q tests/spaces tests/test_spaces_migrations.py` en `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`: **58 passed** en 22.39 s. La primera corrida falló por permisos insuficientes del rol local de PostgreSQL para crear la base de tests y la extensión `btree_gist`; se corrigió el entorno, sin cambios de código.
- **Validación Frontend:** `npm run build` exitoso y `npm test`: 16 archivos, 126 passed, 0 failed, 0 skipped; Frontend `develop` `8cbc76a5ccee77211abb1ca9dacfd1d5e551beb6`. Es independiente del `npm audit`; no se ejecutaron fixes.

## 13. Historial de cambios

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-11-11 | Correcciones a partir de la revisión del PR #28: se separa estado vigente y pendiente, se actualiza K10 al contrato SPEC-09/H1, se dejan las decisiones GLO-04 para v1.1.0 y se documentan resultados reales de validación. La línea base queda aprobada por el Perfil 1; las Fases 1–5 permanecen en `BORRADOR`. |
