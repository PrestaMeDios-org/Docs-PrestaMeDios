# PLAN-02 — Plan técnico de implementación de SPEC-02

| Campo | Valor |
| --- | --- |
| **Spec** | `specs/02-integracion-seguridad-cuenta/spec.md` (v1.0.1, `IMPLEMENTADO`) |
| **Estado del plan** | `COMPLETADO` — 2026-10-08 (cierre documental 2026-10-23, ver §6) |
| **Ramas** | Backend `feat/spec-02-integracion` · Frontend `feat/login-auth-ui` (ambas desde `develop`) |
| **Integración** | Mergeado en `develop` después de la demo: backend PR #7 (2026-10-10) y `074158e` (2026-10-13); frontend PR #4 (2026-10-10) |

---

## 1. Punto de partida (`develop` al 2026-10-08)

El PR #6 de `spaces` (b4c742a) ya incorporó, antes de este plan:

| Ya existe en `develop` | Impacto en SPEC-02 |
| --- | --- |
| Validación de bloqueos al crear reservas y al aprobar; un bloqueo no puede pisar reservas activas | V6 de §3.3 ya cubierta: se conserva y se traduce a `AppError` |
| Transiciones `Pendiente → Aprobada/Rechazada/Cancelada`, `Aprobada → En_Uso/Cancelada`, `En_Uso → Finalizada` | Se conservan; SPEC-02 §3.4 se amplía con `En_Uso`/`Finalizada` para administradores (v1.0.1) |
| `intervalos_disponibles` en `/disponibilidad`, módulo `availability.py` con horario fijo 09:00–16:00 | Se conserva el campo; el horario pasa a recibirse por parámetro (desde `config`) |
| Validación de bloqueo parcial entre 09:00 y 16:00 en el esquema | Pasa al servicio usando el horario de `config` |
| Tests unitarios con sesiones simuladas (`tests/test_spaces_availability.py`) | Se reemplazan por tests de integración equivalentes contra PostgreSQL (NFR-13) |

El frontend (79bd91e) ya consume `intervalos_disponibles` y resolvió el build sin `.figma/`.

---

## 2. Dependencias nuevas

| Repo | Paquete | Uso |
| --- | --- | --- |
| Backend | `tzdata` | Zona `America/Argentina/Ushuaia` en cualquier SO (D-05) |
| Frontend (dev) | `vitest` | Tests unitarios del cliente HTTP y de sesión (NFR-14) |

---

## 3. Backend

### 3.1 Archivos

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `app/core/settings.py` | Modificar | `ZONA_HORARIA_LAB`, `ahora_lab()` |
| `app/core/deps.py` | Modificar | `get_current_user` aplica `CAMBIO_PASSWORD_REQUERIDO`; nueva `get_current_user_permitiendo_cambio`; helper `sede_para_alta(actor, sede)` (PRE-19) |
| `app/modules/users/models.py` | Modificar | `debe_cambiar_password`; modelo `UsuarioHistorialCambios` |
| `app/modules/users/schemas.py` | Modificar | `PerfilUpdate`, `CambioPasswordRequest`, `UsuarioAdminUpdate`; `debe_cambiar_password` en `UsuarioPublico` |
| `app/modules/users/service.py` | Modificar | `actualizar_perfil`, `cambiar_password`, `editar_por_admin`; flag en `crear_por_admin` |
| `app/modules/users/router.py` | Modificar | `PATCH /auth/me`, `POST /auth/me/password`, `PATCH /users/{id}` |
| `app/modules/spaces/models.py` | Modificar | `sede: SedeEnum`; FK `id_usuario` |
| `app/modules/spaces/schemas.py` | Modificar | Contratos §3.2 de SPEC-02 (sin `id_usuario` en el alta, `sede`, disponibilidad sin identidad) |
| `app/modules/spaces/availability.py` | Modificar | Funciones parametrizadas por `apertura`/`cierre` |
| `app/modules/spaces/service.py` | Crear | Validaciones V1–V8, transiciones, alcance de sede |
| `app/modules/spaces/router.py` | Reescribir | Delgado: contrato + permisos → servicio |
| `app/modules/inventory/schemas.py` | Modificar | `UnidadFisicaCreate.sede` opcional; `max_dias_prestamo` opcional |
| `app/modules/inventory/router.py` | Modificar | Auth, alcance, PRE-19, `AppError`, default desde `config` |
| `alembic/versions/0007_spaces_sede_y_usuario.py` | Crear | §3.1 de SPEC-02 |
| `alembic/versions/0008_usuarios_perfil.py` | Crear | §5.1 de SPEC-02 |
| `tests/conftest.py` | Modificar | Fábricas `crear_espacio`, `crear_reserva`; parámetros con anticipación configurable |
| `tests/spaces/*`, `tests/inventory/*`, `tests/users/test_perfil.py`, `tests/users/test_edicion.py` | Crear | AC-31…AC-49 |
| `tests/test_spaces_availability.py`, `tests/test_spaces_schemas.py` | Reemplazar | Casos equivalentes migrados a `tests/spaces/` |

> **Numeración de migraciones:** `develop` ya contiene `0001`–`0006` (SPEC-01 + `0006_inventory_init`); las nuevas son `0007` y `0008`.

### 3.2 Decisiones de diseño

- **Hora local del laboratorio.** `ahora_lab()` devuelve `datetime.now(ZoneInfo("America/Argentina/Ushuaia"))`; el inicio de una reserva se construye como `datetime.combine(fecha, hora_inicio, tzinfo=TZ)`.
- **Rangos semiabiertos** `[inicio, fin)` en solapamientos (EC-24), igual que la restricción GIST.
- **Cambio obligatorio de contraseña.** Se implementa en `get_current_user` (por defecto bloquea); `/auth/me` (GET) y `/auth/me/password` usan la variante permisiva. Así ningún endpoint nuevo puede olvidarlo.
- **Auditoría de ediciones.** `cambios` JSONB `{campo: [antes, después]}`; la contraseña se registra como `["***", "***"]`.
- **Errores.** Todo `HTTPException` de `spaces` e `inventory` migra a `AppError` con los códigos de SPEC-02 §7.

### 3.3 Migraciones

| Migración | `upgrade` | `downgrade` |
| --- | --- | --- |
| `0007` | `espacios.sede` desde `id_sede` (1/2; otro valor → `RAISE EXCEPTION`); borra reservas huérfanas con `RAISE NOTICE`; FK `id_usuario`; índice `ix_espacios_sede` | Restaura `id_sede` (mapeo inverso), quita FK |
| `0008` | `usuarios.debe_cambiar_password`; tabla `usuarios_historial_cambios` | Inversa |

Verificación: `upgrade head` → `downgrade base` → `upgrade head` sobre base vacía; `0007` probado con datos reales de la forma vieja (AC-39).

---

## 4. Frontend

| Archivo | Acción | Contenido |
| --- | --- | --- |
| `src/lib/api.ts` | Crear | `apiRequest`, `ApiError`, token, evento de sesión expirada |
| `src/features/auth/{AuthContext.tsx,SedeContext.tsx,types.ts,authApi.ts,roles.ts}` | Crear | Sesión, sede vista, DTOs, `uiRole()` |
| `src/features/auth/pages/{LoginPage,RegisterPage,ChangePasswordPage}.tsx` | Crear | §6.2 de SPEC-02 |
| `src/features/users/{types,services,pages}` | Crear | Mi perfil, gestión de usuarios |
| `src/features/config/{types,services,pages}` | Crear | Panel de parámetros |
| `src/App.tsx`, `src/main.tsx`, `src/types.ts` | Modificar | Providers, gate de sesión, pantallas nuevas; sin `icse` |
| `src/components/layout/{Navbar,Sidebar,MainLayout}.tsx` | Modificar | Usuario real, selector de sede, cerrar sesión; menú por rol |
| `src/features/spaces/{services/spacesApi.ts,pages/SpacesPage.tsx,types}` | Modificar | Cliente compartido, `sede`, sin `id_usuario`, horario de la API |
| `src/features/inventory/services/inventoryApi.ts`, `pages/CatalogPage.tsx` | Modificar | Cliente compartido; sede de la sesión |
| `package.json` | Modificar | Scripts `typecheck`, `test`; `vitest` |

Ruteo: se mantiene el estado `screen` (D-09); las pantallas de autenticación se renderizan fuera del layout.

---

## 5. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| Conflictos con trabajo paralelo de colegas en `spaces` (front y back) | Rama desde el `develop` más reciente; PR con descripción de cada cambio en su módulo |
| La demo del 09/10 usa `develop` sin auth | D-01: nada de esta rama se mergea antes de la demo |
| Datos de desarrollo de colegas con `id_sede` ≠ 1/2 | `0007` aborta con mensaje claro (no corrompe) |
| Node no instalado en el sistema | Node 22 portátil en `/tmp/opencode` para verificar `typecheck`/`build`/`test` |

---

## 6. Desviaciones respecto del plan (registradas el 2026-10-23)

| Plan | Implementado | Impacto |
| --- | --- | --- |
| `src/features/auth/SedeContext.tsx` como archivo propio (también en SPEC-02 §6.1) | `useSede()` y el estado de sede viven dentro de `src/features/auth/AuthContext.tsx` | Ninguno funcional; los componentes usan `useSede()` |
| `src/features/auth/pages/ChangePasswordPage.tsx` | `src/features/auth/pages/ChangePasswordForm.tsx` | Sólo cambia el nombre |
| Riesgo "Node portátil en `/tmp/opencode`" | Específico del entorno de la sesión de implementación | No aplica a otros entornos |
