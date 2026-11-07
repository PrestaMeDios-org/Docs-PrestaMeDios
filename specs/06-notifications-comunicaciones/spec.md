# SPEC-06 — Comunicaciones y notificaciones (`notifications`)

> **Estado:** `APROBADO` (2026-11-07, con todas las recomendaciones de §12) · **Versión:** 1.0.0 · **Perfil:** 5 (Comunicaciones e IA)
> **Plan y tareas:** `specs/06-notifications-comunicaciones/plan.md` · `specs/06-notifications-comunicaciones/tasks.md`
> **Requisitos:** NOV-01, NOV-02, NOV-04 (Fases A y B) · NOV-03 (Fase C, contrato diferido) · **Responde a:** C12 de SPEC-05, S7 de la revisión del Perfil 4, K6 de SPEC-03
> **Precedencia:** `docs/constitution.md` → `AGENTS.md` → `docs/perfiles.md` → este spec → `MEMORY.md`.
> **Origen:** revisión del Perfil 1 sobre el Perfil 5 (`revision-perfil-5-notifications-assistant.md`, 2026-11-06), que propone escribir el spec por fases para no frenar a `loans` y `spaces`. El asistente de IA (IA-01…IA-03) queda **fuera** de este spec y va en SPEC-07 (D-N09).

---

## 1. Alcance

**Dentro** (módulo `notifications`, backend y frontend):

1. **Fase A — Portal y comunicados (NOV-01, NOV-02).** Sección "Novedades" con un portal estático (normativas, horarios, datos institucionales) y comunicados que publican los administradores, por sede o globales.
2. **Fase B — Centro de notificaciones (NOV-04).** Notificaciones personales con la campanita real, alertas críticas y la **función pública `crear_notificacion`**, que llaman `loans` y `spaces` dentro de su propia transacción.
3. **Fase C — Alertas automáticas y correo (NOV-03, K6).** Se especifica sólo el **contrato** (§6.4 y §13). La implementación queda diferida hasta que existan `loans` (SPEC-05), `app/core/email.py` (SPEC-03) y la ejecución periódica (C5 del Perfil 1).

**Fuera:**

- Asistente de IA (IA-01…IA-03): SPEC-07.
- Llamar a `crear_notificacion` desde `loans`, `spaces` o `users`: lo hace cada perfil dueño en su módulo (§10).
- Transporte de correo (`app/core/email.py`): Perfil 1, SPEC-03.
- Programar la ejecución periódica (cron, contenedor): Perfil 1, despliegue (C5).
- Notificaciones push al navegador o al celular, y tiempo real con WebSocket o SSE (D-N04).
- Cualquier cambio en `core`, `users`, `config`, `inventory`, `loans` o `spaces`.

## 2. Actores y permisos

| Actor | Portal (NOV-01) | Leer comunicados (NOV-02) | Publicar, editar, archivar | Notificaciones propias (NOV-04) |
| :---- | :---- | :---- | :---- | :---- |
| `ESTUDIANTE`, `DOCENTE` | Sí | Los de su sede y los globales, vigentes | No | Sí, sólo las propias |
| `ADMIN_LOCAL` | Sí | Los de su sede y los globales, incluidos los archivados de su sede | Sólo comunicados de su sede | Sí, sólo las propias |
| `SUPERADMIN` | Sí | Todos; puede filtrar por sede | Por sede o globales | Sí, sólo las propias |

Se reutiliza sin cambios: `get_current_user`, `require_roles`, `resolver_alcance_sede`, `puede_ver_sede`, `AppError`, `error_responses`, `RolUsuario`, `SedeEnum`, `enum_values` y `users.service.datos_publicos_por_ids` (SPEC-03 Fase A). Un comunicado o una notificación fuera del alcance del usuario responde `404`, no `403`, para no revelar que existe (Constitución §4.2, P4.5).

**Nadie lee notificaciones ajenas**, tampoco los administradores. Una notificación es un aviso personal, no un registro de auditoría (USR-08 es del Perfil 1).

## 3. Estado actual (verificado en `develop`, 2026-11-06)

| Elemento | Estado |
| :---- | :---- |
| Backend | No existe `app/modules/notifications`. No hay tablas, endpoints ni tests |
| Campanita | Maqueta en `Frontend-PrestaMeDios/src/components/layout/Navbar.tsx:7` (`NOTIFICATIONS_DATA`, datos fijos). Al abrirla marca todo como leído sólo en el estado local |
| "Novedades" | Ítem `news` en `Sidebar.tsx` y título en `App.tsx`, sin pantalla |
| Parámetros | `notificacion.aviso_vencimiento_horas = 24` ya está sembrado (`config/seed.py`). `horario.apertura` y `horario.cierre` se pueden leer con `GET /api/v1/config/{clave}` desde cualquier rol con sesión |
| Correo | `app/core/email.py` **todavía no existe** (SPEC-03 Fase B, sin mergear) |
| `loans` | Migración `0009_loans_init` en `develop`; endpoints en `501`. SPEC-05 reserva `0011` y `0012` |

## 4. Reglas de negocio

### 4.1 Portal y comunicados (Fase A)

- **RN-N1 (portal, NOV-01).** El portal es contenido fijo del frontend (D-N02): normativa (Res. CICSE N° 056/2023), datos de contacto y direcciones de las sedes. El **horario operativo no se escribe en el código**: se lee de `config` (`horario.apertura`, `horario.cierre`) para cumplir P8. Cuando el horario pase a ser por sede (ADR-022 a), se ajustan las claves que se leen (C-N05).
- **RN-N2 (alcance de un comunicado, NOV-02, GLO-01).** Un comunicado es **de una sede** (`sede` con valor, `es_global = false`) o **global** (`sede = NULL`, `es_global = true`). La base lo garantiza con un `CHECK`.
  - `ADMIN_LOCAL`: el comunicado queda en su sede. Indicar otra sede o `es_global = true` responde `403 SEDE_FUERA_DE_ALCANCE`.
  - `SUPERADMIN`: tiene que elegir una sede o `es_global = true`. Si no indica ninguna de las dos, responde `422 SEDE_REQUERIDA`. Si indica ambas, `422` de validación. Un comunicado nunca queda global por omisión.
- **RN-N3 (lectura).** Estudiantes, docentes y `ADMIN_LOCAL` ven los comunicados de su sede más los globales. El filtro se aplica en la consulta SQL. Para estudiantes y docentes sólo se listan los **vigentes**: estado `PUBLICADO` y `vence_en` nulo o futuro. Se ordenan del más nuevo al más viejo.
- **RN-N4 (vencimiento y archivo, D-N03).** `vence_en` es opcional. Un comunicado vencido deja de verse para estudiantes y docentes sin que nadie intervenga. Los administradores pueden archivarlo antes (`ARCHIVADO`) o reactivarlo. No hay borrado físico (P7.3).
- **RN-N5 (edición).** Un `ADMIN_LOCAL` edita y archiva los comunicados de su sede, aunque los haya escrito otro administrador. Los globales sólo los toca el `SUPERADMIN`. La sede y el alcance no se editan: para cambiarlos se archiva el comunicado y se publica uno nuevo.

### 4.2 Notificaciones personales (Fase B)

- **RN-N6 (destinatario único, P6).** Cada notificación tiene un solo destinatario y sólo él la ve. Los endpoints toman el usuario del token y nunca aceptan un `usuario_id` en la ruta, la query ni el body.
- **RN-N7 (contenido por tipo).** El llamador no escribe texto libre: elige un `TipoNotificacion` y pasa `datos`. `notifications` arma el título y el mensaje con la plantilla de ese tipo, usando `string.Template` como SPEC-03 RN-71, sin dependencias nuevas. Cada tipo declara qué claves de `datos` admite. Si falta una clave o sobra alguna, `crear_notificacion` lanza `ValueError` **antes** de guardar nada: es un error de programación del llamador, no un error de negocio. El texto se guarda ya armado, así la notificación no cambia aunque después cambien los datos de origen.
- **RN-N8 (privacidad del contenido, P6).** Las plantillas no incluyen DNI, email ni teléfono de nadie. Las claves admitidas por tipo están en una lista cerrada (§6.2), que se revisa en la aprobación del spec. Un nombre de otra persona sólo aparece si el destinatario ya puede verlo (por ejemplo, el docente que comentó su propia solicitud).
- **RN-N9 (severidad, NOV-04).** Cada tipo tiene una severidad fija: `NORMAL` o `CRITICA`. Son críticas la **cancelación forzada** (PRE-17) y la **aprobación con horario modificado** (PRE-18), como pide NOV-04. Las críticas se muestran destacadas y **no se marcan como leídas por abrir la campanita**: el usuario tiene que abrirlas. Las normales se marcan al abrirlas o con "marcar todas".
- **RN-N10 (transacción, R4 de la revisión).** `crear_notificacion` hace `db.add` y nada más: **no hace `commit`, `rollback` ni `flush`**, igual que `inventory/service.py`. Si el llamador deshace su transacción, la notificación también se deshace. Así nunca se avisa un cambio que no ocurrió.
- **RN-N11 (marcar como leída).** Sólo el destinatario marca sus notificaciones. Marcar una que ya está leída responde `200` sin cambios (idempotente). `leida_en` guarda la primera lectura.
- **RN-N12 (cuentas no activas).** Se notifica aunque el destinatario esté `SUSPENDIDO` o `INACTIVO`: lo va a ver cuando vuelva a entrar. `crear_notificacion` no consulta el estado de la cuenta.
- **RN-N13 (sin notificaciones por comunicados, D-N06).** Publicar un comunicado no crea una notificación por cada usuario de la sede. La pantalla "Novedades" se encarga de mostrarlos.

### 4.3 Concurrencia y paginación

- **RN-N14.** "Marcar todas como leídas" es un único `UPDATE ... WHERE usuario_id = :yo AND leida_en IS NULL AND severidad = 'NORMAL'`: no hay carrera posible con una notificación que llega en ese momento, porque esa queda sin leer. Las listas se paginan con `limit` (1…100, por defecto 20) y `offset`.

## 5. Contratos (prefijo `/api/v1/notifications`, todos con sesión)

Errores en formato `{detail, code}` mediante `AppError` y validación `422` estándar de FastAPI. Los payloads `*Create` y `*Update` usan `extra="forbid"` y `str_strip_whitespace=True`. Los `*Response` usan `from_attributes=True`. Todos los campos llevan `Field(..., examples=[...])`.

### 5.1 Comunicados (NOV-02) — Fase A

| Método y ruta | Roles | Descripción |
| :---- | :---- | :---- |
| `GET /comunicados` | Todos | Lista según RN-N3. Query: `sede` (sólo `SUPERADMIN`; otro rol con otra sede → `403`), `incluir_archivados: bool = false` (sólo admins; para el resto se ignora), `limit`, `offset`. Respuesta: `{items: [ComunicadoResponse], total}` |
| `GET /comunicados/{id}` | Todos | Detalle. Fuera de alcance, archivado o vencido para estudiante o docente → `404 COMUNICADO_NO_ENCONTRADO` |
| `POST /comunicados` | `ADMIN_LOCAL`, `SUPERADMIN` | Publica (RN-N2). `201` |
| `PATCH /comunicados/{id}` | `ADMIN_LOCAL`, `SUPERADMIN` | Edita `titulo`, `contenido` y `vence_en` (RN-N5) |
| `PATCH /comunicados/{id}/estado` | `ADMIN_LOCAL`, `SUPERADMIN` | `{estado: "PUBLICADO" \| "ARCHIVADO"}`. Pasar al mismo estado → `200` idempotente |

```python
class ComunicadoCreate(BaseModel):
    model_config = _INPUT_CONFIG
    titulo: str = Field(..., min_length=3, max_length=150)
    contenido: str = Field(..., min_length=1, max_length=5000)   # texto plano, sin HTML
    sede: SedeEnum | None = None
    es_global: bool = False
    vence_en: datetime | None = None                             # futuro; con zona horaria

class ComunicadoUpdate(BaseModel):          # todos opcionales; al menos uno
    model_config = _INPUT_CONFIG
    titulo: str | None = Field(None, min_length=3, max_length=150)
    contenido: str | None = Field(None, min_length=1, max_length=5000)
    vence_en: datetime | None = None

class ComunicadoResponse(BaseModel):
    id: int
    titulo: str
    contenido: str
    sede: SedeEnum | None
    es_global: bool
    estado: EstadoComunicado                # PUBLICADO | ARCHIVADO
    vigente: bool                           # calculado: PUBLICADO y no vencido
    autor: DatosPublicosUsuario | None      # nombre y apellido; None si el autor se dio de baja
    publicado_en: datetime
    vence_en: datetime | None
    actualizado_en: datetime
```

`contenido` es texto plano: el frontend lo muestra como texto, nunca como HTML, para evitar XSS. Respetar los saltos de línea alcanza (D-N07).

### 5.2 Notificaciones personales (NOV-04) — Fase B

| Método y ruta | Roles | Descripción |
| :---- | :---- | :---- |
| `GET /notificaciones` | Todos | Las del usuario del token. Query: `solo_no_leidas: bool = false`, `limit`, `offset`. Orden: no leídas críticas, luego el resto por `creada_en` descendente. Respuesta: `{items: [NotificacionResponse], total}` |
| `GET /notificaciones/resumen` | Todos | `{no_leidas: int, criticas_no_leidas: int}`. Es la consulta que el frontend repite para el número de la campanita (D-N04) |
| `PATCH /notificaciones/{id}/leida` | Todos | Marca una como leída (RN-N11). Ajena o inexistente → `404 NOTIFICACION_NO_ENCONTRADA` |
| `POST /notificaciones/leer-todas` | Todos | Marca las `NORMAL` no leídas (RN-N9, RN-N14). Respuesta: `{marcadas: int}` |

```python
class NotificacionResponse(BaseModel):
    id: int
    tipo: TipoNotificacion
    severidad: Severidad                    # NORMAL | CRITICA
    titulo: str
    mensaje: str
    referencia: ReferenciaNotificacion | None   # {modulo: "loans" | "spaces" | "users", id: int}
    creada_en: datetime
    leida_en: datetime | None
```

`referencia` le permite al frontend llevar al usuario a la solicitud o reserva correspondiente. Abrir el recurso sigue pasando por los permisos del módulo dueño: la referencia no da acceso a nada.

No hay `POST /notificaciones`: sólo se crean desde el código de servicio (§6).

## 6. Interfaz pública hacia `loans`, `spaces` y `users`

Es el contrato que esperan SPEC-05 (C12) y el Perfil 4 (S7). Se publica con la aprobación de este spec, aunque la Fase B se implemente después, para que los otros perfiles puedan programar contra él.

### 6.1 Funciones (`app/modules/notifications/service.py`)

```python
async def crear_notificacion(
    db: AsyncSession,
    usuario_id: int,
    tipo: TipoNotificacion,
    datos: Mapping[str, str],
    *,
    referencia: ReferenciaNotificacion | None = None,
) -> Notificacion:
    """Agrega una notificación a la transacción de quien llama (NOV-04, RN-N10).

    - No hace ``commit``, ``rollback`` ni ``flush``: la transacción es del llamador.
    - Valida ``datos`` contra las claves del tipo (RN-N7) y lanza ``ValueError``
      antes de agregar nada si falta o sobra una clave.
    - Arma título y mensaje con la plantilla del tipo; no consulta el estado
      de la cuenta del destinatario (RN-N12).
    """

async def crear_notificaciones(
    db: AsyncSession,
    usuario_ids: Iterable[int],
    tipo: TipoNotificacion,
    datos: Mapping[str, str],
    *,
    referencia: ReferenciaNotificacion | None = None,
) -> list[Notificacion]:
    """Lo mismo para varios destinatarios con el mismo mensaje.

    Caso típico: RES-05, al aprobar una reserva se rechazan las solicitudes
    superpuestas. Ids repetidos se notifican una sola vez.
    """
```

`TipoNotificacion`, `Severidad` y `ReferenciaNotificacion` se importan de `app.modules.notifications.enums` y `app.modules.notifications.schemas`. Es la única parte del módulo que otros módulos pueden importar.

### 6.2 Tipos de la Fase B

Los textos de las plantillas son una propuesta y se ajustan al aprobar. Las fechas llegan en `datos` ya formateadas por el llamador (`"12/11 10:00"`), en la zona horaria del laboratorio.

| `TipoNotificacion` | Lo emite | Severidad | Claves de `datos` | Título propuesto |
| :---- | :---- | :---- | :---- | :---- |
| `ORDEN_APROBADA` | `loans` | NORMAL | `numero_orden`, `retiro` | Solicitud aprobada |
| `ORDEN_RECHAZADA` | `loans` | NORMAL | `numero_orden`, `motivo` | Solicitud rechazada |
| `ORDEN_CANCELADA` | `loans` | NORMAL | `numero_orden`, `motivo` | Solicitud cancelada |
| `ORDEN_HORARIO_AJUSTADO` | `loans` (PRE-18) | **CRITICA** | `numero_orden`, `retiro`, `devolucion` | Aprobada con horario modificado |
| `ORDEN_CANCELACION_FORZADA` | `loans` (PRE-17) | **CRITICA** | `numero_orden`, `motivo` | Cancelación por fuerza mayor |
| `ORDEN_NO_RETIRADA` | `loans` (PRE-08) | NORMAL | `numero_orden` | Reserva cancelada por no retiro |
| `PRESTAMO_DEMORADO` | `loans` | NORMAL | `numero_orden`, `devolucion` | Préstamo demorado |
| `RESERVA_APROBADA` | `spaces` (RES-05) | NORMAL | `espacio`, `fecha`, `horario` | Reserva aprobada |
| `RESERVA_RECHAZADA` | `spaces` (RES-05) | NORMAL | `espacio`, `fecha`, `horario`, `motivo` | Reserva rechazada |
| `RESERVA_CANCELACION_FORZADA` | `spaces` (RES-04) | **CRITICA** | `espacio`, `fecha`, `horario`, `motivo` | Reserva cancelada por el laboratorio |

Los tipos de `spaces` se confirman con el Perfil 4 (C-N02). Agregar un tipo es agregar un valor al enum, su fila en el registro de plantillas y su test. No hace falta migración (D-N05).

### 6.3 Ejemplo de uso desde otro módulo

```python
# loans/service.py — dentro de aprobar_orden, antes del commit del endpoint
await crear_notificacion(
    db,
    orden.usuario_id,
    TipoNotificacion.ORDEN_HORARIO_AJUSTADO,
    {"numero_orden": str(orden.id), "retiro": fmt(orden.retiro), "devolucion": fmt(orden.devolucion)},
    referencia=ReferenciaNotificacion(modulo="loans", id=orden.id),
)
```

### 6.4 Fase C — contrato diferido (NOV-03, K6)

Se adelanta para que el Perfil 1 lo tenga en cuenta en SPEC-03 y en el spec de sanciones. **No se implementa en esta versión.**

- Tipos nuevos: `PRESTAMO_POR_VENCER` (NOV-03, con `notificacion.aviso_vencimiento_horas`), `LLAMADO_ATENCION` y `SANCION` (ADR-022 f, emitidos por `users`).
- `crear_notificacion` suma el parámetro `por_correo: bool = False`. Con `True`, la notificación queda marcada como **correo pendiente** en la misma fila.
- La propia tabla `notificaciones` funciona como bandeja de salida (D-N01). Un comando idempotente, `python -m app.modules.notifications.cli enviar-correos`, toma las pendientes **ya confirmadas**, llama a `app/core/email.py` y registra `correo_enviado_en` o el error. Así se cumple RN-72 de SPEC-03 (avisar después del commit) sin que cada llamador tenga que recordarlo. Lo programa el despliegue, igual que `procesar-vencimientos` de `loans` (D-L08, C5).
- El aviso de vencimiento lo genera `loans` en su proceso periódico llamando a `crear_notificacion`. `notifications` no consulta tablas de `loans`.

## 7. Modelo de datos y migración

Migración `00NN_notifications_init`. El número se fija al mergear: hoy la última en `develop` es la `0010`, y SPEC-05 reserva la `0011` y la `0012`. La propuesta es `0013` (D-N08). Los modelos se registran en `alembic/env.py`. La migración es reversible y se valida con `upgrade` → `downgrade -1` → `upgrade` (P7.4).

**`comunicados`** (Fase A)

| Columna | Tipo | Notas |
| :---- | :---- | :---- |
| `id` | `integer` identity, PK | |
| `titulo` | `varchar(150)` | `NOT NULL` |
| `contenido` | `text` | `NOT NULL`, `CHECK (length(contenido) <= 5000)` |
| `sede` | `sede_enum` (compartido, `create_type=False`) | `NULL` si es global |
| `es_global` | `boolean` | `NOT NULL DEFAULT false` |
| `estado` | `estado_comunicado_enum` (`PUBLICADO`, `ARCHIVADO`) | `NOT NULL DEFAULT 'PUBLICADO'` |
| `autor_id` | FK `usuarios.id` `ON DELETE SET NULL` | |
| `publicado_en` | `timestamptz` | `NOT NULL DEFAULT now()` |
| `vence_en` | `timestamptz` | `NULL`; `CHECK (vence_en IS NULL OR vence_en > publicado_en)` |
| `actualizado_en` | `timestamptz` | `NOT NULL DEFAULT now()` |

- `CHECK ((es_global AND sede IS NULL) OR (NOT es_global AND sede IS NOT NULL))`, nombrado `alcance_coherente` (RN-N2).
- Índice `ix_comunicados_estado_sede_publicado` sobre (`estado`, `sede`, `publicado_en DESC`).

**`notificaciones`** (Fase B)

| Columna | Tipo | Notas |
| :---- | :---- | :---- |
| `id` | `bigint` identity, PK | |
| `usuario_id` | FK `usuarios.id` `ON DELETE RESTRICT` | `NOT NULL`. Los usuarios no se borran físicamente (RN-17) |
| `tipo` | `varchar(50)` | `NOT NULL`. Lo valida el enum de Python (D-N05) |
| `severidad` | `severidad_notificacion_enum` (`NORMAL`, `CRITICA`) | `NOT NULL` |
| `titulo` | `varchar(150)` | `NOT NULL` |
| `mensaje` | `varchar(1000)` | `NOT NULL` |
| `referencia_modulo` | `varchar(30)` | `NULL` |
| `referencia_id` | `bigint` | `NULL` |
| `creada_en` | `timestamptz` | `NOT NULL DEFAULT now()` |
| `leida_en` | `timestamptz` | `NULL` |

- `CHECK ((referencia_modulo IS NULL) = (referencia_id IS NULL))`, nombrado `referencia_completa`.
- Índices `ix_notificaciones_usuario_creada` sobre (`usuario_id`, `creada_en DESC`) y uno parcial, `ix_notificaciones_no_leidas`, sobre (`usuario_id`) con `WHERE leida_en IS NULL` (lo usa `/resumen`).
- Los valores de los enums van en mayúsculas, como en `core` (`ACTIVO`). La unificación de estilos sigue pendiente (DT-09, DT-19).

## 8. Frontend (`src/features/notifications/`)

Estructura feature-first: `components/`, `pages/`, `services/` (cliente sobre `src/lib/api.ts`, ruta `/api/v1/notifications`), `types/` (DTOs `snake_case` y `mappers.ts`).

| Pieza | Fase | Contenido |
| :---- | :---- | :---- |
| `NewsPage` (pantalla `news`) | A | Pestañas "Comunicados" e "Información del laboratorio". Comunicados: lista con fecha, alcance ("Global" o la sede) y vencimiento, aviso de "No hay comunicados" y manejo de carga y error. Portal: normativa, contactos y horario leído de `config` (RN-N1) |
| `ComunicadoForm` | A | Sólo admins. Para `ADMIN_LOCAL` no aparece el selector de alcance; para `SUPERADMIN` es obligatorio elegir sede o "Global" (RN-N2). Validación en rojo de campos obligatorios, como PRE-04. Botones de archivar y reactivar |
| `NotificationBell` | B | Reemplaza `NOTIFICATIONS_DATA` en `Navbar.tsx`. Pide `/notificaciones/resumen` al montar y cada 60 s, y no consulta mientras la pestaña está oculta (`visibilitychange`). Al abrirla carga `/notificaciones?limit=20`. Las críticas se muestran arriba y destacadas, y sólo se marcan al abrirlas (RN-N9). Botón "Marcar todas como leídas". Si hay `referencia`, lleva a la pantalla correspondiente |

`Navbar.tsx` está en `components/layout/`, que es compartido. El cambio se limita a reemplazar la maqueta de la campanita por `<NotificationBell />`, sin tocar el resto del layout (C-N06).

## 9. Criterios de aceptación

Se usa el prefijo `NTF-` para no confundirlos con los requisitos NOV-xx. Cada uno tendrá al menos un test (`# NTF-NN`), con `pytestmark = pytest.mark.integracion` y PostgreSQL real.

| ID | Criterio | Fase | Req. |
| :---- | :---- | :---- | :---- |
| NTF-01 | Todo endpoint del módulo responde `401 NO_AUTENTICADO` sin token | A, B | P4.1 |
| NTF-02 | Un `ADMIN_LOCAL` publica: el comunicado queda en su sede. Con otra sede o `es_global = true` → `403 SEDE_FUERA_DE_ALCANCE` | A | NOV-02, GLO-01 |
| NTF-03 | `SUPERADMIN` sin sede ni `es_global` → `422 SEDE_REQUERIDA`; con ambos → `422`; con uno de los dos se crea según lo indicado | A | RN-N2 |
| NTF-04 | Insertar directo en la base un comunicado con `es_global = true` y una sede falla por el `CHECK` `alcance_coherente` | A | P7.1 |
| NTF-05 | Estudiante y docente de Ushuaia ven los de Ushuaia y los globales, y no los de Río Grande; pedir `sede=Río Grande` → `403` | A | RN-N3, P5 |
| NTF-06 | Un comunicado vencido o archivado no aparece para estudiante ni docente, y su `GET /{id}` responde `404`; un admin de la sede lo ve con `incluir_archivados=true` | A | RN-N4 |
| NTF-07 | `SUPERADMIN` sin `sede` ve todos; con `sede` ve los de esa sede más los globales | A | RN-N3 |
| NTF-08 | Estudiante y docente reciben `403 PERMISO_INSUFICIENTE` al publicar, editar o archivar | A | NOV-02 |
| NTF-09 | Un `ADMIN_LOCAL` edita y archiva un comunicado de su sede escrito por otro admin; uno de la otra sede o uno global → `404` | A | RN-N5 |
| NTF-10 | `PATCH /comunicados/{id}` con `sede`, `es_global` u otro campo desconocido → `422` | A | RN-N5 |
| NTF-11 | `vence_en` en el pasado al crear o editar → `422` | A | RN-N4 |
| NTF-12 | La respuesta incluye `autor` con nombre y apellido, sin email, DNI ni teléfono | A | P6 |
| NTF-13 | `crear_notificacion` agrega la fila a la transacción del llamador: con `commit` se guarda; con `rollback` no queda nada | B | RN-N10 |
| NTF-14 | Con una clave faltante o sobrante en `datos`, `crear_notificacion` lanza `ValueError` y no agrega nada | B | RN-N7 |
| NTF-15 | Cada valor de `TipoNotificacion` tiene plantilla y se arma con un `datos` de ejemplo sin variables sin reemplazar; ninguna plantilla incluye DNI, email ni teléfono | B | RN-N7, RN-N8 |
| NTF-16 | `ORDEN_HORARIO_AJUSTADO`, `ORDEN_CANCELACION_FORZADA` y `RESERVA_CANCELACION_FORZADA` se crean con severidad `CRITICA`; el resto, `NORMAL` | B | NOV-04, RN-N9 |
| NTF-17 | `GET /notificaciones` devuelve sólo las del usuario del token; la de otro usuario no aparece y su `PATCH …/leida` responde `404` | B | RN-N6, P6 |
| NTF-18 | `/resumen` cuenta bien `no_leidas` y `criticas_no_leidas` y cambia al marcar | B | NOV-04 |
| NTF-19 | `PATCH …/leida` dos veces responde `200` y conserva el primer `leida_en` | B | RN-N11 |
| NTF-20 | `leer-todas` marca sólo las `NORMAL` del usuario; las críticas siguen sin leer | B | RN-N9, RN-N14 |
| NTF-21 | `crear_notificaciones` con ids repetidos crea una notificación por destinatario | B | §6.1 |
| NTF-22 | Se puede notificar a un usuario `SUSPENDIDO`; la ve al reactivarse | B | RN-N12 |
| NTF-23 | Migración: `upgrade` → `downgrade -1` → `upgrade` sin errores sobre una base de desarrollo | A, B | P7.4 |
| NTF-24 | Frontend: "Novedades" carga los comunicados desde la API (sin datos fijos), muestra "No hay comunicados" y los errores; el horario del portal viene de `config` | A | NOV-01, NOV-02 |
| NTF-25 | Frontend: el selector de alcance no aparece para `ADMIN_LOCAL` y es obligatorio para `SUPERADMIN` | A | RN-N2 |
| NTF-26 | Frontend: la campanita usa la API (sin `NOTIFICATIONS_DATA`), muestra el número de no leídas, destaca las críticas y no las marca al abrirse | B | NOV-04 |

Verificación del frontend: `npm run typecheck`, `npm run build`, `npm test` (mappers y lógica de la campanita) y un recorrido manual contra el backend local con estudiante, `ADMIN_LOCAL` y `SUPERADMIN`. Para probar la campanita antes de que `loans` y `spaces` la usen, los tests crean notificaciones con `crear_notificacion` desde un fixture.

## 10. Coordinación con otros perfiles (a registrar en `MEMORY.md` §5 al aprobar)

| ID | Para | Pedido | Motivo |
| :---- | :---- | :---- | :---- |
| C-N01 | Perfil 3 (`loans`) | Llamar a `crear_notificacion` con los tipos de §6.2 en cada cambio de estado de §10.3 de SPEC-05, dentro de la transacción y sin `commit` propio. Responde C12 | NOV-04, PRE-17, PRE-18, PRE-08 |
| C-N02 | Perfil 4 (`spaces`) | Confirmar los eventos de reservas de §6.2 (aprobada, rechazada por superposición y cancelada por bloqueo administrativo) y usar `crear_notificaciones` al rechazar las superpuestas. Responde S7 | RES-04, RES-05 |
| C-N03 | Perfil 1 (`core`, SPEC-03) | **Respuesta a K6:** los avisos por correo (NOV-03 y ADR-022 f) pasan por `notifications`, que usa `app/core/email.py` como transporte (D-N01, §6.4). Para D-17 del spec de sanciones: la bandeja de salida, si hace falta, es la tabla `notificaciones` | K6, D-17 |
| C-N04 | Perfil 1 (despliegue, C5) | Programar `enviar-correos` (Fase C) junto con `procesar-vencimientos` de `loans` | NOV-03 |
| C-N05 | Perfil 1 (`config`) | Avisar cuando cambien las claves de horario por ADR-022 (a), para actualizar el portal | NOV-01, P8 |
| C-N06 | Equipo (frontend) | Informativo: `Navbar.tsx` sólo cambia para montar `NotificationBell` | NOV-04 |
| C-N07 | Perfil 3 (`loans`) | Informativo para la Fase C: el aviso de vencimiento lo emite `loans` desde su proceso periódico | NOV-03 |

## 11. Casos de borde

- Comunicado con `vence_en` dentro de pocos segundos: se acepta. Deja de verse cuando pasa esa hora, sin ningún proceso que lo archive.
- `ADMIN_LOCAL` que cambia de sede (lo hace el Perfil 1): desde ese momento ve y edita los comunicados de su sede nueva. Los que publicó en la anterior siguen ahí.
- Autor dado de baja: el comunicado sigue visible con `autor = null` ("Laboratorio").
- `GET /comunicados/{id}` con un id inexistente o fuera de alcance: siempre `404 COMUNICADO_NO_ENCONTRADO`.
- `crear_notificacion` con un `usuario_id` inexistente: falla la FK al confirmar y se deshace toda la transacción del llamador. Es un error de programación y no se traduce a un error de negocio.
- `crear_notificaciones` con una lista vacía: no hace nada y devuelve `[]`.
- Muchas notificaciones acumuladas: la campanita muestra las últimas 20 y un enlace "Ver todas". No se borran (D-N10).
- Contenido con `<script>` u otro HTML: se guarda tal cual y el frontend lo muestra como texto (D-N07).

## 12. Decisiones (resueltas)

Todas se resolvieron el 2026-11-07 según la recomendación, que pasa a ser la resolución. Quedan registradas en `MEMORY.md` como ADR-023.

| ID | Pregunta | Opciones | Resolución |
| :---- | :---- | :---- | :---- |
| D-N01 | **K6:** ¿los correos de avisos pasan por `notifications` o cada módulo llama a `core/email.py`? | (a) Por `notifications`, con la tabla como bandeja de salida · (b) Cada módulo llama directo al transporte | **(a)**: una sola fuente, lo que llega por correo también aparece en la campanita, y el envío después del commit queda resuelto en un solo lugar |
| D-N02 | ¿El portal estático (NOV-01) es fijo o editable? | (a) Fijo en el frontend, con el horario leído de `config` · (b) Editable por `SUPERADMIN` | **(a)** (P10). Si la referente lo pide editable, se agrega en una versión siguiente |
| D-N03 | ¿Los comunicados vencen o se archivan a mano? | (a) Las dos cosas · (b) Sólo a mano · (c) Sólo por fecha | **(a)**: vencimiento opcional y archivo manual |
| D-N04 | ¿Cómo se entera el frontend de una notificación nueva? | (a) Consulta cada 60 s a `/resumen` · (b) SSE o WebSocket | **(a)** (P10): una consulta liviana con índice parcial, sin infraestructura nueva. Se revisa si el despliegue lo exige |
| D-N05 | ¿`tipo` es un enum de PostgreSQL o `varchar`? | (a) `varchar(50)` validado en Python · (b) Enum de la base | **(a)**: los otros perfiles agregan tipos sin migración. La severidad sí es enum, porque no cambia |
| D-N06 | ¿Un comunicado nuevo genera notificaciones? | (a) No · (b) Una por usuario de la sede | **(a)**: evita miles de filas por aviso. Se puede sumar un indicador en "Novedades" |
| D-N07 | ¿Los comunicados admiten formato? | (a) Texto plano · (b) Markdown · (c) HTML | **(a)**: sin dependencia nueva y sin riesgo de XSS |
| D-N08 | Numeración del spec y de la migración | — | **SPEC-06**; migración `0013` salvo que la tome otro perfil antes |
| D-N09 | ¿El asistente (IA-01…03) va en este spec? | (a) SPEC-07 aparte · (b) Acá | **(a)**: depende de `loans`, de decidir el proveedor de LLM (dependencia nueva, a justificar en su plan, Constitución §3) y no frena a nadie |
| D-N10 | ¿Se borran las notificaciones viejas? | (a) No por ahora · (b) Purga periódica | **(a)** (YAGNI). Se revisa con datos reales |

## 13. Fases y dependencias

| Fase | Requisitos | Depende de | Entregable |
| :---- | :---- | :---- | :---- |
| **A** | NOV-01, NOV-02 | Nada nuevo (`core` y `config` ya existen) | Tabla `comunicados`, §5.1, `NewsPage` y `ComunicadoForm`; NTF-01…12, 23…25 |
| **B** | NOV-04 | Nada para implementarla; `loans` y `spaces` la conectan después (C-N01, C-N02) | Tabla `notificaciones`, §5.2, §6.1–§6.2 y `NotificationBell`; NTF-13…22, 26 |
| **C** *(diferida)* | NOV-03, K6 | SPEC-05 implementado, `app/core/email.py` (SPEC-03 B1), ejecución periódica (C5) | §6.4. Se especifica en una versión 0.2.0 de este spec, con sus criterios |

Las fases A y B pueden ir en PRs separados, en las ramas `feat/notifications-comunicados` y `feat/notifications-campanita` (backend y frontend). El contrato de §6 se publica con la aprobación, antes de implementar la Fase B.

## 14. Trazabilidad

| Requisito | Endpoints o funciones | Criterios |
| :---- | :---- | :---- |
| NOV-01 | Frontend `NewsPage` (portal), `GET /api/v1/config/{clave}` | NTF-24 |
| NOV-02 | `GET/POST /comunicados`, `GET/PATCH /comunicados/{id}`, `PATCH /comunicados/{id}/estado` | NTF-01…12, 23, 24, 25 |
| NOV-04 | `crear_notificacion`, `crear_notificaciones`, `GET /notificaciones`, `GET /notificaciones/resumen`, `PATCH /notificaciones/{id}/leida`, `POST /notificaciones/leer-todas` | NTF-13…22, 26 |
| GLO-01 (aplicado a comunicados) | RN-N2, RN-N3 | NTF-02, 03, 05, 07, 09 |
| NOV-03 | §6.4 (diferido) | Fase C |

## 15. Historial

| Versión | Fecha | Autor | Cambio |
| :---- | :---- | :---- | :---- |
| 1.0.0 | 2026-11-07 | Perfil 5 | **Aprobado** con todas las recomendaciones de §12 (D-N01…D-N10). Coordinación de §10 registrada en `MEMORY.md` §5; decisiones en ADR-023 |
| 0.1.0 | 2026-11-06 | Perfil 5 (con asistencia de IA) | Borrador inicial a partir de la revisión del Perfil 1. Fases A y B completas, Fase C como contrato diferido. Responde K6 (D-N01), C12 y S7 |
