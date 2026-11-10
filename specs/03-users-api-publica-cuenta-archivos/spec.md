# SPEC-03 — API pública de `users`, recuperación de contraseña, archivos y renovación de sesión

| Campo | Valor |
| --- | --- |
| **ID** | SPEC-03 |
| **Perfil responsable** | Perfil 1 — Identidad, Usuarios, Permisos, Configuración Global y Despliegue |
| **Estado** | `IMPLEMENTADO` — 2026-11-10, todo en `develop`: Fase A (backend PR #18), B2 (backend PR #26, frontend PR #14), B1 (backend PR #27 y #29, frontend PR #15) y B3 (backend PR #31, frontend PR #17). Trazabilidad en §14. Contrato: v1.1.0, `APROBADO` el 2026-11-08 (D-20…D-22 y RN-77); la v1.0.0 se aprobó el 2026-11-03 con D-01…D-19 |
| **Versión** | 1.1.0 |
| **Requisitos cubiertos** | Fase A: soporte de PRE-15, PRE-20 y RES-05 (datos del solicitante), C2 de SPEC-05 · Fase B: USR-02, USR-03 (foto), PRE-05 (almacenamiento del aval, C4 de SPEC-05), D-06 de SPEC-01, infraestructura de correo para los avisos de ADR-022 (f) |
| **Depende de** | SPEC-01 v1.0.0 y SPEC-02 v1.0.1 (`IMPLEMENTADO`, en `develop`) |
| **Contexto** | Tercera entrevista con la referente (16/10/2026), ADR-022 en `MEMORY.md`; impacto en este spec en §2.4. SPEC-05 v1.0.0 (`loans`, Fase 1 en `develop`) y SPEC-06 v1.0.0 (`notifications`, ADR-023) dependen de la Fase B (§2.1) |
| **Módulos afectados** | Backend: `users`, `core`, `files` (nuevo, Perfil 1, D-12) · Frontend: `auth`, `users`, `layout`, `src/lib/api.ts` |
| **Módulos ajenos** | Ninguno se modifica. Lo que necesitan los Perfiles 3, 4 y 5 va como ítem de coordinación (§13) |
| **Constitución** | v1.1.0, con la enmienda 1.1.1 propuesta (ADR-019), **sin ratificar** (ver §2.3) |
| **Fuente de verdad funcional** | `docs/ERS.md` |
| **Plan y tareas** | `specs/03-users-api-publica-cuenta-archivos/plan.md` y `tasks.md` |

> **Regla SDD:** documento `APROBADO`; la implementación debe ajustarse a él. Cualquier cambio requiere una nueva versión en §15 y re-aprobación.

> **Numeración:** el 03 estaba reservado para el Perfil 1 (respuesta a D-L01 de SPEC-05, `MEMORY.md` §1). Los criterios, reglas y casos de borde siguen la numeración de SPEC-01 y SPEC-02: `AC-61…`, `RN-35…`, `EC-34…`, `NFR-17…`.

---

## 0. Resumen ejecutivo

El spec se entrega en dos fases independientes:

- **Fase A (prioritaria, chica) — implementada** (backend PR #18, 2026-11-06). Una función pública de `users`, `datos_publicos_por_ids`, que devuelve nombre y apellido por lote de ids. Desbloquea al Perfil 4 (solicitante en la bandeja de reservas) y al Perfil 3 (C2 de SPEC-05: resumen del solicitante en las respuestas de `loans`). No cambia el esquema ni expone endpoints.
- **Fase B (tres entregas, cada una con su PR), en el orden B2 → B1 → B3 (D-20).**
  - **B1 — USR-02:** recuperación de contraseña por email, con token de un solo uso con vencimiento, respuesta neutra, límite de intentos, revocación de sesiones y pantallas en el frontend. Incluye la infraestructura de correo (`app/core/email.py`), con plantillas por tipo de mensaje y llamable desde cualquier servicio. También la usa `notifications` para los avisos por correo, incluidos los de llamados de atención y sanciones (ADR-023, D-21).
  - **B2 — Archivos:** almacenamiento para la foto de perfil (USR-03) y el PDF de aval de PRE-05 (la resolución del Consejo CICSE/ICSE, obligatoria para estudiantes y docentes; C4 de SPEC-05), con validación de tipo y tamaño, control de acceso a la descarga y limpieza de huérfanos. Va primero porque `loans` ya está en `develop` y rechaza todo pedido de alta gama hasta que exista (D-20).
  - **B3 — Sesión:** se evalúa refresh token con cookie `HttpOnly` frente a ADR-015. Se recomienda **no** adoptarlo y usar renovación deslizante del access token con tope absoluto de sesión (D-13).

---

## 1. Alcance

### 1.1 Dentro del alcance

| # | Capacidad | Requisitos | Fase |
| --- | --- | --- | --- |
| A1 | `datos_publicos_por_ids(db, ids)` en `users/service.py`, con `DatosPublicosUsuario` (id, nombre, apellido) | C2 de SPEC-05, pedido del Perfil 4 (`MEMORY.md` §5), P6 | A |
| B1 | Envío de correo (SMTP) en `app/core/email.py`, configurable por entorno, con plantillas por tipo de mensaje y llamable desde endpoints y servicios; incluye el tipo genérico `NOTIFICACION` para `notifications` (RN-77) | USR-02, ADR-022 (f), ADR-023 | B1 |
| B2 | Solicitud de recuperación con respuesta neutra y límite de intentos | USR-02, P4.5 | B1 |
| B3 | Restablecimiento con token de un solo uso y vencimiento; revocación de sesiones | USR-02, RN-08 | B1 |
| B4 | Pantallas "¿Olvidaste tu contraseña?" y "Restablecer contraseña" | USR-02 | B1 |
| B5 | Módulo `files`: subida, validación, descarga con control de acceso y limpieza de huérfanos | PRE-05, USR-03 | B2 |
| B6 | Foto de perfil: subir, reemplazar, quitar (propia) y quitar (administrador con jurisdicción) | USR-03, USR-04 | B2 |
| B7 | Funciones públicas de `files` para que `loans` vincule y sirva el aval PDF | PRE-05, C4 de SPEC-05 | B2 |
| B8 | Renovación deslizante del access token, tope absoluto de sesión y "cerrar todas mis sesiones" | D-06 de SPEC-01, ADR-015 | B3 |

### 1.2 Fuera del alcance

| Capacidad | Destino |
| --- | --- |
| Campo `solicitante` en `ReservaEspacioResponse` | Perfil 4 (ítem K1) |
| Resumen del solicitante en las respuestas de `loans` | Perfil 3 (ítem K2) |
| Campo `pdf_aval_id` en `OrdenPedidoCreate` y su UI en el formulario de préstamo | Perfil 3 (ítem K3) |
| Catálogo de asignaturas y vínculo docente–asignatura (C2 y C3 de SPEC-05) | Decisión abierta D-04; no entra en esta versión |
| Notificaciones por correo de `notifications` (NOV-03) y su bandeja de salida | Perfil 5, Fase C de SPEC-06 (ADR-023). Envía con `enviar_correo(TipoCorreo.NOTIFICACION, …)` (RN-77) |
| Horario de atención **por sede** (hoy `horario.apertura` y `horario.cierre` son únicos y los leen `spaces` y `loans`) y parámetro nuevo con el **correo de contacto del laboratorio**, para el aviso de anticipación mínima del Perfil 4 (ADR-022 a, c) | Spec siguiente del Perfil 1. Cambia las claves de `config`: se coordina con los Perfiles 3 y 4 (ítem K10) |
| **Delegación temporal del rol de Superadministrador**: sólo a un `ADMIN_LOCAL`, con duración fijada al delegar, revocable antes, y al vencer vuelve a su rol y su sede (ADR-022 g, GLO-01) | Spec siguiente del Perfil 1. El cambio de rol al delegar y al vencer revoca las sesiones con `token_version` (RN-08), compatible con B3 |
| **USR-09 reformulado**: llamados de atención (el 3.º se convierte en falta); con 1 falta el administrador decide si suspende y con 2 la suspensión es automática, por un tiempo fijo que el administrador puede levantar antes. Las cantidades son parámetros de `config`. Cada llamado o sanción se avisa por email (ADR-022 d–f) | Spec siguiente del Perfil 1. Los avisos se emiten con `crear_notificacion` de `notifications` (tipos `LLAMADO_ATENCION` y `SANCION`, SPEC-06 §6.4), que los manda por correo con el transporte de B1 (ADR-023, D-17) |
| **Teléfono obligatorio en el registro** (USR-05, ADR-022 b) | Spec siguiente del Perfil 1, según la recomendación de D-16 |
| Actualización de los requisitos del ERS por la entrevista (DT-29) | Un solo PR al ERS junto con la corrección del CU de USR-02 (ítem K7) |
| Programación periódica de `limpiar-huerfanos` | Spec de despliegue, junto con `procesar-vencimientos` de `loans` (C5 de SPEC-05) y `enviar-correos` de `notifications` (C-N04 de SPEC-06) |
| Antivirus o análisis de contenido de los PDF | Trabajo futuro (P10) |
| USR-06…09, GLO-05, GLO-06 (menú colapsable), Docker y CI | Specs siguientes del Perfil 1 |

---

## 2. Estado actual y dependencias

### 2.1 Verificado en `develop` (backend `3ad6b6b`, frontend `8f7832b`, 2026-11-08)

| Elemento | Estado |
| --- | --- |
| `users/service.py` | Servicios internos de UC-01…UC-12 y, al final, la sección "API pública para otros módulos" con `DatosPublicosUsuario` y `datos_publicos_por_ids` (Fase A, PR #18). La usa `notifications` para el autor de los comunicados (SPEC-06, PR #22); `spaces` (K1) y `loans` (K2) todavía no |
| `spaces/schemas.py` | `ReservaEspacioResponse` expone sólo `id_usuario` (K1 pendiente) |
| `loans` | Fase 1 de SPEC-05 en `develop` (PR #21). `OrdenPedidoCreate.pdf_aval_id: UUID \| None`, pero un ítem de alta gama responde `422 AVAL_REQUERIDO` **aunque traiga el aval**, porque todavía no hay `files` para vincularlo (`loans/service.py`). `asignatura_id` sigue sin FK (D-L13) |
| `notifications` | Fase A de SPEC-06 en `develop` (PR #22). El correo (NOV-03 y avisos de sanciones) es su Fase C, diferida hasta que exista `app/core/email.py` (ADR-023) |
| `core/settings.py` | Sin variables de correo ni de archivos. `jwt_access_token_expire_minutes` = 60 por defecto |
| `core/security.py` | Claims `sub`, `rol`, `sede`, `tv`, `iss`, `iat`, `exp`, `jti`; sin `auth_time` |
| Dependencias | No están `python-multipart` (necesaria para `UploadFile`) ni `Pillow` |
| Migraciones | Cadena `… → 0010_inventory_gestion → 0013_notifications_init` (cabeza). SPEC-05 reserva `0011` y `0012`: `0011_loans_resolucion` está en `feat/loans-validar` (PR #23, abierto) con `down_revision = 0013`. El número es una reserva, no el orden de la cadena (D-22, EC-45) |
| Python | El README dice "≥ 3.11, validado con 3.12"; en el equipo se usan 3.12, 3.13 y 3.14. Un test de la Fase A falla en 3.12 y 3.13 (DT-30, AC-67) |
| Frontend | La pantalla de login no tiene enlace de recuperación; no hay foto de perfil. El token vive en `sessionStorage` (ADR-015). `App.tsx` sigue sin React Router; el PR #12 del Perfil 5 (abierto) también lo modifica |

### 2.2 Brechas

| ID | Brecha | Requisito |
| --- | --- | --- |
| G-1 | Los Perfiles 3 y 4 no pueden mostrar el nombre del solicitante sin importar el modelo `Usuario` o consultarlo por su cuenta | P3.3, P6, PRE-15, RES-05 |
| G-2 | No hay recuperación de contraseña: un usuario que la olvida depende de que un administrador la resetee (UC-12) | USR-02 |
| G-3 | El CU de USR-02 del ERS indica informar "que no existe una cuenta asociada", lo que permite enumerar usuarios | P4.5 (prevalece la Constitución, D-06) |
| G-4 | No hay dónde guardar archivos: USR-03 queda sin foto y `loans` rechaza todo pedido de alta gama con `422 AVAL_REQUERIDO`, aunque traiga el aval (§2.1) | USR-03, PRE-05 |
| G-5 | La sesión se corta a los 60 minutos aunque el usuario esté trabajando (EC-32 de SPEC-02) y una pestaña olvidada sigue válida hasta 60 minutos | D-06 de SPEC-01, ADR-015 |

### 2.3 Enmienda 1.1.1 de la Constitución

Las funciones públicas de este spec (`datos_publicos_por_ids`, `vincular_archivo`, `abrir_archivo`) son compatibles con el texto **vigente** de P3.3, que ya permite colaborar "mediante funciones de servicio públicas". La enmienda 1.1.1 (ADR-019), **todavía sin ratificar**, agrega dos cosas de las que este spec depende:

1. que la función la **declara pública el módulo dueño** (este spec lo hace en §4.1 y §8.3), y que un módulo no importe servicios internos de otro;
2. la excepción explícita para el `Usuario` que devuelven `get_current_user` y `require_roles`, que `spaces` y `loans` ya usan como tipo.

Si el equipo rechaza o modifica la enmienda, la Fase A no cambia de contrato, pero hay que revisar cómo la consumen los Perfiles 3 y 4. Ratificarla es el ítem K5 (C13 de SPEC-05).

### 2.4 Impacto de la tercera entrevista (ADR-022)

| Punto de ADR-022 | Efecto en este spec |
| --- | --- |
| (f) Los llamados de atención y las sanciones se avisan por email | §5.1: el correo deja de ser sólo de USR-02. Plantillas por tipo de mensaje y envío llamable desde un servicio (RN-71…RN-76, D-17). K6 lo respondió el Perfil 5 (ADR-023): los avisos pasan por `notifications`, que usa este transporte con el tipo `NOTIFICACION` (RN-77, D-21) |
| (i) Los docentes también piden alta gama, con regularidad, y el aval es el PDF de la resolución del Consejo (CICSE/ICSE), obligatorio para estudiantes y docentes | §6: el aval lo sube cualquiera de los dos; la descarga queda para el solicitante y los administradores con jurisdicción, no para el docente de la asignatura (D-18). Reutilizar una resolución en varios pedidos queda como D-19 |
| (a), (c), (d), (e), (g) Horario por sede, correo de contacto, sanciones y delegación temporal | No entran: §1.2, con destino en el spec siguiente del Perfil 1. **La Fase A no cambia** |
| (b) Teléfono obligatorio | Decisión D-16: va en el spec siguiente, no en la Fase A |
| Usuario suspendido: no inicia sesión y ve "Tu cuenta está suspendida" | Confirma D-08: sólo las cuentas `ACTIVO` recuperan la contraseña |
| DT-29 (el ERS todavía no refleja ADR-022) | K7: un solo PR al ERS con DT-29 y la corrección del CU de USR-02 |

---

## 3. Actores

| Actor | Fase A | Fase B |
| --- | --- | --- |
| Otros módulos (`spaces`, `loans`) | Llaman a `datos_publicos_por_ids` | Llaman a `vincular_archivo` y `abrir_archivo` |
| Público (sin sesión) | — | Solicita y confirma la recuperación |
| `ESTUDIANTE`, `DOCENTE` | — | Foto propia; suben el aval PDF; renuevan sesión |
| `ADMIN_LOCAL`, `SUPERADMIN` | — | Foto propia; ven fotos y avales de su jurisdicción; quitan fotos de usuarios de su jurisdicción |
| Sistema (CLI) | — | `limpiar-huerfanos` |

---

## 4. Fase A — Datos públicos de usuarios

### 4.1 Contrato

En `app/modules/users/service.py`, en una sección "API pública para otros módulos":

```python
@dataclass(frozen=True, slots=True)
class DatosPublicosUsuario:
    """Identidad mínima mostrable de un usuario (P6). Nunca incluye DNI, email ni teléfono."""
    id: int
    nombre: str
    apellido: str


async def datos_publicos_por_ids(
    db: AsyncSession, ids: Iterable[int]
) -> dict[int, DatosPublicosUsuario]:
    """Nombre y apellido por lote de ids (C2 de SPEC-05; bandeja de reservas del Perfil 4).

    Función pública (P3.3, enmienda 1.1.1). No filtra por sede ni por estado: quien llama
    sólo pasa ids que ya está autorizado a mostrar. No hace commit.
    """
```

### 4.2 Reglas

| ID | Regla |
| --- | --- |
| RN-35 | Los ids repetidos se eliminan antes de consultar; cada id aparece una sola vez en el resultado |
| RN-36 | Una entrada vacía devuelve `{}` **sin consultar la base** |
| RN-37 | Los ids inexistentes se omiten; no es un error. Quien llama trata la ausencia como "sin datos" (con la FK `RESTRICT` y la baja lógica no debería ocurrir) |
| RN-38 | Incluye usuarios en **cualquier** estado (`PENDIENTE_APROBACION`, `ACTIVO`, `SUSPENDIDO`, `INACTIVO`, `RECHAZADO`): el historial muestra a quien solicitó, aunque hoy esté dado de baja |
| RN-39 | **No filtra por sede**, a propósito: un `ADMIN_LOCAL` tiene que ver el nombre de un `SUPERADMIN` (sede nula) que reservó en su sede. La autorización es de quien llama, que sólo pasa ids de registros que ya puede mostrar (P5, P6) |
| RN-40 | Devuelve sólo `id`, `nombre` y `apellido`. La consulta selecciona **esas tres columnas**, no la entidad `Usuario`: el DNI, el email y el teléfono nunca se cargan en la sesión del llamador |
| RN-41 | Una sola consulta por llamada, con los ids en un único parámetro de tipo arreglo (`id = ANY(:ids)`), para no chocar con el límite de 32 767 parámetros de asyncpg en lotes grandes |
| RN-42 | No hace `commit`, `rollback` ni `flush` explícito: la transacción es de quien llama (igual que `inventory/service.py`) |
| RN-43 | **Nunca** se usa para mostrar identidades en la disponibilidad de espacios o equipamiento (RN-30 de SPEC-02), ni para mostrarle a un estudiante datos de otro solicitante (P6.1). Que un docente vea el nombre de sus estudiantes depende de la pregunta 5 de SPEC-05 §15.2 |

No hay endpoint HTTP: es una función de servicio. La forma `{id, nombre, apellido}` es la que cada módulo usa en su propio esquema de respuesta (D-03).

### 4.3 Uso esperado (informativo, lo implementan los Perfiles 3 y 4)

```python
from app.modules.users.service import datos_publicos_por_ids

reservas = (await db.scalars(stmt)).all()          # ya filtradas por alcance
solicitantes = await datos_publicos_por_ids(db, (r.id_usuario for r in reservas))
# ReservaEspacioResponse(..., solicitante=solicitantes.get(r.id_usuario))
```

### 4.4 Implementación

**Implementada** en la rama `feat/users-datos-publicos` (commit `9341c59`, backend PR #18, mergeado en `develop` el 2026-11-06). Sin migración ni dependencias nuevas. Tests en `tests/users/test_datos_publicos.py`.

Consumidores al 2026-11-08: `notifications` muestra el autor de cada comunicado (SPEC-06). El autor es siempre un administrador, no un solicitante, así que no choca con RN-43. Pendientes: `spaces` (K1) y `loans` (K2).

---

## 5. Fase B1 — Recuperación de contraseña (USR-02)

### 5.1 Infraestructura de correo (`app/core/email.py`)

Es un servicio de **transporte** transversal, en `core`. En este spec lo usa USR-02. Lo usa además `notifications` para todos los avisos por correo: NOV-03 y los llamados de atención y sanciones de ADR-022 (f). Así lo decidió el Perfil 5 al responder K6 (ADR-023, SPEC-06 §6.4). Qué se avisa, a quién y cuándo es responsabilidad del módulo que llama; `core` sólo arma el mensaje desde una plantilla y lo envía.

| Variable de entorno | Uso | Valor por defecto |
| --- | --- | --- |
| `EMAIL_BACKEND` | `smtp` o `memoria` (tests) | `smtp` |
| `SMTP_HOST`, `SMTP_PORT` | Servidor | `localhost`, `1025` (Mailpit en desarrollo) |
| `SMTP_USER`, `SMTP_PASSWORD` | Credenciales (secretas, sólo en `.env`) | vacías |
| `SMTP_TLS` | `starttls`, `ssl` o `ninguno` | `starttls` |
| `EMAIL_FROM` | Remitente | `PrestaMeDios <no-responder@...>` (sin valor real en el repo) |
| `FRONTEND_URL` | Base del enlace de recuperación | `http://localhost:8443` |

**Interfaz**

```python
class TipoCorreo(StrEnum):
    """Un valor por tipo de mensaje; cada uno tiene su plantilla (RN-71)."""
    RECUPERACION_PASSWORD = "RECUPERACION_PASSWORD"
    NOTIFICACION = "NOTIFICACION"  # genérico para `notifications` (RN-77, ADR-023)


class ErrorEnvioCorreo(Exception):
    """El transporte no pudo entregar el mensaje (RN-73)."""


def renderizar_correo(tipo: TipoCorreo, contexto: Mapping[str, str]) -> CorreoRenderizado:
    """Asunto y cuerpo desde la plantilla de ``tipo``. Falla si falta una variable."""


async def enviar_correo(
    tipo: TipoCorreo, destinatario: str, contexto: Mapping[str, str]
) -> None:
    """Renderiza y envía. Función común, sin dependencias de FastAPI: se llama desde un
    endpoint (con ``BackgroundTasks``) o desde un servicio, después del commit (RN-72)."""
```

`CorreoRenderizado` es una dataclass frozen (`asunto`, `cuerpo`). El backend `smtp` usa `smtplib` de la biblioteca estándar en un hilo (`asyncio.to_thread`); el `memoria` acumula los mensajes para los tests (D-05).

| ID | Regla |
| --- | --- |
| RN-71 | Cada `TipoCorreo` tiene una plantilla de texto plano en `app/core/plantillas_correo/<tipo>.txt`: la primera línea es el asunto y el resto el cuerpo, con variables `$nombre` de `string.Template` (biblioteca estándar, sin dependencia nueva). Una variable faltante se detecta al renderizar, **antes** de enviar. Agregar un tipo de mensaje es agregar un valor al enum y su plantilla, sin tocar el transporte |
| RN-72 | `enviar_correo` no depende de la request. USR-02 la agenda con `BackgroundTasks` para no revelar por el tiempo de respuesta si la cuenta existe (NFR-20). Fuera de USR-02 se llama **después** de confirmar la transacción que originó el aviso, para no avisar algo que se deshizo. `notifications` lo garantiza con su bandeja de salida (ADR-023, D-17) |
| RN-73 | Un fallo de transporte lanza `ErrorEnvioCorreo` y quien llama decide: USR-02 lo registra y no cambia la respuesta; `notifications` registra el error en la notificación, y el aviso fallido no deshace la sanción (EC-49) |
| RN-74 | El log registra el tipo, el id del usuario cuando lo hay y el resultado; **nunca** el contexto ni el cuerpo, que pueden llevar el enlace de recuperación (NFR-19) |
| RN-75 | Un destinatario por mensaje, sin copias a terceros (P6); asunto con el prefijo "[PrestaMeDios]"; tiempo máximo de conexión SMTP de 10 s |
| RN-76 | El backend `memoria` guarda tipo, destinatario, asunto y cuerpo, y se limpia entre tests |
| RN-77 | `TipoCorreo.NOTIFICACION` es el tipo que usa `notifications` para mandar por correo una notificación que ya armó con su propia plantilla (SPEC-06 RN-N7). Contexto: `titulo` y `mensaje`. Asunto `$titulo`; cuerpo `$mensaje` y un pie fijo con el enlace a la aplicación (`FRONTEND_URL`) y la aclaración de que es un aviso automático. Rigen RN-74 y RN-75. Los avisos de llamados de atención y sanciones no tienen un `TipoCorreo` propio: el tipo de aviso lo decide `notifications` (`LLAMADO_ATENCION`, `SANCION`) y este transporte sólo lo envía (D-21) |

- Un fallo de SMTP en la recuperación se registra en el log **sin** el token ni el enlace (NFR-02) y no cambia la respuesta.
- `.env.example` documenta las variables sin valores reales (NFR-03).

### 5.2 Modelo de datos (migración `0015_users_recuperacion`, D-22)

| Tabla | Columnas | Notas |
| --- | --- | --- |
| `tokens_recuperacion` | `id BIGINT PK`, `usuario_id FK→usuarios ON DELETE CASCADE`, `token_hash CHAR(64) UNIQUE`, `expira_en TIMESTAMPTZ`, `usado_en TIMESTAMPTZ NULL`, `created_at` | Se guarda sólo el SHA-256 del token, nunca el token. Índice `(usuario_id, usado_en)` |
| `intentos_recuperacion` | `id BIGINT PK`, `email_hash CHAR(64)`, `ip VARCHAR(45)`, `created_at` | Registro para el límite de intentos (RN-49). Guarda el hash del email normalizado, no el email. Índices `(email_hash, created_at)` y `(ip, created_at)`. Las filas de más de 24 h se borran al registrar una nueva |

| Variable de entorno | Uso | Defecto |
| --- | --- | --- |
| `RECUPERACION_VIGENCIA_MINUTOS` | Vida del token | `30` |
| `RECUPERACION_MAX_POR_EMAIL_HORA` | Solicitudes por email en una hora | `3` |
| `RECUPERACION_MAX_POR_IP_HORA` | Solicitudes por IP en una hora | `20` |

Son parámetros técnicos de seguridad, no reglas del reglamento: van en el entorno y no en el panel de GLO-03 (D-07).

### 5.3 Endpoints (públicos, declarados como excepción a P4.1)

| Método | Ruta | Request | Éxito | Errores |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/auth/recuperacion` | `{email}` | `202` `{detail}` neutro | `422` (formato), `429 DEMASIADOS_INTENTOS` |
| `POST` | `/api/v1/auth/recuperacion/confirmar` | `{token, password_nueva}` | `200` `{detail}` | `422 TOKEN_RECUPERACION_INVALIDO`, `422` (RN-03) |

Mensaje neutro del `202`: "Si el email corresponde a una cuenta activa, te enviamos un enlace para restablecer la contraseña. Revisá también la carpeta de spam."

Ambos esquemas usan `extra="forbid"` y `str_strip_whitespace`. `password_nueva` reutiliza el validador de RN-03 de SPEC-01.

### 5.4 Reglas

| ID | Regla |
| --- | --- |
| RN-44 | La respuesta de la solicitud es **idéntica** (código, cuerpo y tiempo aproximado) exista o no la cuenta, y cualquiera sea su estado (P4.5). Se modifica el flujo alternativo del CU del ERS (D-06, ítem K7) |
| RN-45 | Sólo se envía correo a cuentas `ACTIVO`. Las `PENDIENTE_APROBACION`, `RECHAZADO`, `SUSPENDIDO` e `INACTIVO` reciben la respuesta neutra sin correo (D-08, confirmada en la entrevista del 16/10: un suspendido no entra y ve "Tu cuenta está suspendida") |
| RN-46 | El token tiene 256 bits (`secrets.token_urlsafe(32)`), se guarda sólo su SHA-256 y vence a los `RECUPERACION_VIGENCIA_MINUTOS` |
| RN-47 | El enlace es `{FRONTEND_URL}/#/restablecer?token=<token>`: el token viaja en el **fragmento**, que el navegador no envía al servidor ni en el `Referer`. El frontend lo lee, lo borra de la barra de direcciones y lo manda en el cuerpo del `POST` (excepción acotada a NFR-15 de SPEC-02) |
| RN-48 | Una solicitud nueva invalida los tokens anteriores sin usar de esa cuenta. Un restablecimiento exitoso invalida todos los demás |
| RN-49 | Límite de solicitudes: por email (hash del email normalizado) y por IP en la última hora. Excedido → `429 DEMASIADOS_INTENTOS`. Como se cuenta por el texto del email, exista o no la cuenta, el `429` no revela nada. La confirmación no lleva límite: la entropía del token, su vencimiento y el uso único bastan (D-07) |
| RN-50 | Confirmar es atómico: `UPDATE tokens_recuperacion SET usado_en = now() WHERE token_hash = :h AND usado_en IS NULL AND expira_en > now() RETURNING usuario_id`. De dos confirmaciones simultáneas sólo una prospera |
| RN-51 | Al confirmar, la cuenta debe seguir `ACTIVO`; si no, `422 TOKEN_RECUPERACION_INVALIDO` (mismo código para token inexistente, vencido, usado o de una cuenta que dejó de estar activa) |
| RN-52 | Restablecer: nuevo hash Argon2id, `token_version + 1` (cierra todas las sesiones, RN-08), `debe_cambiar_password = false` y fila en `usuarios_historial_cambios` con `{"password": ["***", "***"]}` y `actor_id` = el propio usuario. No inicia sesión: el usuario va al login (D-09) |
| RN-53 | Un cambio de email (UC-10 o UC-12 de SPEC-02) invalida los tokens de recuperación pendientes de esa cuenta: el enlace se mandó a la dirección anterior |
| RN-54 | La IP se toma de `request.client.host`. Detrás de un proxy inverso se confía en `X-Forwarded-For` sólo si lo configura el despliegue (`--proxy-headers` de uvicorn); se define en el spec de despliegue |

### 5.5 Frontend

| Pantalla | Contenido |
| --- | --- |
| Login | Enlace "¿Olvidaste tu contraseña?" |
| Recuperar contraseña (pública) | Campo email; al enviar, siempre el mensaje neutro. `429` → "Hiciste demasiados pedidos. Probá de nuevo en una hora." |
| Restablecer contraseña (pública) | Se abre desde el enlace; lee el token del fragmento y lo quita con `history.replaceState`; contraseña y confirmación con validación en línea de RN-03; `TOKEN_RECUPERACION_INVALIDO` → "El enlace no es válido o ya venció" con acceso a pedir otro; éxito → login con aviso |

Sigue sin React Router (D-09 de SPEC-02): `App.tsx` detecta `#/restablecer` al cargar y muestra la pantalla fuera del layout.

---

## 6. Fase B2 — Almacenamiento de archivos

### 6.1 Módulo `files` (nuevo, Perfil 1)

`app/modules/files/{models,schemas,router,service,enums,cli}.py`, montado en `/api/v1/files` con el tag "Archivos" (D-12).

### 6.2 Modelo de datos (migración `0014_files_init`, D-22)

| Tabla / columna | Definición | Motivo |
| --- | --- | --- |
| `archivos` | `id UUID PK` (v4), `propietario_id FK→usuarios ON DELETE RESTRICT`, `proposito proposito_archivo_enum`, `sede sede_enum NULL`, `tipo_mime VARCHAR(100)`, `tamano_bytes INTEGER CHECK > 0`, `sha256 CHAR(64)`, `nombre_original VARCHAR(255)`, `vinculado_en TIMESTAMPTZ NULL`, `created_at` | Metadatos. `sede` = sede del propietario al subir (nula para `SUPERADMIN`). Índice `(vinculado_en, created_at)` para la limpieza |
| `archivos_contenido` | `archivo_id UUID PK FK→archivos ON DELETE CASCADE`, `datos BYTEA` | Contenido aparte, para que las consultas de metadatos no lean los bytes (D-10) |
| `usuarios.foto_id` | `UUID NULL FK→archivos ON DELETE SET NULL` | Foto vigente (USR-03) |

`PropositoArchivo` (`StrEnum`, valores en MAYÚSCULAS como `core`, DT-19): `FOTO_PERFIL`, `AVAL_PRESTAMO`.

| Propósito | Tipos aceptados (por firma de bytes, no por extensión ni `Content-Type`) | Tamaño máximo | Tratamiento |
| --- | --- | --- | --- |
| `FOTO_PERFIL` | JPEG, PNG, WebP | `ARCHIVO_FOTO_MAX_MB` (2) | Se decodifica y se vuelve a codificar como JPEG de hasta 512 px por lado con `Pillow`, lo que descarta los metadatos EXIF (incluida la ubicación) y neutraliza archivos políglotas (D-11) |
| `AVAL_PRESTAMO` | PDF (`%PDF-`) | `ARCHIVO_PDF_MAX_MB` (10) | Se guarda tal cual. Es el PDF de la **resolución del Consejo (CICSE/ICSE)** que respalda un pedido de alta gama, obligatorio para estudiantes y docentes; el administrador lo verifica antes de aprobar (ADR-022 i) |

### 6.3 Endpoints

| Método | Ruta | Roles | Éxito | Errores |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/files/archivos` | `ESTUDIANTE`, `DOCENTE` (multipart: `archivo`, `proposito=AVAL_PRESTAMO`) | `201 ArchivoResponse` | `401`, `403`, `409 DEMASIADOS_ARCHIVOS_PENDIENTES`, `422 TIPO_ARCHIVO_NO_PERMITIDO`, `422 ARCHIVO_DEMASIADO_GRANDE`, `422 PROPOSITO_INVALIDO` |
| `GET` | `/api/v1/files/archivos/{id}/contenido` | Según RN-60 | `200` (bytes) | `401`, `404 ARCHIVO_NO_ENCONTRADO` |
| `PUT` | `/api/v1/auth/me/foto` | Todos (multipart: `archivo`) | `200 UsuarioPublico` | `401`, `403 CAMBIO_PASSWORD_REQUERIDO`, `422` (tipo, tamaño o imagen ilegible) |
| `DELETE` | `/api/v1/auth/me/foto` | Todos | `200 UsuarioPublico` | `401` |
| `DELETE` | `/api/v1/users/{id}/foto` | `ADMIN_LOCAL`, `SUPERADMIN` | `200 UsuarioDetalle` | `401`, `403`, `404 USUARIO_NO_ENCONTRADO` |

`ArchivoResponse`: `{id, proposito, tipo_mime, tamano_bytes, nombre_original, created_at}`. `UsuarioPublico`, `UsuarioResumen` y `UsuarioDetalle` suman `foto_id: UUID | null`.

La foto se sube por `/auth/me/foto` (un solo paso: sube, vincula y reemplaza). El aval se sube por `/files/archivos` y su id viaja después en la orden de `loans` (C4 de SPEC-05).

### 6.4 Reglas

| ID | Regla |
| --- | --- |
| RN-55 | El tipo se decide por la firma de los primeros bytes. La extensión y el `Content-Type` del cliente se ignoran |
| RN-56 | El tamaño se controla mientras se lee: al superar el máximo se corta la lectura y se responde `422 ARCHIVO_DEMASIADO_GRANDE`, sin cargar el resto en memoria |
| RN-57 | `nombre_original` se sanea (sin rutas ni caracteres de control, hasta 255) y sólo se usa como nombre sugerido de descarga |
| RN-58 | Un usuario tiene como máximo 5 archivos sin vincular; el sexto responde `409 DEMASIADOS_ARCHIVOS_PENDIENTES` |
| RN-59 | Reemplazar o quitar la foto borra el archivo anterior en la misma transacción y deja traza en `usuarios_historial_cambios` (`{"foto_id": [antes, después]}`) |
| RN-60 | Descarga. `FOTO_PERFIL`: el propietario y los administradores con jurisdicción sobre la sede **actual** del propietario. `AVAL_PRESTAMO`: el propietario (el estudiante o el docente que pide el equipo) y los administradores con jurisdicción sobre `archivos.sede`, que son quienes verifican la resolución antes de aprobar. **El docente de la asignatura no lo descarga** cuando el solicitante es un estudiante: sólo observa la solicitud (PRE-20) y el aval es una resolución del Consejo, no un dato que necesite (P6.4, D-18). El `SUPERADMIN` ve todo. Cualquier otro caso responde `404`, nunca `403` (RN-11 de SPEC-01) |
| RN-61 | La descarga responde con `Content-Type` guardado, `Content-Disposition: attachment` para PDF e `inline` para fotos, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; sandbox` y `Cache-Control: private, no-store` |
| RN-62 | Un aval vinculado no se borra: forma parte de la orden, que no se borra físicamente (P7.3) |
| RN-63 | `limpiar-huerfanos` borra los archivos sin vincular creados hace más de `ARCHIVO_HUERFANO_HORAS` (24). Es idempotente. La periodicidad la define el despliegue |
| RN-64 | El `ADMIN_LOCAL` sólo quita la foto de usuarios de su jurisdicción y de rol `ESTUDIANTE` o `DOCENTE` (mismas reglas que UC-12 de SPEC-02) |

### 6.5 API pública de `files` (para `loans`)

| Función | Contrato |
| --- | --- |
| `vincular_archivo(db, archivo_id, *, propietario_id, proposito) -> None` | Bloquea la fila (`FOR UPDATE`) y la marca vinculada. Falla con `422 ARCHIVO_INVALIDO` si no existe, es de otro propietario, tiene otro propósito o ya está vinculado (un solo código, para no revelar cuál; ver D-19). No hace `commit`: `loans` la llama en la misma transacción que crea la orden, sea el solicitante estudiante o docente |
| `abrir_archivo(db, archivo_id) -> ArchivoContenido \| None` | `ArchivoContenido` (dataclass frozen: `id`, `tipo_mime`, `nombre_original`, `datos`). **Sin control de acceso**: lo hace quien llama. Para que `loans` sirva el aval desde el detalle de la orden con su propio control de jurisdicción, que debe respetar RN-60 (no al docente de la asignatura) |
| `respuesta_descarga(contenido) -> Response` | Arma la respuesta con los encabezados de RN-61, para que todos los módulos sirvan archivos igual |

### 6.6 Frontend

- `src/lib/api.ts` admite `FormData` (sin `Content-Type` JSON) y respuestas `Blob`.
- Las imágenes y los PDF **no** se piden con `<img src>` ni con un enlace directo, porque el token está en `sessionStorage` y no viaja solo: se descargan con `Authorization` y se muestran con `URL.createObjectURL`, liberando la URL al desmontar. Helper `descargarArchivo(id)` en `src/lib/api.ts`.
- Mi perfil: subir, ver y quitar la foto, con aviso previo de tipo y tamaño. Navbar: avatar con la foto o las iniciales. Gestión de usuarios: la foto en el detalle y "Quitar foto" para administradores.
- La carga del aval en el formulario de préstamo es del Perfil 3 (ítem K3).

---

## 7. Fase B3 — Renovación de sesión (D-06 de SPEC-01 frente a ADR-015)

### 7.1 Opciones evaluadas

| Opción | Cómo funciona | A favor | En contra |
| --- | --- | --- | --- |
| (a) Dejar como está | Access token de 60 min en `sessionStorage` | Nada que hacer | La sesión se corta trabajando (EC-32 de SPEC-02); una pestaña olvidada sigue válida hasta 60 min |
| (b) Refresh token en cookie `HttpOnly` | Access corto en memoria; refresh rotativo en cookie `HttpOnly; Secure; SameSite=Strict`; tabla de sesiones con detección de reutilización | El JavaScript no puede leer el refresh token | Contradice ADR-015: la cookie sobrevive al cierre de la pestaña y los navegadores que restauran la sesión la conservan al reabrirse, justo el riesgo de las computadoras compartidas. Exige frontend y API en el mismo sitio (hoy son orígenes distintos), CORS con credenciales y protección CSRF. Ante un XSS el atacante igual opera desde la página. Tabla y migración nuevas |
| (c) **Renovación deslizante** | `POST /auth/renovar` cambia un access token vigente por otro nuevo; el token lleva `auth_time` (inicio de sesión) y se rechaza la renovación pasado un tope absoluto | Mantiene ADR-015 (cerrar la pestaña cierra la sesión); resuelve el corte mientras se trabaja; permite **acortar** el token a 30 min, así una sesión inactiva vence antes que hoy; sin tablas nuevas | No protege el token de un XSS (tampoco lo hace hoy) |

**Recomendación: (c)** (D-13). Se puede reconsiderar (b) si el despliegue pone frontend y API bajo el mismo dominio y el equipo prioriza endurecer frente a XSS.

### 7.2 Contrato (opción c)

| Método | Ruta | Roles | Éxito | Errores |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/auth/renovar` | Sesión válida (también con cambio obligatorio pendiente) | `200 TokenResponse` | `401 TOKEN_*`, `401 TOKEN_SESION_MAXIMA` |
| `POST` | `/api/v1/auth/me/sesiones/cerrar` | Todos | `200 TokenResponse` (token nuevo para la sesión actual) | `401` |

| ID | Regla |
| --- | --- |
| RN-65 | El token nuevo conserva `auth_time` del original y tiene `exp` = ahora + `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (el valor por defecto pasa de 60 a **30**) |
| RN-66 | Si ahora − `auth_time` supera `JWT_SESION_MAX_HORAS` (por defecto 8), responde `401 TOKEN_SESION_MAXIMA`; el código empieza con `TOKEN_`, así el frontend cierra la sesión como ante cualquier otro `401 TOKEN_*` (SPEC-02 §6.1) |
| RN-67 | La renovación revalida contra la base (estado `ACTIVO` y `token_version`), igual que `get_current_user`. El token anterior no se revoca: vence solo |
| RN-68 | Un token sin `auth_time` (emitido antes de esta versión) usa `iat` como inicio |
| RN-69 | "Cerrar todas mis sesiones" incrementa `token_version` y devuelve un token nuevo para la pestaña actual |
| RN-70 | El frontend renueva sólo si hubo actividad del usuario (teclado, mouse o navegación) en los últimos minutos y faltan menos de 5 para el vencimiento. Sin actividad, el token vence y se vuelve al login con aviso. El token sigue en `sessionStorage` (ADR-015) |

---

## 8. Catálogo de códigos nuevos

| `code` | HTTP | Mensaje sugerido |
| --- | --- | --- |
| `DEMASIADOS_INTENTOS` | 429 | Hiciste demasiados pedidos. Probá de nuevo más tarde. |
| `TOKEN_RECUPERACION_INVALIDO` | 422 | El enlace no es válido o ya venció. Pedí uno nuevo. |
| `TIPO_ARCHIVO_NO_PERMITIDO` | 422 | El tipo de archivo no está permitido. |
| `ARCHIVO_DEMASIADO_GRANDE` | 422 | El archivo supera el tamaño máximo de N MB. |
| `PROPOSITO_INVALIDO` | 422 | Ese tipo de archivo no se puede subir desde acá. |
| `IMAGEN_INVALIDA` | 422 | No se pudo leer la imagen. |
| `DEMASIADOS_ARCHIVOS_PENDIENTES` | 409 | Tenés demasiados archivos sin usar. Esperá o enviá la solicitud. |
| `ARCHIVO_NO_ENCONTRADO` | 404 | Archivo no encontrado. |
| `ARCHIVO_INVALIDO` | 422 | El archivo indicado no es válido para esta operación. |
| `TOKEN_SESION_MAXIMA` | 401 | Pasó el tiempo máximo de la sesión. Iniciá sesión nuevamente. |

El `429` no figura en la lista de la Constitución §4.2; se agrega sólo para el límite de intentos porque es el código estándar que entienden clientes y proxies (D-07). Los errores de archivos usan `422` y no `413`/`415` para mantenerse dentro de esa lista.

---

## 9. Criterios de aceptación

Cada criterio tendrá al menos un test anotado `# AC-NN`, con `pytestmark = pytest.mark.integracion` y PostgreSQL real (P9). Los criterios agregados en la v0.2.0 (AC-100, AC-101) se numeran al final para no renumerar los existentes; lo mismo RN-71…RN-76, EC-47…EC-50 y D-16…D-19.

### 9.1 Fase A — `tests/users/test_datos_publicos.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-61 | Con usuarios existentes devuelve `{id: DatosPublicosUsuario(id, nombre, apellido)}` con los valores de la base | §4.1 |
| AC-62 | Con ids repetidos devuelve una entrada por id y ejecuta **una sola** consulta (contada con un listener `before_cursor_execute`) | RN-35, RN-41 |
| AC-63 | Con una lista vacía (o un generador vacío) devuelve `{}` y no ejecuta ninguna consulta | RN-36 |
| AC-64 | Los ids inexistentes se omiten; si todos son inexistentes devuelve `{}` sin error | RN-37 |
| AC-65 | Incluye usuarios en los cinco estados de cuenta | RN-38 |
| AC-66 | Devuelve en una misma llamada usuarios de Ushuaia, de Río Grande y un `SUPERADMIN` (sede nula) | RN-39 |
| AC-67 | `DatosPublicosUsuario` tiene exactamente los campos `id`, `nombre` y `apellido`. Asignar uno de esos campos lanza `FrozenInstanceError`. Agregar un atributo que no es campo (por ejemplo `dni`) falla y la instancia no tiene `__dict__`. El tipo de excepción no se exige porque depende de la versión de Python: `FrozenInstanceError` en 3.14, `TypeError` en 3.12 y 3.13 (DT-30) | RN-40, P6 |
| AC-68 | Después de la llamada no hay entidades `Usuario` nuevas en el *identity map* de la sesión (no se cargó DNI, email ni teléfono) | RN-40 |
| AC-69 | No confirma la transacción: un cambio pendiente del llamador se descarta con `rollback` después de la llamada, y la sesión sigue en la misma transacción | RN-42 |
| AC-70 | Acepta lista, conjunto y generador, y un lote de 40 000 ids sin error | RN-41 |

### 9.2 Fase B1 — `tests/users/test_recuperacion.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-71 | Email de una cuenta activa → `202` neutro; un correo en el backend `memoria` con un enlace `#/restablecer?token=`; la base guarda sólo el SHA-256 | RN-44, RN-46, RN-47 |
| AC-72 | Email inexistente y cuentas pendiente, rechazada, suspendida e inactiva → el mismo `202` (código y cuerpo) y ningún correo | RN-44, RN-45 |
| AC-73 | Confirmar con un token válido → `200`; el login funciona con la nueva y falla con la anterior; un access token previo → `401 TOKEN_REVOCADO`; `debe_cambiar_password = false`; el historial registra `{"password": ["***","***"]}` | RN-52 |
| AC-74 | Un token usado, vencido, aleatorio o de una cuenta que pasó a `SUSPENDIDO` → `422 TOKEN_RECUPERACION_INVALIDO` | RN-50, RN-51 |
| AC-75 | Una segunda solicitud invalida el token anterior; un restablecimiento invalida los demás; cambiar el email invalida los pendientes | RN-48, RN-53 |
| AC-76 | Dos confirmaciones simultáneas con el mismo token (sesiones independientes, ADR-013): una `200` y otra `422` | RN-50 |
| AC-77 | Una contraseña débil o igual al email → `422` y el token **no** se consume | RN-03 de SPEC-01 |
| AC-78 | La cuarta solicitud con el mismo email en una hora → `429 DEMASIADOS_INTENTOS`, exista o no la cuenta; el límite por IP también se aplica; las filas de más de 24 h se borran | RN-49 |
| AC-79 | Los dos endpoints funcionan sin token; un campo desconocido → `422`; un fallo de SMTP no cambia el `202` y el log no contiene el token | §5.1, P4.4 |
| AC-80 | Migración de B1: upgrade → downgrade → upgrade | P7.4 |
| AC-100 | Cada valor de `TipoCorreo` (`RECUPERACION_PASSWORD` y `NOTIFICACION`) tiene plantilla y se renderiza con un contexto de ejemplo sin variables sin reemplazar; si falta una variable, `renderizar_correo` falla y no se envía nada. `NOTIFICACION` con `titulo` y `mensaje` da el asunto `[PrestaMeDios] <titulo>` y un cuerpo con el mensaje y el enlace a la aplicación | RN-71, RN-75, RN-77 |
| AC-101 | `enviar_correo` se llama desde código de servicio, fuera de una request y sin `BackgroundTasks`, y el mensaje queda en el backend `memoria`; un fallo del transporte llega al llamador como `ErrorEnvioCorreo` y el log no incluye el contexto ni el cuerpo | RN-72…RN-74 |

### 9.3 Fase B2 — `tests/files/`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-81 | Un estudiante y un docente suben cada uno un PDF de aval → `201` con id UUID, tamaño, tipo y hash; quedan sin vincular | §6.3, ADR-022 (i) |
| AC-82 | Un PNG con extensión `.pdf` → `422 TIPO_ARCHIVO_NO_PERMITIDO`; un archivo de más del máximo → `422 ARCHIVO_DEMASIADO_GRANDE`; `proposito=FOTO_PERFIL` en `/files/archivos` → `422 PROPOSITO_INVALIDO` | RN-55, RN-56 |
| AC-83 | `PUT /auth/me/foto` con un JPEG con EXIF de ubicación → `200`, `foto_id` asignado; la imagen guardada es JPEG de hasta 512 px y sin EXIF | §6.2, D-11 |
| AC-84 | Reemplazar la foto borra la anterior; quitarla deja `foto_id = null`; ambas cosas quedan en el historial | RN-59 |
| AC-85 | Descarga del aval: propietario estudiante o docente `200`; `ADMIN_LOCAL` de la sede `200`; `ADMIN_LOCAL` de la otra sede `404`; otro estudiante `404`; un docente que no es el propietario `404`; `SUPERADMIN` `200`. Descarga de la foto con las reglas de RN-60. Encabezados de RN-61 presentes | RN-60, RN-61, D-18 |
| AC-86 | `vincular_archivo` vincula el aval de su propietario; otro propietario, otro propósito, ya vinculado o inexistente → `422 ARCHIVO_INVALIDO`; no hace `commit` | §6.5 |
| AC-87 | El sexto archivo sin vincular → `409 DEMASIADOS_ARCHIVOS_PENDIENTES` | RN-58 |
| AC-88 | `limpiar-huerfanos` borra los no vinculados viejos y conserva los vinculados y los recientes; correrlo dos veces da el mismo resultado | RN-63 |
| AC-89 | `DELETE /users/{id}/foto`: `ADMIN_LOCAL` de la sede `200`; de otra sede `404`; sobre un administrador `403` | RN-64 |
| AC-90 | Migración de B2: upgrade → downgrade → upgrade | P7.4 |

### 9.4 Fase B3 — `tests/users/test_renovacion.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-91 | `POST /auth/renovar` con un token vigente → token nuevo con el mismo `auth_time` y `exp` posterior | RN-65 |
| AC-92 | Pasado `JWT_SESION_MAX_HORAS` desde `auth_time` → `401 TOKEN_SESION_MAXIMA`; con un token revocado o vencido → el `401 TOKEN_*` habitual | RN-66, RN-67 |
| AC-93 | Un token sin `auth_time` se renueva tomando `iat` como inicio | RN-68 |
| AC-94 | "Cerrar todas mis sesiones" → los tokens anteriores responden `401 TOKEN_REVOCADO` y el devuelto funciona | RN-69 |

### 9.5 Frontend (`npm run typecheck`, `npm run build`, Vitest y verificación manual)

| ID | Criterio |
| --- | --- |
| AC-95 | Login con enlace de recuperación; la pantalla de recuperación muestra siempre el mensaje neutro y el de `429` |
| AC-96 | El enlace del correo abre "Restablecer contraseña", el token desaparece de la barra de direcciones, la validación de RN-03 es en línea y al terminar se vuelve al login con aviso |
| AC-97 | Mi perfil sube, muestra y quita la foto; el Navbar muestra el avatar; las imágenes se piden con `Authorization` (sin token en URLs) |
| AC-98 | La sesión se renueva con actividad y vence sin ella; `TOKEN_SESION_MAXIMA` lleva al login con aviso |
| AC-99 | `npm run typecheck`, `npm run build` y los tests de Vitest (lectura del fragmento, cliente con `FormData`/`Blob`, programación de la renovación) en verde |

---

## 10. Casos de borde

| ID | Escenario | Resultado |
| --- | --- | --- |
| EC-34 | `datos_publicos_por_ids` con un id de un usuario dado de baja que tiene reservas | Se devuelve su nombre (RN-38) |
| EC-35 | `datos_publicos_por_ids` dentro de una transacción con cambios sin `flush` | Con `autoflush=False` (configuración del proyecto en `app/database.py` y en los tests), los cambios sin `flush` no se emiten: la consulta no ve usuarios que el llamador agregó sin `flush`, y la función no confirma nada (RN-42) |
| EC-36 | El email de la solicitud de recuperación con mayúsculas o espacios | Se normaliza (RN-04 de SPEC-01) antes de buscar y de calcular el hash del límite |
| EC-37 | Se pide la recuperación con sesiones abiertas en otras computadoras | Al confirmar se cierran todas (RN-52) |
| EC-38 | La cuenta se suspende entre el envío del enlace y la confirmación | `422 TOKEN_RECUPERACION_INVALIDO` (RN-51) |
| EC-39 | Usuario con `debe_cambiar_password = true` pide recuperación | Se envía el correo; al restablecer, el indicador queda en `false` (la contraseña la eligió el usuario) |
| EC-40 | Varias computadoras del laboratorio salen a internet con la misma IP | El límite por IP es holgado (20 por hora); el límite fino es por email |
| EC-41 | El usuario cambia la foto desde dos pestañas a la vez | La fila del usuario se bloquea (`FOR UPDATE`); queda la última y la otra se borra |
| EC-42 | Un PDF de aval cuya orden se rechaza o se cancela | Se conserva vinculado (RN-62) |
| EC-43 | Un `SUPERADMIN` sube un aval | No aplica: sólo `ESTUDIANTE` y `DOCENTE` crean órdenes (D-L06 de SPEC-05); responde `403` |
| EC-44 | Un usuario cambia de sede con un aval vinculado | El aval sigue bajo la jurisdicción de la sede en la que se subió (`archivos.sede`) |
| EC-45 | `loans` integra `0011` o `0012`, u otro módulo integra una migración, antes que las de este spec | El nombre no cambia (D-22). Sólo cambia `down_revision`, que pasa a ser la cabeza de `develop` al abrir el PR; antes de mergear, `alembic heads` debe mostrar una sola cabeza |
| EC-46 | El token vence mientras se completa un formulario sin actividad registrada | El envío falla con `401 TOKEN_EXPIRADO`; se mantiene el comportamiento de EC-32 de SPEC-02 |
| EC-47 | Un docente pide alta gama con su resolución del Consejo | Mismo flujo que un estudiante: sube el PDF, `loans` lo vincula y lo verifica el administrador de su sede (ADR-022 i) |
| EC-48 | El docente de la asignatura intenta descargar el aval de un estudiante | `404 ARCHIVO_NO_ENCONTRADO` (D-18) |
| EC-49 | Falla el correo que avisa un llamado de atención o una sanción (spec siguiente) | La sanción queda registrada igual. `notifications` guarda el error en la notificación, y el log no tiene el contenido (RN-73, RN-74, ADR-023) |
| EC-50 | Usuarios cargados antes de que el teléfono sea obligatorio | Siguen sin teléfono y operan normalmente hasta el spec siguiente (D-16) |

---

## 11. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| NFR-17 | Cobertura ≥ 85 % del código nuevo de `users`, `core` y `files`. Todos los AC de backend automatizados contra PostgreSQL |
| NFR-18 | `datos_publicos_por_ids` con 100 ids: p95 < 20 ms (una consulta por PK) |
| NFR-19 | Los tokens de recuperación, los enlaces y el contenido de los archivos nunca aparecen en logs ni en respuestas de error (NFR-02 de SPEC-01) |
| NFR-20 | La solicitud de recuperación responde en un tiempo similar exista o no la cuenta: el correo se envía fuera del ciclo de la respuesta |
| NFR-21 | Dependencias nuevas de backend: `python-multipart` (B2, la requiere `UploadFile` de FastAPI) y `Pillow` (B2, D-11). Ninguna para B1 (`smtplib` es estándar) ni para B3. Frontend: ninguna |
| NFR-22 | En desarrollo el correo se prueba con Mailpit (SMTP local, sin envío real); se documenta en el README del backend |

---

## 12. Decisiones resueltas

> Aprobadas por el Perfil 1 el 2026-11-03: se adoptan todas las recomendaciones (D-01…D-19). D-04 y D-19 quedan resueltas como "fuera de esta versión": el vínculo docente–asignatura sigue pendiente de la decisión del equipo (K4) y la reutilización del aval, de la respuesta de la referente (§12.2). La v1.1.0 suma D-20…D-22 (§12.1).

| ID | Pregunta | Opciones | Recomendación |
| --- | --- | --- | --- |
| D-01 | ¿Cómo se entrega? | (a) Fase A sola y primero; B1, B2 y B3 en PRs separados · (b) todo junto | **(a)**: la Fase A desbloquea a dos perfiles y no depende de nada |
| D-02 | ¿Hace falta un endpoint HTTP de datos públicos? | (a) Sólo función de servicio · (b) también `GET /users/publicos?ids=` | **(a)**: los consumidores son módulos del backend; un endpoint exigiría reglas de autorización propias (YAGNI) |
| D-03 | ¿Esquema Pydantic compartido para el solicitante? | (a) Cada módulo declara el suyo con la forma `{id, nombre, apellido}` · (b) uno común en `users/schemas.py` o en `core` | **(a)**: no agrega dependencias de esquemas entre módulos; `DatosPublicosUsuario` es compatible con `from_attributes=True` |
| D-04 | Vínculo docente–asignatura (C2 y C3 de SPEC-05), hoy sin dueño | (a) Fuera de esta versión y como decisión del equipo; el Perfil 1 se ofrece a tomarlo en un spec propio · (b) Entra en la Fase A · (c) Lo toma el Perfil 3 dentro de `loans` | **(a)**. Meterlo en la Fase A la demora (requiere catálogo, ABM y migración) y la Fase A tiene que salir rápido. Si el equipo se lo asigna al Perfil 1, la propuesta es: tablas `asignaturas` (sede, código, nombre, activa) y `docentes_asignaturas` en `users`, ABM para administradores con jurisdicción y funciones públicas `asignaturas_de_docente(db, docente_id) -> set[int]` y `asignatura_existe(db, asignatura_id, sede) -> bool`. PRE-20 no necesita matricular estudiantes: la orden ya trae `asignatura_id`. Mientras tanto rige D-L13 de SPEC-05 |
| D-05 | Transporte de correo | (a) `smtplib` estándar en un hilo, con backends `smtp` y `memoria` · (b) `aiosmtplib` · (c) un proveedor por API | **(a)**: sin dependencia nueva (P10) y suficiente para el volumen |
| D-06 | Respuesta ante un email no registrado | (a) Respuesta neutra y corrección del CU del ERS · (b) Informar que no existe, como dice el ERS | **(a)**: la Constitución P4.5 prevalece sobre el ERS; se corrige el flujo alternativo por PR a `Docs-PrestaMeDios` (ítem K7) |
| D-07 | Vigencia y límites de la recuperación | (a) Variables de entorno (30 min, 3 por email y 20 por IP por hora), `429` sólo para el límite · (b) Parámetros del panel GLO-03 | **(a)**: son parámetros técnicos de seguridad, no reglas del reglamento (P8 habla de estas últimas) |
| D-08 | ¿Qué cuentas pueden recuperar? | (a) Sólo `ACTIVO` · (b) también `SUSPENDIDO` | **(a)**: una cuenta no activa no puede iniciar sesión de todos modos. La referente lo confirmó el 16/10: un suspendido no entra y ve "Tu cuenta está suspendida" |
| D-09 | ¿El restablecimiento inicia sesión? | (a) No, lleva al login · (b) Sí, devuelve un token | **(a)**: confirma que el usuario recuerda la contraseña nueva y simplifica el flujo |
| D-10 | ¿Dónde se guardan los archivos? | (a) `BYTEA` en una tabla aparte · (b) Disco local con metadatos en la base · (c) Almacenamiento de objetos (S3, MinIO) | **(a)**: transaccional (no quedan archivos sin fila ni filas sin archivo), una sola copia de seguridad (`pg_dump`), sin volumen extra en Docker y tests simples. El volumen previsto es chico (fotos de 512 px y PDF de hasta 10 MB). Se revisa si el total supera ~5 GB; el servicio aísla el almacenamiento para poder migrar a (c) |
| D-11 | ¿Se vuelve a codificar la foto en el servidor? | (a) Sí, con `Pillow` · (b) Sólo validar la firma y reducir en el navegador | **(a)**: quita la ubicación del EXIF (P6) y neutraliza políglotas en el backend, que es la autoridad (P2.2) |
| D-12 | ¿Dónde vive el almacenamiento? | (a) Módulo nuevo `files` del Perfil 1 · (b) Dentro de `users` · (c) En `core` | **(a)**: lo usan `users` y `loans`, tiene router y tablas propias, y `core` es sólo transversal sin endpoints. Requiere sumarlo a `AGENTS.md` §3 y `docs/perfiles.md` |
| D-13 | Refresh token o cookie `HttpOnly` (D-06 de SPEC-01) | (a) Dejar como está · (b) Refresh en cookie `HttpOnly` · (c) Renovación deslizante con tope | **(c)**, por lo expuesto en §7.1. ADR-015 sigue vigente |
| D-14 | ¿"Cerrar todas mis sesiones" entra en B3? | (a) Sí · (b) No | **(a)**: es un incremento de `token_version` y sirve en computadoras compartidas |
| D-15 | Identificador de archivo | (a) UUID v4 · (b) entero | **(a)**: no se puede recorrer por números consecutivos, aunque el control de acceso se aplica igual |
| D-16 | Teléfono obligatorio en el registro (USR-05, ADR-022 b): ¿dónde entra y qué se hace con los usuarios que ya están cargados sin teléfono? | (a) En el spec siguiente: obligatorio en `RegistroRequest` y `UsuarioAdminCreate`; `PATCH /auth/me` ya no permite borrarlo; la columna **sigue admitiendo nulos** y el frontend pide completarlo con un aviso no bloqueante; pasa a `NOT NULL` en una migración posterior, cuando no queden nulos · (b) En la Fase A · (c) `NOT NULL` ya, con un valor de relleno para los existentes · (d) Un `CHECK (telefono IS NOT NULL) NOT VALID` | **(a)**. (b) demora la Fase A, que no toca el registro. (c) mete datos falsos en la base. (d) parece cómodo pero no sirve: PostgreSQL aplica un `CHECK NOT VALID` a toda fila que se actualiza, así que cualquier edición de un usuario viejo sin teléfono (aprobarlo, suspenderlo, cambiarle el email) fallaría. Además, el texto de USR-05 en el ERS todavía no lo dice (DT-29) y va primero en el PR del ERS (K7) |
| D-17 | ¿Cómo se envían los avisos que dispara un servicio (sanciones)? | (a) Envío directo después del commit, sin reintentos; el fallo queda en el log · (b) Bandeja de salida transaccional (`correos_salientes`) que llena el servicio en su transacción y despacha un proceso aparte, con reintentos | **(a) en este spec**: la interfaz de §5.1 alcanza y no agrega tablas. (b) se decide en el spec de sanciones, después de que el Perfil 5 responda K6: si los avisos pasan por `notifications`, la bandeja (si hace falta) es de ese módulo. La recuperación nunca usa (b), porque guardaría el enlace con el token en claro. **Cerrada el 2026-11-07 por ADR-023:** la bandeja de salida es la tabla `notificaciones` de SPEC-06, y este spec no agrega ninguna |
| D-18 | ¿El docente de la asignatura descarga el aval de un estudiante? | (a) No · (b) Sí, en modo lectura | **(a)**: el que verifica la resolución es el administrador antes de aprobar; el docente sólo observa (PRE-20) y no necesita el documento (P6.4). Si la referente lo pide, `loans` lo habilita con `abrir_archivo` sin cambiar este spec |
| D-19 | ¿Una misma resolución del Consejo se reutiliza en varios pedidos? Los docentes piden alta gama con regularidad | (a) No por ahora: un PDF por orden; se pregunta a la referente · (b) Sí: el propietario puede vincular su aval a más de una orden y listar los suyos (`GET /files/archivos?proposito=AVAL_PRESTAMO`) | **(a)**, con la pregunta de §12.2. Habilitar (b) después es chico: relajar la regla de "ya vinculado" para el mismo propietario y agregar el listado |

### 12.1 Decisiones nuevas de la v1.1.0 (aprobadas por el Perfil 1 el 2026-11-08)

| ID | Pregunta | Opciones | Recomendación |
| --- | --- | --- | --- |
| D-20 | ¿En qué orden se entrega la Fase B? | (a) B2 → B1 → B3 · (b) B1 → B2 → B3, el orden del plan v1.0 | **(a)**. La Fase 1 de `loans` ya está en `develop` y rechaza todo pedido de alta gama con `422 AVAL_REQUERIDO` hasta que exista `files`: es lo que hoy frena a otro perfil (K3). B1 sólo la espera la Fase C de SPEC-06, que está diferida. B1 y B2 no dependen una de otra: sólo comparten `settings.py`, `.env.example` y `conftest.py`, así que la segunda se rebasa sobre la primera. B3 sigue siendo independiente |
| D-21 | ¿Cómo manda `notifications` sus correos con este transporte (ADR-023)? | (a) Un tipo genérico `TipoCorreo.NOTIFICACION` con `titulo` y `mensaje` ya armados por `notifications` (RN-77) · (b) Una función aparte, `enviar_mensaje(destinatario, CorreoRenderizado)`, sin plantilla · (c) Un `TipoCorreo` por cada aviso (`LLAMADO_ATENCION`, `SANCION`…), con su plantilla en `core` | **(a)**. Se mantiene una sola entrada al transporte, con RN-71…RN-75 (prefijo, log sin contenido, un destinatario) para todos los correos. El texto de cada aviso lo arma `notifications`, que ya tiene plantillas por tipo (SPEC-06 RN-N7). (b) duplica la entrada al transporte. (c) duplica las plantillas en dos módulos y obliga a tocar `core` por cada aviso nuevo. Reemplaza a los cuatro tipos que la v1.0.0 dejaba reservados |
| D-22 | ¿Qué número llevan las migraciones de la Fase B? | (a) Números reservados: `0014_files_init` (B2) y `0015_users_recuperacion` (B1). `down_revision` es la cabeza de `develop` al abrir el PR · (b) Renumerar al integrar, como decía EC-45 | **(a)**. `loans` reserva `0011` y `0012` y `notifications` usa `0013` (SPEC-05, SPEC-06). La cadena ya no sigue el orden de los números (`0013` sale de `0010`, y `0011` va a salir de `0013`), así que renumerar no ordena nada y obliga a tocar archivos ya revisados. Responde la parte de numeración de C19 de SPEC-05 |

### 12.2 Pregunta para la referente

1. ¿Una resolución del Consejo (CICSE/ICSE) ampara un solo pedido de alta gama o puede respaldar varios (por ejemplo, todos los de un proyecto de investigación o de un TIF)? (D-19)

---

## 13. Coordinación con otros perfiles (se registra en `MEMORY.md` §5 al aprobar)

| ID | Para | Pedido | Origen |
| --- | --- | --- | --- |
| K1 | Perfil 4 | Agregar `solicitante: {id, nombre, apellido} \| null` a `ReservaEspacioResponse` usando `datos_publicos_por_ids` sobre los ids de la página. La referente lo confirmó el 16/10 para el calendario maestro, **sólo para administradores**. Nunca en la disponibilidad (RN-43). *2026-11-08: la función está en `develop` (PR #18); falta el cambio en `spaces`* | Pedido del Perfil 4 (`MEMORY.md` §5), ADR-022 |
| K2 | Perfil 3 | Resumen del solicitante en las respuestas de `loans` para administradores (y docentes, según la pregunta 5 de SPEC-05 §15.2), con la misma función. *2026-11-08: la Fase 1 de `loans` todavía no la usa* | C2 de SPEC-05 |
| K3 | Perfil 3 | Cuando exista B2: con `pdf_aval_id: UUID` en `OrdenPedidoCreate` (ya está en el esquema), **obligatorio si hay ítems de alta gama, tanto para estudiantes como para docentes** (es el PDF de la resolución del Consejo CICSE/ICSE, ADR-022 i), llamar a `vincular_archivo` en la misma transacción. Si `loans` sirve el aval desde el detalle de la orden (con `abrir_archivo` y `respuesta_descarga`), sólo al solicitante y a los administradores con jurisdicción, no al docente de la asignatura (RN-60, D-18). Hasta entonces, la Fase 1 de `loans` responde `422 AVAL_REQUERIDO` a todo pedido de alta gama (por eso D-20 adelanta B2) | C4 de SPEC-05, ADR-022 (i) |
| K4 | Equipo y Perfil 3 | Decidir el dueño del catálogo de asignaturas y del vínculo docente–asignatura (D-04) | C2 y C3 de SPEC-05 |
| K5 | Equipo | Ratificar la enmienda 1.1.1 (§2.3) y decidir DT-19 | C13 de SPEC-05 |
| K6 | Perfil 5 | ~~Decidir si los avisos por email de llamados de atención y sanciones pasan por `notifications` o si `users` llama directo al transporte.~~ **Respondido el 2026-11-07 (ADR-023, C-N03 de SPEC-06):** pasan por `notifications`, con la tabla `notificaciones` como bandeja de salida y el comando `enviar-correos`. El transporte que usan es `TipoCorreo.NOTIFICACION` (RN-77, D-21) | ADR-022 (f) |
| K7 | Equipo (PR al ERS, lo arma el Perfil 1) | **Un solo PR al ERS** que haga las dos cosas: (1) DT-29, reflejar ADR-022 en USR-05, USR-09, GLO-01, GLO-03, GLO-04, RES-03, PRE-05 y PRE-11 y sus casos de uso; (2) corregir el flujo alternativo del CU de USR-02: respuesta neutra en lugar de "informa que no existe una cuenta" (D-06). Así el equipo revisa una sola vez los requisitos que salen de la entrevista y los de este spec | D-06, DT-29 |
| K8 | Despliegue (Perfil 1) | Variables SMTP en el entorno, Mailpit en el `docker-compose` de desarrollo, programación de `limpiar-huerfanos` junto con `procesar-vencimientos` (C5 de SPEC-05) y `enviar-correos` (C-N04 de SPEC-06), `--proxy-headers` si hay proxy inverso (RN-54) y una versión de Python fija para la imagen y la CI (DT-30) | §5, §6 |
| K9 | Perfiles 2–5 | El módulo `files` es nuevo; quien necesite archivos usa su API pública (§6.5) en vez de guardar por su cuenta | D-12 |
| K10 | Perfiles 3, 4 y 5 | Informativo: en el spec siguiente del Perfil 1, `horario.apertura` y `horario.cierre` pasan a ser por sede y se suma el parámetro con el correo de contacto del laboratorio (para el aviso de anticipación del Perfil 4). El Perfil 5 también lee el horario, en el portal (C-N05 de SPEC-06). Este spec no los cambia: hasta entonces se siguen leyendo las claves actuales | ADR-022 (a, c), C19 de SPEC-05 |
| K11 | Perfiles 3 y 5 | Numeración de migraciones (D-22): este spec usa `0014_files_init` y `0015_users_recuperacion`. Quien abra un PR con migración apunta `down_revision` a la cabeza de `develop` de ese momento y comprueba `alembic heads` antes de mergear. Responde la parte de numeración de C19 | C19 de SPEC-05, D-N08 de SPEC-06 |

---

## 14. Trazabilidad

Verificada el 2026-11-10 contra `develop` (backend `e54ad16`, frontend `e1ae84e`): cada criterio de backend tiene al menos un test anotado `# AC-NN` (tarea C-02). Rutas de tests relativas a `Backend-PrestaMeDios/tests/` y a `Frontend-PrestaMeDios/src/`.

| Requisito | Función o endpoint | Criterios | Bordes | Tests | Fase |
| --- | --- | --- | --- | --- | --- |
| C2 de SPEC-05 / pedido del Perfil 4 (soporte de PRE-15, RES-05) | `users.service.datos_publicos_por_ids` | AC-61…AC-70 | EC-34, EC-35 | `users/test_datos_publicos.py` | A |
| USR-02 | `POST /auth/recuperacion`, `POST /auth/recuperacion/confirmar`, `core.email.enviar_correo`; pantallas de recuperación | AC-71…AC-80, AC-95, AC-96 | EC-36…EC-40 | `users/test_recuperacion.py`, `users/test_schemas.py`, `users/test_migracion_recuperacion.py`; `features/auth/recuperacion.test.ts` | B1 |
| ADR-022 (f), ADR-023 — transporte de los avisos por correo | `core.email.TipoCorreo` (incluido `NOTIFICACION`), `renderizar_correo`, `enviar_correo` | AC-100, AC-101 | EC-49 | `core/test_email.py` | B1 |
| USR-03 (foto) | `PUT` y `DELETE /auth/me/foto`, `GET /files/archivos/{id}/contenido`; Mi perfil y Navbar | AC-83…AC-85, AC-97 | EC-41 | `users/test_foto.py`, `files/test_service.py`, `files/test_archivos.py`; `features/users/services/foto.test.ts`, `lib/api.test.ts` | B2 |
| USR-04 (moderación de foto) | `DELETE /users/{id}/foto` | AC-89 | — | `users/test_foto.py` | B2 |
| PRE-05 (almacenamiento del aval, estudiantes y docentes), C4 de SPEC-05 | `POST /files/archivos`, `files.service.vincular_archivo`, `abrir_archivo`, `respuesta_descarga`, CLI `limpiar-huerfanos` | AC-81, AC-82, AC-85…AC-88 | EC-42…EC-44, EC-47, EC-48 | `files/test_archivos.py`, `files/test_service.py`, `files/test_api_publica.py`, `files/test_cli.py` | B2 |
| USR-05 (teléfono obligatorio, ADR-022 b) | — (spec siguiente, D-16) | — | EC-50 | — | — |
| D-06 de SPEC-01, ADR-015 | `POST /auth/renovar`, `POST /auth/me/sesiones/cerrar`; renovación en `AuthContext` | AC-91…AC-94, AC-98 | EC-46 | `users/test_renovacion.py`, `core/test_security.py`; `features/auth/renovacion.test.ts` | B3 |
| P7.4 (migraciones) | `0015_users_recuperacion`, `0014_files_init` | AC-80, AC-90 | EC-45 | `users/test_migracion_recuperacion.py`, `files/test_migracion_0014.py` | B1, B2 |
| Frontend completo | `npm run typecheck`, `npm run build`, Vitest | AC-99 | — | 16 archivos, 126 tests en `develop` (tarea C-01) | Cierre |

**Bordes sin test propio.** EC-37 lo cubre AC-73 (un access token previo responde `TOKEN_REVOCADO` después de restablecer). EC-40 es un valor por defecto (20 por hora); el mecanismo del límite por IP lo prueba `test_limite_por_ip` (AC-78). EC-46 mantiene el comportamiento de EC-32 de SPEC-02 y se verificó a mano en B3. EC-49 y EC-50 corresponden al spec siguiente y a la Fase C de SPEC-06. **Criterios de frontend** (AC-95…AC-98): los tests de Vitest cubren la lógica (lectura del fragmento, cliente con `FormData` y `Blob`, `debeRenovar`); el resto se verificó con el recorrido manual registrado en las tareas B1-09, B2-09 y B3-03. Los tests de Vitest no llevan la anotación `AC-NN`.

---

## 15. Historial de cambios

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 1.1.0 | 2026-11-10 | Perfil 1 (con asistencia de IA) | **`IMPLEMENTADO`**, sin cambios de contrato. Tareas de cierre (C-01…C-03): §14 con los archivos de test de cada fila y los bordes sin test propio, verificada contra `develop` (backend `e54ad16`, frontend `e1ae84e`). Las lecturas del spec hechas durante la implementación (por ejemplo, que `cerrar_sesiones` conserva `auth_time` y exige el cambio de contraseña resuelto) quedan en `tasks.md` (B3-02) |
| 1.1.0 | 2026-11-08 | Perfil 1 (con asistencia de IA) | **Aprobado** por el Perfil 1 el mismo día, con D-20…D-22 tal como se recomiendan. Puesta al día con SPEC-05 v1.0.0 (Fase 1 de `loans` en `develop`) y SPEC-06 v1.0.0 (ADR-023), sin cambios en el contrato de la Fase A, que queda **implementada** (PR #18, §4.4). **Contrato:** `TipoCorreo.NOTIFICACION` para `notifications` (RN-77, D-21, AC-100), que reemplaza a los cuatro tipos reservados para sanciones. **Decisiones nuevas:** orden B2 → B1 → B3 (D-20) y migraciones `0014_files_init` y `0015_users_recuperacion` (D-22, EC-45, K11). **Correcciones:** EC-35 (con `autoflush=False` los cambios sin `flush` no se emiten, plan §9) y AC-67 (el tipo de excepción al agregar un atributo depende de la versión de Python, DT-30). **Al día:** §2.1 verificado contra `develop`, D-17 cerrada por ADR-023, K1–K3, K6, K8 y K10 actualizados, §1.2, RN-72, RN-73 y EC-49. La pregunta para la referente pasa a §12.2 |
| 1.0.0 | 2026-11-03 | Perfil 1 | **Aprobado** con todas las recomendaciones de §12 (D-01…D-19). Sin cambios de contenido respecto de la v0.2.0 |
| 0.2.0 | 2026-11-02 | Perfil 1 (con asistencia de IA) | Ajustes por la tercera entrevista (ADR-022), sin cambios en la Fase A. §2.4 nuevo con el impacto. §5.1: el correo pasa a ser un transporte con plantillas por tipo de mensaje (`TipoCorreo`, `renderizar_correo`) y llamable desde servicios, pensando en los avisos de sanciones (RN-71…RN-76, AC-100, AC-101, D-17). §6 y K3: el aval es la resolución del Consejo, obligatoria para estudiantes y docentes; el docente de la asignatura no la descarga (RN-60, AC-81, AC-85, D-18); reutilizar una resolución queda abierto (D-19, §12.1). §1.2: horario por sede y correo de contacto, delegación temporal del Superadministrador, USR-09 reformulado, teléfono obligatorio y DT-29, con destino en el spec siguiente del Perfil 1. D-16 (teléfono obligatorio). D-08 confirmada por la referente. K6 pasa a decisión del Perfil 5; K7 propone un solo PR al ERS con DT-29; K10 nuevo. EC-47…EC-50 |
| 0.1.0 | 2026-11-02 | Perfil 1 (con asistencia de IA) | Borrador inicial para revisión |
