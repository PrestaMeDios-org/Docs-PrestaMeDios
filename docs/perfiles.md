# Perfiles del equipo — Guía de trabajo con agentes de IA

> **Versión:** 1.2.0 · **Fecha:** 2026-11-10 · **Mantiene:** Perfil 1

> **Subordinado a:** `docs/constitution.md` → `AGENTS.md`. Ante cualquier diferencia, prevalecen esos documentos. Este archivo **no** agrega reglas: indica qué le toca a cada perfil y cómo arrancar a trabajar con un agente de IA.

> Estado del código verificado contra `develop` de ambos repositorios al 2026-11-02; el del Perfil 1 y las interfaces de §5 que publica, al 2026-11-10.

---

## 1\. Cómo usar este documento

1. Buscá tu perfil en la §4 (la asignación de nombres está en ClickUp).  
2. Antes de pedirle algo a tu agente, dale **estos archivos del repo `Docs-PrestaMeDios`** (no alcanza con el repo de back o de front; cómo armar el workspace con los tres repos: `README.md`):  
   - `docs/constitution.md` — principios no negociables.  
   - `AGENTS.md` — reglas operativas, convenciones y requisitos de cada módulo.  
   - `MEMORY.md` — estado actual, decisiones (ADR) y deuda técnica.  
   - Este archivo.  
   - `docs/ERS.md` — requisitos (al menos los de tu perfil).  
3. Pegale el **prompt de arranque** de tu perfil (§4) como primera instrucción.  
4. Trabajá con el flujo SDD de `AGENTS.md` §4: **spec → aprobación → plan → tareas → código → tests**. Sin spec `APROBADO` en `specs/`, el agente no escribe código de aplicación.

---

## 2\. Contexto común

- **Sistema:** PrestaMeDios — préstamos de equipamiento y notebooks, y reservas de espacios (Aula-Estudio, Isla de Edición) del Laboratorio de Medios Audiovisuales (ICSE — UNTDF).  
- **Sedes aisladas:** Ushuaia y Río Grande. Sólo el `SUPERADMIN` opera sobre ambas.  
- **Roles (cuatro, ADR-001):** `SUPERADMIN`, `ADMIN_LOCAL`, `DOCENTE`, `ESTUDIANTE`. Están en `RolUsuario` (`app/core/enums.py`). No existe el rol "Administrador ICSE".  
- **Reglas operativas configurables (GLO-03):** el plazo de préstamo general (4 días), el de notebooks (15 días), el horario (09:00–16:00) y la anticipación mínima (24 h) son **parámetros** que se leen con `obtener_parametro(db, "<clave>")`. No se escriben fijos en el código.  
- **Stack:** FastAPI \+ SQLAlchemy 2.0 async (`asyncpg`) \+ Alembic \+ PostgreSQL (`btree_gist`) · React 19 \+ TypeScript \+ Vite.  
- **Arquitectura:** monolito modular por dominio (`app/modules/<dominio>/`), API-First. Los elementos transversales viven en `app/core/`.

### Lo que ya existe y hay que reutilizar

| Necesidad | Usar | No hacer |
| :---- | :---- | :---- |
| Saber quién llama | `Depends(get_current_user)` de `app/core/deps.py` | Definir un usuario o un enum de roles propio |
| Restringir por rol | `Depends(require_roles(RolUsuario.ADMIN_LOCAL, ...))` | Comparar strings de rol |
| Filtrar por sede | `resolver_alcance_sede(...)`, `sede_para_alta(...)` | Tomar la sede o el `id_usuario` del body |
| Errores de negocio | `AppError(status, "CODIGO", "mensaje")` → `{detail, code}` | `HTTPException` u otro formato de error |
| Sedes | `SedeEnum` de `app/core/enums.py` | Enteros o strings libres |
| Hora del laboratorio | `ahora_lab()`, `ZONA_HORARIA_LAB` de `app/core/settings.py` | `datetime.now()` sin zona |
| Cliente HTTP (front) | `src/lib/api.ts` (token y errores normalizados) | `fetch` directo sin token |
| Sesión y sede (front) | `useAuth()` / `useSede()` de `src/features/auth/AuthContext.tsx` | Selectores de rol o de usuario simulados |
| Nombre y apellido de otros usuarios | `datos_publicos_por_ids(db, ids)` de `app/modules/users/service.py` (SPEC-03) | Importar el modelo `Usuario` para leer datos de terceros |
| Guardar o servir archivos | `vincular_archivo`, `abrir_archivo` y `respuesta_descarga` de `app/modules/files/service.py` (SPEC-03 §6.5) | Guardar archivos por cuenta propia |
| Mandar un correo | `notifications` (SPEC-06), que usa `enviar_correo(TipoCorreo.NOTIFICACION, …)` de `app/core/email.py` | Llamar a SMTP directamente |

### Precisiones sobre reglas que suelen malinterpretarse

- **Solapamientos temporales.** Lo que ya está **adjudicado** (reservas aprobadas o en uso, unidades reservadas o entregadas) se garantiza en PostgreSQL con `EXCLUDE USING gist`. El servicio **puede** consultar antes para devolver un error claro (por ejemplo, `FRANJA_OCUPADA`), pero la garantía final es la restricción de la base, y su violación se traduce a `409`. Las solicitudes **pendientes** concurrentes están permitidas (RES-02), así que no llevan restricción de exclusión. *(Aclaración propuesta en la enmienda 1.1.1 de la Constitución.)*

- **Aislamiento entre dominios.** Un módulo no importa los modelos ni los servicios internos de otro módulo de negocio. Sí se permite:

  - el kernel `app/core/`;  
  - el `Usuario` que devuelve `get_current_user`;  
  - funciones de servicio públicas que el módulo dueño expone explícitamente;  
  - claves foráneas en la base de datos.

  *(Aclaración propuesta en la enmienda 1.1.1.)*

- **"Filtrar por sede en la base de datos"** significa aplicar el filtro en la consulta SQL (`WHERE sede = ...`), no sólo en la interfaz. No se usa Row Level Security.

- **Autenticación:** se hace con dependencias de FastAPI (`Depends`), no con un middleware.

---

## 3\. Mapa de perfiles

| Perfil | Dominio | Backend | Frontend (`src/features/`) | Requisitos |
| :---- | :---- | :---- | :---- | :---- |
| **1 — Core** | Identidad, usuarios, historiales, configuración global, despliegue | `core`, `users`, `config`, `files` | `auth`, `users`, `config`, layout | USR-01…09, GLO-01, GLO-03, GLO-05, GLO-06, despliegue (Docker, CI) |
| **2 — Catálogo y existencias** | Catálogo e inventario físico | `inventory` | `inventory` | PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 |
| **3 — Préstamos y concurrencia** | Órdenes de pedido, aprobación, entrega y devolución | `loans` | `loans` | PRE-03…11, PRE-13, PRE-15…18, PRE-20 |
| **4 — Espacios** | Reserva de Aula-Estudio e Isla de Edición | `spaces` | `spaces` | RES-01…05, GLO-02, GLO-04 |
| **5 — Comunicaciones e IA** | Comunicados, notificaciones, asistente MCP | `notifications`, `assistant` | `notifications`, `assistant` | NOV-01…04, IA-01…03 |

> **Atención con el ERS:** el Módulo 3 del Subsistema 2 ("Operaciones de Pañol y Control de Stock") está **dividido**. PRE-12, PRE-14 y PRE-19 son del Perfil 2; PRE-11, PRE-13 y PRE-15 a PRE-18 son del Perfil 3, porque operan sobre órdenes de préstamo. Del mismo modo, el Subsistema 5 se reparte: GLO-02 y GLO-04 son del Perfil 4, y el resto del Perfil 1\.

---

## 4\. Detalle por perfil

### Perfil 1 — Core: identidad, usuarios y configuración

**Responsabilidades:** autenticación y permisos; usuarios y sus historiales; parámetros globales; kernel `app/core/`; notas privadas de administradores; preferencias de interfaz; despliegue e integración continua.

| Estado | Detalle |
| :---- | :---- |
| Implementado | SPEC-01 y SPEC-02: registro, login JWT, cuatro roles, aislamiento de sede, directorio y aprobación de cuentas, edición de perfil, cambio obligatorio de contraseña, parámetros con historial. SPEC-03: `datos_publicos_por_ids` para otros módulos; recuperación de contraseña por email (USR-02) con el transporte de correo `app/core/email.py`; módulo `files` (foto de perfil USR-03 y PDF de aval PRE-05); renovación deslizante de la sesión con tope de 8 h y "Cerrar todas mis sesiones". Frontend de login, registro, recuperación de contraseña, perfil con foto, gestión de usuarios y parámetros. Tema claro/oscuro (GLO-06, parcial) |
| Pendiente | USR-06 (panel de solicitudes propias) · USR-07 (historial de actividad) · USR-08 (auditoría global) · USR-09 (llamados de atención, faltas y suspensión automática, ADR-022) · GLO-05 (notas privadas) · lo nuevo de la entrevista del 16/10 (ADR-022): horario por sede, teléfono obligatorio, correo de contacto del laboratorio y delegación temporal del rol de Superadministrador · Docker y CI (K8 de SPEC-03) |
| Depende de otros perfiles | USR-06, USR-07 y USR-08 consumen datos de `loans` y `spaces`. Necesitan que esos módulos expongan funciones de lectura (ver §5) |

**Prompt de arranque:**

```
Trabajo en PrestaMeDios como Perfil 1 (Core: identidad, usuarios, configuración y despliegue).
Leé completos docs/constitution.md, AGENTS.md, MEMORY.md y docs/perfiles.md antes de actuar.
Mis módulos son core, users y config (backend) y auth, users, config y layout (frontend).
No modifiques módulos de otros perfiles: si hace falta un cambio ahí, registralo como
ítem de coordinación en el spec y en MEMORY.md. Seguí el flujo SDD: primero un spec en
specs/ en estado BORRADOR, y no escribas código hasta que yo lo apruebe.
```

---

### Perfil 2 — Catálogo y existencias

**Responsabilidades:** catálogo de equipamiento, unidades físicas, categorías, lockers (1–7 por sede), estados de mantenimiento y vista de stock para administradores.

| Estado | Detalle |
| :---- | :---- |
| Implementado (backend, SPEC-04 Fase A) | Modelos y esquemas de `Categoria`, `Equipamiento` y `UnidadFisica`; alta y listado filtrable por sede, categoría y texto; alta de unidades con sede automática (PRE-19); edición y baja lógica de equipamiento y unidades; matriz de estados en `PATCH /unidades/{id}/estado` (PRE-14; `prestado` sólo lo fija `loans`); vista reducida para estudiantes y docentes; `inventory/service.py` público para `loans`; `CHECK` de locker 1–7 (migración `0010`); autenticación, alcance de sede y plazo por defecto desde `config` |
| Implementado (frontend, SPEC-04 Fase A) | Catálogo conectado a la API (se eliminó el mock); tabla de stock en `admin-stock` con alta, edición, baja lógica y cambio de estado |
| Pendiente | La Fase C de SPEC-04: historial por unidad (PRE-12) y `reservas_afectadas`. Las funciones de lectura de `loans` que necesita (SPEC-05 §10.2) ya están en `develop` (backend PR \#23); la Fase B está en `develop` (PR \#24) |
| Límites | Entrega, devolución, renovación y bandeja de órdenes **no** son de este perfil (son del Perfil 3). El estado de la unidad (`disponible`, `prestado`, `mantenimiento`, `baja`) se debe coordinar con `loans` (ver §5) |

**Prompt de arranque:**

```
Trabajo en PrestaMeDios como Perfil 2 (Catálogo y existencias).
Leé completos docs/constitution.md, AGENTS.md, MEMORY.md y docs/perfiles.md antes de actuar.
Mi módulo es inventory (backend y frontend). Requisitos: PRE-01, PRE-02, PRE-12, PRE-14, PRE-19.
Reutilizá get_current_user, require_roles, resolver_alcance_sede, AppError y obtener_parametro
de app/core y config; no definas roles, usuarios ni formatos de error propios.
No modifiques módulos de otros perfiles: si hace falta un cambio ahí, registralo como
ítem de coordinación. Seguí el flujo SDD: primero un spec en specs/ en estado BORRADOR,
y no escribas código hasta que yo lo apruebe.
```

---

### Perfil 3 — Préstamos y concurrencia

**Responsabilidades:** orden de pedido unificada (simple y carrito), validación de plazos (4 días general, 15 notebooks) y anticipación, PDF de aval para alta gama, bandeja administrativa, aprobación con asignación de unidad y ajuste horario, entrega y devolución, renovación de notebooks, cancelación forzada, cancelación automática por no retiro, calendario maestro y panel de observación docente.

| Estado | Detalle |
| :---- | :---- |
| Implementado (backend, en `develop`) | SPEC-05 v1.0.0 `APROBADO` (2026-11-07). **Fase 1** (PR \#21): reglas, crear orden con validaciones de franja, anticipación, plazo y unidades libres, y consulta de las propias. **Fase 2** (PR \#23 y \#28): bandeja, detalle para administradores, unidades libres por línea, aprobar con asignación de unidades y ajuste horario, rechazar y cancelar, con concurrencia probada y migración `0011`. Funciones públicas para `inventory`: `unidades_libres`, `ocupacion_de_unidades`, `historial_de_unidad` y `reservas_futuras_de_unidad` |
| Implementado (frontend, en `develop`) | Tipos, `loansApi` y carrito conectado al catálogo (PR \#18) |
| En curso | Aval de alta gama (PRE-05, T1.12) en `feat/loans-aval`, según la spec v1.0.2, que espera el OK del Perfil 1 |
| Pendiente | Frontend: formulario de solicitud, "Mis solicitudes" y las pantallas de la Fase 2. Backend: notificaciones de cada transición (espera `crear_notificacion`, SPEC-06 Fase B), horario por sede (K10), renovación (PRE-11), entrega y devolución y cancelación forzada (Fase 3: PRE-13, PRE-17), no retiro automático, calendario maestro y panel docente (Fase 4: PRE-08, PRE-16, PRE-20) |
| Deuda registrada | En `MEMORY.md` §4: DT-20 (estado de la unidad duplicado con `inventory`): ya se respeta al aprobar; se termina de cerrar en la Fase 3, cuando la entrega y la devolución usen `marcar_unidad_prestada` y `liberar_unidad`. DT-16 se cerró con la aprobación de SPEC-05 y DT-17 y DT-18 en el PR \#16 |

**Siguiente:** plan y tareas de la Fase 3 (mostrador) en `specs/05-loans-prestamos/plan.md` y `tasks.md`, y el frontend de las Fases 1 y 2.

**Prompt de arranque:**

```
Trabajo en PrestaMeDios como Perfil 3 (Préstamos y concurrencia).
Leé completos docs/constitution.md, AGENTS.md, MEMORY.md y docs/perfiles.md antes de actuar.
Mi módulo es loans (backend y frontend). Requisitos: PRE-03…11, PRE-13, PRE-15…18, PRE-20.
El módulo ya tiene contratos, modelos y la migración 0009 en develop, sin lógica, y su spec
está en specs/05-loans-prestamos/spec.md (BORRADOR). Trabajá sobre ese spec hasta que yo lo
apruebe; resuelve DT-16 a DT-20 de MEMORY.md. Usá get_current_user,
RolUsuario, AppError y obtener_parametro del proyecto; no definas usuarios, roles ni
formatos de error propios. No modifiques inventory ni otros módulos: lo que necesites de
ellos va como ítem de coordinación. No escribas código hasta que yo apruebe el spec.
```

---

### Perfil 4 — Espacios

**Responsabilidades:** espacios reservables por sede, solicitudes de reserva concurrentes en estado pendiente, aprobación con rechazo automático de solapadas, bloqueos administrativos de días o franjas, horario operativo y calendario interactivo.

> "Infraestructura" en este perfil significa **infraestructura física** (Aula-Estudio, Isla de Edición), como la usa el ERS. El despliegue (Docker, CI, servidores) es del Perfil 1\. En el código sólo aparece como la etiqueta de OpenAPI "Espacios e Infraestructura" del módulo `spaces`.

| Estado | Detalle |
| :---- | :---- |
| Implementado | Modelos y contratos de `Espacio`, `ReservaEspacio` y `BloqueoEspacio`; `EXCLUDE USING gist` con `tsrange` para reservas `Aprobada`/`En_Uso`; validaciones de horario, anticipación, ventana máxima, bloqueos y duplicados; transiciones (`Pendiente` → `Aprobada`/`Rechazada`/`Cancelada`, `Aprobada` → `En_Uso`, `En_Uso` → `Finalizada`); disponibilidad sin identidad de otros usuarios. Frontend: calendario conectado a la API, bandeja de aprobación, bloqueos y alta de espacios |
| Pendiente | DT-09 (estados como `ENUM` de PostgreSQL) · rehabilitar fechas bloqueadas (GLO-04) · Isla de Digitalización (requisito futuro) |

**Prompt de arranque:**

```
Trabajo en PrestaMeDios como Perfil 4 (Espacios).
Leé completos docs/constitution.md, AGENTS.md, MEMORY.md y docs/perfiles.md antes de actuar.
Mi módulo es spaces (backend y frontend). Requisitos: RES-01…05, GLO-02, GLO-04.
El módulo ya integra autenticación y alcance de sede (SPEC-02): respetá spaces/service.py
y los criterios AC-31…AC-39 de specs/02-integracion-seguridad-cuenta/spec.md.
No modifiques módulos de otros perfiles: si hace falta un cambio ahí, registralo como
ítem de coordinación. Seguí el flujo SDD: primero un spec en specs/ en estado BORRADOR,
y no escribas código hasta que yo lo apruebe.
```

---

### Perfil 5 — Comunicaciones e IA

**Responsabilidades:** portal estático, comunicados segmentados por sede o globales, centro de notificaciones (campanita), alertas de vencimiento y el asistente de IA (MCP) que consume la API REST.

| Estado | Detalle |
| :---- | :---- |
| Implementado | Nada en el backend. En el frontend, la campanita de `Navbar.tsx` y el ítem "Novedades" usan datos de ejemplo |
| Pendiente | Módulos `notifications` y `assistant` completos (backend y frontend) |
| Límites | El asistente **nunca** accede a la base de datos: usa los mismos endpoints REST que el frontend, con la sesión del usuario (Constitución P2.3). Aunque IA-02 del ERS diga "acceso de lectura a la base de datos", prevalecen la Constitución y la sección de Arquitectura del ERS. Las consultas de stock y disponibilidad se apoyan en los endpoints de `inventory` y `spaces` (y en los futuros de `loans`). Si hace falta un endpoint nuevo, se pide al perfil dueño como ítem de coordinación |

**Prompt de arranque:**

```
Trabajo en PrestaMeDios como Perfil 5 (Comunicaciones e IA).
Leé completos docs/constitution.md, AGENTS.md, MEMORY.md y docs/perfiles.md antes de actuar.
Mis módulos son notifications y assistant (backend y frontend). Requisitos: NOV-01…04, IA-01…03.
El asistente nunca accede a la base de datos: consume la API REST con la sesión del usuario.
Comunicados y notificaciones respetan el aislamiento de sede (SUPERADMIN puede emitir globales).
No modifiques módulos de otros perfiles: si necesitás un endpoint o un evento de ellos,
registralo como ítem de coordinación. Seguí el flujo SDD: primero un spec en specs/ en
estado BORRADOR, y no escribas código hasta que yo lo apruebe.
```

---

## 5\. Interfaces entre perfiles (a definir en los specs)

| Interfaz | Entre | Propuesta | Se define en |
| :---- | :---- | :---- | :---- |
| Estado de la unidad física | Perfil 2 ↔ Perfil 3 | Una única fuente de verdad. `loans` no presta unidades en `mantenimiento` o `baja`, y la entrega o devolución actualiza la unidad mediante una función pública de `inventory` (DT-20). **Lado de `inventory` publicado** (SPEC-04): `unidades_asignables`, `unidad_es_asignable`, `marcar_unidad_prestada`, `liberar_unidad` | Spec de `loans` (SPEC-05) |
| Disponibilidad del catálogo (PRE-01) | Perfil 2 ← Perfil 3 | `loans` expone una función de lectura de ocupación por unidad y período | Spec de `loans` |
| Historial y panel del usuario (USR-06, USR-07, USR-08) | Perfil 1 ← Perfiles 3 y 4 | `loans` y `spaces` exponen funciones de lectura de las solicitudes de un usuario (`loans`: `ordenes_de_usuario`, SPEC-05 §10.2) | Spec del Perfil 1 |
| Datos públicos de usuarios | Perfiles 3 y 4 ← Perfil 1 | `users/service.py` expone `datos_publicos_por_ids(db, ids)` → `{id: DatosPublicosUsuario(id, nombre, apellido)}`, sin DNI, email ni teléfono (P6). No filtra por sede: quien llama sólo pasa ids que ya puede mostrar. **Publicada** (backend PR #18): la usan `loans` (K2) y `notifications`; falta `spaces` (K1) | SPEC-03 (Fase A) |
| Archivos (aval PRE-05) | Perfil 3 ← Perfil 1 | `files/service.py` expone `vincular_archivo` (dentro de la transacción del llamador, sin `commit`), `abrir_archivo` y `respuesta_descarga`. **Publicada** (backend PR #26); falta que `loans` reemplace el `422 AVAL_REQUERIDO` (K3) | SPEC-03 (Fase B2) |
| Transporte de correo | Perfil 5 ← Perfil 1 | `core/email.py` expone `enviar_correo(TipoCorreo.NOTIFICACION, destinatario, {"titulo", "mensaje"})` y `ErrorEnvioCorreo`. **Publicado** (backend PR #29); lo usa la Fase C de SPEC-06 (K6, C-N03) | SPEC-03 (Fase B1) |
| Notificaciones (NOV-03, NOV-04, PRE-17) | Perfiles 3 y 4 → Perfil 5 | `notifications` expone una función pública para crear notificaciones, que `loans` y `spaces` llaman al cambiar de estado | Spec de `notifications` |
| Endpoints para el asistente (IA-02, IA-03) | Perfil 5 ← Perfiles 2, 3 y 4 | El asistente usa los endpoints existentes; los nuevos los implementa el perfil dueño | Spec de `assistant` |

---

## 6\. Flujo de Git

- Ramas: `main` (entregas), `staging` (preproducción), `develop` (integración), `feat/<tema>` y `fix/<tema>` desde `develop`.  
- Todo entra por Pull Request hacia `develop` con al menos una revisión. Commits con *Conventional Commits* en español: `feat(loans): …`.  
- Flujo en ClickUp: Backlog → En Desarrollo → Code Review → QA.  
- El agente **no** hace commit, push ni merge sin un pedido explícito.

---

## 7\. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 1.2.1 | 2026-11-11 | Perfil 3 al día (SPEC-05 aprobado, Fases 1 y 2 en `develop`, aval en curso); el Perfil 2 ya no depende de `loans` para su Fase C |
| 1.2.0 | 2026-11-10 | Cierre de SPEC-03 (Perfil 1): estado del Perfil 1 al día (§4); `datos_publicos_por_ids`, `files` y el transporte de correo en "Lo que ya existe" (§2) y como interfaces publicadas (§5) |
| 1.1.0 | 2026-11-02 | Estado al día con `develop`: Perfil 2 con SPEC-04 Fase A implementada; Perfil 3 con endpoints protegidos (`501`) y SPEC-05 en borrador; Perfil 1 con SPEC-03 por fases; nueva interfaz "Datos públicos de usuarios" (§5) |
| 1.0.0 | 2026-10-23 | Versión inicial. Adapta el documento "Perfiles de tareas v1" (externo) a la asignación de `AGENTS.md` y al código: los requisitos del Módulo 3 de Préstamos quedan en `loans`; el Perfil 1 asume USR-06…09, GLO-05, GLO-06 y el despliegue; se corrigen los roles (cuatro), el horario (configurable) y la autenticación (`Depends`); se aclara que "infraestructura" es física; se incorpora el flujo SDD |

&nbsp;