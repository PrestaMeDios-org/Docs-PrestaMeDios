# PLAN-08 — Espacios y reservas (`spaces`)

> **Estado:** `BORRADOR (retroactivo)` · **Versión:** 1.0.0 · **Fecha:** 2026-11-11 · **Perfil:** 4
> **Spec:** `specs/08-spaces-espacios-reservas/spec.md` v1.0.0 (`BORRADOR (retroactivo)`)
> **Alcance:** retrospectivo; documenta el estado de `spaces` y ordena las brechas sin implementar código antes de la aprobación.

## 1. Enfoque

El módulo ya está integrado con autenticación, sede, calendario, reservas y bloqueos (SPEC-02; `docs/perfiles.md:170-173`). Este plan separa esa línea base de las brechas observadas en los requisitos revisados del ERS: K1 (nombre del solicitante), K10 (parámetros por sede), GLO-04 (reversión de bloqueos), C-N02 (notificaciones) y DT-09 (estados como `ENUM`). La auditoría de Backend fue sobre `origin/develop` `3e85feb`; el checkout local estaba en `e5d0b29`, y no se ejecutaron tests.

Las brechas se implementarán tarea por tarea, sólo después de aprobación explícita del spec, con criterios de aceptación y pruebas PostgreSQL reales (Constitución P1 y P9, `docs/constitution.md:18-25,77-81`; `AGENTS.md:75-82`).

## 2. Estado actual y brechas

| Área | Estado verificado | Próximo paso |
| --- | --- | --- |
| Modelos e integridad temporal | `Espacio`, `ReservaEspacio`, `BloqueoEspacio`; exclusión GIST en reservas aprobadas/en uso (`Backend-PrestaMeDios/app/modules/spaces/models.py:26-112`). | Mantener garantía concurrente y revisar en aprobación la ausencia de `CHECK` de base para rangos. |
| API y permisos | Rutas de espacios, reservas, estados, bloqueos y disponibilidad; sesión obligatoria y alcance por rol/sede (`Backend-PrestaMeDios/app/modules/spaces/router.py:38-176`; `Backend-PrestaMeDios/app/modules/spaces/service.py:111-121,163-168,183-186,238-280`). | Extender los contratos dentro del módulo `spaces` sin aceptar usuario o sede no confiables. |
| Horario y anticipación | Horario global y reglas de anticipación/ventana desde `config` (`Backend-PrestaMeDios/app/modules/spaces/service.py:99-104,190-213`). | Coordinar K10 con Perfil 1; cambiar las lecturas sólo cuando `config` publique parámetros por sede. |
| Datos del solicitante | La respuesta actual no incluye nombre/apellido (`Backend-PrestaMeDios/app/modules/spaces/schemas.py:85-99`); `users.datos_publicos_por_ids` está disponible (`docs/perfiles.md:222`). | Completar K1 sólo para consultas administrativas. |
| Bloqueos | Crear/listar; bloques completos o parciales; no pueden pisar reservas activas (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`; `Backend-PrestaMeDios/app/modules/spaces/service.py:375-405`). | Implementar la reversión GLO-04 sin borrar el historial ni cancelar reservas automáticamente. |
| Notificaciones | `spaces` no invoca `notifications`; la interfaz de SPEC-06 define los eventos y `crear_notificaciones` (`Backend-PrestaMeDios/app/modules/spaces/service.py:307-405`; `specs/06-notifications-comunicaciones/spec.md:148-180,202-204,322-323`). | Atender C-N02 cuando la función esté disponible en el backend. |
| Frontend | Calendario mensual, solicitudes propias, bandeja administrativa, alta de espacios y creación de bloqueos (`Frontend-PrestaMeDios/src/features/spaces/pages/SpacesPage.tsx:65-67,85-122,149-174,240-281,287-327,482-681`). | Añadir visualización de motivo y acción para revertir bloqueos; preservar el alcance de sede al cambiar de contexto. |
| Validación de pruebas | Tests de contrato, integración y migraciones existen en `origin/develop`; no se ejecutaron por checkout distinto y `TEST_DATABASE_URL` unset (`Backend-PrestaMeDios/tests/spaces/test_contratos.py:35-120`; `Backend-PrestaMeDios/tests/spaces/test_espacios_reservas.py:50-417`; `Backend-PrestaMeDios/tests/test_spaces_migrations.py:13-37`). | Ejecutar tras implementación en un checkout `develop` y PostgreSQL configurado. |

## 3. Fases y dependencias

### Fase 0 — Verificación retrospectiva

Verificar requisitos, API, modelos, frontend, tests existentes y discrepancias. Esta fase se completa sólo como auditoría documental; no es evidencia de tests ejecutados.

### Fase 1 — Privacidad y nombre del solicitante (K1)

1. Añadir a la respuesta de reserva los datos públicos mínimos (`id`, `nombre`, `apellido`) mediante la función pública de `users`.
2. Incluir el resumen sólo en respuestas a administradores con jurisdicción; no en disponibilidad ni en respuestas del usuario común.
3. Ajustar el mapper/UI de la bandeja administrativa y pruebas para privacidad por sede y ausencia de DNI, email y teléfono.

**Dependencia:** `users.datos_publicos_por_ids` ya está publicado (`docs/perfiles.md:46,222`; `MEMORY.md:146,149`). Sin migración esperada.

### Fase 2 — Parámetros operativos por sede (K10)

1. Coordinar con Perfil 1 la disponibilidad de horario de apertura/cierre por sede y correo de contacto del laboratorio en `config`.
2. Actualizar el servicio de `spaces` para leer los parámetros de la sede del espacio al validar, calcular disponibilidad y construir el aviso de anticipación.
3. Actualizar calendario y selector de franjas en frontend para reflejar los valores del servidor y mostrar el correo de contacto ante `ANTICIPACION_INSUFICIENTE`.
4. Mantener el límite máximo de 120 días y manejar de forma clara la discrepancia actual entre la navegación mensual del frontend y el límite de servidor.

**Dependencia:** entrega de claves/contratos de Perfil 1 (K10, `MEMORY.md:149,159`; requisitos `docs/ERS.md:272,276,859-864,1226`). Este plan no modifica `config`.

### Fase 3 — Reversión de bloqueos (GLO-04)

1. Aprobar el modelo de reversión: conservar cada bloqueo histórico y hacer que la reversión sea explícita e idempotente; no borrarlo físicamente ni cancelar reservas aprobadas de forma implícita (P7.3 y AC-S08).
2. Agregar el contrato administrativo de reversión y la persistencia necesaria mediante migración reversible si el modelo actual no alcanza.
3. Mostrar motivo y estado del bloqueo en el calendario; añadir la acción de revertir con autorización por sede.
4. Verificar que, revertido el bloqueo, el intervalo vuelva a ofrecerse sólo si no hay reserva adjudicada ni otro bloqueo activo.

La ruta propuesta sigue el patrón `PATCH /<recurso>/{id}/estado`; el nombre del estado y el payload quedan sujetos a aprobación del spec (Constitución §4.2, `docs/constitution.md:115-120`). La API actual sólo tiene `POST/GET /bloqueos` (`Backend-PrestaMeDios/app/modules/spaces/router.py:129-156`).

### Fase 4 — Eventos de notificación (C-N02 / S7)

1. Cuando `crear_notificaciones` esté implementada y disponible, emitir las notificaciones al solicitante al aprobar, rechazar y rechazar solicitudes superpuestas.
2. Emitir `RESERVA_CANCELACION_FORZADA` sólo cuando una acción administrativa cancele efectivamente una reserva por una contingencia.
3. Añadir llamadas dentro de la transacción de `spaces`, sin `commit` propio; probar rollback y que ninguna notificación se envíe si la transición no se confirma.

**Dependencia:** Perfil 5 / SPEC-06 §6.1-6.2 y C-N02; el contrato admite creación transaccional y notificaciones múltiples (`specs/06-notifications-comunicaciones/spec.md:148-180,202-204,322-323`).

### Fase 5 — Deuda DT-09 y cierre

1. Mantener `String(20)` y valores existentes hasta una decisión explícita de migración de enums.
2. Si el equipo prioriza DT-09, definir compatibilidad, migración reversible y valores persistidos antes de cambiar el modelo.
3. Ejecutar validaciones backend, frontend y migraciones en entornos adecuados; registrar resultados verdaderos y actualizar la memoria sólo en el alcance autorizado.

**Dependencia:** decisión del equipo (`MEMORY.md:131`; `docs/perfiles.md:173`).

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

No se prevén dependencias externas nuevas. Las pruebas de integración deben ejecutarse contra PostgreSQL real (Constitución P9, `docs/constitution.md:77-81`; `Backend-PrestaMeDios/README.md:163`).

## 5. Riesgos y coordinación

| Riesgo | Mitigación |
| --- | --- |
| `config` aún usa horario global, pese al ERS por sede | No desplegar un fallback silencioso; coordinar K10 antes de cambiar la regla. |
| Solicitudes superpuestas deben disparar varias notificaciones atómicas | Usar `crear_notificaciones` en la transacción y probar rollback. |
| Reversión de bloqueos puede afectar calendario y auditoría | Conservar el bloqueo como histórico y evitar cancelación implícita de reservas aprobadas. |
| Frontend muestra cuatro meses mientras el servidor limita a 120 días | Tratar respuesta del servidor como autoridad y comunicar claramente el límite. |
| Tests locales no disponibles con el checkout actual | No afirmar resultados; configurar PostgreSQL y usar el ref correcto antes del cierre técnico. |
