# PLAN-08 — Espacios y reservas (`spaces`)

> **Estado:** `BORRADOR` (v1.1.0; pendiente de decisión de Facundo) · línea base v1.0.0 aprobada retroactivamente · **Versión:** 1.1.0 · **Fecha:** 2026-11-11 · **Perfil:** 4
> **Spec:** `specs/08-spaces-espacios-reservas/spec.md` v1.1.0 (`BORRADOR`; no autoriza implementación)
> **Alcance:** retrospectivo; documenta el estado de `spaces` y ordena las brechas sin implementar código antes de la aprobación.

## 1. Enfoque

El módulo ya está integrado con autenticación, sede, calendario, reservas y bloqueos (SPEC-02; docs/perfiles.md §4, Perfil 4). Este plan separa la línea base v1.0.0 aprobada de las brechas de las Fases 1–5. La revisión v1.1.0 sigue en `BORRADOR`, pendiente de Facundo; sus recomendaciones no autorizan implementación. La auditoría funcional de Backend fue sobre `origin/develop` `3e85feb`. Backend #32 y Frontend #20 están abiertos y no integrados: se inspeccionaron para trazar las discrepancias, no se tomaron como código de `develop`. Backend #32 crea bloqueos generales, pero revierte con `DELETE` físico y no agrupa filas; además agrega un test que permite al dueño cancelar una reserva aprobada después del inicio, contrario a RES-03. Frontend #20 envía una reserva por hora y deshabilita horas con una `Pendiente` ajena. La propuesta recomienda baja lógica, agrupación por `id_grupo`, consolidar corridas contiguas, conservar RN-S02 y preservar la ventana de cancelación de RES-03. En Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, `pytest -q tests/spaces tests/test_spaces_migrations.py` dio 58 passed; una primera corrida falló por permisos del rol local de PostgreSQL para crear la base de tests y `btree_gist`, y se corrigió el entorno sin cambios de código.

Las brechas se implementarán tarea por tarea, sólo después de aprobación explícita del spec, con criterios de aceptación y pruebas PostgreSQL reales (Constitución P1, P9; SDD §4 de AGENTS.md).

## 2. Estado actual y brechas

| Área | Estado verificado | Próximo paso |
| --- | --- | --- |
| Modelos e integridad temporal | `Espacio`, `ReservaEspacio`, `BloqueoEspacio`; exclusión GIST en reservas aprobadas/en uso (`Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`). | Mantener garantía concurrente y revisar en aprobación la ausencia de `CHECK` de base para rangos. |
| API y permisos | Rutas de espacios, reservas, estados, bloqueos y disponibilidad; sesión obligatoria y alcance por rol/sede (`Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:111-121,163-168,183-186,238-280`). | Extender los contratos dentro del módulo `spaces` sin aceptar usuario o sede no confiables. |
| Horario y anticipación | Horario global y reglas de anticipación/ventana desde `config` (`Backend-PrestaMeDios/app/modules/spaces/service.py:99-104,190-213`). | Consumir SPEC-09 §4.4-§4.5/H1 cuando la Fase A esté en Backend `develop`; ya no requiere acordar claves con Perfil 1. |
| Datos del solicitante | La respuesta actual no incluye nombre/apellido (`Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99`); `users.datos_publicos_por_ids` está disponible (docs/perfiles.md §5, K1). | Sólo admins con jurisdicción reciben `solicitante_nombre`/`solicitante_apellido`, también en respuestas administrativas de cambio de estado; dueño omite las claves y disponibilidad nunca las contiene. Listados usan una llamada en lote. |
| Bloqueos | Crear/listar; bloques completos o parciales; no pueden pisar reservas activas (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`; `Backend-PrestaMeDios/app/modules/spaces/service.py:375-405`). | Recomendación no aprobada: baja lógica y `PATCH /bloqueos/{id}/estado`; bloqueo general sólo SUPERADMIN, filas por espacio con `id_grupo`, reversión de grupo completa. Contratos y migración siguen pendientes. |
| Selección RES-02 (Frontend) | #20 permite seleccionar varias horas y envía una solicitud por hora; deshabilita las franjas con una solicitud `Pendiente` ajena. | Recomendación no aprobada: una reserva por serie contigua, varias reservas para series no contiguas; las pendientes ajenas siguen seleccionables y no bloqueantes, como exige RN-S02. |
| Notificaciones | `spaces` no invoca `notifications`; SPEC-06 publica los eventos y `crear_notificaciones` (SPEC-06 §6.1-§6.2, C-N02) (`Backend-PrestaMeDios/app/modules/spaces/service.py:307-405`). | Atender C-N02 cuando la función esté disponible en el backend. |
| Frontend | Calendario mensual, solicitudes propias, bandeja administrativa, alta de espacios y creación de bloqueos (`Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,240-281,287-327,482-681`). | Añadir visualización de motivo y acción para revertir bloqueos; preservar el alcance de sede al cambiar de contexto. |
| Validación de pruebas | Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, `pytest -q tests/spaces tests/test_spaces_migrations.py`: 58 passed (22.39 s). Una primera corrida falló por permisos insuficientes del rol local de PostgreSQL para crear la base de tests y `btree_gist`; se corrigió el entorno sin cambios de código. | Resultado vigente: suite Backend completa. |

## 3. Fases y dependencias

### Fase 0 — Verificación retrospectiva

Verificar requisitos, API, modelos, frontend, tests existentes y discrepancias. Esta fase se completa sólo como auditoría documental; no es evidencia de tests ejecutados.

### Fase 1 — Privacidad y nombre del solicitante (K1)

1. Añadir `solicitante_nombre` y `solicitante_apellido` a `ReservaEspacioResponse` como campos condicionales: administradores con jurisdicción los reciben; respuestas del dueño omiten ambas claves (no se serializan como `null`); disponibilidad nunca las incluye.
2. Completar la condición en `GET /reservas`, `POST /reservas` y `PATCH /reservas/{id}/estado`: el dueño que crea o cambia el estado de su reserva conserva su respuesta sin `solicitante_*`; toda respuesta administrativa a una reserva devuelve ambos datos.
3. Resolver los nombres con `users.datos_publicos_por_ids`: una llamada por lote de IDs únicos en `GET /reservas`, no N consultas; las respuestas unitarias administrativas usan la misma interfaz pública.
4. Ajustar el mapper/UI de la bandeja administrativa y pruebas para privacidad por sede, exclusión para el dueño y ausencia de DNI, email y teléfono.

**Dependencia:** `users.datos_publicos_por_ids` ya está publicado (docs/perfiles.md §5, K1). Sin migración esperada.

**Trabajo frontend RES-02, incorporado a esta fase sin crear una fase nueva:** antes de enviar, unir cada serie de franjas contiguas en una reserva; cada serie no contigua se envía por separado, con confirmación previa y manejo de errores parciales. Las horas con `Pendiente` ajena permanecen seleccionables conforme a RN-S02; la aprobación manual sigue siendo el único bloqueo final.

### Fase 2 — Parámetros operativos por sede (K10/H1)

1. Depender de que la Fase A de SPEC-09 esté en Backend `develop`; SPEC-09 permanece en `BORRADOR`, por lo que la integración aún no está disponible. No reabrir el acuerdo de claves con Perfil 1. El borrador define el contrato de `config.service.datos_de_sede(db, sede)` y `datos_de_sedes(db)` (§4.4; H1).
2. Actualizar `spaces` para consumir `datos_de_sede(db, espacio.sede)` en la validación del horario y el cálculo de disponibilidad.
3. Actualizar frontend para obtener las sedes con `GET /api/v1/config/sedes` y presentar el horario/correo de la sede ante `ANTICIPACION_INSUFICIENTE`, conforme a SPEC-09 §4.5 y H1.
4. Mantener el límite máximo de 120 días y manejar de forma clara la discrepancia actual entre la navegación mensual del frontend y el límite de servidor.

**Dependencia:** Cuando la Fase A de SPEC-09 esté en Backend `develop`; K10/H1; ERS GLO-02, GLO-03, ADR-022. Este plan no modifica `config`.

### Fase 3 — Reversión de bloqueos (GLO-04)

1. Presentar para decisión D-S01…D-S03: se recomienda baja lógica (`revertido_en`, `revertido_por`) en lugar de `DELETE`, porque GLO-04 precisa preservar quién creó el bloqueo, su motivo/intervalo y el historial de disponibilidad (Constitución P7.3).
2. Se recomienda que ADMIN_LOCAL revierta bloqueos individuales sólo dentro de su sede; SUPERADMIN puede revertirlos y es el único que puede deshacer un bloqueo general. Para la fila de grupo que ADMIN_LOCAL no puede revertir, responder `403 PERMISO_INSUFICIENTE`.
3. Se recomienda `id_grupo UUID NULL` para reunir las filas que crea el bloqueo general. `PATCH /bloqueos/{id}/estado` sobre cualquier fila activa del grupo las revierte juntas en una transacción; se descarta agrupar por fechas/motivo porque no identifica una creación de forma inequívoca.
4. Diseñar `POST /bloqueos/general` para SUPERADMIN, con todas las sedes/espacios, `201` y lista de filas; si no hay espacios, `404 ESPACIOS_NO_ENCONTRADOS`; ante error en cualquier espacio, rollback completo. El PATCH responde `200`, `404 BLOQUEO_NO_ENCONTRADO` para ID ausente y deja estado, fecha y actor de reversión.
5. Si se aprueba `id_grupo`, crear migración Alembic manual y reversible apuntando a la cabeza vigente de `develop` al abrir el PR; verificar una sola cabeza con `alembic heads` (AGENTS.md §6; K11 de MEMORY.md). Registrar `upgrade`/`downgrade` y la política de datos de reversión.
6. Mostrar motivo y estado de los bloqueos; añadir la acción de reversión y confirmación de grupo en el frontend. Sólo los bloqueos activos afectan disponibilidad; las reservas existentes no se alteran implícitamente.

La ruta futura y su payload quedan sujetos a SPEC-08 v1.1.0; la API actual sólo tiene `POST/GET /bloqueos` (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`).

**Orden de integración relacionado:** Backend #32 debe integrarse antes de Frontend #20, que consume sus rutas/contratos. La propuesta de SPEC-08 v1.1.0 no está aprobada; ambos PRs deben alinearse con ella después de la decisión de Facundo, antes de dar por terminados los cambios pendientes.

### Fase 4 — Eventos de notificación (C-N02 / S7)

1. Cuando `crear_notificaciones` esté implementada y disponible, emitir las notificaciones al solicitante al aprobar, rechazar y rechazar solicitudes superpuestas.
2. Emitir `RESERVA_CANCELACION_FORZADA` sólo cuando una acción administrativa cancele efectivamente una reserva por una contingencia.
3. Añadir llamadas dentro de la transacción de `spaces`, sin `commit` propio; probar rollback y que ninguna notificación se envíe si la transición no se confirma.

**Dependencia:** Perfil 5 / SPEC-06 §6.1-§6.2 y C-N02; el contrato admite creación transaccional y notificaciones múltiples.

### Fase 5 — Deuda DT-09 y cierre

1. Mantener `String(20)` y valores existentes hasta una decisión explícita de migración de enums.
2. Si el equipo prioriza DT-09, definir compatibilidad, migración reversible y valores persistidos antes de cambiar el modelo.
3. Ejecutar validaciones backend, frontend y migraciones en entornos adecuados; registrar resultados verdaderos y actualizar la memoria sólo en el alcance autorizado.

**Dependencia:** decisión del equipo (DT-09; docs/perfiles.md §4, Perfil 4).

## 4. Archivos previstos

| Repositorio | Ruta | Cambio futuro | Motivo |
| --- | --- | --- | --- |
| Backend | `app/modules/spaces/models.py` | Modificar si se aprueba D-S01/D-S03 | `revertido_en`, `revertido_por`, `id_grupo`; DT-09 sólo si se aprueba por separado. |
| Backend | `app/modules/spaces/schemas.py` | Modificar | Solicitante administrativo, contrato de reversión y validaciones. |
| Backend | `app/modules/spaces/service.py` | Modificar | K1, K10, GLO-04 y eventos C-N02. |
| Backend | `app/modules/spaces/router.py` | Modificar | Contrato del bloqueo reversible. |
| Backend | `alembic/versions/` | Crear si se aprueba baja lógica/grupo | Migración manual reversible, `down_revision` a la cabeza vigente de `develop`; comprobar `alembic heads`. |
| Backend | `tests/spaces/` | Modificar/crear | Criterios de privacidad, sede, concurrencia, reversión y notificaciones. |
| Frontend | `src/features/spaces/pages/SpacesPage.tsx` | Modificar | Agrupación de solicitudes RES-02, motivo y control administrativo de bloqueos. |
| Frontend | `src/features/spaces/components/CalendarGrid.tsx` | Modificar si el contrato requiere estado/motivo visible | Mostrar el rango y motivo; respetar límites del servidor. |
| Frontend | `src/features/spaces/services/spacesApi.ts` | Modificar | Llamada de reversión y mapeo de campos nuevos. |
| Frontend | `src/features/spaces/types/index.ts` | Modificar | Tipos para solicitante y estado de bloqueo. |
| Frontend | `src/features/spaces/**/*.test.*` | Crear/modificar | Verificación de la UI y los mappers. |

No se prevén dependencias externas nuevas. Las pruebas de integración deben ejecutarse contra PostgreSQL real (Constitución P9; `Backend-PrestaMeDios/README.md:163`).

## 5. Riesgos y coordinación

| Riesgo | Mitigación |
| --- | --- |
| `config` aún usa horario global, pese al ERS por sede | Cuando la Fase A de SPEC-09 esté en Backend `develop`, consumir §4.4-§4.5/H1; no agregar fallbacks. |
| Solicitudes superpuestas deben disparar varias notificaciones atómicas | Usar `crear_notificaciones` en la transacción y probar rollback. |
| Reversión de bloqueos puede afectar calendario y auditoría | Propuesta D-S01…D-S03: baja lógica y grupo explícito; aún requiere aprobación. No asumir cancelación de reservas. |
| PRs abiertos divergen de las recomendaciones propuestas | Revisar Backend #32 antes que Frontend #20 después de la decisión de Facundo: el primero usa borrado físico y agrega una cancelación posterior al inicio contraria a RES-03; el segundo permite seleccionar varias horas sin fusionarlas y bloquea `Pendiente` ajena. |
| Frontend muestra cuatro meses mientras el servidor limita a 120 días | Tratar respuesta del servidor como autoridad y comunicar claramente el límite. |
| Tests locales no disponibles con el checkout actual | No afirmar resultados; configurar PostgreSQL y usar el ref correcto antes del cierre técnico. |
