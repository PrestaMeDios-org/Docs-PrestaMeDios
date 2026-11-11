# PLAN-08 — Espacios y reservas (`spaces`)

> **Estado:** Línea base IMPLEMENTADO (retroactivo, aprobado por el Perfil 1 el 2026-11-11) · Fases 1–5 BORRADOR · **Versión:** 1.0.0 · **Fecha:** 2026-11-11 · **Perfil:** 4
> **Spec:** `specs/08-spaces-espacios-reservas/spec.md` v1.0.0 (línea base IMPLEMENTADO; Fases 1–5 BORRADOR)
> **Alcance:** retrospectivo; documenta el estado de `spaces` y ordena las brechas sin implementar código antes de la aprobación.

## 1. Enfoque

El módulo ya está integrado con autenticación, sede, calendario, reservas y bloqueos (SPEC-02; docs/perfiles.md §4, Perfil 4). Este plan separa la línea base aprobada de las brechas observadas en las Fases 1–5, que siguen en `BORRADOR`: K1 (nombre del solicitante), K10 (parámetros por sede), GLO-04 (reversión de bloqueos), C-N02 (notificaciones) y DT-09 (estados como `ENUM`). La auditoría funcional de Backend fue sobre `origin/develop` `3e85feb`. En Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, `pytest -q tests/spaces tests/test_spaces_migrations.py` dio 58 passed; una primera corrida falló por permisos del rol local de PostgreSQL para crear la base de tests y `btree_gist`, y se corrigió el entorno sin cambios de código.

Las brechas se implementarán tarea por tarea, sólo después de aprobación explícita del spec, con criterios de aceptación y pruebas PostgreSQL reales (Constitución P1, P9; SDD §4 de AGENTS.md).

## 2. Estado actual y brechas

| Área | Estado verificado | Próximo paso |
| --- | --- | --- |
| Modelos e integridad temporal | `Espacio`, `ReservaEspacio`, `BloqueoEspacio`; exclusión GIST en reservas aprobadas/en uso (`Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`). | Mantener garantía concurrente y revisar en aprobación la ausencia de `CHECK` de base para rangos. |
| API y permisos | Rutas de espacios, reservas, estados, bloqueos y disponibilidad; sesión obligatoria y alcance por rol/sede (`Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:111-121,163-168,183-186,238-280`). | Extender los contratos dentro del módulo `spaces` sin aceptar usuario o sede no confiables. |
| Horario y anticipación | Horario global y reglas de anticipación/ventana desde `config` (`Backend-PrestaMeDios/app/modules/spaces/service.py:99-104,190-213`). | Consumir SPEC-09 §4.4-§4.5/H1 cuando la Fase A esté en Backend `develop`; ya no requiere acordar claves con Perfil 1. |
| Datos del solicitante | La respuesta actual no incluye nombre/apellido (`Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99`); `users.datos_publicos_por_ids` está disponible (docs/perfiles.md §5, K1). | Completar K1 sólo para consultas administrativas. |
| Bloqueos | Crear/listar; bloques completos o parciales; no pueden pisar reservas activas (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`; `Backend-PrestaMeDios/app/modules/spaces/service.py:375-405`). | En SPEC-08 v1.1.0, decidir baja lógica vs. DELETE físico y política de bloqueos generales con Backend #32 / Frontend #20. No decidir ahora si se conserva el historial. |
| Notificaciones | `spaces` no invoca `notifications`; SPEC-06 publica los eventos y `crear_notificaciones` (SPEC-06 §6.1-§6.2, C-N02) (`Backend-PrestaMeDios/app/modules/spaces/service.py:307-405`). | Atender C-N02 cuando la función esté disponible en el backend. |
| Frontend | Calendario mensual, solicitudes propias, bandeja administrativa, alta de espacios y creación de bloqueos (`Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,240-281,287-327,482-681`). | Añadir visualización de motivo y acción para revertir bloqueos; preservar el alcance de sede al cambiar de contexto. |
| Validación de pruebas | Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, `pytest -q tests/spaces tests/test_spaces_migrations.py`: 58 passed (22.39 s). Una primera corrida falló por permisos insuficientes del rol local de PostgreSQL para crear la base de tests y `btree_gist`; se corrigió el entorno sin cambios de código. | Resultado vigente: suite Backend completa. |

## 3. Fases y dependencias

### Fase 0 — Verificación retrospectiva

Verificar requisitos, API, modelos, frontend, tests existentes y discrepancias. Esta fase se completa sólo como auditoría documental; no es evidencia de tests ejecutados.

### Fase 1 — Privacidad y nombre del solicitante (K1)

1. Añadir a la respuesta de reserva los datos públicos mínimos (`id`, `nombre`, `apellido`) mediante la función pública de `users`.
2. Incluir el resumen sólo en respuestas a administradores con jurisdicción; no en disponibilidad ni en respuestas del usuario común.
3. Ajustar el mapper/UI de la bandeja administrativa y pruebas para privacidad por sede y ausencia de DNI, email y teléfono.

**Dependencia:** `users.datos_publicos_por_ids` ya está publicado (docs/perfiles.md §5, K1). Sin migración esperada.

### Fase 2 — Parámetros operativos por sede (K10/H1)

1. Depender de que la Fase A de SPEC-09 esté en Backend `develop`; SPEC-09 permanece en `BORRADOR`, por lo que la integración aún no está disponible. No reabrir el acuerdo de claves con Perfil 1. El borrador define el contrato de `config.service.datos_de_sede(db, sede)` y `datos_de_sedes(db)` (§4.4; H1).
2. Actualizar `spaces` para consumir `datos_de_sede(db, espacio.sede)` en la validación del horario y el cálculo de disponibilidad.
3. Actualizar frontend para obtener las sedes con `GET /api/v1/config/sedes` y presentar el horario/correo de la sede ante `ANTICIPACION_INSUFICIENTE`, conforme a SPEC-09 §4.5 y H1.
4. Mantener el límite máximo de 120 días y manejar de forma clara la discrepancia actual entre la navegación mensual del frontend y el límite de servidor.

**Dependencia:** Cuando la Fase A de SPEC-09 esté en Backend `develop`; K10/H1; ERS GLO-02, GLO-03, ADR-022. Este plan no modifica `config`.

### Fase 3 — Reversión de bloqueos (GLO-04)

1. En SPEC-08 v1.1.0, decidir baja lógica frente a DELETE físico y la política para bloqueos generales, coordinando con Backend #32 y Frontend #20. Esta v1.0.0 no decide si el historial se conserva o elimina; respetar P7.3 al resolverlo.
2. Tras esa decisión, agregar el contrato administrativo de reversión y definir si hace falta cambiar la persistencia y su migración.
3. Mostrar motivo y estado del bloqueo en el calendario; añadir la acción de revertir con autorización por sede.
4. Verificar que, revertido el bloqueo, el intervalo vuelva a ofrecerse sólo si no hay reserva adjudicada ni otro bloqueo activo.

La ruta futura y su payload quedan sujetos a SPEC-08 v1.1.0; la API actual sólo tiene `POST/GET /bloqueos` (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`).

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
| Backend | `app/modules/spaces/models.py` | Cambio condicionado | Reversión persistente de bloqueos; DT-09 sólo si se aprueba. |
| Backend | `app/modules/spaces/schemas.py` | Modificar | Solicitante administrativo, contrato de reversión y validaciones. |
| Backend | `app/modules/spaces/service.py` | Modificar | K1, K10, GLO-04 y eventos C-N02. |
| Backend | `app/modules/spaces/router.py` | Modificar | Contrato del bloqueo reversible. |
| Backend | `alembic/versions/` | Crear sólo si el diseño cambia el esquema | Migración reversible sobre la cabeza vigente, coordinada con el equipo. |
| Backend | `tests/spaces/` | Modificar/crear | Criterios de privacidad, sede, concurrencia, reversión y notificaciones. |
| Frontend | `src/features/spaces/pages/SpacesPage.tsx` | Modificar | Aviso, motivo y control administrativo de bloqueos. |
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
| Reversión de bloqueos puede afectar calendario y auditoría | Dejar baja lógica vs. DELETE físico y política de bloqueos generales para SPEC-08 v1.1.0, coordinado con Backend #32 y Frontend #20; no asumir cancelación de reservas. |
| Frontend muestra cuatro meses mientras el servidor limita a 120 días | Tratar respuesta del servidor como autoridad y comunicar claramente el límite. |
| Tests locales no disponibles con el checkout actual | No afirmar resultados; configurar PostgreSQL y usar el ref correcto antes del cierre técnico. |
