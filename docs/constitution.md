# Constitución del Proyecto PrestaMeDios

> **Versión:** 1.1.0 · **Ratificada:** pendiente de aprobación del equipo · **Última revisión:** 2026-11-02 · **Enmienda propuesta:** 1.1.1 (§10.1)
>
> Este documento define los principios **no negociables** que gobiernan el diseño, la construcción y la evolución de PrestaMeDios. Todo spec, plan, tarea, Pull Request o salida de un agente de IA debe cumplirlo. Ante un conflicto entre este documento y cualquier otro artefacto, **prevalece la Constitución**, salvo enmienda formal (§10).

---

## 1. Propósito y contexto

PrestaMeDios es la plataforma de gestión de préstamos de equipamiento, computadoras portátiles y reservas de espacios (Aula-Estudio e Isla de Edición) del **Laboratorio de Medios Audiovisuales (LMA)** del ICSE — UNTDF, con sedes en **Ushuaia** (Yrigoyen 879) y **Río Grande** (Thorne 302).

- **Cliente / referente:** Natalia Ader (Superadministradora del LMA).
- **Marco normativo:** Resolución CICSE N° 056/2023 — Reglamento del LMA.
- **Fuente de verdad funcional:** `docs/ERS.md` (ERS según IEEE 830, Casos de Uso, DER y Arquitectura).
- **Equipo:** Matías Araujo, Joaquín Eberle, Daniel Sardinas, Fabrizio Verdú, Facundo Zamora — Laboratorio de Software, curso 2026.

---

## 2. Principios rectores

### P1 — Spec-Driven Development (SDD)

1. **Ninguna funcionalidad se implementa sin un spec aprobado** en `specs/`.
2. Flujo obligatorio: **Spec → Plan → Tareas → Implementación → Verificación**. Cada etapa se revisa antes de avanzar.
3. El spec define el **qué** y el **por qué** (casos de uso, contratos, reglas, criterios de aceptación); el plan define el **cómo**; las tareas son unidades verificables.
4. Si durante la implementación se descubre que el spec es incorrecto o incompleto, **se detiene, se corrige el spec y se re-aprueba**; el código nunca diverge silenciosamente del spec.
5. Todo requisito del ERS (`USR-xx`, `PRE-xx`, `RES-xx`, `NOV-xx`, `GLO-xx`, `IA-xx`) debe ser trazable a un spec, a endpoints y a tests.

### P2 — API-First

1. Los contratos (esquemas Pydantic v2 → OpenAPI) se definen **antes** que la persistencia y la UI.
2. El backend es la **única** autoridad sobre reglas de negocio. El frontend valida para mejorar la UX, nunca como garantía.
3. El agente de IA (Subsistema 6) consume la API REST igual que el frontend: **jamás** accede directamente a la base de datos ni elude validaciones.

### P3 — Monolito Modular por Dominio

1. El backend se organiza verticalmente en `app/modules/<dominio>/` (`users`, `config`, `inventory`, `spaces`, `loans`, `notifications`, `assistant`).
2. Cada módulo es dueño de sus modelos, esquemas, router, servicios, migraciones y tests.
3. Un módulo **no importa modelos internos de otro**. La colaboración entre módulos se hace mediante funciones de servicio públicas o el kernel compartido `app/core/`.
4. `app/core/` contiene sólo elementos transversales: configuración, seguridad, dependencias de autenticación/autorización, errores y enums compartidos.

### P4 — Seguridad por defecto

1. **Todo endpoint requiere autenticación**, salvo excepciones explícitas declaradas en un spec (p. ej. registro, login, health check).
2. La autorización combina **rol** (`SUPERADMIN`, `ADMIN_LOCAL`, `DOCENTE`, `ESTUDIANTE`) y **alcance de sede**, y siempre se evalúa en el servidor con datos vigentes de la base.
3. Contraseñas sólo como hash robusto (Argon2id). Secretos sólo en variables de entorno; **nunca** en código, migraciones, logs, parámetros globales ni repositorio.
4. Los payloads de entrada rechazan campos desconocidos (`extra="forbid"`) para impedir *mass assignment*.
5. Los mensajes de error no deben facilitar la enumeración de usuarios ni filtrar datos de otra sede.

### P5 — Aislamiento estricto de sedes

1. Inventario, espacios, solicitudes, usuarios y comunicados pertenecen a **una** sede.
2. `ESTUDIANTE`, `DOCENTE` y `ADMIN_LOCAL` operan exclusivamente sobre su sede. Sólo `SUPERADMIN` tiene alcance global ("Ambas sedes").
3. No se permite solicitar, reservar ni retirar bienes de una sede desde la otra.
4. El filtrado por sede se aplica en la **consulta a la base de datos**, nunca sólo en la UI.

### P6 — Privacidad de la información

1. Un estudiante sólo ve sus propios movimientos; nunca el historial, las solicitudes ni la identidad de otros solicitantes.
2. Un docente sólo ve las solicitudes vinculadas a sus asignaturas, en modo lectura/observación.
3. Los administradores ven la información de su jurisdicción.
4. Los datos personales (DNI, teléfono, email) se exponen sólo a quien los necesita según su rol.

### P7 — Integridad de datos en la base

1. Las invariantes críticas se garantizan **en PostgreSQL** (PK, FK, `UNIQUE`, `CHECK`, `EXCLUDE USING gist`), no sólo en Python.
2. Las operaciones concurrentes sobre un mismo recurso se serializan (restricciones de exclusión, bloqueo de fila u optimista).
3. No se borran físicamente entidades con valor histórico (usuarios, préstamos, reservas): se usa **baja lógica** y tablas de historial.
4. Todo cambio de esquema se realiza mediante **migraciones Alembic** versionadas y reversibles (`upgrade` + `downgrade`).

### P8 — Configuración sobre código

1. Las variables operativas del reglamento (plazos, tolerancias, horarios, ventanas de anticipación) se leen del **Panel de Parámetros Globales** (GLO-03), no se codifican de forma fija.
2. Los valores por defecto del reglamento vigente (préstamo general 4 días, notebooks 15 días, horario 09:00–16:00) se siembran por migración.

### P9 — Calidad verificable

1. Cada criterio de aceptación de un spec tiene al menos un test automatizado.
2. Los tests de integración corren contra **PostgreSQL real** (no SQLite), porque el sistema depende de tipos y restricciones propios de PostgreSQL.
3. Un Pull Request no se integra sin: tests en verde, revisión de al menos un integrante y trazabilidad al spec.

### P10 — Simplicidad y foco académico

1. Se implementa lo que el spec exige; las mejoras se registran como trabajo futuro (YAGNI).
2. Se prefieren soluciones estándar y mantenidas del ecosistema sobre desarrollos propios.
3. La documentación es breve, precisa y vive junto al código.

---

## 3. Stack tecnológico aprobado

| Capa | Tecnología | Notas |
| --- | --- | --- |
| Backend | Python 3.11+, FastAPI, Uvicorn | API asíncrona; OpenAPI automático |
| Validación / contratos | Pydantic v2, pydantic-settings | |
| Persistencia | PostgreSQL 15+, SQLAlchemy 2.0 async (`asyncpg`), Alembic | Extensión `btree_gist` requerida |
| Seguridad | PyJWT (HS256), pwdlib[argon2] | Definido en SPEC-01 |
| Testing backend | pytest, pytest-asyncio, httpx | |
| Frontend | React 19, TypeScript 5 (estricto), Vite, Tailwind CSS 4 | |
| Gestión | Git + GitHub (org `PrestaMeDios-org`), ClickUp (Scrum) | |

Incorporar una dependencia nueva requiere justificarla en el plan del spec correspondiente.

---

## 4. Convenciones de diseño

### 4.1 Idioma

- **Dominio en español** (entidades, campos, endpoints de recurso, mensajes al usuario): `usuarios`, `equipamiento`, `reservas`, `fecha_reserva`.
- **Nombres de módulos y términos técnicos en inglés**: `app/modules/inventory`, `router.py`, `schemas.py`.
- Mensajes de error al usuario en español rioplatense neutro.

### 4.2 API REST

- Prefijo `/api/v1/<modulo>`; recursos en plural o sustantivo de dominio.
- Cambios de estado mediante `PATCH /<recurso>/{id}/estado` (patrón ya adoptado en `inventory` y `spaces`).
- Errores de negocio: `{"detail": "<mensaje>", "code": "<CODIGO>"}`; errores de validación: formato estándar de FastAPI (`422`).
- Códigos HTTP: `200` lectura/actualización · `201` creación · `401` no autenticado · `403` sin permiso · `404` inexistente o fuera de alcance · `409` conflicto de estado/unicidad/concurrencia · `422` validación.
- Campos JSON en `snake_case`; fechas ISO-8601 con zona horaria (UTC en persistencia).

### 4.3 Persistencia

- Nombres de tablas en plural y `snake_case`.
- Restricciones nombradas según `NAMING_CONVENTION` de `app/database.py`.
- Enums de dominio como `StrEnum` en Python y `ENUM` de PostgreSQL con `values_callable` (persistir el valor, no el nombre).
- Migraciones numeradas `000N_<descripcion>.py`, una por cambio lógico.

### 4.4 Frontend

- Organización por funcionalidad: `src/features/<dominio>/{components,pages,services,types}`.
- DTOs espejo 1:1 de los esquemas Pydantic (`snake_case`); *mappers* hacia modelos de vista.
- URL base del backend vía `VITE_API_URL`.

---

## 5. Reglas de negocio constitucionales (derivadas del Reglamento y el ERS)

| # | Regla | Origen |
| --- | --- | --- |
| R1 | Toda solicitud de préstamo o reserva requiere **aprobación manual** de un administrador con jurisdicción. Nada se confirma automáticamente. | PRE-10, RES-05 |
| R2 | Los docentes **no** aprueban ni rechazan solicitudes: sólo observan y comentan. | PRE-20, Iteración 2 |
| R3 | Préstamo general: máximo 4 días corridos para estudiantes. Notebooks: hasta 15 días, renovación sólo presencial. | PRE-07, PRE-11 |
| R4 | Las reservas operan en el horario del laboratorio (09:00–16:00 por defecto), con supervisión presencial. | Restricciones, GLO-02 |
| R5 | Las cuentas autorregistradas requieren validación manual antes de operar. | USR-05 |
| R6 | No existe el rol "Administrador ICSE": las aprobaciones del ICSE son resoluciones del CICSE, fuera del sistema. | Iteración 2 |

---

## 6. Gobierno de specs

- Ubicación: una carpeta por spec, `specs/NN-<slug>/`, con `spec.md`, `plan.md` y `tasks.md`.
- Estados: `BORRADOR` → `EN_REVISION` → `APROBADO` → `IMPLEMENTADO` → (`OBSOLETO`).
- Contenido mínimo: alcance, actores, casos de uso, contratos con códigos HTTP, modelo de datos, reglas de negocio, criterios de aceptación, casos de borde, decisiones abiertas y trazabilidad.
- Las decisiones arquitectónicas relevantes se registran también en `MEMORY.md`.

### 6.1 Documentación de los repositorios

| Documento | Ubicación | Propósito |
| --- | --- | --- |
| ERS (IEEE 830) | `docs/ERS.md` | Documento académico y fuente de verdad funcional: requisitos, casos de uso, diseño e iteraciones |
| README del backend | `Backend-PrestaMeDios/README.md` | Guía técnica: instalación, configuración, endpoints, tests y migraciones |
| README del frontend | `Frontend-PrestaMeDios/README.md` | Guía técnica: instalación, variables, estructura y convenciones |
| Constitución, `AGENTS.md`, `MEMORY.md`, perfiles | Repo `Docs-PrestaMeDios` | Gobierno del proyecto, reglas para agentes y memoria compartida |
| Specs, plan y tareas | `Docs-PrestaMeDios/specs/` | Especificaciones SDD |

- Un cambio de requisitos se refleja primero en el ERS (vía PR a `Docs-PrestaMeDios`) y después en los specs afectados.
- Los README describen el estado **operativo** del código; se actualizan en el mismo PR que cambia la instalación, la configuración o los endpoints.

---

## 7. Flujo de trabajo con Git

- Ramas: `main` (estable, entregas), `develop` (integración), `feat/<tema>`, `fix/<tema>`.
- Commits con *Conventional Commits* en español: `feat(users): …`, `fix(spaces): …`, `docs(spec-01): …`.
- Todo cambio entra por Pull Request hacia `develop` con al menos una revisión.
- Prohibido versionar `.env`, logs de ejecución, artefactos de build o `node_modules`.

---

## 8. Uso de agentes de IA

1. Los agentes siguen `AGENTS.md` y esta Constitución.
2. Un agente **no** genera código de aplicación para una funcionalidad sin spec `APROBADO`.
3. Un agente **no** modifica módulos de otro perfil sin indicación explícita; propone el cambio como ítem de coordinación.
4. Un agente **no** realiza commits, push ni cambios en configuración de Git sin pedido explícito.
5. Toda salida de un agente es revisada por un integrante humano antes de integrarse.

---

## 9. Definición de Hecho (Definition of Done)

Una funcionalidad está terminada cuando:

- [ ] Existe un spec `APROBADO` y el código lo cumple.
- [ ] Todos los criterios de aceptación tienen tests automatizados en verde.
- [ ] Hay migración Alembic (con `downgrade`) si cambió el esquema.
- [ ] Los endpoints están documentados en OpenAPI con ejemplos y respuestas de error.
- [ ] Se respetan autenticación, roles y aislamiento de sede.
- [ ] El PR fue revisado y aprobado por otro integrante.
- [ ] `MEMORY.md` se actualizó si hubo decisiones o deuda técnica nuevas.

---

## 10. Enmiendas

Las enmiendas se proponen por PR que modifique este archivo, con justificación, y requieren la aprobación de la mayoría del equipo. Se versiona con SemVer: **MAJOR** al eliminar o redefinir un principio, **MINOR** al agregar uno, **PATCH** para aclaraciones.

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.1.0 | 2026-10-08 | El ERS se mueve a `Backend-PrestaMeDios/docs/ERS.md`; se agrega §6.1 (documentación de los repositorios) |
| 1.0.0 | 2026-10-07 | Versión inicial, consolidada a partir del ERS y del código existente del equipo |

### 10.1 Enmiendas propuestas (no vigentes hasta su aprobación)

> Se presenta al equipo por PR al repo `Docs-PrestaMeDios`. Al aprobarse, el texto propuesto reemplaza al vigente y la versión se registra en la tabla anterior.

**Enmienda 1.1.1 (PATCH, aclaraciones)** · Propone: Perfil 1 · Fecha: 2026-10-23 (parte C: 2026-11-02) · Estado: `PROPUESTA` · Ver ADR-019 y ADR-021 en `MEMORY.md`.

#### A. P3.3 — Aislamiento entre módulos

- *Vigente:* "Un módulo **no importa modelos internos de otro**. La colaboración entre módulos se hace mediante funciones de servicio públicas o el kernel compartido `app/core/`."
- *Propuesto:* "Un módulo **no importa modelos ni servicios internos de otro módulo de negocio**. La colaboración se hace mediante el kernel compartido `app/core/` o funciones de servicio que el módulo dueño declara públicas. Se exceptúan: (a) la entidad `Usuario` que devuelven `get_current_user` y `require_roles`, que forma parte del contrato del kernel; (b) las claves foráneas entre tablas de distintos módulos, declaradas por nombre de tabla."
- *Motivo:* `core/deps.py`, `config`, `inventory` y `spaces` ya usan `Usuario` como tipo del usuario autenticado. La regla literal los declaraba en infracción.

#### B. P7.2 — Concurrencia e integridad temporal

- *Vigente:* "Las operaciones concurrentes sobre un mismo recurso se serializan (restricciones de exclusión, bloqueo de fila u optimista)."
- *Propuesto:* "Las operaciones concurrentes sobre un mismo recurso se serializan (restricciones de exclusión, bloqueo de fila u optimista). La no superposición de recursos **adjudicados** (reservas aprobadas o en uso, unidades reservadas o entregadas) se garantiza en PostgreSQL con `EXCLUDE USING gist`, y su violación se traduce a `409`. El servicio puede verificar antes los solapamientos para devolver un error específico, pero esa verificación nunca reemplaza a la restricción. Las solicitudes pendientes concurrentes están permitidas cuando el requisito lo indica (RES-02)."
- *Motivo:* SPEC-02 (V6–V8) y `spaces/service.py` validan bloqueos y duplicados antes de insertar. Los bloqueos contra reservas y las solicitudes pendientes no se pueden expresar con una única restricción de exclusión.

#### C. §1 y §6.1 — Ubicación de la documentación (ya aplicada al texto)

- *Antes (v1.1.0):* el ERS estaba en `Backend-PrestaMeDios/docs/ERS.md`, y la Constitución, `AGENTS.md`, `MEMORY.md` y los specs vivían en la raíz del workspace, que no es un repositorio.
- *Ahora:* el ERS está en `docs/ERS.md` del repo `Docs-PrestaMeDios`, junto con la Constitución, `AGENTS.md`, `MEMORY.md`, los perfiles y `specs/`. Los cambios de requisitos se hacen por PR a ese repo (§6.1).
- *Motivo:* ADR-021. El cambio ya está aplicado en §1 y §6.1 y en los repos de código (backend PR \#15, frontend PR \#10); esta enmienda lo ratifica y lo registra en la tabla de versiones.
