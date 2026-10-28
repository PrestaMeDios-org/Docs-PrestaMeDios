# SPEC-02 — Integración de seguridad en Espacios e Inventario, Gestión de Cuenta y Frontend de Identidad

| Campo | Valor |
| --- | --- |
| **ID** | SPEC-02 |
| **Perfil responsable** | Perfil 1 — Identidad, Usuarios, Permisos y Configuración Global |
| **Estado** | `IMPLEMENTADO` — 2026-10-08 (verificación en `specs/02-integracion-seguridad-cuenta/tasks.md`) |
| **Versión** | 1.0.1 |
| **Fecha** | 2026-10-08 |
| **Requisitos cubiertos** | GLO-01, GLO-02, GLO-03 (consumo), USR-03, USR-04 (edición), USR-05 (UI), RES-01…RES-05 (seguridad), RES-04/GLO-04 (bloqueos efectivos), PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 (seguridad) |
| **Depende de** | SPEC-01 v1.0.0 (`IMPLEMENTADO`, mergeado en `develop`) |
| **Módulos afectados** | Backend: `core`, `users`, `spaces`, `inventory` · Frontend: `auth` (nuevo), `users` (nuevo), `config` (nuevo), `spaces`, `inventory`, `layout` |
| **Autorización de módulos ajenos** | Los responsables de `inventory` y `spaces` autorizaron las modificaciones (2026-10-07) |
| **Fuente de verdad funcional** | `docs/ERS.md` |
| **Gobernado por** | `docs/constitution.md` |

> **Regla SDD:** documento `APROBADO`; la implementación debe ajustarse a él. Cualquier cambio requiere nueva versión en §14 y re-aprobación.

---

## 0. Resumen ejecutivo

SPEC-01 construyó la identidad (usuarios, JWT, roles, sedes, parámetros), pero **ningún endpoint de negocio la usa todavía** y el frontend sigue simulando el rol con un selector. Este spec cierra esa brecha en tres frentes:

1. **Integración (backend):** `spaces` e `inventory` exigen sesión, aplican roles y aislamiento de sede, toman el usuario del token y leen reglas operativas de `config` (horario, anticipación mínima y máxima). Se resuelven DT-02, DT-03, DT-06 (parcial), DT-10 y DT-14.
2. **Cuenta (backend, Perfil 1):** el usuario edita sus datos de contacto y su contraseña (USR-03); el administrador edita perfiles, rol y sede (USR-04); las cuentas creadas por un administrador exigen cambiar la contraseña en el primer ingreso.
3. **Frontend de identidad:** login, registro, sesión real, pantalla de perfil, directorio y bandeja de aprobación de usuarios, panel de parámetros y selector de sede del Superadministrador. Se elimina el selector de rol simulado y el rol `icse`.

> ⚠️ **Riesgo de demo (09/10):** proteger los endpoints rompe el frontend actual. Backend y frontend de este spec deben **integrarse a `develop` juntos** (D-01). Hasta entonces, `develop` queda como está.

---

## 1. Alcance

### 1.1 Dentro del alcance

| # | Capacidad | Requisitos |
| --- | --- | --- |
| A1 | `spaces`: sede como `SedeEnum`; usuario de la reserva tomado del token; FK a `usuarios` | GLO-01, DT-02, DT-03 |
| A2 | `spaces`: autorización por rol y sede en todos los endpoints | GLO-01, RES-01…05 |
| A3 | `spaces`: validación de horario (config), anticipación mínima y máxima, bloqueos y franja ya adjudicada al crear reservas | GLO-02, GLO-03, RES-02, RES-04, D-07 de SPEC-01 |
| A4 | `spaces`: transiciones de estado válidas; cancelación por el propio usuario | RES-03, RES-05 |
| A5 | `spaces`: disponibilidad sin exponer identidad de otros usuarios; horario operativo en la respuesta | P6, RES-01 |
| A6 | `inventory`: autenticación, alcance de sede en lectura, roles en escritura, sede automática para `ADMIN_LOCAL` | GLO-01, PRE-01, PRE-02, PRE-12, PRE-14, PRE-19 |
| A7 | `inventory`: plazo por defecto del equipamiento leído de `config` | GLO-03, DT-06 |
| A8 | Perfil propio: editar teléfono y email; cambiar contraseña | USR-03 |
| A9 | Cambio obligatorio de contraseña en el primer ingreso de cuentas creadas por un administrador | SPEC-01 UC-06 |
| A10 | Edición administrativa de perfiles (datos, rol, sede) con jurisdicción y auditoría | USR-04, USR-08 |
| A11 | Frontend: login, registro, sesión, cierre de sesión por token inválido | USR-01, USR-05 |
| A12 | Frontend: perfil, directorio + bandeja de aprobación, alta de cuentas, panel de parámetros, selector de sede | USR-03, USR-04, USR-05, GLO-01, GLO-03 |
| A13 | Frontend: `spaces` consume la API autenticada (sin `id_usuario` simulado ni horario fijo) | GLO-02, RES-01…03 |

### 1.2 Fuera del alcance

| Capacidad | Requisito | Destino |
| --- | --- | --- |
| Recuperación de contraseña por email | USR-02 | SPEC-03 (requiere infraestructura de correo) |
| Foto de perfil | USR-03 (parcial) | SPEC-03, junto con el almacenamiento de archivos que también necesita el PDF de PRE-05 (D-04) |
| Refresh token / "recordarme" | D-06 de SPEC-01 | SPEC-03 |
| Catálogo del frontend conectado a la API real (hoy usa mocks) | PRE-01 | Responsable de `inventory` |
| Estados de reserva como `ENUM` de PostgreSQL | DT-09 | Responsable de `spaces` |
| Préstamos, notificaciones, asistente IA | PRE-03…, NOV-*, IA-* | Specs de sus módulos |

---

## 2. Modelo de autorización transversal

Se reutilizan los artefactos de SPEC-01 (`get_current_user`, `require_roles`, `resolver_alcance_sede`, `AppError`, `obtener_parametro`). Regla general para todo recurso con sede:

| Operación | `ESTUDIANTE` / `DOCENTE` | `ADMIN_LOCAL` | `SUPERADMIN` |
| --- | --- | --- | --- |
| Leer recursos con sede | Sólo su sede (filtro forzado) | Sólo su sede (filtro forzado) | Ambas o la filtrada |
| Pedir explícitamente otra sede | `403 SEDE_FUERA_DE_ALCANCE` | `403 SEDE_FUERA_DE_ALCANCE` | Permitido |
| Acceder por ID a un recurso de otra sede | `404 <RECURSO>_NO_ENCONTRADO` | `404 <RECURSO>_NO_ENCONTRADO` | Permitido |
| Crear recursos con sede | — | Sede asignada automáticamente; si envía otra: `403 SEDE_FUERA_DE_ALCANCE` | Sede **obligatoria** (`422 SEDE_REQUERIDA`) |

> El backend **nunca** toma `id_usuario` ni la sede del solicitante desde el body o los query params (Constitución P4/P5).

---

## 3. Integración en `spaces`

### 3.1 Cambios de modelo

| Tabla | Cambio | Motivo |
| --- | --- | --- |
| `espacios` | `id_sede INTEGER` → `sede sede_enum NOT NULL` (índice `ix_espacios_sede`) | D-01 de SPEC-01, DT-02 |
| `reservas_espacios` | FK `fk_reservas_espacios_id_usuario_usuarios` → `usuarios.id` `ON DELETE RESTRICT` | DT-03, integridad (P7) |

**Migración `0007_spaces_sede_y_usuario`** (reversible):

1. Agrega `espacios.sede` (nullable), la completa con el mapeo `1 → 'Ushuaia'`, `2 → 'Río Grande'`; si existe otro valor aborta con un mensaje explícito (D-02); la pasa a `NOT NULL` y elimina `id_sede`.
2. Elimina reservas cuyo `id_usuario` no exista en `usuarios` (datos de la demo sin autenticación) informando la cantidad con `RAISE NOTICE` (D-03); crea la FK.
3. `downgrade`: restaura `id_sede` con el mapeo inverso y quita la FK (las reservas eliminadas no se recuperan; se documenta).

### 3.2 Contratos y permisos

| Método | Ruta | Roles | Cambio respecto de hoy |
| --- | --- | --- | --- |
| `GET` | `/api/v1/spaces/espacios?sede=` | Todos (autenticados) | `id_sede` → `sede`; alcance forzado |
| `POST` | `/api/v1/spaces/espacios` | `ADMIN_LOCAL`, `SUPERADMIN` | Body `{nombre, tipo, sede?}`; regla de creación §2 |
| `GET` | `/api/v1/spaces/disponibilidad?fecha=&sede=&id_espacio=` | Todos | `id_sede` → `sede` (opcional; forzado salvo `SUPERADMIN`); respuesta sin identidad de usuarios + horario |
| `POST` | `/api/v1/spaces/reservas` | `ESTUDIANTE`, `DOCENTE` | Body **sin** `id_usuario` ni `estado_reserva`; validaciones §3.3 |
| `GET` | `/api/v1/spaces/reservas?id_espacio=&fecha=&estado=` | Todos | Estudiante/Docente: sólo las propias. Admin: las de su alcance. Se elimina el filtro `id_usuario` para no administradores |
| `PATCH` | `/api/v1/spaces/reservas/{id}/estado` | Todos (con reglas §3.4) | Dueño puede cancelar; admin aprueba/rechaza/cancela en su sede |
| `POST` | `/api/v1/spaces/bloqueos` | `ADMIN_LOCAL`, `SUPERADMIN` | Sólo sobre espacios de su alcance |
| `GET` | `/api/v1/spaces/bloqueos?id_espacio=&fecha=` | Todos | Alcance de sede |

**`EspacioResponse`**: `{id_espacio, nombre, tipo, sede}`.

**`ReservaEspacioCreate`** (`extra="forbid"`): `{id_espacio, fecha_reserva, hora_inicio, hora_fin, motivo?}`. Enviar `id_usuario` → `422`.

**`ReservaEspacioResponse`**: igual que hoy (`id_reserva, id_usuario, id_espacio, fecha_reserva, hora_inicio, hora_fin, estado_reserva, motivo, created_at`). Sólo se devuelve al dueño o a un administrador con jurisdicción.

**`DisponibilidadResponse`**:

```json
{
  "fecha": "2026-10-12",
  "sede": "Ushuaia",
  "id_espacio": 3,
  "horario_apertura": "09:00",
  "horario_cierre": "16:00",
  "franjas_ocupadas": [
    { "id_espacio": 3, "hora_inicio": "10:00:00", "hora_fin": "11:30:00", "estado_reserva": "Aprobada" }
  ],
  "bloqueos": [ { "id_bloqueo": 15, "id_espacio": 3, "fecha_inicio": "2026-10-12", "fecha_fin": "2026-10-12",
                  "hora_inicio": null, "hora_fin": null, "motivo": "Feriado" } ]
}
```

> `franjas_ocupadas` reemplaza a `reservas_ocupadas` y **no incluye `id_usuario` ni `id_reserva`** (P6: un estudiante no puede conocer la identidad de otros solicitantes).
>
> Se conserva además el campo `intervalos_disponibles` (`[{id_espacio, intervalos_libres: [{hora_inicio, hora_fin}]}]`) incorporado por el PR #6, calculado con el horario de `config` en lugar del fijo 09:00–16:00.

### 3.3 Validaciones al crear una reserva (`POST /reservas`)

Se evalúan en este orden; la hora se interpreta en la zona del laboratorio `America/Argentina/Ushuaia` (ambas sedes, D-05).

| # | Regla | Error |
| --- | --- | --- |
| V1 | `hora_fin > hora_inicio` (contrato) | `422` |
| V2 | El espacio existe y pertenece a la sede del usuario | `404 ESPACIO_NO_ENCONTRADO` |
| V3 | `horario.apertura ≤ hora_inicio` y `hora_fin ≤ horario.cierre` (de `config`) | `422 FUERA_DE_HORARIO` |
| V4 | `inicio ≥ ahora + solicitud.anticipacion_min_horas` | `422 ANTICIPACION_INSUFICIENTE` |
| V5 | `fecha_reserva ≤ hoy + reserva_espacio.anticipacion_max_dias` | `422 FUERA_DE_VENTANA` |
| V6 | No se solapa con un bloqueo del espacio (día completo o franja) | `409 ESPACIO_BLOQUEADO` |
| V7 | No se solapa con una reserva `Aprobada`/`En_Uso` del espacio | `409 FRANJA_OCUPADA` |
| V8 | El mismo usuario no tiene otra reserva `Pendiente`/`Aprobada` que se solape en ese espacio | `409 RESERVA_DUPLICADA` |

Las reservas `Pendiente` de **otros** usuarios no impiden crear una nueva (RES-02: solicitudes concurrentes permitidas). La restricción GIST existente sigue siendo la garantía final al aprobar.

> Se elimina el validador fijo 09:00–16:00 de `spaces/schemas.py`: el horario pasa a ser configurable (GLO-03). Los tests de contrato que lo verificaban se reemplazan por tests de integración de V3.

### 3.4 Transiciones de estado de reserva

| Actor | Desde | Hacia | Reglas |
| --- | --- | --- | --- |
| Admin con jurisdicción | `Pendiente` | `Aprobada` | Rechaza automáticamente las `Pendiente` solapadas (comportamiento actual, RES-05) |
| Admin con jurisdicción | `Pendiente` | `Rechazada` | `motivo_rechazo` obligatorio (actual) |
| Admin con jurisdicción | `Pendiente`, `Aprobada` | `Cancelada` | Cancelación forzada; `motivo_rechazo` obligatorio |
| Admin con jurisdicción | `Aprobada` | `En_Uso` | Registro de uso efectivo (ya existente en `develop`, PR #6) |
| Admin con jurisdicción | `En_Uso` | `Finalizada` | Cierre del turno (ya existente en `develop`, PR #6) |
| Dueño (`ESTUDIANTE`/`DOCENTE`) | `Pendiente`, `Aprobada` | `Cancelada` | RES-03; motivo opcional; sólo si el inicio aún no ocurrió |
| Cualquier otro caso | | | `409 TRANSICION_INVALIDA` · dueño intentando aprobar/rechazar → `403 PERMISO_INSUFICIENTE` · reserva ajena fuera de alcance → `404 RESERVA_NO_ENCONTRADA` |

---

## 4. Integración en `inventory`

| Método | Ruta | Roles | Regla |
| --- | --- | --- | --- |
| `GET` | `/api/v1/inventory/categorias` | Todos | Categorías globales (sin sede) |
| `POST` | `/api/v1/inventory/categorias` | `ADMIN_LOCAL`, `SUPERADMIN` | Duplicado → `409 CATEGORIA_DUPLICADA` |
| `GET` | `/api/v1/inventory/equipamiento?sede=&categoria=&q=` | Todos | Las unidades se filtran por el alcance (§2). Estudiante/Docente ven sólo ítems con al menos una unidad en su sede; los administradores ven además los ítems sin unidades (alta reciente) |
| `GET` | `/api/v1/inventory/equipamiento/{id}?sede=` | Todos | Unidades filtradas por alcance; ítem sin unidades visibles para Estudiante/Docente → `404 EQUIPAMIENTO_NO_ENCONTRADO` |
| `POST` | `/api/v1/inventory/equipamiento` | `ADMIN_LOCAL`, `SUPERADMIN` | PRE-19 en cada unidad (§2). `max_dias_prestamo` omitido → valor de `prestamo.general.max_dias` |
| `POST` | `/api/v1/inventory/equipamiento/{id}/unidades` | `ADMIN_LOCAL`, `SUPERADMIN` | PRE-19 |
| `GET` | `/api/v1/inventory/unidades?sede=&estado=&equipamiento_id=` | `ADMIN_LOCAL`, `SUPERADMIN` | PRE-12 (vista de stock de administración); alcance §2 |
| `PATCH` | `/api/v1/inventory/unidades/{id}/estado` | `ADMIN_LOCAL`, `SUPERADMIN` | Unidad de otra sede → `404 UNIDAD_NO_ENCONTRADA` (PRE-14) |

**Cambio de contrato:** `UnidadFisicaCreate.sede` pasa a ser **opcional** (la completa el servidor para `ADMIN_LOCAL`). Errores existentes migran a `AppError`: `CATEGORIA_INEXISTENTE` (422), `INVENTARIO_DUPLICADO` (409), `EQUIPAMIENTO_NO_ENCONTRADO`, `UNIDAD_NO_ENCONTRADA` (404).

---

## 5. Gestión de cuenta (Perfil 1)

### 5.1 Cambios de modelo (migración `0008_usuarios_perfil`)

| Tabla / columna | Definición | Motivo |
| --- | --- | --- |
| `usuarios.debe_cambiar_password` | `BOOLEAN NOT NULL DEFAULT false` | A9 |
| `usuarios_historial_cambios` | `id BIGINT PK`, `usuario_id FK→usuarios ON DELETE CASCADE`, `actor_id FK→usuarios ON DELETE SET NULL`, `cambios JSONB NOT NULL` (`{campo: [antes, después]}`), `created_at TIMESTAMPTZ` | Auditoría de ediciones (USR-08, RN-22) |

> En `cambios` nunca se guardan contraseñas ni hashes: un cambio de contraseña se registra como `{"password": ["***", "***"]}`.

### 5.2 Endpoints

| Método | Ruta | Roles | Caso de uso |
| --- | --- | --- | --- |
| `PATCH` | `/api/v1/auth/me` | Todos | UC-10 Editar datos de contacto |
| `POST` | `/api/v1/auth/me/password` | Todos (incluso con cambio obligatorio pendiente) | UC-11 Cambiar contraseña |
| `PATCH` | `/api/v1/users/{id}` | `ADMIN_LOCAL`, `SUPERADMIN` | UC-12 Edición administrativa |

### UC-10 — Editar datos de contacto (USR-03)

**Request `PerfilUpdate`** (`extra="forbid"`; al menos un campo):

| Campo | Reglas |
| --- | --- |
| `telefono` | `string \| null` (mismo patrón que SPEC-01); `null` lo borra |
| `email` | `EmailStr`, normalizado. **Requiere `password_actual`** |
| `password_actual` | Obligatorio sólo si cambia `email` |

| Código | `code` | Cuándo |
| --- | --- | --- |
| `200` | — | `UsuarioPublico` actualizado |
| `403` | `PASSWORD_ACTUAL_INCORRECTA` | Cambio de email con contraseña incorrecta o ausente |
| `409` | `EMAIL_YA_REGISTRADO` | Email en uso |
| `422` | — | Campos protegidos (`dni`, `nombre`, `apellido`, `rol`, `sede`, `estado`…), payload vacío o inválido |

### UC-11 — Cambiar contraseña (USR-03, A9)

**Request** `{password_actual, password_nueva}`; `password_nueva` cumple RN-03 de SPEC-01 y es distinta de la actual.

- Éxito `200` → `TokenResponse` con un **token nuevo**: se incrementa `token_version` (se cierran las demás sesiones), se pone `debe_cambiar_password = false` y se registra en el historial de cambios.
- `403 PASSWORD_ACTUAL_INCORRECTA` · `422` contraseña débil o igual a la actual.

### Cambio obligatorio en el primer ingreso (A9)

- `POST /users` (alta por `SUPERADMIN`) y el reseteo de contraseña por un administrador (UC-12) dejan `debe_cambiar_password = true`. El CLI de bootstrap **no** (el Superadministrador elige su propia contraseña).
- El login funciona y devuelve `usuario.debe_cambiar_password = true`.
- Mientras el flag sea `true`, **todo** endpoint protegido responde `403 CAMBIO_PASSWORD_REQUERIDO`, salvo `GET /auth/me` y `POST /auth/me/password`.

### UC-12 — Edición administrativa de perfiles (USR-04)

**Request `UsuarioAdminUpdate`** (`extra="forbid"`; al menos un campo): `nombre`, `apellido`, `dni`, `telefono`, `email`, `rol`, `sede`, `password_nueva` (reseteo).

| Regla | Error |
| --- | --- |
| Objetivo fuera de la jurisdicción del `ADMIN_LOCAL` | `404 USUARIO_NO_ENCONTRADO` |
| `ADMIN_LOCAL` sobre un administrador | `403 PERMISO_INSUFICIENTE` |
| `ADMIN_LOCAL` asigna un rol distinto de `ESTUDIANTE`/`DOCENTE` | `403 PERMISO_INSUFICIENTE` |
| `ADMIN_LOCAL` cambia la sede (la cuenta saldría de su jurisdicción) | `403 SEDE_FUERA_DE_ALCANCE` |
| Coherencia rol–sede tras aplicar los cambios (RN-02) | `422` |
| Un administrador cambia su **propio** rol o sede | `403 OPERACION_SOBRE_SI_MISMO` (sus datos de contacto los edita por UC-10) |
| Quitar el rol al último `SUPERADMIN` activo | `409 ULTIMO_SUPERADMIN` |
| Email o DNI duplicados | `409 EMAIL_YA_REGISTRADO` / `DNI_YA_REGISTRADO` |

Efectos: cambio de `rol`, `sede` o `password_nueva` → `token_version + 1` (RN-08); `password_nueva` → `debe_cambiar_password = true`; toda edición → fila en `usuarios_historial_cambios`. Respuesta `200 UsuarioDetalle` (incluye `debe_cambiar_password`).

> Resuelve EC-21 de SPEC-01: una cuenta pendiente con sede equivocada la corrige el `SUPERADMIN` antes de aprobarla.

---

## 6. Frontend de identidad

### 6.1 Arquitectura

| Artefacto | Ubicación | Responsabilidad |
| --- | --- | --- |
| Cliente HTTP compartido | `src/lib/api.ts` | `BASE_URL` desde `VITE_API_URL`; header `Authorization`; normaliza errores a `ApiError {status, code, detail, campos?}` (incluye los `422` de FastAPI); ante `401` con `code` `TOKEN_*` dispara el cierre de sesión |
| Sesión | `src/features/auth/AuthContext.tsx` | `usuario`, `token`, `login`, `logout`, `refrescar` (`/auth/me`); token en `sessionStorage` (D-06); rehidrata al recargar |
| Selector de sede | `src/features/auth/SedeContext.tsx` | `sedeVista`: para `SUPERADMIN` elegible ("Ushuaia" / "Río Grande" / "Ambas sedes"); para el resto, fija en su sede (GLO-01) |
| Tipos espejo | `src/features/auth/types.ts`, `src/features/users/types.ts`, `src/features/config/types.ts` | DTOs `snake_case` 1:1 con Pydantic |
| Rol de UI | `src/types.ts` | `Role = "student" \| "teacher" \| "admin"` derivado de `RolUsuario` (`uiRole()`); **se elimina `icse`**. Los componentes de los colegas siguen recibiendo `role` (D-07) |

### 6.2 Pantallas

| Pantalla | Quién | Contenido | Requisitos |
| --- | --- | --- | --- |
| Login | Público | Email + contraseña; mensajes por `code` (pendiente, rechazada, suspendida con fecha, inactiva, credenciales) | USR-01 |
| Registro | Público | Formulario con validación en línea (RN-03), rol Estudiante/Docente, sede; pantalla final "pendiente de aprobación" | USR-01, USR-05 |
| Cambio obligatorio de contraseña | Usuario con flag | Bloquea el resto de la app hasta cambiarla | A9 |
| Mi perfil | Todos | Datos (protegidos en sólo lectura), editar teléfono/email, cambiar contraseña | USR-03 |
| Gestión de usuarios | Admins | Pestañas "Pendientes" (aprobar / rechazar con motivo) y "Directorio" (filtros por rol, estado, búsqueda; paginación; suspender, dar de baja, reactivar, editar); "Nueva cuenta" sólo `SUPERADMIN` | USR-04, USR-05, GLO-01 |
| Parámetros globales | `SUPERADMIN` edita; `ADMIN_LOCAL` sólo lee | Tabla con valor, unidad, rango; edición con manejo de `CONFLICTO_VERSION`; historial por clave | GLO-03 |
| Navbar | Todos | Nombre, rol y sede reales; selector de sede sólo `SUPERADMIN`; "Cerrar sesión". **Sin selector de rol** | GLO-01 |

### 6.3 Adaptación de `spaces` (frontend)

- `spacesApi.ts` usa el cliente compartido; elimina `id_usuario` de `createReserva` y de `listReservas`; `idSede: number` → `sede: Sede`.
- `SpacesPage.tsx` elimina `USER_BY_ROLE`; "mis reservas" = `GET /reservas` sin filtros (el backend devuelve las propias); horario de la grilla desde `horario_apertura`/`horario_cierre` de la disponibilidad; los errores `ANTICIPACION_INSUFICIENTE`, `FUERA_DE_HORARIO`, `ESPACIO_BLOQUEADO`, `FRANJA_OCUPADA` se muestran con su `detail`.
- La bandeja de administración muestra el nombre del solicitante cuando está disponible (admins) en lugar de `Usuario #id` sólo si no requiere endpoints nuevos; si no, se mantiene el id.

### 6.4 Adaptación de `inventory` (frontend)

- `inventoryApi.ts` usa el cliente compartido (header de autenticación).
- `CatalogPage` recibe `userSede` desde la sesión. La conexión del catálogo a la API real queda fuera (§1.2).

---

## 7. Catálogo de códigos de error nuevos

| `code` | HTTP | Mensaje sugerido |
| --- | --- | --- |
| `SEDE_REQUERIDA` | 422 | Indicá la sede del recurso. |
| `ESPACIO_NO_ENCONTRADO` | 404 | Espacio no encontrado. |
| `RESERVA_NO_ENCONTRADA` | 404 | Reserva no encontrada. |
| `FUERA_DE_HORARIO` | 422 | La reserva debe estar dentro del horario del laboratorio (HH:MM–HH:MM). |
| `ANTICIPACION_INSUFICIENTE` | 422 | Las solicitudes se envían con al menos N horas de anticipación. |
| `FUERA_DE_VENTANA` | 422 | Sólo se puede reservar hasta N días a futuro. |
| `ESPACIO_BLOQUEADO` | 409 | El espacio está bloqueado en esa franja: <motivo>. |
| `FRANJA_OCUPADA` | 409 | La franja ya fue adjudicada a otra reserva. |
| `RESERVA_DUPLICADA` | 409 | Ya tenés una solicitud para esa franja. |
| `CATEGORIA_DUPLICADA` | 409 | La categoría ya existe. |
| `CATEGORIA_INEXISTENTE` | 422 | La categoría indicada no existe. |
| `INVENTARIO_DUPLICADO` | 409 | Número de serie, código de inventario o código ya registrado. |
| `EQUIPAMIENTO_NO_ENCONTRADO` | 404 | Equipamiento no encontrado. |
| `UNIDAD_NO_ENCONTRADA` | 404 | Unidad física no encontrada. |
| `PASSWORD_ACTUAL_INCORRECTA` | 403 | La contraseña actual no es correcta. |
| `CAMBIO_PASSWORD_REQUERIDO` | 403 | Tenés que cambiar tu contraseña antes de continuar. |
| `BLOQUEO_CON_RESERVAS` | 409 | No se puede bloquear: existe una reserva aprobada o en uso en esa franja. *(v1.0.1: regla del PR #6)* |
| `MOTIVO_REQUERIDO` | 422 | Indicá el motivo de la cancelación administrativa. *(v1.0.1)* |
| `ALCANCE_INCOHERENTE` | 422 | Un SUPERADMIN no tiene sede; el resto de los roles requiere una. *(v1.0.1: código del 422 de UC-12)* |

Se reutilizan de SPEC-01: `NO_AUTENTICADO`, `TOKEN_*`, `PERMISO_INSUFICIENTE`, `SEDE_FUERA_DE_ALCANCE`, `TRANSICION_INVALIDA`, `OPERACION_SOBRE_SI_MISMO`, `ULTIMO_SUPERADMIN`, `EMAIL_YA_REGISTRADO`, `DNI_YA_REGISTRADO`, `USUARIO_NO_ENCONTRADO`.

> `PASSWORD_ACTUAL_INCORRECTA` es `403` y no `401` a propósito: un `401` cerraría la sesión en el frontend.

---

## 8. Reglas de negocio

| ID | Regla |
| --- | --- |
| RN-24 | Todo endpoint de `spaces` e `inventory` requiere sesión activa (salvo `/health`). |
| RN-25 | El solicitante de una reserva es siempre el usuario autenticado. |
| RN-26 | Sólo `ESTUDIANTE` y `DOCENTE` crean reservas de espacios (RES-02); los administradores gestionan, aprueban y bloquean. |
| RN-27 | Horario, anticipación mínima y ventana máxima se leen de `config` en cada operación (RN-21 de SPEC-01: rigen para operaciones nuevas). |
| RN-28 | Fechas y horas de reservas se interpretan en `America/Argentina/Ushuaia`. |
| RN-29 | Un bloqueo administrativo impide crear reservas que lo solapen (RES-04, GLO-04). |
| RN-30 | Ningún listado o disponibilidad expone a un estudiante la identidad de otros solicitantes (P6). |
| RN-31 | Las unidades físicas y espacios creados por un `ADMIN_LOCAL` reciben su sede automáticamente (PRE-19). |
| RN-32 | Cambiar email requiere la contraseña actual. Cambiar la contraseña cierra las demás sesiones. |
| RN-33 | Con `debe_cambiar_password = true` sólo se permite consultar el perfil y cambiar la contraseña. |
| RN-34 | Toda edición de perfil (propia o administrativa) queda en `usuarios_historial_cambios`, sin contraseñas. |

---

## 9. Criterios de aceptación

### 9.1 `spaces`

```gherkin
AC-31  Endpoints de spaces exigen sesión
  Cuando llamo a cualquier endpoint de /api/v1/spaces sin token → 401 NO_AUTENTICADO

AC-32  Aislamiento de espacios
  Dado espacios en Ushuaia y Río Grande
  Cuando un ESTUDIANTE de Ushuaia lista espacios → sólo ve los de Ushuaia
  Cuando pide ?sede=Río Grande → 403 SEDE_FUERA_DE_ALCANCE
  Cuando un SUPERADMIN lista sin filtro → ve ambos

AC-33  Alta de espacio con PRE-19
  ADMIN_LOCAL de Río Grande crea sin sede → 201 con sede "Río Grande"
  ADMIN_LOCAL de Río Grande crea con sede "Ushuaia" → 403 SEDE_FUERA_DE_ALCANCE
  SUPERADMIN crea sin sede → 422 SEDE_REQUERIDA
  ESTUDIANTE crea → 403 PERMISO_INSUFICIENTE

AC-34  La reserva pertenece al usuario del token
  Cuando un ESTUDIANTE crea una reserva válida → 201, id_usuario = su id, estado "Pendiente"
  Cuando envía id_usuario en el body → 422

AC-35  Validaciones de creación
  Espacio de otra sede → 404 ESPACIO_NO_ENCONTRADO
  08:00–09:00 con apertura 09:00 → 422 FUERA_DE_HORARIO
  Tras cambiar horario.cierre a 18:00, 16:00–17:00 → 201 (horario configurable)
  Inicio dentro de las próximas 24 h → 422 ANTICIPACION_INSUFICIENTE
  Con solicitud.anticipacion_min_horas = 0, mañana a primera hora → 201
  Fecha a 121 días → 422 FUERA_DE_VENTANA
  Solapa un bloqueo de día completo o de franja → 409 ESPACIO_BLOQUEADO
  Solapa una reserva Aprobada → 409 FRANJA_OCUPADA
  Solapa una Pendiente de otro usuario → 201
  Solapa una Pendiente propia → 409 RESERVA_DUPLICADA

AC-36  Privacidad de reservas
  Un ESTUDIANTE lista reservas → sólo las propias, aunque envíe ?id_usuario=<otro>
  La disponibilidad no incluye id_usuario ni id_reserva
  Un ADMIN_LOCAL lista reservas → sólo las de espacios de su sede

AC-37  Transiciones
  El dueño cancela su reserva Pendiente o Aprobada futura → 200 Cancelada
  El dueño intenta aprobar → 403 PERMISO_INSUFICIENTE
  Otro estudiante intenta cancelarla → 404 RESERVA_NO_ENCONTRADA
  ADMIN_LOCAL aprueba una reserva de otra sede → 404 RESERVA_NO_ENCONTRADA
  Aprobar una Rechazada → 409 TRANSICION_INVALIDA
  Admin cancela una Aprobada sin motivo → 422
  Aprobar sigue rechazando automáticamente las Pendientes solapadas (RES-05)

AC-38  Bloqueos con alcance
  ADMIN_LOCAL bloquea un espacio de otra sede → 404 ESPACIO_NO_ENCONTRADO
  DOCENTE crea un bloqueo → 403 PERMISO_INSUFICIENTE

AC-39  Migración 0007
  Sobre una base con espacios id_sede 1 y 2 y reservas huérfanas:
  upgrade → espacios con sede "Ushuaia"/"Río Grande", huérfanas eliminadas, FK creada
  downgrade → id_sede restaurado
  id_sede = 3 → la migración aborta con mensaje explícito
```

### 9.2 `inventory`

```gherkin
AC-40  Inventario exige sesión → 401 sin token en todos los endpoints

AC-41  Alcance de lectura
  ESTUDIANTE de Ushuaia lista equipamiento → sólo unidades de Ushuaia; ítems sin unidades en Ushuaia no aparecen
  ADMIN_LOCAL ve además ítems sin unidades
  ESTUDIANTE pide ?sede=Río Grande → 403 SEDE_FUERA_DE_ALCANCE
  ESTUDIANTE lista /unidades → 403 PERMISO_INSUFICIENTE

AC-42  PRE-19 en unidades
  ADMIN_LOCAL crea equipamiento con unidades sin sede → todas con su sede
  SUPERADMIN crea una unidad sin sede → 422 SEDE_REQUERIDA
  ADMIN_LOCAL agrega una unidad con otra sede → 403 SEDE_FUERA_DE_ALCANCE

AC-43  Estado de unidades con alcance (PRE-14)
  ADMIN_LOCAL cambia el estado de una unidad de otra sede → 404 UNIDAD_NO_ENCONTRADA
  DOCENTE cambia un estado → 403 PERMISO_INSUFICIENTE

AC-44  Plazo por defecto desde config
  Con prestamo.general.max_dias = 3, crear equipamiento sin max_dias_prestamo → 3

AC-45  Errores homogéneos
  Categoría duplicada → 409 CATEGORIA_DUPLICADA; categoría inexistente → 422 CATEGORIA_INEXISTENTE
  Número de serie duplicado → 409 INVENTARIO_DUPLICADO
```

### 9.3 Cuenta

```gherkin
AC-46  Editar contacto
  PATCH /auth/me {telefono} → 200
  PATCH /auth/me {dni} o {rol} o {} → 422
  PATCH /auth/me {email} sin password_actual o con la incorrecta → 403 PASSWORD_ACTUAL_INCORRECTA
  PATCH /auth/me {email, password_actual} → 200; el login posterior usa el email nuevo
  Email de otra cuenta → 409 EMAIL_YA_REGISTRADO
  Existe fila en usuarios_historial_cambios con antes/después

AC-47  Cambiar contraseña
  Con la actual correcta → 200 con token nuevo; el token anterior → 401 TOKEN_REVOCADO
  Actual incorrecta → 403 PASSWORD_ACTUAL_INCORRECTA
  Nueva débil o igual a la actual → 422
  El historial registra {"password": ["***","***"]}

AC-48  Cambio obligatorio
  Cuenta creada por SUPERADMIN → login 200 con debe_cambiar_password = true
  Con ese token: GET /api/v1/spaces/espacios → 403 CAMBIO_PASSWORD_REQUERIDO; GET /auth/me → 200
  Tras POST /auth/me/password → flag false y los endpoints responden normalmente
  El CLI crear-superadmin deja el flag en false

AC-49  Edición administrativa
  ADMIN_LOCAL edita nombre y teléfono de un estudiante de su sede → 200
  ADMIN_LOCAL cambia ESTUDIANTE → DOCENTE → 200 y el token del usuario queda revocado
  ADMIN_LOCAL asigna ADMIN_LOCAL → 403; cambia la sede → 403 SEDE_FUERA_DE_ALCANCE
  ADMIN_LOCAL edita un usuario de otra sede → 404
  SUPERADMIN corrige la sede de una cuenta pendiente → 200
  SUPERADMIN pasa un ESTUDIANTE a SUPERADMIN sin anular la sede → 422
  Un administrador cambia su propio rol → 403 OPERACION_SOBRE_SI_MISMO
  SUPERADMIN resetea la contraseña → el usuario debe cambiarla en el próximo ingreso
  DNI duplicado → 409 DNI_YA_REGISTRADO
```

### 9.4 Frontend (verificación manual + build)

```gherkin
AC-50  Sin sesión se muestra el login; tras recargar con sesión válida se mantiene
AC-51  Cada code de login muestra su mensaje (pendiente, rechazada, suspendida con fecha, inactiva, credenciales)
AC-52  El registro valida en línea y termina en la pantalla "pendiente de aprobación"
AC-53  Un 401 TOKEN_* en cualquier pantalla cierra la sesión y vuelve al login con aviso
AC-54  No existe selector de rol ni rol "icse"; el menú corresponde al rol real
AC-55  Un ADMIN_LOCAL aprueba y rechaza (con motivo) desde "Pendientes"; sólo ve su sede
AC-56  El SUPERADMIN cambia la sede vista y el directorio se actualiza; crea una cuenta nueva
AC-57  El SUPERADMIN edita un parámetro; ante CONFLICTO_VERSION se informa y se recarga
AC-58  El usuario con cambio obligatorio no puede navegar hasta cambiar la contraseña
AC-59  En Espacios, un estudiante reserva sin elegir usuario; los errores de anticipación/horario se muestran con su mensaje; la grilla usa el horario de config
AC-60  npm run typecheck y npm run build terminan sin errores
```

---

## 10. Casos de borde

| ID | Escenario | Resultado |
| --- | --- | --- |
| EC-23 | Reserva para hoy cuando faltan 25 h para el inicio y `anticipacion_min_horas` = 24 | `201` (se compara con la hora local del laboratorio) |
| EC-24 | Bloqueo de franja 10–12 y reserva 12–13 (bordes contiguos) | `201` (rangos semiabiertos `[inicio, fin)`) |
| EC-25 | El horario de cierre se reduce con reservas aprobadas posteriores | No se alteran (RN-21 de SPEC-01) |
| EC-26 | `ADMIN_LOCAL` filtra `GET /reservas?id_usuario=` | Se ignora el filtro de usuario si el usuario no está en su sede; nunca filtra fuera de su alcance |
| EC-27 | El dueño intenta cancelar una reserva cuyo inicio ya pasó | `409 TRANSICION_INVALIDA` |
| EC-28 | Usuario de una reserva dado de baja | La reserva se conserva (FK `RESTRICT`, baja lógica) |
| EC-29 | Un estudiante cambia su email a uno con mayúsculas | Se normaliza; el login funciona con cualquier capitalización |
| EC-30 | `PATCH /auth/me` con `password_actual` pero sin cambiar email | `422` (campo sin propósito) |
| EC-31 | El `SUPERADMIN` en vista "Ambas sedes" abre Espacios | Ve los espacios de ambas sedes, agrupados por sede |
| EC-32 | Token expirado mientras se completa un formulario | El envío falla con `401 TOKEN_EXPIRADO`; el frontend avisa y lleva al login sin perder el mensaje |
| EC-33 | Usuario con `debe_cambiar_password` intenta `PATCH /auth/me` | `403 CAMBIO_PASSWORD_REQUERIDO` |

---

## 11. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| NFR-11 | Cobertura ≥ 85 % en `app/modules/spaces`, `app/modules/inventory` y en el código nuevo de `users`. |
| NFR-12 | Todos los AC de backend (AC-31…AC-49) automatizados contra PostgreSQL. |
| NFR-13 | Los tests existentes de `spaces` se conservan o se reemplazan por equivalentes de integración (sin perder casos). |
| NFR-14 | Frontend: `tsc --noEmit` sin errores; tests unitarios (Vitest) del cliente HTTP y del mapeo de errores/roles. |
| NFR-15 | Ningún secreto ni token en `localStorage`, logs de consola o URLs. |
| NFR-16 | Dependencia nueva de backend: `tzdata` (zonas horarias en Windows). Frontend: `vitest` (dev). |

---

## 12. Decisiones resueltas

> Aprobadas por el Perfil 1 el 2026-10-08: se adoptan todas las recomendaciones.

| ID | Decisión | Opciones | Resolución |
| --- | --- | --- | --- |
| D-01 | Estrategia de integración | (a) Backend y frontend en PRs separados que se mergean juntos a `develop` después de la demo del 09/10; (b) flag `AUTH_REQUERIDA=false` para mergear antes sin romper | **(a)**: un flag de seguridad desactivable es riesgoso y suele quedar olvidado. La demo usa el `develop` actual |
| D-02 | Mapeo de `id_sede` existente | (a) `1 → Ushuaia`, `2 → Río Grande`, otro valor aborta; (b) borrar espacios existentes | **(a)**: coincide con el orden de `SedeEnum` y con el uso del frontend |
| D-03 | Reservas con `id_usuario` inexistente | (a) Eliminarlas en la migración con aviso; (b) abortar la migración | **(a)**: son datos de la demo sin autenticación; no hay producción |
| D-04 | Foto de perfil (USR-03) | (a) Diferir a SPEC-03 junto con el almacenamiento de archivos de PRE-05; (b) subir a disco local ahora | **(a)**: diseñar el almacenamiento una sola vez |
| D-05 | Zona horaria | (a) `America/Argentina/Ushuaia` fija en código; (b) parámetro de entorno | **(a)** con constante en `app/core/settings.py`; ambas sedes comparten zona |
| D-06 | Almacenamiento del token en el navegador | (a) `sessionStorage`; (b) `localStorage`; (c) cookie `HttpOnly` | **(a)**: el laboratorio usa computadoras compartidas; cerrar la pestaña cierra la sesión. (c) llega con el refresh token en SPEC-03 |
| D-07 | Rol en el frontend | (a) Mantener `student/teacher/admin` derivado de `RolUsuario`; (b) usar los valores del backend en toda la UI | **(a)**: no obliga a reescribir componentes de otros perfiles; `esSuperadmin` se expone aparte |
| D-08 | ¿Los administradores pueden crear reservas de espacios? | (a) No (RES-02 nombra a estudiantes y docentes); (b) Sí | **(a)**; para clases, el docente reserva. Revisable con la referente |
| D-09 | Ruteo del frontend | (a) Mantener el estado `screen` actual + pantallas de auth fuera del layout; (b) incorporar React Router | **(a)**: menos cambios para los colegas; el ruteo se evalúa aparte |

---

## 13. Matriz de trazabilidad

| Requisito | Endpoints / pantallas | Criterios | Bordes |
| --- | --- | --- | --- |
| GLO-01 | Todos los de `spaces` e `inventory`; selector de sede | AC-32, AC-33, AC-36…AC-38, AC-41…AC-43, AC-55, AC-56 | EC-26, EC-31 |
| GLO-02 / GLO-03 | `POST /reservas`, `GET /disponibilidad`, `POST /equipamiento`; panel de parámetros | AC-35, AC-44, AC-57, AC-59 | EC-23, EC-25 |
| RES-02 / RES-03 / RES-05 | `/reservas` | AC-34, AC-35, AC-37 | EC-27, EC-28 |
| RES-04 / GLO-04 | `/bloqueos`, validación V6 | AC-35, AC-38 | EC-24 |
| PRE-12 / PRE-14 / PRE-19 | `/unidades`, `/equipamiento` | AC-41…AC-43 | — |
| USR-03 | `PATCH /auth/me`, `POST /auth/me/password`; Mi perfil | AC-46, AC-47 | EC-29, EC-30 |
| USR-04 | `PATCH /users/{id}`; Gestión de usuarios | AC-49, AC-55, AC-56 | — |
| USR-01 / USR-05 (UI) | Login, Registro, Pendientes | AC-50…AC-53, AC-55 | EC-32 |
| SPEC-01 UC-06 (primer ingreso) | `debe_cambiar_password` | AC-48, AC-58 | EC-33 |
| DT-02 / DT-03 / DT-14 | Migración `0007`, V4/V5 | AC-34, AC-35, AC-39 | — |

---

## 14. Historial de cambios

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 1.0.1 | 2026-10-23 | Perfil 1 | Nota documental, sin cambio de contrato: la conciliación v1.0.1 se aplicó sin una re-aprobación registrada (regla del encabezado); se deja constancia. En §6.1, `SedeContext` se implementó dentro de `AuthContext.tsx` (ver `plan-02` §6). Mergeado en `develop` (backend PR #7 y `074158e`; frontend PR #4) |
| 1.0.1 | 2026-10-08 | Perfil 1 | **Implementado** en Backend (`feat/spec-02-integracion`) y Frontend (`feat/login-auth-ui`). |
| 1.0.1 | 2026-10-08 | Perfil 1 | Conciliación con el PR #6 de `spaces` mergeado en paralelo: se conservan las transiciones `Aprobada → En_Uso → Finalizada` y el campo `intervalos_disponibles`. Se nombran tres códigos que el borrador dejaba como `422`/`409` genéricos (`BLOQUEO_CON_RESERVAS`, `MOTIVO_REQUERIDO`, `ALCANCE_INCOHERENTE`). Sin cambio de alcance ni de criterios |
| 1.0.0 | 2026-10-08 | Perfil 1 | **Aprobado** con todas las recomendaciones de §12 (D-01…D-09) |
| 0.1.0 | 2026-10-08 | Perfil 1 (con asistencia de IA) | Borrador inicial para revisión |
