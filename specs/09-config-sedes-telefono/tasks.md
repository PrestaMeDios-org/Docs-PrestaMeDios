# TASKS-09 — Horario y correo de contacto por sede, y teléfono obligatorio

> **Spec:** `specs/09-config-sedes-telefono/spec.md` v1.0.0 (`APROBADO` el 2026-11-11) · **Plan:** `specs/09-config-sedes-telefono/plan.md` v1.0.0 (`APROBADO` el 2026-11-11) · **Estado:** `EN CURSO` (Fase A mergeada: backend PR #35, frontend PR #26; Fase B en revisión: backend PR #38, frontend PR #27; resta cerrar con C-01)
> Marcar `[x]` al cerrar. Cada tarea tiene su verificación; no se pasa a la siguiente con tests en rojo. Cada bloque es un PR (plan §2). **Orden de merge: A antes que B (D-12).**
> Comandos de backend desde `Backend-PrestaMeDios/` (venv activo, `TEST_DATABASE_URL` definida); de frontend desde `Frontend-PrestaMeDios/`.

---

## Bloque 0 — Preparación

- [x] **T-00 · Documentación de la aprobación.** Registrar (el Docs PR #29 ya está mergeado) en `MEMORY.md` lo de plan §7, fila "Al aprobar el spec": ADR, las dos DT nuevas, H1…H4 en §5 y las preguntas de spec §10.1 en §6.
  *Verificación:* PR a `Docs-PrestaMeDios` sin conflictos con `main`.
  ✔ 2026-11-11: ADR-025, DT-33, DT-34, H1…H3 en §5 y las preguntas en §6 de `MEMORY.md`, en el Docs PR #31 (rama `docs/spec-09-revision`, con `main` integrado).
- [x] **T-01 · Línea base.** `develop` actualizado en backend y frontend; `pytest -q`, `alembic heads` (una sola cabeza); `npm run typecheck`, `npm run build` y `npm test`.
  *Verificación:* resultados anotados en el PR del bloque A; si algo falla de entrada, se informa antes de seguir.
  ✔ 2026-11-11 (backend): `develop` `e54ad16`, 895 pasados (Python 3.12.3, PostgreSQL), una sola cabeza (`0015_users_recuperacion`). Frontend: `develop` `f313433`, typecheck y build limpios, 157 tests de Vitest.

## Bloque A — Configuración por sede (backend `feat/config-sedes`)

- [x] **A-01 · Migración y semilla.** `0017_config_sedes.py` con las constantes congeladas, el upgrade y el downgrade de plan §4.2; `seed.py` con el estado posterior; `test_semilla.py` reconstruye lo esperado desde `0005` y `0017` e incluye AC-109.
  *Verificación:* `pytest tests/config/test_semilla.py -q` en verde; `alembic upgrade head` → `downgrade -1` → `upgrade head` sobre la base de desarrollo; `alembic heads` con una sola cabeza. *Cubre:* AC-109.
  ✔ 2026-11-11: `0017_config_sedes` copia el valor vigente con `INSERT … SELECT` (falla si falta la global) y marca las obsoletas con `PREFIJO_OBSOLETA`; `seed.py` suma `editable` (`NotRequired`). Ciclo real sobre la base de desarrollo: con el cierre global en `20:00`, las dos sedes copiaron `20:00` (D-03).
- [x] **A-02 · Tests de la migración.** `tests/config/test_migracion_0017.py`: valores copiados del horario vigente (con `horario.apertura` en `08:30` antes de migrar), correos en `""`, globales no editables con el prefijo, y el ciclo upgrade → downgrade → upgrade.
  *Verificación:* en verde. *Cubre:* AC-102, AC-112 y la parte de migración de AC-103.
  ✔ 2026-11-11: la migración se corre de verdad sobre PostgreSQL con un `Operations` de Alembic ligado a la sesión (no con mocks), partiendo del estado previo a `0017`; 5 tests.
- [x] **A-03 · Tests del servicio y del endpoint primero.** `tests/config/test_sedes.py` con AC-103 (`PUT` → `409`), AC-104…AC-108, AC-110 y AC-111, anotados con `# AC-NN`.
  *Verificación:* fallan por lo que falta (`ImportError` de `datos_de_sede`, `404` de `/sedes`, reglas por sede ausentes), no por errores del test.
  ✔ 2026-11-11: `tests/config/test_sedes.py`; fallaban por `ImportError`. Los tres casos de AC-28 de `test_parametros.py` que editaban el horario global pasan a las claves por sede.
- [x] **A-04 · Reglas por sede y validación del correo.** `SEGMENTO_SEDE` y sus helpers, pares por sede en `_REGLAS_CRUZADAS`, validación y normalización de `contacto.*.email` (plan §4.3).
  *Verificación:* AC-104, AC-105 y AC-107 en verde. *Cubre:* RN-78, RN-79 (sin el bloqueo), RN-80.
  ✔ 2026-11-11.
- [x] **A-05 · Bloqueo del par (G-5).** `_claves_vinculadas` y la consulta única ordenada por clave con `FOR UPDATE` en `actualizar` (plan §4.3).
  *Verificación:* AC-106 en verde en los dos órdenes y también sobre un par global; `tests/config/test_parametros.py` completo en verde. *Cubre:* RN-79, EC-53.
  ✔ 2026-11-11: AC-106 retiene cada edición después de validar hasta que la otra valide. Con el bloqueo anterior (sólo la fila editada) los tres casos fallan, incluido el par global de plazos; con el nuevo pasan.
- [x] **A-06 · Lectura pública.** `DatosSede`, `datos_de_sede` y `datos_de_sedes` en la sección "API pública para otros módulos".
  *Verificación:* AC-108 en verde (una consulta, sin `commit`, `None` con `""`, `500` sin una clave). *Cubre:* RN-82, NFR-24.
  ✔ 2026-11-11.
- [x] **A-07 · Endpoint.** `DatosSedeResponse` y `GET /api/v1/config/sedes` con `get_current_user`.
  *Verificación:* AC-110 y AC-111 en verde; el endpoint aparece en `/docs`. *Cubre:* RN-83, RN-85.
  ✔ 2026-11-11.
- [x] **A-08 · Cierre del backend A.** `pytest -q` completo; cobertura de lo nuevo de `config` ≥ 85 %; README del backend; PR hacia `develop` con la trazabilidad de spec §12.
  *Verificación:* suite en verde; `alembic heads` con una sola cabeza después del rebase (plan §8).
  ⏳ 2026-11-11 (en revisión, backend PR #35): `develop` sumó `0016_loans_aval` (PR #34), así que la rama se rebasó y `0017` cuelga de `0016`; una sola cabeza. 938 pasados sobre `develop` `03e7ff9`; cobertura de `app/modules/config` 99 % (lo nuevo, entero). README actualizado.
  ✔ 2026-11-11: **backend PR #35 mergeado en `develop`** (`068e8f7`).

## Bloque A-F — Configuración por sede (frontend `feat/config-sedes`)

- [x] **AF-01 · Cliente.** `DatosSedeDTO`, *view model* y `obtenerDatosSedes()` en `features/config`, con su test de Vitest.
  *Verificación:* `npm test` en verde.
  ✔ 2026-11-11: `DatosSedeDTO`, `DatosSede` y `aDatosSede` (`services/mappers.ts`); `obtenerDatosSedes()`, `esCorreoContacto` y `correoValido` en `configApi.ts`, con `configApi.test.ts` (3 tests).
- [x] **AF-02 · Panel de parámetros.** Campo de email para `contacto.*.email`, "Sin configurar" con `""`, obsoletas sin edición.
  *Verificación:* recorrido manual contra el backend A como `SUPERADMIN` y como `ADMIN_LOCAL`. *Cubre:* AC-120.
  ✔ 2026-11-11: recorrido como `SUPERADMIN` contra el backend PR #35 con la base en `0017`: claves por sede, globales sin "Editar", correo inválido marcado y sin poder guardar, `Lab.RG@Example.com` guardado como `lab.rg@example.com` (versión 2, historial "Sin configurar → …"). El borde de error usa `useInputStyle(invalido)`; la primera versión mezclaba `borderColor` con `border` y React lo advertía. No se recorrió como `ADMIN_LOCAL`: lo cubre AC-111 en el backend y el panel ya ocultaba "Editar" a quien no es `SUPERADMIN`.
- [x] **AF-03 · Cierre del frontend A.** `npm run typecheck`, `npm run build` y `npm test`; PR hacia `develop` después del merge del backend A.
  *Verificación:* en verde. *Cubre:* AC-122 (parte A).
  ⏳ 2026-11-11 (en revisión, frontend PR #26, rebasado sobre `develop` `2854caf`): typecheck, build y 160 tests en verde. Se mergea después del backend PR #35.
  ✔ 2026-11-11: **frontend PR #26 mergeado en `develop`** (`6ae5db4`).
- [x] **AF-04 · Avisos de la Fase A.** Lo de plan §7, fila "Fase A mergeada": H1…H3 a los Perfiles 3, 4 y 5, con el pedido de priorizar H1 y H2 porque Ushuaia va a extender su horario.
  *Verificación:* PR a `Docs-PrestaMeDios`; los avisos quedan en `MEMORY.md` §5.
  ✔ 2026-11-12: aviso en `MEMORY.md` §5 con el contrato de `datos_de_sede` y `obtenerDatosSedes`; la fila de H1…H3 del 2026-11-11 pasa a "la Fase A ya está en `develop`"; interfaz en `docs/perfiles.md` §5 (v1.3.0) y estado en `AGENTS.md` §3.

## Bloque B — Teléfono obligatorio (backend `feat/users-telefono`)

- [x] **B-01 · Ajustar los tests existentes.** Sumar un teléfono válido a todos los cuerpos de registro y de alta en `tests/` (plan §5.3), con los esquemas todavía sin cambiar.
  *Verificación:* `pytest -q` en verde, sin cambios en `app/`.
  ✔ 2026-11-11: `test_schemas.py`, `test_estado.py` (alta directa), `test_perfil.py` (alta con cambio obligatorio y CLI) y `test_cli.py`; ningún test fuera de `tests/users/` crea cuentas por la API. 230 pasados en `tests/users/` sin cambios en `app/`.
- [x] **B-02 · Tests primero.** `tests/users/test_telefono.py` con AC-113…AC-119.
  *Verificación:* fallan los que dependen del cambio (registro sin teléfono → `201` en vez de `422`, etc.); AC-118 ya pasa.
  ✔ 2026-11-11: `tests/users/test_telefono.py`; antes del cambio fallaban 8 y pasaban los 2 esperados (registro con teléfono y AC-118).
- [x] **B-03 · Esquemas y CLI.** `_DatosCuentaBase.telefono` obligatorio; `null` rechazado en `PerfilUpdate` y `UsuarioAdminUpdate`; `--telefono` obligatorio en `crear-superadmin`.
  *Verificación:* AC-113…AC-119 en verde. *Cubre:* RN-86…RN-88, D-11.
  ✔ 2026-11-11: el mensaje "El teléfono no puede quedar vacío." sale de `_TELEFONO_NO_VACIO`; `test_borrar_telefono` (SPEC-02) pasa a `test_no_se_puede_borrar_el_telefono`. 240 pasados en `tests/users/`.
- [ ] **B-04 · Cierre del backend B.** `pytest -q` completo; cobertura de lo nuevo de `users` ≥ 85 %; README del backend y `AGENTS.md` §5 con `--telefono`; PR hacia `develop` después del merge del backend A.
  *Verificación:* suite en verde; `crear-superadmin` probado sin y con `--telefono`.
  ⏳ 2026-11-11 (en revisión, backend PR #38, rebasado sobre `develop` `1c89c53`, que ya trae la Fase A y `0019`): 971 pasados; cobertura de `app/modules/users` 97 % (lo nuevo de `schemas.py`, entero). README con `--telefono`; `AGENTS.md` §5 actualizado en este PR de Docs. Durante la fase falló en `develop` un test de `spaces` (*deadlock* al revertir bloqueos del mismo grupo, PR #32 del Perfil 4); lo corrigió el PR #37 antes de abrir el #38.

## Bloque B-F — Teléfono obligatorio (frontend `feat/users-telefono`)

- [x] **BF-01 · Formularios.** Teléfono obligatorio en el registro y en el alta; no se puede vaciar en Mi perfil ni en la edición administrativa.
  *Verificación:* test de Vitest de la validación; recorrido manual. *Cubre:* AC-121 (parte de formularios).
  ✔ 2026-11-11: `features/users/services/telefono.ts` (`validarTelefono`, `validarCambioTelefono`, `necesitaTelefono`) con 6 tests; `roles.test.ts` suma el caso del teléfono en `validarRegistro`. Recorrido: registro y alta sin teléfono muestran "El teléfono es obligatorio." sin enviar nada; "123" en Mi perfil, el mensaje de formato sin `PATCH`.
- [x] **BF-02 · Aviso.** Aviso no bloqueante en `MainLayout` para las cuentas sin teléfono, con enlace a Mi perfil.
  *Verificación:* con una cuenta sin teléfono el aviso aparece y desaparece al guardarlo. *Cubre:* AC-121 (parte del aviso).
  ✔ 2026-11-11: `AvisoTelefono` en la ranura `aviso` de `MainLayout`. Recorrido con el Superadmin de desarrollo (sin teléfono): el aviso aparece, "Ir a Mi perfil" lleva a la pantalla y al guardar `+54 2901 555123` (`PATCH /auth/me` → 200) desaparece.
- [ ] **BF-03 · Cierre del frontend B.** `npm run typecheck`, `npm run build` y `npm test`; PR hacia `develop` después del merge del backend B.
  *Verificación:* en verde. *Cubre:* AC-122 (parte B).
  ⏳ 2026-11-11 (en revisión, frontend PR #27, rebasado sobre `develop` `6ae5db4`): typecheck, build y 220 tests en verde. Se mergea después del backend PR #38.

## Bloque C — Cierre

- [ ] **C-01 · Cierre de SPEC-09.** Corrida final sobre `develop` con las dos fases; trazabilidad completa en spec §12; spec en `IMPLEMENTADO`; `MEMORY.md` §1, `docs/perfiles.md` y `AGENTS.md` §3 al día.
  *Verificación:* PR a `Docs-PrestaMeDios`.
