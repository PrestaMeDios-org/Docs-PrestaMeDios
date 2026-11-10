# AGENTS.md — Guía operativa para agentes de IA

> Instrucciones para cualquier agente de IA (OpenCode, Claude, Copilot, etc.) que trabaje en el espacio de trabajo **PrestaMeDios**. Leer completo antes de actuar.

> **Orden de precedencia:** `docs/constitution.md` → este archivo → `docs/perfiles.md` → spec aprobado de la tarea → `MEMORY.md` → instrucciones puntuales del usuario.

---

## 1\. Qué es este proyecto

Plataforma web para gestionar **préstamos de equipamiento audiovisual y notebooks** y **reservas de espacios** (Aula-Estudio, Isla de Edición) del Laboratorio de Medios Audiovisuales (ICSE — UNTDF), con dos sedes estrictamente aisladas: **Ushuaia** y **Río Grande**.

- Requisitos completos (ERS IEEE 830 \+ casos de uso): `docs/ERS.md`.  
- Guías técnicas de instalación y uso: `README.md` de cada repositorio.  
- Principios no negociables: `docs/constitution.md`.  
- Qué le toca a cada perfil y cómo arrancar con un agente: `docs/perfiles.md`.  
- Estado, decisiones y deuda técnica: `MEMORY.md`.

---

## 2\. Estructura del espacio de trabajo

```
Proyecto-PrestaMeDios/            ← raíz del workspace (NO es un repo git; contiene los tres clones)
├── CLAUDE.md · opencode.json · AGENTS.md  ← copias locales de workspace/: cargan este archivo al iniciar
├── Docs-PrestaMeDios/            ← repo git (documentación del proyecto)
│   ├── AGENTS.md                 ← este archivo
│   ├── MEMORY.md                 ← memoria persistente del proyecto
│   ├── docs/
│   │   ├── ERS.md                ← ERS / documento académico (fuente de verdad funcional)
│   │   ├── diseno/               ← arquitectura, modelo de datos y casos de uso (Mermaid + originales en historico/)
│   │   ├── constitution.md       ← principios y reglas del proyecto
│   │   └── perfiles.md           ← división del trabajo en 5 perfiles (subordinado a este archivo)
│   ├── specs/                    ← especificaciones SDD
│   │   └── NN-<slug>/            ← una carpeta por spec
│   │       └── {spec,plan,tasks}.md
│   └── workspace/                ← plantillas para la raíz del workspace
├── Backend-PrestaMeDios/         ← repo git (FastAPI)
│   ├── README.md                 ← guía técnica del backend
│   ├── app/
│   │   ├── main.py               ← registro explícito de routers
│   │   ├── database.py           ← engine async, Base, NAMING_CONVENTION, get_db
│   │   ├── core/                 ← kernel compartido (SPEC-01): settings, security, deps, errors, enums
│   │   └── modules/<dominio>/    ← models.py · schemas.py · router.py · enums.py · service.py
│   ├── alembic/versions/         ← migraciones 000N_<desc>.py
│   └── tests/
└── Frontend-PrestaMeDios/        ← repo git (React + TS + Vite)
    ├── README.md                 ← guía técnica del frontend
    └── src/
        ├── components/{layout,ui}/
        └── features/<dominio>/{components,pages,services,types}/
```

Documentación, Backend y Frontend son **tres repositorios Git independientes** (org `PrestaMeDios-org`; algunos clones locales del backend apuntan a `github.com/PrestaMeDios/Backend-PrestaMeDios`), clonados uno al lado del otro en la raíz del workspace. Ejecutar comandos Git dentro del repo correspondiente: el ERS, specs, `MEMORY.md` y estos documentos se versionan **sólo** en `Docs-PrestaMeDios`.

> **Rutas:** en los documentos de `Docs-PrestaMeDios`, las rutas `AGENTS.md`, `MEMORY.md`, `docs/…` y `specs/…` son relativas a ese repo; `Backend-PrestaMeDios/…` y `Frontend-PrestaMeDios/…` son los repos hermanos.

Ramas de Backend y Frontend: `main` (entregas), `staging`, `develop` (integración), `feat/<tema>` y `fix/<tema>`.

---

## 3\. Dominios y responsables

| Perfil | Dominio | Módulo backend | Requisitos | Estado |
| :---- | :---- | :---- | :---- | :---- |
| **Perfil 1** | Identidad, Usuarios e Historiales, Permisos, Configuración Global y Despliegue | `core`, `users`, `config`, `files` | USR-01…09, GLO-01, GLO-03, GLO-05, GLO-06, despliegue (Docker, CI) | SPEC-01 (v1.0.0) y SPEC-02 (v1.0.1) en `develop`. SPEC-03 (v1.1.0): Fase A en `develop` (PR \#18); B2 (archivos y foto) en revisión (backend PR \#26, frontend PR \#14); B1 (USR-02 y correo) en revisión (backend PR \#27, frontend PR \#15); sigue B3 (sesión). Pendientes: USR-06…09, GLO-05, despliegue |
| **Perfil 2** | Catálogo y Existencias | `inventory` | PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 | Implementado (SPEC-04, Fase A) en backend y frontend. Pendiente la Fase B (disponibilidad por fechas e historial por unidad), que depende de `loans` |
| **Perfil 3** | Préstamos y Concurrencia | `loans` | PRE-03…11, PRE-13, PRE-15…18, PRE-20 | SPEC-05 v1.0.0 `APROBADO`. Fase 1 implementada en `develop` (PR \#21); Fase 2 (validar) en el PR \#23 (`feat/loans-validar`), salvo T2.9, T2.10 y T2.13 (DT-16, DT-20) |
| **Perfil 4** | Espacios (infraestructura física) | `spaces` | RES-01…05, GLO-02, GLO-04 | Implementado con auth y alcance de sede (SPEC-02) |
| **Perfil 5** | Comunicaciones e IA | `notifications`, `assistant` | NOV-01…04, IA-01…03 | Pendiente (sin módulos) |

> Responsabilidades, estado detallado, interfaces entre perfiles y prompts de arranque: `docs/perfiles.md`. La asignación nominal de los perfiles 2–5 se gestiona en ClickUp. Un agente que trabaja para un perfil **no modifica módulos ajenos**: documenta el cambio necesario como ítem de coordinación en el spec y en `MEMORY.md`.

---

## 4\. Flujo de trabajo obligatorio (Spec-Driven Development)

1. **Leer** la Constitución, este archivo, `docs/perfiles.md`, `MEMORY.md` y los requisitos relevantes de `docs/ERS.md`.  
2. **Especificar:** redactar o actualizar `specs/NN-<slug>/spec.md` (estado `BORRADOR`). Presentarlo al usuario.  
3. **Esperar aprobación explícita.** Sin spec `APROBADO` no se escribe código de aplicación.  
4. **Planificar:** `specs/NN-<slug>/plan.md` (archivos a crear/modificar, migraciones, dependencias nuevas).  
5. **Descomponer:** `specs/NN-<slug>/tasks.md` (tareas pequeñas, verificables, ordenadas).  
6. **Implementar** tarea por tarea, con tests de cada criterio de aceptación.  
7. **Verificar:** correr tests; confirmar trazabilidad requisito → endpoint → test.  
8. **Registrar** decisiones y deuda técnica nuevas en `MEMORY.md`.

Si el spec resulta incorrecto durante la implementación: **detenerse, proponer la corrección del spec y pedir re-aprobación**.

---

## 5\. Comandos

### Backend (`Backend-PrestaMeDios/`)

```sh
python -m venv .venv && source .venv/bin/activate      # Python ≥ 3.11 (validado con 3.12)
pip install -r requirements-dev.txt                    # incluye requirements.txt + pytest/httpx/cov
cp .env.example .env                     # DATABASE_URL, JWT_SECRET_KEY (obligatoria, ≥ 32 car.), TEST_DATABASE_URL…
alembic upgrade head                     # requiere extensión btree_gist en PostgreSQL
python -m app.modules.users.cli crear-superadmin --email … --nombre … --apellido … --dni …
uvicorn app.main:app --reload            # http://localhost:8000 · Swagger en /docs
pytest -q                                # integración contra TEST_DATABASE_URL (se omiten si no está)
pytest --cov=app/core --cov=app/modules/users --cov=app/modules/config
```

> La app **no arranca** sin `JWT_SECRET_KEY`. `TEST_DATABASE_URL` debe apuntar a una base cuyo nombre contenga `test`: el fixture la recrea desde cero en cada corrida.

### Frontend (`Frontend-PrestaMeDios/`)

```sh
npm install
npm run dev                              # http://localhost:8443 (VITE_API_URL → backend)
npm run build
```

---

## 6\. Convenciones de código (extraídas del código existente)

### Backend

- **SQLAlchemy 2.0 async** con `Mapped[...]`/`mapped_column`; todos los modelos heredan de `app.database.Base`.  
- **Enums de dominio** como `StrEnum` en `enums.py` del módulo; persistidos con `SAEnum(..., values_callable=enum_values, name="<x>_enum")` (`enum_values` de `app/core/enums.py`). Hoy conviven tres estilos de valores (`core`: `ACTIVO`; `inventory`/`loans`: `disponible`; `spaces`: `Pendiente`); unificarlos está pendiente de decisión (DT-09, DT-19).  
- **Esquemas Pydantic v2**: `*Create` con `_INPUT_CONFIG = ConfigDict(extra="forbid", str_strip_whitespace=True)`; `*Response` con `ConfigDict(from_attributes=True)`; `Field(..., examples=[...])` en todos los campos.  
- **Routers** por módulo, montados en `main.py` con `prefix="/api/v1/<modulo>"` y `tags` en español.  
- **Unicidad / concurrencia:** traducir `IntegrityError` a `409` (ver `_commit_or_409` en `inventory/router.py`).  
- **Integridad temporal** en base de datos (ej. `ExcludeConstraint` GIST en `reservas_espacios`).  
- **Cambios de estado:** `PATCH /<recurso>/{id}/estado`.  
- **Migraciones** manuales y reversibles: `alembic/versions/000N_<desc>.py`; registrar los modelos nuevos en `alembic/env.py`.  
- Docstrings en español que referencien el requisito (`"""... (PRE-14)."""`).

### Frontend

- Feature-first: `src/features/<dominio>/{components,pages,services,types}`.  
- DTOs `snake_case` espejo de Pydantic \+ `mappers.ts` hacia view models.  
- Cliente HTTP compartido `src/lib/api.ts` (base `VITE_API_URL`, header `Authorization`, errores normalizados a `ApiError {status, code, detail}`); cada feature define su ruta `/api/v1/<modulo>`.  
- Sesión y sede vista con `useAuth()` / `useSede()` de `src/features/auth/AuthContext.tsx`.  
- Tema claro/oscuro vía `ThemeCtx` (`src/theme.ts`).

### Seguridad (SPEC-01)

- Endpoints protegidos con `Depends(get_current_user)` / `Depends(require_roles(...))` desde `app/core/deps.py`.  
- Filtrado por jurisdicción con `resolver_alcance_sede(...)`; nunca confiar en `id_usuario` o `sede` enviados en el body.  
- Errores de negocio con `AppError(status, "CODIGO", "mensaje")` de `app/core/errors.py` (respuesta `{detail, code}`).  
- Reglas operativas (plazos, horario, anticipación mínima) con `await obtener_parametro(db, "<clave>")` de `app/modules/config/service.py`; no codificarlas.  
- `SedeEnum` canónico en `app/core/enums.py` (`inventory.enums` lo re-exporta).

### Tests

- Fixtures en `tests/conftest.py`: `client` (httpx async), `db`, `crear_usuario(rol, sede, estado)` y `auth(usuario)` → header `Authorization`.  
- Marcar los tests que usan base de datos con `pytestmark = pytest.mark.integracion`.  
- Anotar cada test con el criterio que cubre (`# AC-NN`, `# EC-NN`).

---

## 7\. Reglas para agentes

**Siempre**

- Citar el requisito (`USR-05`, `GLO-03`…) en specs, docstrings y descripciones de PR.  
- Preferir editar archivos existentes a crear nuevos.  
- Validar en backend y garantizar invariantes en PostgreSQL.  
- Mantener el aislamiento de sedes y la privacidad entre usuarios.  
- Referenciar código como `ruta/archivo.py:linea`.

**Nunca**

- Generar código de aplicación sin spec aprobado.  
- Versionar secretos, `.env`, logs (`uvicorn.log`, `uvicorn.err`) o credenciales por defecto.  
- Hacer commit, push, merge o cambiar configuración de Git sin pedido explícito.  
- Reintroducir el rol "Administrador ICSE" (eliminado en la Iteración 2).  
- Hacer que el asistente IA acceda directamente a la base de datos.  
- Usar SQLite para tests de integración.  
- Modificar módulos de otro perfil sin indicación explícita.

---

## 8\. Entorno conocido

- Puertos: backend `8000`, frontend `8443` (CORS por defecto apunta a `http://localhost:8443`).