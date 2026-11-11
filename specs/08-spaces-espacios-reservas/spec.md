# SPEC-08 — Espacios y reservas (`spaces`)

> **Estado:** `BORRADOR (retroactivo)` · **Versión:** 1.0.0 · **Fecha:** 2026-11-11 · **Perfil:** 4 (Espacios)
> **Tipo:** documentación retrospectiva del módulo existente y especificación de las brechas pendientes.
> **Requisitos:** RES-01…RES-05, GLO-02 y GLO-04.
> **Dependencias:** SPEC-01, SPEC-02, `config`, `users` (SPEC-03: `datos_publicos_por_ids`), y SPEC-06 (interfaz para eventos S7).
> **Fuentes funcionales:** `docs/ERS.md`; las referencias a rutas y líneas de código describen `origin/develop`, no autorizan cambios de aplicación.

## 0. Estado y precedencia

Este spec registra retrospectivamente la funcionalidad ya implementada en `spaces` y explicita las brechas que aún requieren trabajo. No reemplaza ni modifica el ERS. Las reglas funcionales siguen la precedencia de `docs/constitution.md` §6 y `AGENTS.md` §4; no se implementa código de aplicación hasta que el spec sea aprobado (`docs/constitution.md:151-160`; `AGENTS.md:75-82`).

La asignación del Perfil 4 comprende espacios físicos, calendario, reservas y bloqueos, no infraestructura de despliegue (`docs/perfiles.md:164-168`). La matriz actual clasifica como implementados los modelos, contratos, restricciones de solapamiento, validaciones, transiciones y pantallas; registra como pendientes DT-09, la reversión de bloqueos GLO-04 y la Isla de Digitalización, que es requisito futuro (`docs/perfiles.md:170-173`).

## 1. Alcance

### 1.1 Incluye

1. Calendario y disponibilidad del Aula-Estudio y la Isla de Edición por sede (RES-01).
2. Solicitudes de turnos en estado `Pendiente`, permitiendo solicitudes concurrentes de distintos usuarios para la misma franja (RES-02).
3. Cancelación por el solicitante antes del inicio, tanto de solicitudes pendientes como aprobadas (RES-03).
4. Bloqueos administrativos por día completo o intervalo, con motivo, aplicados al calendario (RES-04, GLO-02, GLO-04).
5. Aprobación y rechazo manual por un administrador con jurisdicción; aprobación adjudica una reserva y rechaza las solicitudes pendientes que se superponen (RES-05).
6. Horario operativo configurado por sede, anticipación mínima y aviso con el correo de contacto del laboratorio (GLO-02, GLO-03; ADR-022).
7. Nombre del solicitante en vistas administrativas, sin divulgar identidad en disponibilidad pública ni a otros solicitantes (P6, K1).
8. Eventos de notificación de aprobación, rechazo y cancelación administrativa, integrados mediante la interfaz pública de SPEC-06.

### 1.2 Fuera de alcance

- Implementar o modificar `core`, `users`, `config` o `notifications`, que pertenecen a otros perfiles. Las dependencias se coordinan con sus responsables.
- Inventario y préstamos de equipamiento, comunicados y asistente de IA.
- La futura Isla de Digitalización de Archivos Físicos, todavía no incluida en el catálogo actual (`docs/ERS.md:190`).
- Cambios de código en esta tarea documental.

### 1.3 Línea base verificada

La auditoría de Backend corresponde a `origin/develop` (`3e85feb`), mientras que su checkout de trabajo estaba en `e5d0b29`; la rama no se cambió. En ese ref existen los modelos, schemas, router, servicio, cálculo de disponibilidad y tests de `spaces` (`Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`; `Backend-PrestaMeDios/app/modules/spaces/schemas.py:36-189`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:99-121,183-246,253-280,307-405,433-517`; `Backend-PrestaMeDios/app/modules/spaces/availability.py:16-69`; `Backend-PrestaMeDios/tests/spaces/test_contratos.py:35-120`; `Backend-PrestaMeDios/tests/spaces/test_espacios_reservas.py:50-417`).

La API actual ofrece `GET/POST /espacios`, `POST/GET /reservas`, `PATCH /reservas/{id_reserva}/estado`, `POST/GET /bloqueos` y `GET /disponibilidad` bajo `/api/v1/spaces`; no existe operación para revertir un bloqueo (`Backend-PrestaMeDios/README.md:41`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`). `ReservaEspacioResponse` no incluye `solicitante`; `BloqueoEspacio` no tiene estado de reversión; el servicio usa `horario.apertura`/`horario.cierre` globales, no claves por sede; y el servicio no invoca `notifications` (`Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99,121-156`; `Backend-PrestaMeDios/app/modules/spaces/models.py:96-112`; `Backend-PrestaMeDios/app/modules/spaces/service.py:99-104,183-213,307-405`).

El frontend auditado está en `origin/develop` (`03ce339`). Tiene el calendario, selector de sede/espacio, solicitud y cancelación del usuario, bandeja administrativa y creación de bloqueos; no ofrece control para revertirlos (`Frontend-PrestaMeDios/src/App.tsx:22-25,95-111,133-135`; `Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,212-238,240-281,287-327,437-477,482-606,608-681`). La grilla presenta turnos de una hora y permite navegar por mes hasta el mes actual más cuatro; el backend sólo exige que la hora final sea posterior a la inicial, valida contra horario y aplica una ventana de 120 días (`Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:21-33,437-477`; `Frontend-PrestaMeDios/src/features/spaces/components/CalendarGrid.tsx:14-58,131-165`; `Backend-PrestaMeDios/app/modules/spaces/schemas.py:77-83`; `Backend-PrestaMeDios/app/modules/spaces/service.py:183-213`; `docs/ERS.md:276,1226`).

**Verificación no ejecutada:** no se corrió `pytest`. `TEST_DATABASE_URL` está unset; los tests de integración requieren PostgreSQL y el checkout local de Backend (`e5d0b29`) no contiene `tests/spaces/`, aunque el ref auditado sí (`Backend-PrestaMeDios/tests/conftest.py:3,43-56`; `Backend-PrestaMeDios/README.md:163`; `origin/develop` `3e85feb`). Por lo tanto, el spec no afirma que la suite pase.

## 2. Actores y permisos

| Acción | ESTUDIANTE | DOCENTE | ADMIN_LOCAL | SUPERADMIN |
| --- | --- | --- | --- | --- |
| Consultar calendario y disponibilidad | Sí, sede propia | Sí, sede propia | Sí, sede propia | Ambas sedes |
| Crear una solicitud de reserva | Sí | Sí | No | No |
| Consultar y cancelar sus reservas antes del inicio | Sí | Sí | No aplica | No aplica |
| Ver bandeja y resolver solicitudes | No | No | Sí, su sede | Sí |
| Crear y revertir bloqueos | No | No | Sí, su sede | Sí |
| Crear espacios | No | No | Sí, su sede | Sí, eligiendo sede |
| Ver identidad del solicitante | Sólo la propia reserva | Sólo la propia reserva | Sí, con jurisdicción | Sí |

El filtrado por sede debe aplicarse en las consultas de datos, no sólo en la interfaz (Constitución P5.2-P5.4, `docs/constitution.md:51-56`). Toda ruta requiere autenticación y autorización del lado del servidor salvo excepción explícita en el spec (P4.1-P4.5, `docs/constitution.md:43-50`). Los recursos ajenos o fuera de jurisdicción no deben revelar su existencia (Constitución §4.2, P4.5).

## 3. Reglas de negocio

- **RN-S01 — Disponibilidad:** el calendario presenta espacios, franjas operativas, ocupaciones adjudicadas y bloqueos, pero no identifica a otros solicitantes (RES-01; `docs/ERS.md:249`; SPEC-02 §3.2, `specs/02-integracion-seguridad-cuenta/spec.md:102-123`).
- **RN-S02 — Solicitud pendiente y concurrencia:** una solicitud nueva se guarda como `Pendiente`. Las solicitudes pendientes de otras personas pueden coexistir en una franja; no adjudican ni bloquean por sí solas el espacio (RES-02; `docs/ERS.md:250,837-865`).
- **RN-S03 — Adjudicación única:** sólo un administrador con alcance puede aprobar. La aprobación hace que el espacio quede ocupado y rechaza las solicitudes pendientes que se solapan con la aprobada (RES-05; `docs/ERS.md:253,868-896`).
- **RN-S04 — Integridad temporal:** las reservas aprobadas o en uso no se superponen para el mismo espacio. La restricción de base de datos es la garantía final; solicitudes pendientes concurrentes no se incluyen en esa restricción (P7.1-P7.2, `docs/constitution.md:65-72`; ADR-004, `MEMORY.md:79`).
- **RN-S05 — Cancelación del solicitante:** el dueño puede cancelar su reserva pendiente o aprobada sólo antes del inicio; la disponibilidad se actualiza inmediatamente. No se permite cancelar una reserva cuyo turno empezó (RES-03; `docs/ERS.md:251,899-916`).
- **RN-S06 — Horario por sede:** la franja solicitada debe quedar dentro del horario configurado para la sede del espacio. El horario no se codifica como constante; se lee de `config` (GLO-02/GLO-03, `docs/ERS.md:272,276`; P8, `docs/constitution.md:73-76`).
- **RN-S07 — Anticipación:** una reserva debe respetar el mínimo configurable de anticipación. Si el inicio es anterior al mínimo, el sistema rechaza la solicitud y muestra el correo de contacto del laboratorio para canalizar urgencias (ADR-011, `MEMORY.md:72`; caso de uso actualizado, `docs/ERS.md:859-864`).
- **RN-S08 — Ventana máxima:** no se permite reservar más allá de la ventana futura configurada, cuyo valor vigente en el ERS es 120 días (GLO-03, `docs/ERS.md:276,1226`; SPEC-02 V5, `specs/02-integracion-seguridad-cuenta/spec.md:146`).
- **RN-S09 — Bloqueo:** un bloqueo puede abarcar días completos o un intervalo horario, exige motivo y evita nuevas solicitudes en el rango. El calendario debe mostrar el motivo; cuando la contingencia termina, el administrador puede revertir el bloqueo (GLO-04, `docs/ERS.md:277,918-934,1040-1050`).
- **RN-S10 — Privacidad del solicitante:** identidad del solicitante sólo se devuelve a administradores con jurisdicción y en reservas que pueden gestionar. Disponibilidad no incluye identidad ni identificadores de otras reservas (P6, `docs/constitution.md:58-63`; SPEC-02 §3.2 y AC-36, `specs/02-integracion-seguridad-cuenta/spec.md:102-123,377-381`).
- **RN-S11 — Rechazo:** el administrador debe ingresar un motivo al rechazar una solicitud; el solicitante puede consultar ese motivo (Iteración 5, `docs/ERS.md:1231-1240`; ERS CU de aprobación, `docs/ERS.md:868-896`).
- **RN-S12 — Notificaciones:** las notificaciones de dominio se agregan a la transacción de `spaces` mediante el contrato de SPEC-06, sin `commit` independiente. Al aprobar una solicitud se notifican la aprobación y los rechazos por superposición; un bloqueo sólo notifica la cancelación forzada de reservas cuando el administrador efectivamente las cancela (SPEC-06 §6, `specs/06-notifications-comunicaciones/spec.md:148-180,202-204,322-323`).
- **RN-S13 — Bloqueo y reservas ya aprobadas:** crear un bloqueo no cancela de forma implícita reservas ya adjudicadas. Si una contingencia exige cancelar una reserva aprobada, el administrador debe resolverla explícitamente y registrar el motivo (RES-03/RES-05 y GLO-04; `docs/ERS.md:251,253,277`).
- **RN-S14 — Conservación del historial:** revertir un bloqueo no debe borrar el registro histórico de que existió (P7.3, `docs/constitution.md:65-72`).

## 4. Casos de uso

| ID | Caso | Actor | Requisitos | Resultado |
| --- | --- | --- | --- | --- |
| CU-S01 | Consultar disponibilidad | Cualquier usuario autenticado | RES-01, GLO-02 | Ve calendario de espacios de su sede; SUPERADMIN puede elegir sede. |
| CU-S02 | Solicitar turno | ESTUDIANTE, DOCENTE | RES-02, GLO-02 | Se registra la solicitud pendiente si horario, anticipación, ventana y bloqueos lo permiten. |
| CU-S03 | Cancelar solicitud propia | ESTUDIANTE, DOCENTE | RES-03 | Se cancela sólo antes del inicio y se libera la franja. |
| CU-S04 | Resolver solicitudes | ADMIN_LOCAL, SUPERADMIN | RES-05 | Aprueba o rechaza manualmente; rechazo requiere motivo; aprobación rechaza las solicitudes pendientes superpuestas. |
| CU-S05 | Bloquear calendario | ADMIN_LOCAL, SUPERADMIN | RES-04, GLO-02, GLO-04 | Registra bloqueo con motivo para un día o intervalo y evita nuevas solicitudes en ese rango. |
| CU-S06 | Revertir bloqueo | ADMIN_LOCAL, SUPERADMIN | GLO-04 | Reactiva el rango sin borrar la evidencia histórica del bloqueo. |
| CU-S07 | Consultar bandeja administrativa | ADMIN_LOCAL, SUPERADMIN | RES-05 | Ve sólo las reservas de su jurisdicción e identidad pública mínima del solicitante. |

## 5. Contratos actuales

La base de rutas existente es `/api/v1/spaces`; SPEC-02 documentó `GET /espacios`, `POST /espacios`, `GET /disponibilidad`, `POST /reservas`, `GET /reservas`, `PATCH /reservas/{id}/estado` y `POST/GET /bloqueos` (SPEC-02 §3.2, `specs/02-integracion-seguridad-cuenta/spec.md:100-107`).

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
| GLO-04, reversión de bloqueos | Sólo existen `POST/GET /bloqueos`; el modelo no tiene estado de reversión ni ruta `DELETE/PATCH` (`router.py:129-156`; `models.py:96-112`). | Diseñar transición reversible y auditable, incluida la política de disponibilidad, antes de agregar endpoint o columna. |
| K1, identidad pública | `ReservaEspacioResponse` expone `id_usuario`, pero no `solicitante`; no se usa `users.datos_publicos_por_ids` desde `spaces` (`schemas.py:85-99`; `service.py:253-280`). | Extender sólo las respuestas administrativas con `id/nombre/apellido`, respetando P6 y jurisdicción. |
| K10, configuración por sede | `horario()` consulta las claves globales `horario.apertura` y `horario.cierre` (`service.py:99-104`). | Coordinar claves y contrato de `config` con Perfil 1 antes de adaptar `spaces`. |
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

La integridad temporal de las reservas adjudicadas usa `btree_gist` y la restricción `excl_reserva_aprobada_sin_solapamiento`, que compara igualdad de `id_espacio` con intersección de `tsrange(fecha_reserva + hora_inicio, fecha_reserva + hora_fin)`. `0001_spaces_init.py:19-21,52-66` sólo restringía `Aprobada`; `0003_reserva_en_uso.py:18-33` amplió la condición a `Aprobada` y `En_Uso`; el modelo vigente coincide (`models.py:42-75`). No hay restricciones `CHECK` en las migraciones para rangos de fecha/hora; esas reglas viven en Pydantic/servicio y requieren evaluar una migración, no asumir que ya están garantizadas en PostgreSQL (Constitución P7, `docs/constitution.md:65-72`; AGENTS §6, `AGENTS.md:126-127`).

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

El campo `solicitante` aún debe incorporarse a la respuesta administrativa de reserva mediante `users.datos_publicos_por_ids`; hoy no existe en el schema y no se agrega a disponibilidad. La interfaz se encuentra publicada y el pendiente se registra como K1 (`MEMORY.md:146,149`; `docs/perfiles.md:222`; `schemas.py:85-99`).

## 7. Hallazgos de conformidad

Esta tabla registra diferencias verificadas entre el comportamiento implementado y las fuentes de requisitos/convenciones. Son propuestas para decisión o trabajo futuro; **no se corrigieron en esta entrega documental**.

| Fuente | Hallazgo verificado en el código | Propuesta (sin implementación) |
| --- | --- | --- |
| ERS RES-05 / SPEC-06 C-N02 | El servicio rechaza automáticamente solicitudes pendientes superpuestas al aprobar, pero no llama a `notifications` ni notifica a sus dueños (`service.py:351-364`; ERS `docs/ERS.md:822,868-896`; SPEC-06 `specs/06-notifications-comunicaciones/spec.md:202-204,322-323`). | Coordinar Perfil 5 y emitir los eventos desde la transacción una vez disponible la interfaz; conservar el comportamiento de rollback. |
| ERS GLO-02/GLO-03 / ADR-022 | El servicio consulta horario global (`horario.apertura`/`horario.cierre`) y el error de anticipación no añade un correo de contacto; los requisitos revisados piden parametrización por sede y aviso de contacto (`service.py:99-104,183-213`; `docs/ERS.md:272,276,859-864`). | Coordinar las claves y el contrato de `config` con Perfil 1 y luego adaptar `spaces`; no agregar fallbacks ni datos de contacto supuestos. |
| ERS GLO-04 | El ERS prevé retirar el bloqueo cuando termina la contingencia; el router sólo expone `POST/GET /bloqueos` y la entidad no tiene estado de reversión (`docs/ERS.md:965`; `router.py:129-156`; `models.py:96-112`). | Acordar un modelo de reversión auditable y su efecto sobre disponibilidad antes de diseñar ruta/migración. |
| ERS GLO-03 / calendario | El servidor usa la ventana configurable (120 días en el ERS), mientras la UI permite navegar hasta el mes actual más cuatro; el rango visible puede superar la ventana del servidor (`service.py:209-213`; `Frontend-PrestaMeDios/src/features/spaces/components/CalendarGrid.tsx:14-58,131-165`; `docs/ERS.md:1226`). | Alinear el calendario a la ventana servida y manejar el límite como error no confirmado. |
| ERS RES-05 / estados | El ERS utiliza “Ocupado” para la adjudicación; el contrato y almacenamiento trabajan con `Aprobada` y `En_Uso` (`docs/ERS.md:249`; `schemas.py:22-33`; `models.py:87-90`). | Acordar una etiqueta de interfaz uniforme sin cambiar silenciosamente los valores persistidos. |
| SPEC-02 AC-39 / migración 0007 | AC-39 cubre la conversión y eliminación de reservas huérfanas; `upgrade` las borra y `downgrade` no las restaura (`specs/02-integracion-seguridad-cuenta/spec.md:395-403`; `0007_spaces_sede_y_usuario.py:5-9,56-90`). Es una pérdida deliberada y documentada, no una reversión completa de datos. | Mantener el aviso de migración y exigir copia/conciliación previa si una instalación conserva reservas huérfanas. |
| SPEC-03 K1 / P6 | El listado mantiene privacidad por dueño/jurisdicción, pero `ReservaEspacioResponse` no incluye `solicitante` ni llama a `users.datos_publicos_por_ids` (`schemas.py:85-99, service.py:253-280`; `docs/perfiles.md:222`; `MEMORY.md:146,149`). | Completar K1 sólo para el contexto administrativo autorizado y sin sumar DNI, teléfono o email. |
| Constitución P7 / AGENTS §6 | La exclusión GIST protege solapamientos activos, pero los rangos invertidos/pares incompletos sólo se rechazan en Pydantic; no hay `CHECK` persistido (`models.py:42-75,96-112`; `schemas.py:77-82,133-143`; `docs/constitution.md:65-72`; `AGENTS.md:126-127`). | Evaluar `CHECK` PostgreSQL reversible para los invariantes de rango; mantener validación de API para mensajes útiles. |
| AGENTS §6, enums | El dominio define `EstadoReserva`, pero persiste `estado_reserva` como `String(20)`, no como `SAEnum`; AGENTS registra expresamente DT-09 pendiente (`models.py:87-89`; `schemas.py:22-33`; `AGENTS.md:123`; `MEMORY.md:131`). | No cambiarlo dentro de SPEC-08 sin decisión de migración y compatibilidad de datos. |
| AGENTS §6, tests | La guía pide anotar cada test con AC/EC; por ejemplo, el test de aprobaciones concurrentes no lleva etiqueta AC/EC en su definición (`AGENTS.md:152`; `tests/spaces/test_espacios_reservas.py:346-365`). | Añadir etiquetas de trazabilidad cuando se editen esos tests; no se modificaron aquí. |

## 8. Criterios de aceptación

Los criterios AC-31…AC-39 de SPEC-02 siguen vigentes para autenticación, jurisdicción, creación, propiedad, validaciones, privacidad, transiciones y bloqueos iniciales (`specs/02-integracion-seguridad-cuenta/spec.md:343-403`). Cada criterio nuevo indica la prueba existente más directa; `SIN TEST` marca explícitamente un requisito todavía no cubierto por una prueba de Backend/Frontend.

| ID | Criterio verificable | ERS / SPEC-02 | Test existente |
| --- | --- | --- | --- |
| AC-S01 | ESTUDIANTE/DOCENTE no listan espacios, reservas o disponibilidad de otra sede; SUPERADMIN puede consultar ambas o filtrar sede. | GLO-01, RES-01; SPEC-02 AC-32, AC-36 | `tests/spaces/test_espacios_reservas.py::test_aislamiento_de_espacios`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_listado_con_alcance` |
| AC-S02 | Crear una reserva válida produce `Pendiente`, con el dueño derivado de la sesión; solicitudes distintas pueden coexistir en una franja mientras estén pendientes. | RES-02; SPEC-02 AC-34, AC-35 | `tests/spaces/test_espacios_reservas.py::test_reserva_pertenece_al_usuario_del_token`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia` |
| AC-S03 | Horario, anticipación mínima, ventana futura, bloqueo, reserva activa y duplicado se rechazan con sus códigos HTTP/AppError documentados; el horario y límites provienen de `config`. | GLO-02, GLO-03, RES-04; SPEC-02 AC-35 | `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_fuera_de_horario_y_horario_configurable`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_minima`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_anticipacion_en_hora_local_del_laboratorio`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_ventana_maxima`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_bloqueos_de_dia_y_de_franja`; `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia` |
| AC-S04 | Al aprobar, sólo una solicitud queda adjudicada y las pendientes que se solapan se rechazan; el evento de notificación de esas transiciones queda pendiente. | RES-05; SPEC-02 AC-37; SPEC-06 C-N02 | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_descarta_pendientes_y_ciclo_de_uso`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobar_rechaza_si_hay_bloqueo`; notificación: **SIN TEST** |
| AC-S05 | El rechazo requiere motivo y la cancelación administrativa también; el motivo queda consultable por el solicitante. | RES-05; SPEC-02 AC-37 (transiciones/cancelación) | `tests/spaces/test_contratos.py::TestReservaEspacioUpdateStatus::test_rechazada_requiere_motivo`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_cancelacion_admin_exige_motivo`; lectura visible del motivo: **SIN TEST** |
| AC-S06 | El dueño puede cancelar una solicitud pendiente o aprobada futura; no puede cancelarla después del inicio ni cambiarla a otro estado. | RES-03; SPEC-02 AC-37 | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_cancela`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_aprueba_y_terceros_no_ven`; `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_dueno_no_cancela_pasada` |
| AC-S07 | ADMIN_LOCAL/SUPERADMIN pueden crear bloqueos completos o parciales dentro de alcance; se rechazan bloqueos fuera de horario o sobre reservas activas. | RES-04, GLO-02; SPEC-02 AC-38 | `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_alcance_y_roles`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_franja_fuera_de_horario`; `tests/spaces/test_espacios_reservas.py::TestBloqueos::test_no_pisa_reservas_activas`; `tests/spaces/test_contratos.py::TestBloqueoEspacioCreate::test_dia_completo` |
| AC-S08 | El calendario debe mostrar el motivo; revertir bloqueos debe conservar historial y liberar sólo el intervalo sin conflictos. | GLO-04; no está en SPEC-02 AC-31…39 | Motivo en calendario y reversión: **SIN TEST** (el endpoint no existe). |
| AC-S09 | Las respuestas administrativas deben añadir nombre/apellido; disponibilidad y respuestas de otros solicitantes no divulgan identidad. | P6, K1; SPEC-02 AC-36 cubre privacidad actual | Privacidad implementada: `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`; nombre/apellido administrativo nuevo: **SIN TEST** (campo ausente). |
| AC-S10 | Aprobación, rechazo por solapamiento y cancelación por contingencia generan notificaciones dentro de la transacción y sin `commit` independiente. | RES-05/NOV-04; SPEC-06 §6/C-N02 | **SIN TEST** (integración con `notifications` no implementada en `spaces`). |
| AC-S11 | La UI de una hora y navegación de cinco meses debe respetar la ventana configurada por servidor (120 días según el ERS) y no confirmar solicitudes rechazadas. | GLO-03; SPEC-02 AC-35 (límite servidor) | Backend: `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_ventana_maxima`; UI/límite combinado: **SIN TEST**. |
| AC-S12 | Disponibilidad no expone identidad ni IDs de reservas de otros; las consultas aplican alcance de sede. | P6; SPEC-02 AC-36 | `tests/spaces/test_espacios_reservas.py::test_privacidad_de_reservas`; `tests/spaces/test_espacios_reservas.py::test_disponibilidad_intervalos_y_alcance` |
| AC-S13 | Dos aprobaciones concurrentes no pueden dejar reservas activas solapadas; GIST es la garantía final en PostgreSQL. | P7.2; SPEC-02 AC-37 (transición) | `tests/spaces/test_espacios_reservas.py::TestTransiciones::test_aprobaciones_concurrentes_solapadas`; migración/modelo: `tests/test_spaces_migrations.py::test_modelo_excluye_solapamientos_en_reservas_aprobadas_y_en_uso` |

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
| K1 | Nombre y apellido del solicitante en respuestas administrativas. | El servicio público `users.datos_publicos_por_ids` está disponible; queda pendiente conectarlo a `spaces`, sólo en contextos administrativos (`MEMORY.md:146,149`; `docs/perfiles.md:222`; el schema actual carece del campo, `Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99`). |
| K10 | Parámetros de horario por sede y correo de contacto del laboratorio. | Dependencia del Perfil 1 (`config`); no cambiar `config` desde este perfil. Se adopta el requerimiento actualizado del ERS (`docs/ERS.md:276,859-864,1226`; `MEMORY.md:149,159`). |
| GLO-04 | Reversión de bloqueos. | Pendiente; el router sólo tiene `POST/GET /bloqueos` y el modelo no guarda estado de reversión (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`; `Backend-PrestaMeDios/app/modules/spaces/models.py:96-112`). Preservar el historial (DT de Perfil 4, `docs/perfiles.md:173`). La operación/estado concreto de reversión queda para aprobar junto con el diseño de datos. |
| C-N02 / S7 | Notificaciones al resolver solicitudes y al cancelar por bloqueo administrativo. | El contrato está en SPEC-06; confirmar la invocación desde `spaces` cuando la función esté disponible (`MEMORY.md:154`; `specs/06-notifications-comunicaciones/spec.md:202-204,322-323`). |
| DT-09 | Estados persistidos como `String` frente a `ENUM` de PostgreSQL. | Deuda pendiente; no se unifica en este spec sin decisión de migración (`MEMORY.md:131`; `docs/perfiles.md:173`; `Backend-PrestaMeDios/app/modules/spaces/models.py:87-90`). |
| Isla de Digitalización | Nuevo espacio físico futuro. | Excluido de esta entrega; el ERS lo identifica como requisito futuro (`docs/ERS.md:190`). |

## 11. Trazabilidad

| Requisito | Caso de uso | Criterios | Evidencia previa |
| --- | --- | --- | --- |
| RES-01 | CU-S01 | AC-S01, AC-S11, AC-S12 | `docs/ERS.md:249`; SPEC-02 AC-36 |
| RES-02 | CU-S02 | AC-S02, AC-S03 | `docs/ERS.md:250`; SPEC-02 AC-34, AC-35 |
| RES-03 | CU-S03 | AC-S06 | `docs/ERS.md:251,899-916`; SPEC-02 AC-37 |
| RES-04 | CU-S05, CU-S06 | AC-S07, AC-S08 | `docs/ERS.md:252,277,918-934`; SPEC-02 AC-38 |
| RES-05 | CU-S04, CU-S07 | AC-S04, AC-S05, AC-S09, AC-S10 | `docs/ERS.md:253,868-896`; SPEC-06 C-N02 |
| GLO-02 | CU-S01, CU-S02, CU-S05 | AC-S01, AC-S03, AC-S07 | `docs/ERS.md:272,276` |
| GLO-04 | CU-S05, CU-S06 | AC-S07, AC-S08 | `docs/ERS.md:277,1040-1050` |

## 12. Fuentes verificadas

- `docs/constitution.md`: P3-P9 y gobierno de specs, líneas 36-81 y 151-160.
- `AGENTS.md`: orden de lectura, SDD y restricciones de perfil, líneas 64-82 y 111-120; convenciones de código de §6, líneas 118-152.
- `docs/perfiles.md`: Perfil 4 y estado de `spaces`, líneas 164-177; interfaz de datos públicos, línea 222.
- `docs/ERS.md`: requisitos RES-01…05 y GLO-02/04, líneas 249-253, 272-277; casos de uso, líneas 837-934; requisito futuro, línea 190; Iteración 5, líneas 1219-1240.
- `specs/02-integracion-seguridad-cuenta/spec.md`: contrato, validaciones y AC-31…AC-39, líneas 81-166 y 343-403.
- `specs/06-notifications-comunicaciones/spec.md`: contrato de notificaciones para `spaces`, líneas 148-180, 202-204 y 322-323.
- Backend auditado sobre `origin/develop` (`3e85feb`, distinto de su checkout `e5d0b29`): `Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`; `Backend-PrestaMeDios/app/modules/spaces/schemas.py:22-189`; `Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:51-60,71-80,99-121,135-177,183-246,253-280,283-405,415-427,433-517`; `Backend-PrestaMeDios/app/core/deps.py:83-132`; `Backend-PrestaMeDios/app/core/errors.py:1-65`; `Backend-PrestaMeDios/app/modules/spaces/availability.py:16-69`; `Backend-PrestaMeDios/alembic/versions/0001_spaces_init.py:19-75`; `Backend-PrestaMeDios/alembic/versions/0002_espacios.py:19-52`; `Backend-PrestaMeDios/alembic/versions/0003_reserva_en_uso.py:18-51`; `Backend-PrestaMeDios/alembic/versions/0004_bloqueos_created_at.py:19-27`; `Backend-PrestaMeDios/alembic/versions/0007_spaces_sede_y_usuario.py:27-90`; `Backend-PrestaMeDios/tests/spaces/test_contratos.py:35-120`; `Backend-PrestaMeDios/tests/spaces/test_espacios_reservas.py:50-417`; `Backend-PrestaMeDios/tests/test_spaces_migrations.py:13-37`. Se revisó que `Backend-PrestaMeDios/app/modules/spaces/enums.py` no existe en ese ref; los estados se declaran en `Backend-PrestaMeDios/app/modules/spaces/schemas.py:22-33`.
- Frontend auditado sobre `origin/develop` (`03ce339`): `Frontend-PrestaMeDios/src/App.tsx:22-25,95-111,133-135`; `Frontend-PrestaMeDios/src/features/auth/roles.ts:5-11`; `Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,212-238,240-281,287-327,437-477,482-606,608-681`; `Frontend-PrestaMeDios/src/features/spaces/components/CalendarGrid.tsx:14-58,131-165`; `Frontend-PrestaMeDios/src/features/spaces/services/spacesApi.ts:7-13,82-153`; `Frontend-PrestaMeDios/src/features/spaces/types/index.ts:3-43`.
- Historial verificado con `git log --oneline origin/develop -- app/modules/spaces`: Backend `98b2e70`, `6a65a9a`, `b4c742a`, `cf8e084`; commits de Frontend indicados en la tabla de bloques implementados de `tasks.md`.
- **Pruebas no ejecutadas:** `TEST_DATABASE_URL` estaba unset y el checkout local de Backend (`e5d0b29`) no tiene `tests/spaces/`; las suites existen en `origin/develop` (`3e85feb`). No se afirma que pasen. El README del Backend exige PostgreSQL real para integración (`Backend-PrestaMeDios/tests/conftest.py:3,43-56`; `Backend-PrestaMeDios/README.md:163`).
