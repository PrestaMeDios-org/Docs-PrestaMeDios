# TASKS-08 — Espacios y reservas (`spaces`)

> **Estado:** `BORRADOR` (v1.1.0; pendiente de decisión de Facundo) · línea base v1.0.0 aprobada retroactivamente · **Versión:** 1.1.0 · **Fecha:** 2026-11-11 · **Perfil:** 4
> **Spec:** `specs/08-spaces-espacios-reservas/spec.md` v1.1.0 (`BORRADOR`) · **Plan:** `specs/08-spaces-espacios-reservas/plan.md` v1.1.0 (`BORRADOR`)
> Las tareas de las Fases 1–5 quedan pendientes de aprobación; ninguna casilla significa que los cambios abiertos en Backend #32 o Frontend #20 ya estén integrados. Esta revisión sólo modifica documentación.

Leyenda: `[ ]` pendiente · `[~]` bloqueada/en curso · `[x]` completada.

## Auditoría retrospectiva

| ID | Tarea | Verificación | Estado |
| --- | --- | --- | --- |
| **T0.1** | Leer Constitución, `AGENTS.md`, perfiles, ERS y specs que ya cubren `spaces`. | Identificadores estables de Docs en `spec.md` §12. | `[x]` |
| **T0.2** | Contrastar API, modelos, validaciones y tests de Backend. | Auditoría de `origin/develop` (`3e85feb`); evidencia citada en `spec.md` §1.3 y §12. | `[x]` |
| **T0.3** | Contrastar montaje, calendario, servicios, tipos y UI de Frontend. | Auditoría de `origin/develop` (`03ce339`); refs citadas en `spec.md` §1.3 y §12. | `[x]` |
| **T0.4** | Registrar resultado real de pruebas Backend. | Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`, `pytest -q tests/spaces tests/test_spaces_migrations.py`: **58 passed** en 22.39 s. La primera corrida falló por permisos del rol local de PostgreSQL para crear la base de tests y la extensión `btree_gist`; se corrigió el entorno, sin cambios de código. | `[x]` |

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
| **T1.1** | Completar `ReservaEspacioResponse` y las respuestas de `GET /reservas`, `POST /reservas` y `PATCH /reservas/{id}/estado`: sólo admins con jurisdicción reciben `solicitante_nombre`/`solicitante_apellido`; el dueño omite ambas claves y disponibilidad no las incluye. | AC-S09, AC-S14 | `test_solicitante_solo_admin_con_jurisdiccion_en_reservas`, `test_solicitante_ausente_en_post_y_respuesta_del_dueno`, `test_privacidad_de_reservas`, `test_disponibilidad_intervalos_y_alcance`. No exponer DNI/email/teléfono. | `[ ]` |
| **T1.2** | Completar el enriquecimiento administrativo de `GET /reservas` en lote con `users.datos_publicos_por_ids`; aplicar la misma interfaz pública a respuestas administrativas unitarias, sin N consultas. Ajustar mapper/bandeja. | AC-S09, AC-S14 | `test_datos_publicos_por_ids_se_consultan_en_lote`; tests de contrato para GET y PATCH; test del mapper/bandeja. | `[ ]` |
| **T1.3** | (RES-02, Frontend, sin abrir fase nueva) Consolidar cada serie de horarios contiguos en una reserva; enviar series no contiguas como reservas separadas y conservar sólo las series fallidas para reintento. Mostrar la selección agrupada antes de confirmar. | AC-S17 | Tests propuestos en `src/features/spaces/pages/SpacesPage.test.tsx`: `testAgrupaHorariosContiguos`, `testEnviaCorridasNoContiguasPorSeparado`, `testConservaSoloCorridasFallidasParaReintento`; no se identificó suite automatizada de `spaces` en Frontend #20. | `[ ]` |
| **T1.4** | (RES-02, Frontend, sin abrir fase nueva) Mantener seleccionables las franjas con solicitud `Pendiente` ajena; conservar deshabilitación por pasado, reserva adjudicada y bloqueo activo. No cambiar RN-S02 ni hacer que la UI sustituya la validación del backend. | AC-S18 | Test propuesto `SpacesPage.test.tsx::testPermiteSeleccionarPendienteAjena`; conservar `tests/spaces/test_espacios_reservas.py::TestValidacionesDeCreacion::test_franja_ocupada_y_concurrencia`. | `[ ]` |

### Fase 2 — K10: horario por sede y aviso

| ID | Tarea | Criterios | Dependencia | Estado |
| --- | --- | --- | --- | --- |
| **T2.1** | Cuando la Fase A de SPEC-09 esté en Backend `develop`, integrar el contrato definido: `config.service.datos_de_sede(db, sede)` para otros módulos y `GET /api/v1/config/sedes` para frontend. | AC-S03 | SPEC-09 está en `BORRADOR`; cuando su Fase A esté en Backend `develop`, seguir §4.4-§4.5 y H1. No requiere acordar claves nuevas con Perfil 1. | `[ ]` |
| **T2.2** | Leer `datos_de_sede(db, espacio.sede)` en la validación del horario y el cálculo de disponibilidad; conservar la zona del laboratorio. | AC-S01, AC-S03, AC-S07 | T2.1 | `[ ]` |
| **T2.3** | Obtener horario/correo por sede desde `GET /api/v1/config/sedes` y mostrar el correo ante `ANTICIPACION_INSUFICIENTE`; no confirmar solicitudes rechazadas. | AC-S03 | T2.1, T2.2; SPEC-09 §4.5/H1 | `[ ]` |
| **T2.4** | Resolver el límite de ventana entre calendario por meses y máximo de 120 días configurado por servidor. | AC-S11 | Contrato actual `CalendarGrid` y `config`. | `[ ]` |

### Fase 3 — GLO-04: reversión del bloqueo

| ID | Tarea | Criterios | Verificación | Estado |
| --- | --- | --- | --- | --- |
| **T3.1** | Presentar para decisión D-S01: conservar historial con `revertido_en`/`revertido_por` y `PATCH /bloqueos/{id}/estado`, en vez de `DELETE` físico; justificar por Constitución P7.3 y valor histórico de la contingencia. No ejecutar código antes de aprobación. | AC-S08, AC-S16 | Revisión de alternativas en spec; la opción recomendada no está aprobada. | `[ ]` |
| **T3.2** | Si se aprueba D-S01, agregar estado de reversión a bloqueo, migración Alembic manual y reversible, `down_revision` a cabeza de `develop` y verificación `alembic heads`. | AC-S08, AC-S16 | Test upgrade/downgrade/upgrade; `tests/test_spaces_migrations.py::test_migracion_reversion_bloqueos`; comprobar una sola cabeza. | `[ ]` |
| **T3.3** | Implementar `POST /bloqueos/general` (sólo SUPERADMIN, ambas sedes y todos los espacios) y `PATCH /bloqueos/{id}/estado`; los IDs de grupo usan `id_grupo UUID NULL`, el revertido del grupo es atómico. | AC-S15, AC-S16 | `TestBloqueos::test_bloqueo_general_solo_superadmin_y_en_ambas_sedes`, `::test_bloqueo_general_es_atomico_si_hay_reserva_activa`, `::test_bloqueo_general_sin_espacios`, `::test_reversion_logica_y_alcance`, `::test_admin_local_no_revierte_bloqueo_general`, `::test_revertir_bloqueo_general_revierte_grupo_completo`, `::test_bloqueo_no_encontrado`, `::test_reversion_de_bloqueo_ya_revertido`. | `[ ]` |
| **T3.4** | Mostrar motivo y estado del bloqueo y añadir acción de reversión con confirmación; un bloqueo general se revierte como grupo. Sólo bloqueos activos afectan disponibilidad; no cancelar ni alterar reservas existentes. | AC-S08, AC-S16 | Tests propuestos: `CalendarGrid.test.tsx::testMuestraMotivoYEstadoDeBloqueo`, `SpacesPage.test.tsx::testConfirmaReversionDeBloqueoGeneral`; recorrido manual con ADMIN_LOCAL/SUPERADMIN en ambas sedes. | `[ ]` |

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
| **T5.3** | Cerrar validación de suites backend/frontend. | AC-S01…AC-S13 | Backend `develop` `e54ad16c9dea04eb91473c21e8ceb07e7339c41a`: `pytest -q tests/spaces tests/test_spaces_migrations.py`, 58 passed en 22.39 s. La primera corrida falló por permisos del rol local de PostgreSQL para crear la base de tests y `btree_gist`; se corrigió el entorno sin cambios de código. Frontend `develop` `8cbc76a5ccee77211abb1ca9dacfd1d5e551beb6`: `npm run build` exitoso; `npm test`: 16 archivos, 126 passed. Resultados separados del `npm audit`, en `spec.md` §1.3 y §12. | `[x]` |

## Orden y bloqueos

1. T1.1 → T1.2 puede avanzar independientemente de K10, usando la interfaz pública de `users`.
2. T1.3 y T1.4 son cambios del Frontend #20, incluidos sin crear una fase adicional; se deben ajustar a RES-02/RN-S02.
3. T2.1 bloquea T2.2 y T2.3; depende de que la Fase A de SPEC-09 esté en Backend `develop`.
4. T3.1 precede cualquier cambio de persistencia/API para GLO-04; T3.2/T3.3 requieren decisión explícita de Facundo.
5. Backend #32 debe integrarse antes de Frontend #20, que consume sus rutas/contratos. La recomendación del spec implica ajustar los dos PRs después de la aprobación; no se trataron como integrados.
6. T4.1 bloquea T4.2 y T4.3; coordinación C-N02 con Perfil 5.
7. T5.1 requiere decisión del equipo; no se agrupa automáticamente con GLO-04.
8. La validación Backend/Frontend de T5.3 pasó en su repetición; la primera ejecución Backend con errores de conexión queda documentada como antecedente. No se hicieron reparaciones de código.
