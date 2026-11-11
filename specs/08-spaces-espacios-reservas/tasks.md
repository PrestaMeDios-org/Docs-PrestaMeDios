# TASKS-08 — Espacios y reservas (`spaces`)

> **Estado:** `BORRADOR (retroactivo)` · **Versión:** 1.0.0 · **Fecha:** 2026-11-11 · **Perfil:** 4
> **Spec:** `specs/08-spaces-espacios-reservas/spec.md` v1.0.0 (`BORRADOR (retroactivo)`) · **Plan:** `specs/08-spaces-espacios-reservas/plan.md` v1.0.0 (`BORRADOR (retroactivo)`)
> Las tareas nuevas de brechas quedan pendientes de aprobación explícita del spec. Los bloques de código ya implementados se registran por separado abajo; esta revisión sólo modifica documentación.

Leyenda: `[ ]` pendiente · `[~]` bloqueada/en curso · `[x]` completada.

## Auditoría retrospectiva

| ID | Tarea | Verificación | Estado |
| --- | --- | --- | --- |
| **T0.1** | Leer Constitución, `AGENTS.md`, perfiles, ERS y specs que ya cubren `spaces`. | Identificadores estables de Docs en `spec.md` §12. | `[x]` |
| **T0.2** | Contrastar API, modelos, validaciones y tests de Backend. | Auditoría de `origin/develop` (`3e85feb`); evidencia citada en `spec.md` §1.3 y §12. | `[x]` |
| **T0.3** | Contrastar montaje, calendario, servicios, tipos y UI de Frontend. | Auditoría de `origin/develop` (`03ce339`); refs citadas en `spec.md` §1.3 y §12. | `[x]` |
| **T0.4** | Registrar resultado real de pruebas Backend. | Repetición en Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, comando `pytest -q tests/spaces tests/test_spaces_migrations.py`: **58 passed, 0 failed, 0 errors, 0 skipped** en 22.39 s. La primera ejecución había dado 22 passed y 36 errores de setup por conexiones cerradas; la repetición pasó sin cambios de código. | `[x]` |

## Bloques de implementación ya entregados

Estos bloques describen trabajo que ya existe en `origin/develop`; las casillas no significan que se haya implementado en la rama documental actual. La auditoría T0 constituye evidencia y no sustituye este historial de implementación.

| ID | Bloque implementado | Commit / PR verificado | Criterios cubiertos |
| --- | --- | --- | --- |
| **I1** | Modelos iniciales, schemas, API, tablas de reservas/bloqueos y exclusión GIST inicial para reservas `Aprobada`. | Backend `98b2e70` (`feat(spaces): esquemas, modelos, endpoints y migraciones para reservas`); `PrestaMeDios-org/Backend-PrestaMeDios#6`. | RES-01/02/04/05; AC-S02, AC-S04, AC-S07. |
| **I2** | Extensión de exclusión GIST a `En_Uso` e incorporación de `created_at` a bloqueos. | Backend `6a65a9a` (`correcciones`); migraciones `0003` y `0004`. | AC-S04, AC-S13. |
| **I3** | Mejora de cálculo/listado de disponibilidad y manejo de intervalos. | Backend `b4c742a` (`Improve space reservation availability`). | AC-S03, AC-S07, AC-S12. |
| **I4** | Autenticación, alcance por sede, propietario desde token, parámetros de configuración, reglas de disponibilidad y migración de sede/FK usuario. | Backend `cf8e084` (`feat(spaces,inventory,users): integrar seguridad y gestion de cuenta (SPEC-02)`). | SPEC-02 AC-31…AC-39; AC-S01, AC-S02, AC-S03, AC-S05, AC-S06, AC-S07, AC-S12. |
| **I5** | Calendario mensual inicial de espacios. | Frontend `999324eb366f7d605e07db8990f391982e50cecb` (`Agrego calendario interactivo de reserva de espacios v1`). | AC-S01, AC-S11. |
| **I6** | Conexión de las reservas de espacios a la API. | Frontend `79bd91e917696eeb5a87118b4fd3903862a39b8b` (`Connect spaces reservations to API`). | AC-S01, AC-S02, AC-S06, AC-S07, AC-S12. |
| **I7** | Sesión real y alcance de sede aplicados a la app. | Frontend `af81452f80d01930d302bb1ff239a34c51ff5aca` (`feat(auth,users,config): frontend de identidad y sesion real (SPEC-02 §6)`). | AC-S01, AC-S06, AC-S12. |
| **I8** | Formulario administrativo de creación de espacios. | Frontend `e90f98cb084e350ddfd157354f922aa4a134c90c` (`Add space creation form for administrators`). | Alta API trazable a SPEC-02 AC-33; Backend `tests/spaces/test_espacios_reservas.py::test_alta_de_espacio_pre19`. No se identificó test automatizado de este formulario frontend. |

## Tareas posteriores a la aprobación

### Fase 1 — K1: solicitante administrativo

| ID | Tarea | Criterios | Verificación | Estado |
| --- | --- | --- | --- | --- |
| **T1.1** | Completar el contrato `ReservaEspacioResponse` con `DatosPublicosUsuario` opcional, obtenido por `users.datos_publicos_por_ids`. | AC-S09 | Dueño y admin con alcance reciben datos según permisos; UI no ve datos ajenos ni PII adicional. | `[ ]` |
| **T1.2** | Incorporar el resumen en la bandeja de administradores y en el mapper de frontend, no en disponibilidad. | AC-S09, AC-S12 | Tests de contrato, consulta por sede y renderizado de la bandeja. | `[ ]` |

### Fase 2 — K10: horario por sede y aviso

| ID | Tarea | Criterios | Dependencia | Estado |
| --- | --- | --- | --- | --- |
| **T2.1** | Integrar el contrato ya publicado: `config.service.datos_de_sede(db, sede)` para otros módulos y `GET /api/v1/config/sedes` para frontend. | AC-S03 | SPEC-09 Fase A disponible en Backend `develop`; §4.4-§4.5, H1. No requiere acordar claves nuevas con Perfil 1. | `[ ]` |
| **T2.2** | Leer `datos_de_sede(db, espacio.sede)` en la validación del horario y el cálculo de disponibilidad; conservar la zona del laboratorio. | AC-S01, AC-S03, AC-S07 | T2.1 | `[ ]` |
| **T2.3** | Obtener horario/correo por sede desde `GET /api/v1/config/sedes` y mostrar el correo ante `ANTICIPACION_INSUFICIENTE`; no confirmar solicitudes rechazadas. | AC-S03 | T2.1, T2.2; SPEC-09 §4.5/H1 | `[ ]` |
| **T2.4** | Resolver el límite de ventana entre calendario por meses y máximo de 120 días configurado por servidor. | AC-S11 | Contrato actual `CalendarGrid` y `config`. | `[ ]` |

### Fase 3 — GLO-04: reversión del bloqueo

| ID | Tarea | Criterios | Verificación | Estado |
| --- | --- | --- | --- | --- |
| **T3.1** | En SPEC-08 v1.1.0, decidir baja lógica frente a DELETE físico y política para bloqueos generales; no fijar ahora conservación/eliminación de historial. | AC-S08 | Coordinación Backend #32 / Frontend #20; evaluar P7.3 antes de aprobar el diseño. | `[ ]` |
| **T3.2** | Implementar el servicio y endpoint administrativo de reversión que se apruebe, validando sede y autorización. | AC-S07, AC-S08 | `ADMIN_LOCAL` dentro/fuera de sede, `SUPERADMIN`, bloqueo inexistente/revertido y reserva activa. | `[ ]` |
| **T3.3** | Añadir acción en UI y exponer motivo/estado del bloqueo en el calendario. | AC-S08 | Tests del componente y recorrido manual con roles y sedes. | `[ ]` |

### Fase 4 — C-N02: notificaciones de reserva

| ID | Tarea | Criterios | Dependencia | Estado |
| --- | --- | --- | --- | --- |
| **T4.1** | Confirmar que `notifications.crear_notificacion` y `crear_notificaciones` estén disponibles en `develop`. | AC-S10 | SPEC-06 Fase B / Perfil 5. | `[ ]` |
| **T4.2** | Notificar aprobación, rechazo por solapamiento y cancelación administrativa dentro de la transacción de `spaces`. | AC-S10 | T4.1 | `[ ]` |
| **T4.3** | Probar rollback, deduplicación de destinatarios y ausencia de notificaciones ante error de transición. | AC-S10 | PostgreSQL real. | `[ ]` |

### Fase 5 — Integridad y cierre

| ID | Tarea | Criterios | Verificación | Estado |
| --- | --- | --- | --- | --- |
| **T5.1** | Decidir si se resuelve DT-09 y, en tal caso, redactar migración de enum compatible y reversible antes de cambiar modelos. | P7, DT-09 | Aprobación del equipo; upgrade/downgrade/upgrade. | `[ ]` |
| **T5.2** | Revisar y cerrar brechas de integridad temporal identificadas, incluidos límites de rango a nivel PostgreSQL. | AC-S02, AC-S03, AC-S13 | Casos válidos/inválidos y concurrencia contra PostgreSQL. | `[ ]` |
| **T5.3** | Cerrar validación de suites backend/frontend. | AC-S01…AC-S13 | Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`: rerun de `pytest -q tests/spaces tests/test_spaces_migrations.py`, 58 passed, 0 failed, 0 errors, 0 skipped en 22.39 s. Frontend `develop` `8cbc76a5ccee77211abb1ca9dacfd1d5e551beb6`: `npm run build` exitoso; `npm test`: 16 archivos, 126 passed, 0 failed, 0 skipped. Resultados separados del `npm audit`, en `spec.md` §1.3 y §12. | `[x]` |

## Orden y bloqueos

1. T1.1 → T1.2 puede avanzar independientemente de K10, usando la interfaz pública de `users`.
2. T2.1 bloquea T2.2 y T2.3; depende de la Fase A de SPEC-09 ya disponible en Backend `develop`.
3. T3.1 precede cualquier cambio de persistencia/API para GLO-04.
4. T4.1 bloquea T4.2 y T4.3; coordinación C-N02 con Perfil 5.
5. T5.1 requiere decisión del equipo; no se agrupa automáticamente con GLO-04.
6. La validación Backend/Frontend de T5.3 pasó en su repetición; la primera ejecución Backend con errores de conexión queda documentada como antecedente. No se hicieron reparaciones de código.
