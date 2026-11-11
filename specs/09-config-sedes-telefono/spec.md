# SPEC-09 — Horario y correo de contacto por sede, y teléfono obligatorio

| Campo | Valor |
| --- | --- |
| **ID** | SPEC-09 |
| **Perfil responsable** | Perfil 1 — Identidad, Usuarios, Permisos, Configuración Global y Despliegue |
| **Estado** | `APROBADO` — 2026-11-11, por el Perfil 1, con las recomendaciones de §10 (D-01…D-12) |
| **Versión** | 1.0.0 |
| **Requisitos cubiertos** | Fase A: GLO-03 (horario de cada sede y correo de contacto del laboratorio) y el dato que necesita GLO-02 ("según el horario de atención de esa sede"); ADR-022 (a) y (c) · Fase B: USR-05 (teléfono obligatorio), ADR-022 (b), D-16 de SPEC-03 |
| **Responde a** | K10 de SPEC-03; C19 (la parte del horario) y C1 de SPEC-05; C-N05 de SPEC-06; pedido (b) al Perfil 4 del 2026-11-02 (`MEMORY.md` §5) |
| **Depende de** | SPEC-01 v1.0.0 (`config`, `users`) y SPEC-03 v1.1.0 (D-16), `IMPLEMENTADO`, en `develop` |
| **Módulos afectados** | Backend: `config`, `users` · Frontend: `config`, `auth`, `users`, `layout` |
| **Módulos ajenos** | Ninguno se modifica. `spaces`, `loans` y `notifications` cambian la lectura del horario y muestran el correo de contacto: va como coordinación (§11) |
| **Relación con SPEC-08** | SPEC-08 es el spec de `spaces` del Perfil 4 (v1.0.0, línea base aprobada en el Docs PR #28). Su Fase 2 (K10, tareas T2.1…T2.3) ya adopta el contrato de §4.4 y §4.5 de este spec (H1) y espera a que la Fase A esté en `develop` |
| **Relación con SPEC-05** | La tarea T1.13 de SPEC-05 (AC-L63, RN-L04) consume `datos_de_sede` y ya define `sede` en `ReglasResponse` y `?sede=` para el `SUPERADMIN` (H2, EC-57) |
| **Constitución** | v1.1.0, con la enmienda 1.1.1 propuesta (ADR-019), sin ratificar. Las funciones públicas de §4.4 son compatibles con el texto vigente de P3.3 |
| **Fuente de verdad funcional** | `docs/ERS.md` (GLO-02, GLO-03, USR-05 y el flujo alternativo 02 del CU de reserva de espacios, actualizados por el Docs PR #25) |
| **Plan y tareas** | `specs/09-config-sedes-telefono/plan.md` y `tasks.md` |

> **Regla SDD:** spec `APROBADO`. Un cambio de alcance o de contrato se propone como versión nueva y vuelve a aprobarse.

> **Numeración:** el 07 está reservado para `assistant` (Perfil 5, `MEMORY.md` §1) y el 08 es el spec de `spaces` del Perfil 4, así que este spec es el 09. Los criterios, reglas, casos de borde y requisitos no funcionales siguen la numeración de SPEC-01…SPEC-03: `AC-102…`, `RN-78…`, `EC-51…`, `NFR-23…`. Las decisiones empiezan en `D-01`, como en cada spec.

---

## 0. Resumen ejecutivo

En la entrevista del 16/10 (ADR-022) la referente pidió tres cosas que son del Perfil 1 y que hoy frenan a otros perfiles. Este spec las agrupa en dos fases independientes, cada una con su PR:

- **Fase A — Configuración por sede (prioritaria).** El horario de atención pasa a ser **uno por sede**, y se agrega el **correo de contacto del laboratorio**, también por sede, para el aviso que se muestra cuando una solicitud no cumple la anticipación mínima. `config` publica una función de lectura (`datos_de_sede`) y un endpoint (`GET /api/v1/config/sedes`), para que `spaces`, `loans` y el portal dejen de leer las claves globales con un cambio de una línea. Las claves globales `horario.apertura` y `horario.cierre` quedan como obsoletas y no editables hasta que nadie las lea.
- **Fase B — Teléfono obligatorio.** Se aplica D-16 de SPEC-03, ya aprobada: el teléfono es obligatorio en el registro, en el re-registro y en el alta de cuentas, y ya no se puede borrar. La columna sigue admitiendo nulos para no romper las cuentas cargadas antes. El frontend le pide el teléfono a quien no lo tiene, con un aviso que no bloquea.

La **delegación temporal del rol de Superadministrador** (ADR-022 g) queda para un spec aparte, porque cambia la autorización del kernel (D-10).

---

## 1. Alcance

### 1.1 Dentro del alcance

| # | Capacidad | Requisitos | Fase |
| --- | --- | --- | --- |
| A1 | Seis parámetros nuevos de `config`: apertura y cierre del horario, y correo de contacto, para cada sede (§4.1) | GLO-03, ADR-022 a y c | A |
| A2 | Migración `0017_config_sedes`: crea las claves por sede con el horario vigente y deja las globales como obsoletas (§4.2) | P7.4, P8 | A |
| A3 | Validaciones: apertura anterior al cierre en cada sede, con las ediciones simultáneas de un par serializadas (G-5); correo con formato válido (§4.3) | GLO-03, RN-19 y RN-20 de SPEC-01 | A |
| A4 | Lectura para otros módulos: `datos_de_sede(db, sede)` y `datos_de_sedes(db)` en `config/service.py` (§4.4) | P3.3, P8 | A |
| A5 | `GET /api/v1/config/sedes` para el frontend (portal, aviso de anticipación, calendarios) (§4.5) | GLO-02, GLO-03, NOV-01 | A |
| A6 | Panel de parámetros: las claves nuevas se editan; las obsoletas se ven como no editables; el correo se carga en un campo de email (§4.7) | GLO-03 | A |
| B1 | Teléfono obligatorio al registrarse, al volver a registrarse después de un rechazo, en el alta administrativa y en la CLI `crear-superadmin` (§5.1) | USR-05, ADR-022 b | B |
| B2 | El teléfono se puede cambiar, pero no borrar, desde Mi perfil y desde la edición administrativa (§5.1) | USR-05, D-16 de SPEC-03 | B |
| B3 | Aviso no bloqueante para las cuentas sin teléfono, con enlace a Mi perfil (§5.3) | D-16 de SPEC-03 | B |

### 1.2 Fuera del alcance

| Capacidad | Destino |
| --- | --- |
| Que `spaces`, `loans` y el portal lean el horario de la sede (`datos_de_sede` o `GET /config/sedes`) y que el aviso de anticipación muestre el correo de contacto | Perfiles 3, 4 y 5 (H1…H3, §11). Este spec publica la lectura; no toca esos módulos |
| Borrar `horario.apertura` y `horario.cierre` | Migración posterior del Perfil 1, cuando ningún módulo las lea (RN-81, DT nueva al aprobar) |
| `NOT NULL` en `usuarios.telefono` | Migración posterior, cuando no queden cuentas sin teléfono (RN-87, DT nueva al aprobar) |
| Días de atención por sede (qué días abre cada laboratorio) | D-09: fuera de esta versión; los días de cierre se cargan como bloqueos (GLO-04) y se le pregunta a la referente (§10.1) |
| Que un `ADMIN_LOCAL` edite los parámetros de su sede | D-08: sigue editando sólo el `SUPERADMIN` (D-05 de SPEC-01) |
| Delegación temporal del rol de Superadministrador (GLO-01, ADR-022 g) | Spec propio del Perfil 1 (D-10) |
| Llamados de atención, faltas y suspensión (USR-09, ADR-022 d–f) y sus parámetros | Spec propio del Perfil 1, después de la Fase B de SPEC-06 y de las respuestas de la referente (`MEMORY.md` §6) |
| Verificar el teléfono (por SMS o llamada) o normalizarlo a un formato internacional | Trabajo futuro (P10). Se mantiene el formato que ya valida `users` |

---

## 2. Estado actual

### 2.1 Verificado en `develop` (backend `e54ad16`, frontend `8cbc76a`, 2026-11-11)

> Revisado de nuevo el 2026-11-11: el backend no cambió; el frontend sólo sumó el PR #21 (nombre e ícono de la página), que no toca nada de esta tabla.

| Elemento | Estado |
| --- | --- |
| `config/seed.py` | Ocho claves semilla, entre ellas `horario.apertura` (`09:00`) y `horario.cierre` (`16:00`), de tipo `HORA`, únicas para las dos sedes. Las siembra la migración `0005` con una copia congelada que `tests/config/test_semilla.py` compara con `PARAMETROS_SEMILLA`. `tests/conftest.py` siembra la base de tests con esa misma lista |
| `config/service.py` | `obtener_parametro(db, clave)` es la lectura pública. La regla cruzada `horario.apertura < horario.cierre` está en `_REGLAS_CRUZADAS`. Tipos admitidos: `ENTERO`, `DECIMAL`, `BOOLEANO`, `TEXTO` (1 a 300 caracteres) y `HORA`. `actualizar` bloquea con `FOR UPDATE` sólo la fila que se edita; `validar_reglas_cruzadas` lee la otra clave del par sin bloquearla |
| Quién lee el horario global | `spaces/service.py:99` (`horario(db)`, que usa la validación de franjas y la respuesta de disponibilidad); `loans/service.py:67` (`GET /loans/reglas`), `:279` (ajuste horario al aprobar) y `:850` (alta de orden, con el comentario "Horario global hasta que config publique el de cada sede (K10)"); el portal del frontend (`notifications/services/notificationsApi.ts:51`, que lee las dos claves y muestra "en ambas sedes") |
| Correo de contacto | No existe. `spaces` responde `422 ANTICIPACION_INSUFICIENTE` sin datos de contacto; `loans` usa el mismo código |
| `usuarios.telefono` | `String(20)` que admite nulos (`users/models.py:71`). En `_DatosCuentaBase` (registro y alta administrativa), `PerfilUpdate` y `UsuarioAdminUpdate` es `Telefono \| None = None`, con el formato `^\+?[0-9 \-]{6,20}$`. Mandar `null` lo borra. La CLI `crear-superadmin` lo toma como opcional (`users/cli.py:107`) |
| Frontend | El registro y el alta en Gestión de usuarios dicen "Teléfono (opcional)" y mandan `null` si el campo está vacío; Mi perfil permite vaciarlo. El panel de parámetros arma el control según `tipo` y respeta `editable` |

### 2.2 Brechas

| ID | Brecha | Requisito |
| --- | --- | --- |
| G-1 | Un solo horario para las dos sedes: Río Grande no puede abrir a otra hora que Ushuaia | GLO-02, GLO-03, ADR-022 a |
| G-2 | El aviso de anticipación mínima no tiene un correo para canalizar la urgencia | CU de reserva de espacios, FA-02; ADR-022 c |
| G-3 | Los Perfiles 3, 4 y 5 esperan que `config` publique el horario por sede para cambiar su lectura (K10, C19, C-N05) | P8 |
| G-4 | Se pueden crear cuentas sin teléfono y borrarlo después | USR-05, ADR-022 b |
| G-5 | Dos ediciones simultáneas de las dos claves de una regla cruzada (por ejemplo, apertura y cierre) se validan cada una contra el valor viejo de la otra y pueden dejar el par inconsistente. Ya pasa hoy con los tres pares globales; con seis claves de horario más, pasa a ser más probable | RN-20 de SPEC-01 |

---

## 3. Actores

| Actor | Fase A | Fase B |
| --- | --- | --- |
| `SUPERADMIN` | Edita el horario y el correo de cada sede en el panel | Teléfono obligatorio al dar de alta cuentas; no lo puede borrar |
| `ADMIN_LOCAL` | Ve los parámetros y su historial; no los edita (D-08) | Igual que el `SUPERADMIN`, sobre las cuentas de su sede |
| `ESTUDIANTE`, `DOCENTE` | Leen el horario y el correo de las dos sedes (`GET /config/sedes`) | Teléfono obligatorio al registrarse; aviso si su cuenta no lo tiene |
| Otros módulos (`spaces`, `loans`) | Llaman a `datos_de_sede` | — |
| Operador (CLI) | — | `crear-superadmin` exige `--telefono` |

---

## 4. Fase A — Configuración por sede

### 4.1 Claves nuevas (D-01, D-04)

Cada sede tiene un **segmento** fijo para formar la clave, porque los valores de `SedeEnum` llevan mayúsculas, espacios y tilde, y el `CHECK clave_formato` de `parametros_globales` sólo admite `[a-z0-9_]`:

| `SedeEnum` | Segmento |
| --- | --- |
| `USHUAIA` (`"Ushuaia"`) | `ushuaia` |
| `RIO_GRANDE` (`"Río Grande"`) | `rio_grande` |

| Clave | Tipo | Valor inicial | Descripción |
| --- | --- | --- | --- |
| `horario.ushuaia.apertura` | `HORA` | el de `horario.apertura` al migrar (D-03) | Hora de apertura del laboratorio de Ushuaia (GLO-02, GLO-03) |
| `horario.ushuaia.cierre` | `HORA` | el de `horario.cierre` al migrar | Hora de cierre del laboratorio de Ushuaia |
| `horario.rio_grande.apertura` | `HORA` | el de `horario.apertura` al migrar | Hora de apertura del laboratorio de Río Grande |
| `horario.rio_grande.cierre` | `HORA` | el de `horario.cierre` al migrar | Hora de cierre del laboratorio de Río Grande |
| `contacto.ushuaia.email` | `TEXTO` | `""` (sin configurar, D-05) | Correo de contacto del laboratorio de Ushuaia, para el aviso de anticipación mínima (ADR-022 c) |
| `contacto.rio_grande.email` | `TEXTO` | `""` (sin configurar) | Correo de contacto del laboratorio de Río Grande |

Ninguna lleva `unidad`, `valor_min` ni `valor_max`. Todas son `editable = true`.

### 4.2 Migración `0017_config_sedes`

- Nombre fijo; `down_revision` es la cabeza de `develop` al abrir el PR, y antes de mergear `alembic heads` muestra una sola cabeza (D-22 de SPEC-03). `0012` sigue reservado para `loans`, y `0016_loans_aval` ya lo usa el Perfil 3 (rama `feat/loans-aval`, 2026-11-10).
- **Upgrade:** lee el valor vigente de `horario.apertura` y `horario.cierre` (no el de la semilla: respeta lo que el Superadministrador haya cambiado) e inserta las seis claves de §4.1 con versión 1. Marca las dos globales con `editable = false` y antepone a su descripción "Obsoleta (SPEC-09): usar el horario de cada sede." Usa SQL con parámetros, como `0005`, y no importa código de la aplicación.
- **Downgrade:** borra las seis claves (su historial se borra por `ON DELETE CASCADE`) y devuelve las globales a `editable = true` con su descripción original.
- `config/seed.py` suma las seis claves a `PARAMETROS_SEMILLA`, con los valores iniciales de la semilla (`09:00`, `16:00` y `""`), para que la base de tests las tenga. La copia congelada de `0005` no cambia; `test_semilla.py` pasa a comparar `PARAMETROS_SEMILLA` con la unión de las copias de `0005` y `0017` (el detalle va en el plan).

### 4.3 Reglas

| ID | Regla |
| --- | --- |
| RN-78 | **Claves por sede.** El horario y el correo de una sede se leen de `horario.<segmento>.apertura`, `horario.<segmento>.cierre` y `contacto.<segmento>.email`, con el segmento de §4.1. El mapa `SedeEnum → segmento` vive en `config/service.py` y cubre todos los valores de `SedeEnum` (AC-109) |
| RN-79 | **Apertura antes del cierre, en cada sede.** `_REGLAS_CRUZADAS` suma un par por sede (`horario.<segmento>.apertura < horario.<segmento>.cierre` → `422 PARAMETROS_INCONSISTENTES`). Cambiar el horario de una sede no valida ni toca el de la otra. **Serialización (G-5):** `actualizar` deja de bloquear sólo la fila editada y bloquea, en **una** consulta `SELECT … WHERE clave IN (…) ORDER BY clave FOR UPDATE`, la clave editada junto con todas las claves de sus reglas cruzadas, antes de cualquier otra lectura. Así dos ediciones del mismo par se esperan, y la segunda se valida contra el valor que confirmó la primera. El orden por clave evita el *deadlock* que aparecería si cada sesión bloqueara primero su propia fila y después la del par. Vale para todos los pares de `_REGLAS_CRUZADAS`, no sólo para los nuevos (EC-53) |
| RN-80 | **Correo de contacto.** Es un `TEXTO` que, además, tiene que ser una dirección de correo válida (misma validación que `EmailStr`, hasta 254 caracteres); si no, `422 VALOR_PARAMETRO_INVALIDO`. Se guarda sin espacios y en minúsculas. El valor `""` sólo existe como valor inicial ("sin configurar") y sólo lo escribe la migración: por la API no se puede volver a dejar vacío, porque la validación vigente de `TEXTO` ya exige de 1 a 300 caracteres (D-05, D-06). La validación se asocia a las claves `contacto.*.email`, sin un tipo nuevo de parámetro |
| RN-81 | **Claves globales obsoletas.** `horario.apertura` y `horario.cierre` quedan con `editable = false` (un `PUT` responde `409 PARAMETRO_NO_EDITABLE`) y `obtener_parametro` las sigue devolviendo, para que `spaces`, `loans` y el portal funcionen igual hasta que cambien su lectura (H1…H3). Se borran en una migración posterior del Perfil 1, cuando `grep` sobre `develop` no encuentre lectores (D-02) |
| RN-82 | **Lectura pública** (§4.4): `datos_de_sede` y `datos_de_sedes` hacen una sola consulta, no hacen `commit` ni `flush`, devuelven `correo_contacto = None` si el valor es `""`, y responden `500 PARAMETRO_NO_CONFIGURADO` si falta alguna clave (como `obtener_parametro`: indica una migración faltante) |
| RN-83 | **Lectura por la API** (§4.5): cualquier usuario autenticado lee el horario y el correo de las dos sedes. No son datos personales (P6.4) y el estudiante necesita el correo de su sede para el aviso de anticipación |
| RN-84 | **Vigencia.** Un cambio de horario rige para las solicitudes y validaciones nuevas; no modifica reservas ni préstamos ya aprobados (RN-21 de SPEC-01) |
| RN-85 | **Quién edita.** Sólo el `SUPERADMIN`, como el resto del panel (D-05 de SPEC-01, D-08). Cada cambio queda en el historial del parámetro, con motivo opcional (RN-22 de SPEC-01) |

### 4.4 API pública de `config` (para `spaces` y `loans`)

```python
# app/modules/config/service.py — sección "API pública para otros módulos"

@dataclass(frozen=True, slots=True)
class DatosSede:
    sede: SedeEnum
    horario_apertura: time
    horario_cierre: time
    correo_contacto: str | None        # None mientras la clave valga "" (RN-80)

async def datos_de_sede(db: AsyncSession, sede: SedeEnum) -> DatosSede: ...
async def datos_de_sedes(db: AsyncSession) -> dict[SedeEnum, DatosSede]: ...
```

Uso esperado (informativo; lo implementa cada perfil dueño, §11):

- `spaces`: `horario(db)` pasa a `datos_de_sede(db, espacio.sede)` en la validación de franja y en la disponibilidad, que ya informa `horario_apertura` y `horario_cierre` (sin cambio de contrato para su frontend).
- `loans`: el alta de orden usa la sede del solicitante (RN-L04 ya lo pide), el ajuste horario usa la sede de la orden y `GET /loans/reglas` la sede del actor, o la de `?sede=` para el `SUPERADMIN` (T1.13 de SPEC-05).
- El aviso de anticipación mínima puede sumar `correo_contacto` al cuerpo del `422 ANTICIPACION_INSUFICIENTE` (`AppError` admite campos extra) o tomarlo el frontend de `GET /config/sedes`. Lo decide cada perfil.

### 4.5 Endpoint

| Método y ruta | Rol | Respuesta |
| --- | --- | --- |
| `GET /api/v1/config/sedes` | Cualquier usuario autenticado (`get_current_user`) | `200 list[DatosSedeResponse]`, una entrada por sede en el orden de `SedeEnum` · `401` sin sesión |

```python
class DatosSedeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sede: SedeEnum = Field(..., examples=["Río Grande"])
    horario_apertura: time = Field(..., examples=["10:00:00"])
    horario_cierre: time = Field(..., examples=["17:00:00"])
    correo_contacto: str | None = Field(default=None, examples=["laboratorio@example.com"])
```

El endpoint existe para que el portal y los formularios no dependan de los nombres de las claves (D-07). Los demás endpoints de `config` no cambian: las claves nuevas aparecen en `GET /parametros` y se editan con `PUT /parametros/{clave}`.

### 4.6 Transición

Mientras los Perfiles 3, 4 y 5 no cambien su lectura (H1…H3), las reservas, los préstamos y el portal siguen usando el horario global, que queda fijo en el valor que tenía al migrar. Un cambio en el horario de una sede **no tiene efecto** en esos módulos hasta entonces (EC-51). Por eso la Fase A se coordina antes de mergearla, y el panel lo aclara en la descripción de las claves nuevas hasta que se borren las obsoletas.

### 4.7 Frontend (`features/config`)

- `ParametersPage` no cambia de estructura: lista las claves nuevas y deshabilita las obsoletas porque ya respeta `editable`.
- Las claves `contacto.*.email` se editan con un campo `type="email"` y validación en línea; si el valor es `""`, se muestra "Sin configurar".
- `configApi.ts` suma `obtenerDatosSedes()` (`GET /config/sedes`) con su DTO espejo, para que lo usen el portal y los formularios de otros perfiles.

---

## 5. Fase B — Teléfono obligatorio

### 5.1 Contrato

| Esquema o comando | Antes | Después |
| --- | --- | --- |
| `RegistroRequest` (registro y re-registro, UC-01) y `UsuarioAdminCreate` (alta administrativa) | `telefono: Telefono \| None = None` | `telefono: Telefono` (obligatorio). Si falta o es `null` → `422` de validación |
| `PerfilUpdate` (`PATCH /auth/me`) | `telefono` opcional; `null` lo borra | Opcional; si se manda, no puede ser `null` → `422` "El teléfono no puede quedar vacío." |
| `UsuarioAdminUpdate` (`PATCH /users/{id}`) | Igual que `PerfilUpdate` | Igual que `PerfilUpdate` |
| `UsuarioPublico`, `UsuarioDetalle` | `telefono: str \| None` | Sin cambios: las cuentas viejas pueden no tenerlo (RN-87) |
| CLI `crear-superadmin` | `--telefono` opcional | `--telefono` obligatorio (D-11) |

El formato no cambia (`^\+?[0-9 \-]{6,20}$`). Sin migración: la columna sigue igual.

### 5.2 Reglas

| ID | Regla |
| --- | --- |
| RN-86 | **Toda cuenta nueva tiene teléfono**: registro, re-registro después de un rechazo (UC-01 FA-03, que reemplaza el teléfono anterior), alta administrativa y CLI (USR-05) |
| RN-87 | **La columna sigue admitiendo nulos** (D-16 de SPEC-03). Una cuenta sin teléfono inicia sesión, opera y se puede aprobar, suspender o editar en otros campos sin error. La migración a `NOT NULL` se hace cuando no queden nulos |
| RN-88 | **El teléfono no se borra.** Se puede reemplazar por otro válido (queda en el historial de la cuenta, como hoy), pero ni el usuario ni un administrador lo pueden dejar vacío |
| RN-89 | **Visibilidad sin cambios** (P6.4): el teléfono lo ven el titular y los administradores con jurisdicción, como hoy. `datos_publicos_por_ids` sigue sin incluirlo |

### 5.3 Frontend (`features/auth`, `features/users`, `layout`)

- Registro y alta en Gestión de usuarios: "Teléfono" obligatorio, con la misma validación en línea que hoy.
- Mi perfil y edición administrativa: no se puede guardar el campo vacío.
- Si la sesión es de una cuenta sin teléfono (`usuario.telefono === null`), el layout muestra un aviso **que no bloquea**: "Completá tu teléfono en Mi perfil", con enlace. Desaparece al guardarlo.

---

## 6. Códigos de error

Sin códigos nuevos. Se reutilizan los de SPEC-01: `VALOR_PARAMETRO_INVALIDO` (`422`), `PARAMETROS_INCONSISTENTES` (`422`), `PARAMETRO_NO_EDITABLE` (`409`), `PARAMETRO_NO_CONFIGURADO` (`500`) y los `422` de validación de FastAPI para el teléfono.

---

## 7. Criterios de aceptación

Cada criterio de backend tiene al menos un test anotado `# AC-NN`, con `pytestmark = pytest.mark.integracion` y PostgreSQL real (P9).

### 7.1 Fase A — `tests/config/test_sedes.py` y `tests/config/test_migracion_0017.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-102 | Después de `0017` existen las seis claves de §4.1. Si antes de migrar `horario.apertura` valía `08:30`, las dos aperturas por sede valen `08:30`; los correos valen `""` | §4.2, D-03 |
| AC-103 | `horario.apertura` y `horario.cierre` quedan con `editable = false`: un `PUT` del `SUPERADMIN` → `409 PARAMETRO_NO_EDITABLE`, y `obtener_parametro` sigue devolviendo su valor | RN-81 |
| AC-104 | El `SUPERADMIN` pone Río Grande en `10:00`–`17:00` → `200`, una entrada de historial por clave, y Ushuaia sigue en su horario | RN-78, RN-85 |
| AC-105 | Apertura igual o posterior al cierre en una sede → `422 PARAMETROS_INCONSISTENTES`; el mismo valor es válido en la otra sede si su cierre es posterior | RN-79 |
| AC-106 | Dos sesiones cambian a la vez la apertura y el cierre de la misma sede de forma que cada cambio solo es válido pero juntos invierten el horario (por ejemplo, con `09:00`–`16:00`, una pone la apertura en `15:00` y la otra el cierre en `14:00`): una responde `200` y la otra `422 PARAMETROS_INCONSISTENTES`, sin `500` ni *deadlock*, y el par queda válido (sesiones independientes, ADR-013) | RN-79, EC-53 |
| AC-107 | `contacto.rio_grande.email`: `"no-es-un-correo"` → `422 VALOR_PARAMETRO_INVALIDO`; `" Lab.RG@Example.com "` → `200` y se guarda `lab.rg@example.com`; después, `""` → `422` | RN-80 |
| AC-108 | `datos_de_sede` y `datos_de_sedes` devuelven `time` y `str \| None` (`None` con `""`), ejecutan **una** consulta (contada con `before_cursor_execute`), no confirman la transacción del llamador, y sin una de las claves → `500 PARAMETRO_NO_CONFIGURADO` | RN-82 |
| AC-109 | Todo valor de `SedeEnum` tiene segmento y sus tres claves existen en `PARAMETROS_SEMILLA` | RN-78 |
| AC-110 | `GET /api/v1/config/sedes` con cada rol → `200` con Ushuaia y Río Grande, en ese orden, y sólo los campos de `DatosSedeResponse`; sin token → `401` | RN-83 |
| AC-111 | Un `ADMIN_LOCAL` que edita una clave de su sede → `403` | RN-85 |
| AC-112 | Migración `0017`: upgrade → downgrade → upgrade; el downgrade borra las seis claves y su historial, y devuelve las globales a editables con su descripción original | §4.2, P7.4 |

### 7.2 Fase B — `tests/users/test_telefono.py`

| ID | Criterio | Regla |
| --- | --- | --- |
| AC-113 | Registro sin teléfono o con `null` → `422`; con un teléfono válido → `201` y queda guardado | RN-86 |
| AC-114 | Re-registro de una cuenta `RECHAZADO` sin teléfono → `422`; con teléfono → vuelve a `PENDIENTE_APROBACION` con el teléfono nuevo | RN-86 |
| AC-115 | Alta administrativa (`POST /users`) sin teléfono → `422` | RN-86 |
| AC-116 | `PATCH /auth/me` con `{"telefono": null}` → `422`; con otro teléfono válido → `200` y el cambio queda en el historial | RN-88 |
| AC-117 | `PATCH /users/{id}` con `{"telefono": null}` → `422` | RN-88 |
| AC-118 | Una cuenta sin teléfono (cargada directo en la base) inicia sesión, `GET /auth/me` devuelve `telefono: null`, cambia su email y un administrador la aprueba y la suspende sin error | RN-87 |
| AC-119 | `crear-superadmin` sin `--telefono` termina con error de argumentos y no crea la cuenta | RN-86, D-11 |

### 7.3 Frontend (`npm run typecheck`, `npm run build`, Vitest y verificación manual)

| ID | Criterio |
| --- | --- |
| AC-120 | El panel de parámetros muestra las claves por sede, edita el correo con un campo de email ("Sin configurar" si está vacío) y muestra las globales obsoletas sin edición |
| AC-121 | Registro y alta administrativa exigen el teléfono; Mi perfil y la edición administrativa no permiten vaciarlo; una cuenta sin teléfono ve el aviso con enlace a Mi perfil, que desaparece al guardarlo |
| AC-122 | `npm run typecheck`, `npm run build` y Vitest en verde, con tests de `obtenerDatosSedes` y de la validación del teléfono |

---

## 8. Casos de borde

| ID | Escenario | Resultado |
| --- | --- | --- |
| EC-51 | El `SUPERADMIN` cambia el horario de Río Grande antes de que `spaces` y `loans` lean el de la sede | No tiene efecto en reservas ni préstamos hasta H1 y H2: siguen con el global (RN-81, §4.6) |
| EC-52 | Se acorta el horario de una sede con reservas o préstamos aprobados fuera del nuevo horario | Siguen como están; el horario nuevo rige para lo nuevo (RN-84). Mover o cancelar lo afectado es una decisión del administrador en cada módulo |
| EC-53 | Dos `SUPERADMIN` editan a la vez la apertura y el cierre de la misma sede | El bloqueo de las dos filas del par, en orden de clave y en una sola consulta, serializa la validación sin *deadlock* (RN-79, AC-106) |
| EC-54 | Se agrega una sede a `SedeEnum` | AC-109 falla hasta que una migración agregue su segmento y sus claves |
| EC-55 | Aviso de anticipación con el correo de la sede todavía sin configurar | `correo_contacto` es `None`; el módulo que avisa muestra el mensaje sin correo |
| EC-56 | El usuario de una sede pregunta por el correo de la otra | `GET /config/sedes` devuelve las dos: no es un dato de una sede ajena que haya que aislar (RN-83) |
| EC-57 | Un `SUPERADMIN` (sin sede) pide `GET /loans/reglas` | Ya lo define SPEC-05 (T1.13, AC-L63): `?sede=` para el `SUPERADMIN` y `sede` en `ReglasResponse`. `config` sólo provee `datos_de_sede` (H2) |
| EC-58 | Una cuenta sin teléfono es rechazada y se vuelve a registrar | El re-registro exige el teléfono (AC-114) |
| EC-59 | Un administrador edita el nombre de una cuenta vieja sin teléfono | `200`: sólo se valida el teléfono si viene en el cuerpo (RN-87) |

---

## 9. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| NFR-23 | Cobertura ≥ 85 % del código nuevo de `config` y `users`. Todos los AC de backend automatizados contra PostgreSQL |
| NFR-24 | `datos_de_sedes` hace una sola consulta por primary key sobre seis filas |
| NFR-25 | Sin dependencias nuevas: la validación del correo usa `email-validator`, que ya está en `requirements.txt` |

---

## 10. Decisiones

> **Resueltas el 2026-11-11:** el Perfil 1 adoptó todas las recomendaciones (columna "Decisión").

| ID | Pregunta | Opciones | Decisión |
| --- | --- | --- | --- |
| D-01 | ¿Cómo se guarda un parámetro por sede? | (a) Una clave por sede con el segmento de §4.1, sin cambiar el esquema de `parametros_globales` · (b) Columna `sede` en `parametros_globales`, con clave primaria compuesta · (c) Un tipo nuevo `HORARIO` con un JSON que tenga las dos sedes | **(a)**. Mantiene el catálogo cerrado, el bloqueo optimista, el historial y el panel tal como están, y `obtener_parametro` no cambia de firma. (b) toca la clave primaria y la FK del historial, y obliga a cambiar `obtener_parametro` en todos los módulos. (c) mezcla dos sedes en una versión: editar una pisa la otra |
| D-02 | ¿Qué pasa con `horario.apertura` y `horario.cierre`? | (a) Quedan no editables y marcadas obsoletas; se borran cuando nadie las lea · (b) Se borran ya, y el Perfil 1 cambia la lectura en `spaces`, `loans` y el portal · (c) Quedan editables como horario "por defecto" | **(a)**. (b) modifica módulos de otros perfiles (Constitución §8.3). (c) deja dos horarios editables sin saber cuál rige. Con (a), nada se rompe al mergear y cada perfil cambia una línea cuando puede |
| D-03 | ¿Con qué valores arranca el horario de cada sede? | (a) El vigente de las claves globales, para las dos · (b) El ejemplo del ERS (Ushuaia 09:00–16:00, Río Grande 10:00–17:00) | **(a)**. El ERS lo da "por ejemplo" y la referente no lo fijó como valor; (a) no cambia nada hasta que el `SUPERADMIN` lo edite. Se le pregunta a la referente (§10.1). Dato del 2026-11-11: Ushuaia va a extender su horario y Río Grande lo mantiene, así que los horarios van a ser distintos; los valores se cargan en el panel cuando rijan, sin migración nueva |
| D-04 | ¿Un correo de contacto o uno por sede? | (a) Uno por sede · (b) Uno solo para el laboratorio | **(a)**. El aviso se muestra a un usuario de una sede, y la urgencia la resuelve el administrador de esa sede. Si el laboratorio tiene una sola dirección, se carga la misma en las dos. El ERS dice "el correo de contacto del laboratorio" sin aclarar, y cada sede tiene su laboratorio |
| D-05 | ¿Con qué valor arranca el correo? | (a) `""`, que se lee como "sin configurar", y el aviso sale sin correo hasta que el `SUPERADMIN` lo cargue · (b) La dirección real, que se le pide antes a la referente y se siembra en la migración · (c) Una dirección de ejemplo | **(a)**. No bloquea la Fase A esperando la respuesta y no muestra datos inventados. (c) podría quedar a la vista de los estudiantes. La dirección se le pide igual a la referente (§10.1) |
| D-06 | ¿Cómo se valida el correo? | (a) `TEXTO` con una validación extra para las claves `contacto.*.email` · (b) Un tipo nuevo `EMAIL` en `parametro_tipo_enum` | **(a)**. (b) necesita `ALTER TYPE … ADD VALUE` en PostgreSQL (no se revierte con un downgrade simple) y un caso más en el frontend, para dos claves |
| D-07 | ¿Hace falta `GET /config/sedes`? | (a) Sí · (b) No: cada frontend lee las claves con `GET /parametros/{clave}` | **(a)**. El portal, el aviso de anticipación y los calendarios necesitan los mismos datos; con (b) cada perfil depende de los nombres de las claves y hace seis pedidos |
| D-08 | ¿Quién edita los parámetros de una sede? | (a) Sólo el `SUPERADMIN` (D-05 de SPEC-01) · (b) También el `ADMIN_LOCAL` de esa sede | **(a)**. (b) necesita autorización por clave, que hoy no existe. Se revisa si la referente lo pide (§10.1) |
| D-09 | GLO-02 habla de "días y horarios" de cierre: ¿se configuran los días de atención? | (a) No en esta versión: los días de cierre se cargan como bloqueos (GLO-04) y se le pregunta a la referente · (b) Un parámetro de días de atención por sede | **(a)**. Hoy ningún módulo controla el día de la semana y `config` no tiene un tipo lista. Si la referente confirma que los laboratorios no abren algunos días, va en una versión siguiente |
| D-10 | ¿La delegación temporal del Superadministrador (ADR-022 g) entra en este spec? | (a) No: spec propio · (b) Sí, como Fase C | **(a)**. Cambia `require_roles`, `resolver_alcance_sede` y el `token_version`, necesita su propia revisión de seguridad y no destraba a nadie. Este spec tiene que salir rápido porque lo esperan tres perfiles |
| D-11 | ¿La CLI `crear-superadmin` exige el teléfono? | (a) Sí · (b) No: el Superadministrador inicial lo carga después en Mi perfil | **(a)**. Con (a) ninguna cuenta nueva queda sin teléfono, y la migración a `NOT NULL` (RN-87) sólo depende de las cuentas viejas |
| D-12 | ¿Cómo se entrega? | (a) Fase A y Fase B en PRs separados, la A primero · (b) Todo junto | **(a)**. La A destraba a tres perfiles; la B no depende de nada y no tiene migración |

### 10.1 Preguntas para la referente

1. ¿Cuál es el horario de atención real de cada laboratorio (Ushuaia y Río Grande)? (D-03). **Respuesta parcial (2026-11-11):** Ushuaia va a extender su horario y Río Grande lo mantiene; faltan las horas exactas y desde cuándo rige el de Ushuaia
2. ¿Qué dirección de correo se muestra para cada sede cuando una solicitud no cumple la anticipación mínima? ¿Es una sola para el laboratorio? (D-04, D-05)
3. ¿Hay días de la semana en que algún laboratorio no abre (por ejemplo, sábados)? (D-09)
4. ¿Los Administradores Locales tienen que poder cambiar el horario de su sede, o sólo la Superadministradora? (D-08)

---

## 11. Coordinación con otros perfiles (se registra en `MEMORY.md` §5 al aprobar)

| ID | Para | Pedido | Origen |
| --- | --- | --- | --- |
| H1 | Perfil 4 (ya adoptado en la Fase 2 de SPEC-08, T2.1…T2.3) | Cambiar `spaces/service.horario(db)` por `datos_de_sede(db, espacio.sede)` en la validación de franja y en la disponibilidad. En el aviso de anticipación mínima (CU de reserva, FA-02), mostrar el correo de la sede: sumándolo al `422 ANTICIPACION_INSUFICIENTE` o desde `GET /config/sedes` en el frontend. Avisar cuando esté en `develop`, para borrar las claves globales | K10 de SPEC-03, pedido (b) del 2026-11-02 |
| H2 | Perfil 3 | Cambiar las tres lecturas de `horario.apertura` y `horario.cierre` de `loans/service.py` (alta de orden con la sede del solicitante, ajuste horario con la sede de la orden y `GET /loans/reglas`) por `datos_de_sede`; es la T1.13 de SPEC-05, que ya define `?sede=` para el `SUPERADMIN` (EC-57). Opcional: el correo en el `422 ANTICIPACION_INSUFICIENTE`. **C1:** las demás claves de `config` alcanzan, no hacen falta claves nuevas. **C19:** la parte del horario se resuelve con este spec | C1 y C19 de SPEC-05, RN-L04 |
| H3 | Perfil 5 | El portal pasa de leer `horario.apertura` y `horario.cierre` a `GET /config/sedes` (con `obtenerDatosSedes()` de `features/config`), y muestra el horario de cada sede en lugar de "en ambas sedes" | C-N05 de SPEC-06, RN-N1 |
| H4 | Equipo | Hacer las preguntas de §10.1 a la referente | D-03, D-04, D-05, D-08, D-09 |

Se responde también la pregunta (a) que el Perfil 2 hizo al Perfil 1 el 2026-10-23 sobre la ventana del calendario: ya la había retirado SPEC-04 v1.2.0 (D-07 de ese spec), así que este spec no agrega esa clave.

---

## 12. Trazabilidad

| Requisito | Función o endpoint | Criterios | Bordes | Fase |
| --- | --- | --- | --- | --- |
| GLO-03 (horario de cada sede), ADR-022 a | Claves `horario.<segmento>.*`, migración `0017`, `PUT /config/parametros/{clave}` | AC-102…AC-106, AC-111, AC-112, AC-120 | EC-51…EC-54 | A |
| GLO-03 (correo de contacto), ADR-022 c | Claves `contacto.<segmento>.email` | AC-102, AC-107, AC-120 | EC-55 | A |
| GLO-02 (dato del horario por sede; el bloqueo lo aplican `spaces` y `loans`) | `config.service.datos_de_sede`, `datos_de_sedes`, `GET /config/sedes` | AC-108…AC-110 | EC-56, EC-57 | A |
| USR-05 (teléfono obligatorio), ADR-022 b, D-16 de SPEC-03 | `POST /auth/register`, `POST /users`, `PATCH /auth/me`, `PATCH /users/{id}`, CLI `crear-superadmin`; registro, Gestión de usuarios, Mi perfil y aviso | AC-113…AC-119, AC-121 | EC-58, EC-59 | B |
| Frontend completo | `npm run typecheck`, `npm run build`, Vitest | AC-122 | — | A y B |

---

## 13. Historial de cambios

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 1.0.0 | 2026-11-11 | Perfil 1 | **Aprobado**, con las recomendaciones de §10 (D-01…D-12). Suma la respuesta parcial a la pregunta 1 de §10.1: Ushuaia extiende su horario y Río Grande lo mantiene, lo que confirma la necesidad de horarios distintos por sede (G-1). Plan y tareas en `plan.md` y `tasks.md` |
| 0.2.0 | 2026-11-11 | Perfil 1 (con asistencia de IA) | Revisión antes de aprobar, sin cambiar las decisiones. **RN-79 corregida:** bloquear "las dos filas en orden alfabético" después de que `actualizar` ya bloqueó la editada podía terminar en *deadlock*; ahora se bloquean la editada y su par en una sola consulta ordenada por clave, para todos los pares de `_REGLAS_CRUZADAS` (G-5 nueva; AC-106 y EC-53 más precisos). RN-80 aclara que el `""` sólo lo escribe la migración. Alineado con SPEC-08 v1.0.0 (H1 ya adoptado en su Fase 2) y con la T1.13 de SPEC-05 (EC-57, H2). §2.1 verificado de nuevo sobre `develop` |
| 0.1.0 | 2026-11-11 | Perfil 1 (con asistencia de IA) | Borrador inicial. Se redactó como SPEC-08 y pasó a ser el 09 porque el 08 es del Perfil 4 (`spaces`); la migración pasa a `0017_config_sedes` porque `0016` la usa `loans`. Fase A (horario y correo de contacto por sede, ADR-022 a y c) y Fase B (teléfono obligatorio, ADR-022 b, D-16 de SPEC-03). Decisiones D-01…D-12 con recomendación, preguntas para la referente (§10.1) y coordinación H1…H4 |
