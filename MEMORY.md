# MEMORY.md — Memoria persistente del proyecto PrestaMeDios

> Registro vivo del estado del proyecto, decisiones de arquitectura (ADR), deuda técnica y coordinación entre perfiles. Lo actualizan humanos y agentes de IA al cerrar cada tarea relevante. Entradas nuevas **arriba** dentro de cada sección.

> **Última actualización:** 2026-11-02 · Perfil 1 (orden de documentación y registro de la tercera entrevista)

---

## 1\. Estado actual (snapshot al 2026-11-02)

| Ítem | Valor |
| :---- | :---- |
| Próxima entrega | A confirmar (la entrega parcial del 09/10/2026 ya pasó) |
| Metodología | Scrum (ClickUp) \+ Spec-Driven Development |
| Perfiles | Cinco, según `AGENTS.md` §3 y `docs/perfiles.md` (ADR-017, ADR-018). Desde el 2026-10-23 los perfiles 2–5 reciben la Constitución, `AGENTS.md` y `MEMORY.md` |
| Specs implementados | `spec-01` (v1.0.0), `spec-02` (v1.0.1) y `spec-04` (inventory, v1.0.1, Fase A), los tres mergeados en `develop` (SPEC-04: backend PR \#14, frontend PR \#9, 2026-10-23) |
| Specs en borrador | `spec-05` (`loans`, v0.1.0, Perfil 3, `BORRADOR`). Su §16 tiene pedidos al Perfil 1 (C1–C7, C13) |
| Numeración | `spec-03` queda reservado para el próximo spec del Perfil 1 (responde D-L01 de SPEC-05) |
| Spec siguiente (Perfil 2) | **Fase B de SPEC-04** (disponibilidad por fechas e historial por unidad, INV-26): bloqueada hasta que `loans` publique sus funciones de lectura (ver §5) |
| Spec siguiente (Perfil 1\) | **SPEC-03**, en dos fases. Fase A: API pública de `users` (datos públicos por lote de ids, pedido por los Perfiles 3 y 4). Fase B: USR-02 (recuperación por email), almacenamiento de archivos (foto de perfil USR-03 \+ PDF de aval PRE-05) y refresh token / cookie HttpOnly (a reevaluar frente a ADR-015). Luego USR-06…09, GLO-05 y despliegue (ADR-018). **Alcance nuevo por la entrevista del 16/10 (ADR-022):** horario por sede, teléfono obligatorio, correo de contacto del laboratorio, delegación temporal del rol de Superadministrador, llamados de atención con faltas y suspensión automática (USR-09) y aviso por email de las sanciones |
| Constitución | v1.1.0 vigente, **sin ratificación del equipo registrada**. Enmienda 1.1.1 propuesta (ADR-019 y, desde el 2026-11-02, ADR-021) |
| Ramas backend | `main` \= PR \#8 (2026-10-08, anterior a SPEC-02) · `staging` \= PR \#13 (2026-10-14, incluye SPEC-02 y los contratos de `loans`) · `develop` \= `origin/develop` (`73fb4b9`, 2026-11-02: SPEC-04, refactor de `loans` PR \#16 y ERS fuera del repo PR \#15) |
| Ramas frontend | `main` \= PR \#5 (2026-10-08) · `staging` \= PR \#8 (2026-10-22) · `develop` \= `origin/develop` (`5d72123`, 2026-11-02: SPEC-04 PR \#9 y ERS fuera del repo PR \#10) |
| Entorno local | Python ≥ 3.11 (validado con 3.12) · PostgreSQL local con `btree_gist` · base de tests `prestamedios_test` |

### Backend (`develop`)

| Módulo | Perfil | Estado | Notas |
| :---- | :---- | :---- | :---- |
| `core` | 1 | Implementado | `settings` (`ahora_lab`), `enums` (`SedeEnum`, `RolUsuario`), `errors` (`AppError`), `security` (Argon2id \+ JWT), `deps` (`get_current_user`, `require_roles`, `resolver_alcance_sede`, `sede_para_alta`) |
| `users` | 1 | Implementado | Registro, login, `/auth/me` (GET/PATCH), cambio de contraseña, directorio, alta, edición y estados; CLI `crear-superadmin`. Migraciones `0005`, `0008` |
| `config` | 1 | Implementado | Parámetros con bloqueo optimista e historial; `obtener_parametro()`; 8 claves semilla |
| `inventory` | 2 | Implementado (SPEC-04 Fase A, PR \#14) | Auth, alcance de sede, vista reducida para estudiantes y docentes, edición y baja lógica de equipamiento y unidades, matriz de estados, `service.py` público para `loans`. Migraciones `0006` y `0010`. Falta la Fase B (disponibilidad por fechas e historial por unidad, depende de `loans`) |
| `spaces` | 4 | Implementado | Con auth, alcance de sede y validaciones V1–V8 (SPEC-02); GIST con `tsrange`. Migraciones `0001`–`0004`, `0007` |
| `loans` | 3 | Sólo contratos | Esquemas, modelos, migración `0009` (GIST con `tstzrange`) y 5 endpoints en `/api/v1/loans` que exigen sesión y rol (`get_current_user`, `require_roles`) y responden `501 NO_IMPLEMENTADO` (PR \#16). Sin servicio. Tests de contrato y esquemas en `tests/loans/`. Spec en `BORRADOR` (SPEC-05) |
| `notifications`, `assistant` | 5 | No iniciado |  |
| Tests | — | 320 en verde al 2026-10-23 (con SPEC-04; cobertura de `inventory` 98 %). PR \#16 sumó `tests/loans/`; no se volvió a correr la suite completa después | `loans` sólo tiene tests de contrato y esquemas |

### Frontend (`develop`)

| Feature | Perfil | Estado | Notas |
| :---- | :---- | :---- | :---- |
| `auth`, `users`, `config` | 1 | Implementado | Sesión real (`AuthContext` con `useAuth`/`useSede`), login, registro, perfil, gestión de usuarios, parámetros. Sin rol `icse` |
| `inventory` | 2 | Implementado (SPEC-04 Fase A, PR \#9) | Catálogo conectado a la API, tabla de stock en `admin-stock`, alta, edición, baja lógica y estados (47 tests de frontend en verde). Se montó `StockPage` en `App.tsx` con la conformidad del Perfil 1 |
| `spaces` | 4 | Implementado | Calendario conectado a la API, aprobación, bloqueos y alta de espacios |
| `loans` | 3 | Placeholder | `.gitkeep` |
| Notificaciones | 5 | Maqueta | Campanita con datos fijos en `Navbar.tsx` |

---

## 2\. Decisiones de arquitectura (ADR)

| ID | Fecha | Decisión | Motivo | Estado |
| :---- | :---- | :---- | :---- | :---- |
| ADR-022 | 2026-11-02 | Reglas surgidas de la tercera entrevista (16/10/2026, demo del Sprint 1) y completadas por el equipo, porque el Reglamento no fija cantidades: (a) **horario de atención por sede** (p. ej. Ushuaia 09:00–16:00, Río Grande 10:00–17:00); (b) **teléfono obligatorio** en el registro; (c) **correo de contacto del laboratorio** en el aviso de anticipación mínima; (d) **llamados de atención**: el 1.º y el 2.º no son falta, el 3.º se convierte en una falta; con 1 falta el administrador decide si suspende, con 2 la suspensión es **automática**; (e) la suspensión dura un **tiempo fijo** configurable y el administrador puede levantarla antes; (f) cada llamado de atención o sanción se notifica por **email**; (g) **delegación temporal del rol de Superadministrador**: sólo a un `ADMIN_LOCAL`, con duración fijada al delegar (días, una semana o vacaciones) y revocable antes del vencimiento; (h) la **renovación de notebooks** es presencial y se hace con una **nueva solicitud** desde la app; (i) **docentes** también piden alta gama, con el PDF de la resolución del Consejo (CICSE/ICSE); (j) no hay estudiantes sin DNI argentino (confirma D-03). Las cantidades de (d) y (e) son parámetros de `config` | Validación del Sprint 1 con la referente (ERS, Iteración 5); (d), (e) y (g) los definió el Perfil 1 a falta de reglamento | Vigente — falta reflejarlo en los requisitos del ERS (DT-29) y en los specs |
| ADR-021 | 2026-10-27 | La documentación del proyecto (ERS, Constitución, `AGENTS.md`, `MEMORY.md`, perfiles y specs) se versiona en un repo propio, `Docs-PrestaMeDios`. El ERS pasa de `Backend-PrestaMeDios/docs/ERS.md` a `docs/ERS.md` de ese repo (copia sin historial; el historial anterior queda en el backend) y los cambios de requisitos se hacen por PR ahí | Que todo el equipo versione specs y memoria en un solo lugar, sin mezclarlos con el código. Constitución §1 y §6.1 actualizadas; desde el 2026-11-02 el cambio se somete a ratificación como parte C de la enmienda 1.1.1 (§10.1) | Vigente — pendiente de ratificar con la enmienda 1.1.1 |
| ADR-020 | 2026-10-23 | SPEC-04 (`inventory`): (D-02) `prestado` ya no se puede fijar por la API, sólo `loans` mediante `inventory/service.py`; (D-03) `baja` es terminal; (D-04) estudiantes y docentes reciben una vista reducida del catálogo, sin unidades, series ni códigos de inventario; (D-05) `equipamientos.es_notebook` decide el plazo por defecto (`prestamo.notebook.max_dias`); (D-06) un `ADMIN_LOCAL` edita ítems de su alcance pero sólo el `SUPERADMIN` da de baja un ítem con unidades en ambas sedes; (D-09) `mantenimiento` = "En Mantenimiento" (temporal) y `baja` = "Fuera de servicio" (definitivo); la categoría se filtra en la pantalla. Migración `0010` | Cerrar la doble fuente de verdad del estado de la unidad (DT-20), mínimo dato necesario (P4, P6) y reglas del ERS (PRE-14) | Vigente — aprobado por el Perfil 2 (SPEC-04 `IMPLEMENTADO`, Fase A) |
| ADR-019 | 2026-10-23 | Enmienda 1.1.1 de la Constitución (aclaraciones; desde el 2026-11-02 incluye también la ubicación de la documentación, ADR-021): validaciones previas de solapamiento en el servicio permitidas, con `EXCLUDE` como garantía final para lo adjudicado (P7.2); `Usuario` devuelto por `get_current_user` y funciones de servicio públicas como excepciones explícitas al aislamiento de módulos (P3.3). La propone el Perfil 1 al equipo | El documento de perfiles prohibía literalmente lo que hacen SPEC-02 y `spaces/service.py`, y `core`, `config`, `inventory` y `spaces` ya importan `Usuario` | **Propuesta** — texto en `docs/constitution.md` §10.1 |
| ADR-018 | 2026-10-23 | El Perfil 1 asume USR-06…09, GLO-05, GLO-06 y el despliegue (Docker, CI) | No tenían responsable en `AGENTS.md` | Vigente |
| ADR-017 | 2026-10-23 | La división del trabajo es la de `AGENTS.md` §3: PRE-11, PRE-13 y PRE-15…18 (Módulo 3 del ERS) pertenecen a `loans` (Perfil 3), no al Perfil 2\. El documento externo "Perfiles de tareas v1" se incorpora adaptado como `docs/perfiles.md`, subordinado a `AGENTS.md` | El documento externo asignaba el Módulo 3 completo al Perfil 2 y se contradecía con su propio Perfil 3; el código de `loans` ya implementa PRE-15 y PRE-18 | Vigente |
| ADR-016 | 2026-10-08 | El ERS pasa de `Backend-PrestaMeDios/README.md` a `Backend-PrestaMeDios/docs/ERS.md` (con `git mv`, conserva historial); cada repo tiene un README técnico. Constitución v1.1.0 | El README de un repo debe explicar cómo usarlo; el ERS es el documento académico | Vigente |
| ADR-015 | 2026-10-08 | Token JWT del frontend en `sessionStorage` (SPEC-02 D-06) | Computadoras compartidas del laboratorio: cerrar la pestaña cierra la sesión | Vigente |
| ADR-014 | 2026-10-08 | SPEC-02 se integra a `develop` **después de la demo del 09/10**, backend y frontend juntos, sin flag que desactive la seguridad (D-01) | Proteger endpoints sin el login del frontend rompe la demo; un flag de seguridad suele quedar olvidado | Vigente |
| ADR-013 | 2026-10-07 | Tests de integración: esquema recreado por sesión con `create_all` \+ `TRUNCATE` por test; **una sesión por request** (como en producción) para poder probar concurrencia real. La migración se valida aparte con upgrade/downgrade/upgrade | El rollback por test con una sola conexión impedía probar `FOR UPDATE` y carreras de `UNIQUE` | Vigente |
| ADR-012 | 2026-10-07 | Cobertura con `concurrency = greenlet` (`.coveragerc`) | SQLAlchemy async ejecuta en greenlets; sin esto la cobertura se subestima (\~78 % vs 95 % real) | Vigente |
| ADR-011 | 2026-10-07 | **Anticipación mínima de solicitud \= 24 h** (D-07): "plazos mínimos (24 horas)" del ERS se interpreta como antelación mínima entre el envío de una solicitud (préstamo o reserva) y el inicio del retiro/turno. Parámetro `solicitud.anticipacion_min_horas` (reemplaza a `prestamo.min_horas` del borrador) | Definido por Perfil 1 en la revisión de SPEC-01 | Vigente — lo aplican `loans` y `spaces` |
| ADR-010 | 2026-10-07 | **Cuentas rechazadas se conservan** en estado `RECHAZADO` con motivo obligatorio; se permite re-registro con el mismo email (vuelve a `PENDIENTE_APROBACION`). No hay borrado físico de usuarios (D-04) | Auditoría (USR-08) e integridad del historial. Se modificó el CU "Registro y validación de cuentas" del ERS (`Backend-PrestaMeDios/docs/ERS.md`, ex `README.md`) | Vigente |
| ADR-009 | 2026-10-07 | **Sin restricción de dominio de email** para el registro (D-02); se acepta cualquier email válido | Estudiantes usan correos personales; la validación manual (USR-05) mitiga cuentas falsas | Vigente |
| ADR-008 | 2026-10-07 | Resto de decisiones de SPEC-01: sede como `SedeEnum` textual (D-01); DNI numérico 7–8 (D-03); sólo `SUPERADMIN` edita parámetros (D-05); sólo access token 60 min (D-06); sancionado no inicia sesión (D-08); directorio paginado (D-09) | Ver `specs/01-auth-users/spec.md` §13 | Vigente |
| ADR-007 | 2026-10-07 | Autenticación con JWT HS256 (PyJWT) \+ hash Argon2id (pwdlib); revocación por `token_version` | Librerías mantenidas; revocación inmediata ante sanciones sin lista negra | Vigente (SPEC-01) |
| ADR-006 | 2026-10-07 | Parámetros globales como catálogo cerrado clave-valor tipado (`JSONB`) con bloqueo optimista e historial | GLO-03 sin claves huérfanas; auditable | Vigente (SPEC-01) |
| ADR-005 | 2026-10-07 | Kernel compartido `app/core/` (settings, security, deps, errors, enums) | Evitar que cada módulo reimplemente auth y alcance de sede | Vigente (SPEC-01) |
| ADR-004 | 2026-10-06 | Integridad temporal de reservas con `EXCLUDE USING gist` (requiere `btree_gist`), aplicada a estados `Aprobada` y `En_Uso` | ACID frente a concurrencia, sin lógica en Python | Vigente (`spaces`) |
| ADR-003 | 2026-10-05 | SQLAlchemy 2.0 async \+ asyncpg; `NAMING_CONVENTION` común en `app/database.py` | Nombres de restricciones deterministas para migraciones | Vigente |
| ADR-002 | Iteración 4 | Monolito Modular por Dominio, API-First (FastAPI \+ PostgreSQL; React \+ TS) | Desarrollo en paralelo de 5 integrantes; OpenAPI consumible por el agente MCP | Vigente |
| ADR-001 | Iteración 2–3 | Roles: `SUPERADMIN` (ambas sedes), `ADMIN_LOCAL` (una sede), `DOCENTE`, `ESTUDIANTE`. Se elimina "Administrador ICSE" | Entrevistas con la referente (04/09 y 18–21/09/2026) | Vigente |

---

## 3\. Conocimiento de dominio clave

- **Administradores reales:** Natalia Ader (Superadministradora, ambas sedes), Victoria (Admin Local Ushuaia), Facundo (Admin Local Río Grande).  
- **Aprobación:** el estudiante solicita **directo al administrador**; el docente sólo observa y comenta (PRE-20). Ninguna aprobación es automática.  
- **Plazos reglamentarios:** préstamo general ≤ 4 días; notebooks ≤ 15 días (renovación presencial); préstamos especiales/alta gama requieren PDF de aval (PRE-05).  
- **Horario operativo:** 09:00–16:00 (supervisión presencial obligatoria).  
- **Anticipación mínima:** toda solicitud de préstamo o reserva se envía con al menos 24 h de antelación (configurable, ADR-011).  
- **Registro:** cualquier email válido; la cuenta queda "Pendiente en aprobación" hasta que un administrador con jurisdicción la valida. Un rechazo conserva la cuenta (ADR-010).  
- **Lockers:** numerados 1–7 por sede.  
- **Horario por sede (2026-10-16):** cada sede tiene su propio horario de atención (p. ej. Ushuaia 09:00–16:00, Río Grande 10:00–17:00). Hoy `config` tiene un único `horario.apertura`/`horario.cierre`.
- **Sanciones (ADR-022):** llamado de atención (faltas leves: retrasos, equipos devueltos helados) → al 3.º, una falta → con 1 falta el admin evalúa, con 2 suspensión automática por tiempo fijo, que el admin puede levantar antes. Cada llamado o sanción se avisa por email.
- **Renovación de notebooks:** presencial (se revisa el equipo en el mostrador) y mediante una nueva solicitud en la app, para dar oportunidad a otros solicitantes.
- **Delegación de Superadministrador:** temporal, sólo a un Admin Local, con duración fijada al delegar y revocable antes.
- **Alta gama:** la piden estudiantes y docentes (estos con regularidad); el aval es el PDF de la resolución del Consejo (CICSE/ICSE).
- **Requisito futuro:** Isla de Digitalización de Archivos Físicos (VHS, S-VHS, Beta, Hi8).

---

## 4\. Deuda técnica e inconsistencias detectadas

| ID | Severidad | Descripción | Ubicación | Responsable sugerido |
| :---- | :---- | :---- | :---- | :---- |
| DT-29 | Media | La tercera entrevista (16/10/2026) quedó registrada en el ERS (bibliografía e Iteración 5), pero los textos de USR-05, USR-09, GLO-01, GLO-03, GLO-04, RES-03, PRE-05 y PRE-11 y sus casos de uso todavía no reflejan ADR-022 | `docs/ERS.md` | Perfil 1 (PR al ERS) |
| DT-16 | Alta | **Parcial (2026-11-02):** `specs/05-loans-prestamos/spec.md` existe en `BORRADOR` (v0.1.0). Se cierra cuando el spec esté `APROBADO`. Mientras tanto `loans` no tiene criterios de aceptación aprobados (Constitución P1.1) | `specs/05-loans-prestamos/`, `app/modules/loans/` | Perfil 3 |
| ~~DT-17~~ | — | ~~`loans/dependencies.py` placeholder con `RolEnum` propio y endpoints que respondían 500 sin sesión~~ → **Resuelto 2026-11-02 (PR \#16)**: se eliminó `dependencies.py`; los 5 endpoints usan `get_current_user`/`require_roles(RolUsuario...)` y responden `501 NO_IMPLEMENTADO` con `AppError` | `loans/router.py` | Perfil 3 |
| ~~DT-18~~ | — | ~~Errores `{codigo, detalle}` y `HTTPException` en `loans`~~ → **Resuelto 2026-11-02 (PR \#16)**: `loans` usa `AppError` (`{detail, code}`) | `loans/schemas.py`, `loans/router.py` | Perfil 3 |
| DT-19 | Baja | Tres estilos de valores de enum: `core` en MAYÚSCULAS (`ACTIVO`), `inventory`/`loans` en minúsculas (`disponible`, `pendiente`), `spaces` capitalizados (`Pendiente`). Requiere decisión del equipo antes de unificar | Varios módulos | Equipo |
| DT-20 | Alta | **Parcial (2026-10-23, SPEC-04):** `inventory` publica `service.py` (`unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad`) y rechaza `prestado` por la API. **Pendiente en `loans`:** usar esas funciones y no asignar unidades en `mantenimiento`/`baja`; sigue habiendo dos fuentes (`PRESTADO` en `inventory` frente a `ENTREGADO` en `loans`) hasta que lo adopte | `inventory/service.py`, `loans/` | Perfil 3 |
| DT-26 | Baja | `NAMING_CONVENTION` vuelve a prefijar los nombres de `CheckConstraint` pasados a `create_table` o `op.create_check_constraint`: las bases creadas con Alembic tienen `ck_<tabla>_ck_<tabla>_<x>` y las creadas con `create_all` (tests) `ck_<tabla>_<x>`. Afecta a `0006` y a cualquier migración con `CHECK`. `0010` lo evita con SQL directo y tolera ambos nombres | `alembic/versions/0006_inventory_init.py`, `app/database.py` | Perfil 1 |
| DT-27 | Baja | Un ítem con todas sus unidades en `baja` se ve como "Ocupado" con 0/0 uds. para estudiantes y docentes; SPEC-04 RN-I5 pide "No disponible" | `components/ui/Badge.tsx` (`StatusBadge`), `inventory/pages/CatalogPage.tsx` | Perfil 2 |
| DT-28 | Baja | La prueba de concurrencia a nivel API del cambio de estado (`test_cambios_concurrentes_de_estado`) tiene aserciones laxas y no detectaría una carrera; la serialización con `FOR UPDATE` sí está probada de forma efectiva en `test_service.py` | `tests/inventory/test_gestion.py` | Perfil 2 |
| DT-21 | Media | El `.gitignore` de `origin/main` (backend) no tiene `.coverage` ni `htmlcov/` (sí están en `develop` y `staging`). Se resuelve con el próximo merge `develop` → `main` | `Backend-PrestaMeDios/.gitignore` | Perfil 1 |
| ~~DT-22~~ | — | ~~El catálogo del frontend usa sólo `mockInventory.ts`~~ → **Resuelto 2026-10-23 (SPEC-04)**: el catálogo y la tabla de stock usan la API; el mock se eliminó | `features/inventory/` | Perfil 2 |
| ~~DT-23~~ | — | ~~Locker sólo con `CHECK >= 1`~~ → **Resuelto 2026-10-23 (SPEC-04)**: migración `0010` con `CHECK` entre 1 y 7 (falla con los ids si hay datos fuera de rango) | `inventory/models.py`, `0010` | Perfil 2 |
| ~~DT-24~~ | — | ~~El README del backend decía que `loans` estaba "Pendiente" y sin prefijo~~ → **Resuelto 2026-11-02**: README actualizado (prefijo `/api/v1/loans`, requisitos según ADR-017, estado "contratos, `501`"); la descripción de `app/main.py` ya mencionaba préstamos | `Backend-PrestaMeDios/README.md` | Perfil 1 |
| DT-25 | Baja | IA-02 del ERS decía "acceso de lectura a la base de datos", contra la Arquitectura del propio ERS y la Constitución P2.3. **2026-11-02:** corregido en `docs/ERS.md` (IA-02 y paso 3 del CU del asistente: lectura mediante la API REST con la sesión del usuario); se cierra al mergear el PR con revisión del Perfil 5 | `docs/ERS.md` | Perfil 1 (PR al ERS) |
| ~~DT-01~~ | — | ~~Ningún endpoint exige autenticación~~ → **Resuelto 2026-10-08 (SPEC-02)**: auth transversal en `spaces` e `inventory` | `inventory/`, `spaces/` | Perfil 1 |
| ~~DT-02~~ | — | ~~Doble representación de sede~~ → **Resuelto 2026-10-08 (SPEC-02)**: migración `0007_spaces_sede_y_usuario` unifica en `SedeEnum` | `spaces/` | Perfil 1 |
| ~~DT-03~~ | — | ~~`id_usuario` sin FK y recibido en el body~~ → **Resuelto 2026-10-08 (SPEC-02)**: FK a `usuarios` en migración `0007`; usuario tomado del token | `spaces/` | Perfil 1 |
| ~~DT-04~~ | — | ~~`inventory` sin migración Alembic (500 en base nueva)~~ → **Resuelto 2026-10-07**: migración `0006_inventory_init`, idempotente (omite tablas ya creadas con `create_all`); esquema \= modelos sin diferencias | `alembic/versions/` | Perfil 1 (autorizado) |
| ~~DT-05~~ | — | ~~Carpeta plantilla vacía `specs/001-nombre-spec/`~~ → **Resuelto 2026-10-07**: ya no existe en el workspace | `specs/` | Equipo |
| ~~DT-06~~ | — | ~~Reglas fijas en código~~ → **Resuelto 2026-10-08 (SPEC-02)**: horario de `spaces` y plazo por defecto de `inventory` leídos desde `config` | `spaces/`, `inventory/` | Perfil 1 |
| ~~DT-07~~ | — | ~~`uvicorn.log`/`uvicorn.err` versionados~~ → **Resuelto 2026-10-07**: `git rm --cached` en el commit `7b95956` (siguen en `.gitignore`; el historial anterior los conserva) | Raíz backend | Perfil 1 |
| ~~DT-08~~ | — | ~~No existe `.env.example`~~ → **Resuelto 2026-10-07** | Raíz backend | Perfil 1 |
| DT-09 | Baja | `spaces` usa `str, Enum` y estados como `String(20)`, distinto del patrón `StrEnum` \+ `SAEnum` de `inventory` | `spaces/` | `spaces` |
| ~~DT-10~~ | — | ~~`spaces` no traducía IntegrityError~~ → **Resuelto 2026-10-08 (SPEC-02)**: AppError y manejo de concurrencia en `spaces/service.py` | `spaces/service.py` | Perfil 1 |
| ~~DT-11~~ | — | ~~Título de la app sólo mencionaba inventario~~ → **Resuelto 2026-10-07** ("PrestaMeDios API") | `app/main.py` | Perfil 1 |
| ~~DT-12 (parcial)~~ | Baja | El rol `icse` fue **eliminado** del frontend (SPEC-02 §6). Queda renombrar `figma-make-app` en `package.json` | `package.json` | Frontend |
| ~~DT-13~~ | — | ~~El ERS describía que un rechazo "elimina la petición"~~ → **Resuelto 2026-10-07**: CU actualizado (ADR-010) | `Backend-PrestaMeDios/docs/ERS.md` (ex `README.md`) | Perfil 1 |
| DT-15 | Baja | `app/database.py` lee `DATABASE_URL` por su cuenta y `app/core/settings.py` también (duplicación tolerada para no tocar el engine compartido) | `app/database.py` | Perfil 1 |
| ~~DT-14~~ | — | ~~`spaces` no validaba anticipación mínima de 24 h~~ → **Resuelto 2026-10-08 (SPEC-02)**: V4 en `spaces/service.py` lee `solicitud.anticipacion_min_horas` | `spaces/service.py` | Perfil 1 |

---

## 5\. Coordinación pendiente entre perfiles

| Fecha | De → Para | Pedido | Estado |
| :---- | :---- | :---- | :---- |
| 2026-11-02 | Perfil 1 → Perfil 3 | Entrevista del 16/10 (ADR-022): (a) **la renovación de notebooks contradice SPEC-05**: el spec la plantea como una extensión que hace el administrador (CU-L09, `PATCH …/renovacion`), y la referente pidió que el estudiante presente el equipo y emita **una nueva solicitud** desde la app; corregir el spec antes de aprobarlo; (b) PRE-05: los docentes también piden alta gama y el aval es el PDF de la resolución del Consejo (CICSE/ICSE); (c) el horario pasará a ser por sede (las claves de `config` cambian, se avisa en SPEC-03) | Abierto |
| 2026-11-02 | Perfil 1 → Perfil 4 | Entrevista del 16/10: (a) nombre del solicitante en el calendario maestro, sólo para administradores (confirma el pedido del Perfil 4; hoy la bandeja muestra `Usuario #id`); (b) aviso emergente al fallar la anticipación mínima, con el correo del laboratorio (parámetro nuevo de `config`, lo agrega el Perfil 1); (c) mostrar el motivo al pasar el mouse sobre un día bloqueado; (d) revertir bloqueos (GLO-04, no hay endpoint); (e) el horario pasará a ser por sede | Abierto |
| 2026-11-02 | Perfil 1 → Perfil 5 | Los llamados de atención y sanciones se avisan por email (ADR-022). Definir si los mails salen de `notifications` o de una función de correo de `core` que el Perfil 1 diseña para USR-02 (SPEC-03) | Abierto |
| 2026-11-02 | Perfil 4 → Perfil 1 | `users`: función pública liviana para obtener nombre y apellido por lote de ids, para mostrar el solicitante en la bandeja de reservas sin importar el modelo `Usuario` en `spaces`. Es el mismo pedido que C2 de SPEC-05 (Perfil 3). Se implementa una sola función, `datos_publicos_por_ids(db, ids) -> dict[int, DatosPublicosUsuario]` (`id`, `nombre`, `apellido`), en la Fase A de SPEC-03. Sin filtro de sede: quien llama sólo pasa ids que ya puede mostrar (P6). El campo `solicitante` en `ReservaEspacioResponse` lo documenta y lo implementa el Perfil 4 | Aceptado — pendiente de SPEC-03 Fase A |
| 2026-11-02 | Perfil 1 → Perfil 4 | Publicar en `spaces/service.py` una función de lectura de reservas por usuario, para USR-06 y USR-07 (`docs/perfiles.md` §5) | Abierto |
| 2026-11-02 | Perfil 1 → Perfil 3 | Respuestas a SPEC-05 §16: D-L01 confirmado (`spec-03` reservado para el Perfil 1); C2 entra en SPEC-03 Fase A (función compartida con el pedido del Perfil 4; el vínculo docente–asignatura depende de C3); C4 (archivos) en SPEC-03 Fase B; C6 resuelto (DT-24). Quedan abiertos C1, C3, C5 y C13 | Abierto |
| 2026-10-23 | Perfil 2 → Perfil 1 | **Para revisar y resolver:** SPEC-04 Fase A quedó implementada, así que hay que actualizar los documentos que mantiene el Perfil 1: (a) `docs/perfiles.md` §4 Perfil 2 — backend: edición y baja lógica de equipamiento y unidades, matriz de estados, `inventory/service.py`, `CHECK` de locker 1–7 (migración `0010`); frontend: catálogo conectado a la API (se eliminó el mock), tabla de stock en `admin-stock`, alta, edición y baja; Pendiente: sólo la Fase B (disponibilidad por fechas e historial por unidad). (b) `AGENTS.md` §3, fila del Perfil 2: pasar de "El catálogo del frontend usa datos de ejemplo" a "Implementado (SPEC-04, Fase A); pendiente Fase B". (c) `docs/perfiles.md` §5: la interfaz "Estado de la unidad física" ya tiene el lado de `inventory` publicado | Cerrado 2026-11-02: `AGENTS.md` §3 y `docs/perfiles.md` §4 y §5 actualizados |
| 2026-10-23 | Perfil 2 → Perfil 3 | **Para continuar cuando se avance con `loans`:** retomar la **Fase B de SPEC-04 (INV-26)**, hoy bloqueada. Requiere que `loans` publique: (1) lectura de ocupación por unidad y período, sin identidad de solicitantes (PRE-01); (2) historial de movimientos de una unidad, sólo para administradores con jurisdicción (PRE-12); (3) reservas futuras aprobadas por unidad (PRE-17). Con eso el Perfil 2 implementa `GET /equipamiento/{id}/disponibilidad`, `GET /unidades/{id}/historial`, el campo `reservas_afectadas` al pasar una unidad a mantenimiento y el mini-calendario del detalle (spec §5.4–5.5, plan §8). También queda pendiente definir con el Perfil 1 el parámetro de ventana máxima del calendario (SPEC-04 D-07) y que `loans` adopte `inventory/service.py` (DT-20) | Abierto — retomar al avanzar `loans` |
| 2026-10-23 | Perfil 2 → Perfil 3 | SPEC-04 §6: usar `inventory/service.py` (`unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad`) en vez de escribir el estado de la unidad; no asignar unidades en `mantenimiento` o `baja`. Desde SPEC-04 un admin ya no puede poner `prestado` por la API (D-02) | Abierto |
| 2026-10-23 | Perfil 2 → Perfil 3 | Exponer funciones públicas de lectura, sin identidad salvo para admins: (a) ocupación por unidad y período (PRE-01), (b) historial de movimientos de una unidad (PRE-12), (c) reservas futuras aprobadas por unidad (PRE-17). Bloquean la Fase B de SPEC-04. PRE-17 (cancelación forzada al pasar a mantenimiento) se resuelve en el spec de `loans` | Abierto |
| 2026-10-23 | Perfil 2 → Perfil 1 | `config`: (a) parámetro de ventana máxima del calendario de disponibilidad (SPEC-04 D-07, Fase B); (b) el `CHECK` de `equipamientos.max_dias_prestamo` fija el tope 15 en la base (P8), evaluar si se parametriza | Abierto |
| 2026-10-23 | Perfil 2 → Perfil 5 | Para consultas de stock y disponibilidad, el asistente usa `GET /api/v1/inventory/equipamiento` (respuesta reducida para no admins, SPEC-04 RN-I7); no hay endpoints especiales para IA | Informativo |
| 2026-10-23 | Perfil 1 → Perfil 2 | Confirmado: el Perfil 2 puede modificar `src/App.tsx` para montar `StockPage` en `admin-stock` (cambio mínimo, SPEC-04 F-06) → **Completado 2026-10-23** (3 líneas en `App.tsx`) | Cerrado |
| 2026-10-23 | Perfil 1 → Perfiles 2–5 | Compartir con cada integrante (y su agente) `docs/constitution.md`, `AGENTS.md`, `MEMORY.md` y `docs/perfiles.md`; trabajar con spec aprobado en `specs/` | Abierto |
| 2026-10-23 | Perfil 1 → Perfil 3 | Redactar el spec de `loans` cubriendo lo ya hecho y resolviendo DT-16…DT-18 (usar `get_current_user`, `RolUsuario`, `AppError`); hasta tener la lógica, proteger los endpoints o quitar el router → **Parcial 2026-11-02**: endpoints protegidos con `501` (PR \#16) y SPEC-05 en `BORRADOR`; falta su aprobación | Abierto |
| 2026-10-23 | Perfil 1 → Perfiles 2 y 3 | Acordar en el spec de `loans` la interfaz de estado y disponibilidad de unidades (DT-20, PRE-01, PRE-13, PRE-14) | Abierto |
| 2026-10-23 | Perfil 1 → Perfil 2 | Conectar el catálogo a la API (DT-22) y agregar el `CHECK` de locker 1–7 (DT-23) → **Completado 2026-10-23 (SPEC-04, Fase A)** | Cerrado |
| 2026-10-23 | Perfil 1 → Perfiles 3 y 4 | Exponer funciones de lectura de solicitudes por usuario para USR-06…08 (`docs/perfiles.md` §5) | Abierto |
| 2026-10-23 | Perfil 1 → Perfil 5 | Definir en el spec de `notifications` la función pública que llamarán `loans` y `spaces`; el asistente sólo consume REST | Abierto |
| 2026-10-07 | Perfil 1 → `spaces` | Migrar `id_sede` a `SedeEnum`; FK `id_usuario`; tomar usuario del token; leer horario y anticipación → **Completado 2026-10-08 (SPEC-02)** en `feat/spec-02-integracion` | Cerrado |
| 2026-10-07 | Perfil 1 → `loans` | Validar anticipación mínima con `solicitud.anticipacion_min_horas` y plazos con `prestamo.*.max_dias` | Abierto |
| 2026-10-07 | Perfil 1 → `inventory` | `SedeEnum`, migración `0006`, `require_roles`, sede automática PRE-19 y plazo por defecto desde config → **Completado 2026-10-08 (SPEC-02)** en `feat/spec-02-integracion` | Cerrado |
| 2026-10-07 | Perfil 1 → Frontend | DTOs espejo, sin `icse`, `AuthContext`, `SedeContext`, `lib/api.ts` con token y pantallas de identidad → **Completado 2026-10-08 (SPEC-02)** en `feat/login-auth-ui` | Cerrado |

---

## 6\. Preguntas abiertas para la referente (Natalia Ader)

1. ¿La anticipación mínima de 24 h aplica también a los **docentes**? (ADR-011 asume que sí; la entrevista del 16/10 sólo lo confirmó para estudiantes, en préstamos y reservas de espacios)
2. Sanciones (ADR-022): ¿el contador de llamados de atención vuelve a cero al convertirse en falta (cada 3 llamados, 1 falta)? ¿Las faltas vencen (por ejemplo, por cuatrimestre)? ¿Cuántos días dura la suspensión por defecto?

> Resueltas el 2026-11-02 (entrevista del 16/10 y definiciones del equipo, ADR-022): no hay estudiantes sin DNI argentino (D-03 confirmada); el usuario suspendido no inicia sesión y ve "Tu cuenta está suspendida" (D-08 confirmada); la anticipación de 24 h aplica a las reservas de espacios de estudiantes.

> Resueltas internamente el 2026-10-07: dominio de email (D-02 → sin restricción) e interpretación de las 24 h (D-07 → anticipación mínima).

---

## 7\. Bitácora

| Fecha | Autor | Evento |
| :---- | :---- | :---- |
| 2026-11-02 | Perfil 1 | Registro de la **tercera entrevista con la referente** (16/10/2026, demo del Sprint 1), con asistencia de IA: ERS (bibliografía e Iteración 5), ADR-022 con las reglas validadas y las que completó el equipo (sanciones, delegación temporal), conocimiento de dominio, DT-29, coordinación con los Perfiles 3, 4 y 5 y preguntas de §6 actualizadas |
| 2026-11-02 | Perfil 1 | Orden de documentación (con asistencia de IA): snapshot al día con `develop` (SPEC-04 mergeado, PR \#16 de `loans`, ERS fuera de los repos de código, SPEC-05 en `BORRADOR`); DT-17, DT-18 y DT-24 cerradas, DT-16 y DT-25 parciales; `AGENTS.md` §3 y `docs/perfiles.md` §4–§5 actualizados; ADR-021 sumado a la enmienda 1.1.1 como parte C; IA-02 del ERS corregido (DT-25); pedido del Perfil 4 (datos públicos de usuarios) aceptado para SPEC-03 Fase A |
| 2026-10-27 | Perfil 1 | Reorganización de `specs/` (con asistencia de IA): una carpeta por spec, `specs/NN-<slug>/{spec,plan,tasks}.md`, en lugar de `specs/{spec,plan,tasks}-NN-<slug>.md`. Referencias actualizadas en `AGENTS.md`, `docs/constitution.md` §6, `docs/perfiles.md`, este archivo y los propios specs. Los identificadores cortos (`spec-01`, `plan-02` §6) se mantienen como nombres. Además, la documentación (`AGENTS.md`, `MEMORY.md`, `docs/`, `specs/`) pasa a un repo propio, `Docs-PrestaMeDios`, clonado junto a Backend y Frontend; la raíz del workspace lleva copias de `workspace/` (`CLAUDE.md` con `@` para Claude Code, `opencode.json` con `instructions` para OpenCode y un `AGENTS.md` puntero de respaldo) para que el agente cargue `Docs-PrestaMeDios/AGENTS.md` al iniciar |
| 2026-10-23 | Perfil 2 | **SPEC-04 Fase A implementada** (con asistencia de IA) y publicada por `Farvi-1986` en `feat/inventory-gestion` (backend, `b93017f`) y `feat/inventory-catalogo` (frontend, `128b749`), sin PR todavía; el `package-lock.json` modificado del frontend no se incluyó: backend 320 tests en verde (63 nuevos, cobertura de `inventory` 98 %), migración `0010` validada con upgrade/downgrade/upgrade y con un locker inválido; frontend `typecheck`, `build` y 47 tests (31 nuevos); INV-24 e INV-25 verificados a mano en el navegador contra un backend local con base descartable. Ítems de coordinación registrados (§5), ADR-020, DT-22 y DT-23 cerradas, DT-26…DT-28 abiertas. Pendiente: Fase B (necesita funciones de lectura de `loans`), revisión y PR |
| 2026-10-23 | Perfil 1 | Revisión de coherencia documental (con asistencia de IA): snapshot actualizado; `docs/perfiles.md` creado a partir de "Perfiles de tareas v1" (ADR-017, ADR-018); `AGENTS.md` actualizado; enmienda constitucional 1.1.1 propuesta (ADR-019); deuda DT-16…DT-25 registrada; plan y tareas de SPEC-02 cerrados con sus desviaciones documentadas |
| 2026-10-23 | Perfil 1 | Backend: restaurados `htmlcov/`, `*.err` y `*.log` en el `.gitignore` local (`1958feb`, sin push), que se habían perdido en un merge local |
| 2026-10-13 | Equipo | Backend PR \#12 (`feat/loans`) mergeado en `develop`: contratos, modelos y migración `0009` de `loans`, sin spec en `specs/` (DT-16) |
| 2026-10-10…13 | Equipo | SPEC-02 mergeado en `develop` (backend PR \#7 y `074158e`; frontend PR \#4). Alta de espacios en frontend (`e90f98c`) |
| 2026-10-08 | Perfil 1 | **SPEC-02 implementado y verificado**: Backend `de28749` (257 tests, cobertura 96 %, migraciones 0007/0008); Frontend `af81452` (build, 14 unitarios Vitest, 11 verificaciones E2E Playwright AC-50…AC-59). Publicados en `origin/feat/spec-02-integracion` y `origin/feat/login-auth-ui`, listos para merge post-demo (D-01) |
| 2026-10-08 | Perfil 1 | Conciliación de SPEC-02 (v1.0.1) con PR \#6 de `spaces`: se incorporan En\_Uso/Finalizada e intervalos\_disponibles |
| 2026-10-08 | Perfil 1 | ERS movido a `Backend-PrestaMeDios/docs/ERS.md` y README técnicos en backend y frontend; constitución v1.1.0. El build del front sin `.figma/` ya lo había resuelto un colega en `develop` (79bd91e) |
| 2026-10-08 | Perfil 1 | **SPEC-02 aprobado** con todas las recomendaciones |
| 2026-10-08 | Perfil 1 | Redacción de SPEC-02 (borrador). USR-02, foto de perfil y refresh token se proponen para SPEC-03 |
| 2026-10-07 | Perfil 1 | **Commit `7b95956`** (`feat/users-core`): SPEC-01 \+ migración `0006` de `inventory` (DT-04) \+ logs fuera del índice (DT-07). 46 archivos, 157 tests en verde. Publicado en `origin/feat/users-core`; también quedó en `origin/develop` por el upstream anterior. PR pendiente |
| 2026-10-07 | Perfil 1 | **SPEC-01 implementado**: 157 tests, cobertura 95 %, migración `0005` verificada, prueba de humo E2E OK |
| 2026-10-07 | Perfil 1 | Plan y tareas aprobados; responsables de `inventory` y `spaces` autorizan modificaciones en sus módulos |
| 2026-10-07 | Perfil 1 | Redacción de `specs/01-auth-users/plan.md` y `specs/01-auth-users/tasks.md` |
| 2026-10-07 | Perfil 1 | ERS (entonces `README.md`): CU "Registro y validación de cuentas" — el rechazo conserva la cuenta con motivo y permite re-registro (ADR-010) |
| 2026-10-07 | Perfil 1 | **SPEC-01 aprobado (v1.0.0)** con ajustes en D-02, D-04 y D-07 (ADR-008 a ADR-011) |
| 2026-10-07 | Perfil 1 | Redacción de Constitución v1.0.0, AGENTS.md, MEMORY.md y SPEC-01 (borrador) |
| 2026-10-07 | Equipo | Merge frontend PR \#2: calendario de reservas de espacios v1 |
| 2026-10-06 | Equipo | Merge backend PR \#2 y \#3: inventario y espacios |
| 2026-10-05 | Equipo | Plantilla base del frontend y primeros contratos de inventario |

&nbsp;