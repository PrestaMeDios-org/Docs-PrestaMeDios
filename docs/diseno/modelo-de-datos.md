# Modelo de datos

> **Estado:** refleja los modelos de `Backend-PrestaMeDios` en `develop` (migraciones `0001`…`0014`) al 2026-11-09. Las tablas de un PR abierto se marcan como *en revisión*.
> **Diseño original:** [historico/der-v1.webp](historico/der-v1.webp) (Figura 2 del ERS). Era un DER conceptual (Chen); acá se documenta el modelo físico que existe en PostgreSQL.
> **Fuente de verdad:** `app/modules/<modulo>/models.py` y `alembic/versions/`. Si este documento y el código difieren, manda el código: corregir el documento.

## Vista general

Sólo entidades y relaciones. El detalle de columnas está en los diagramas por dominio.

```mermaid
erDiagram
    usuarios ||--o{ usuarios_historial_estado : "cambia de estado"
    usuarios ||--o{ usuarios_historial_cambios : "edita perfil"
    usuarios ||--o{ archivos : "sube"
    archivos ||--|| archivos_contenido : "bytes"
    usuarios |o--o| archivos : "foto vigente"
    parametros_globales ||--o{ parametros_globales_historial : "versiona"

    categorias ||--o{ equipamientos : "agrupa"
    equipamientos ||--o{ unidades_fisicas : "tiene stock"
    usuarios ||--o{ ordenes_pedido : "solicita"
    ordenes_pedido ||--|{ detalles_prestamo : "contiene"
    equipamientos ||--o{ detalles_prestamo : "se pide"
    unidades_fisicas |o--o{ detalles_prestamo : "se asigna"
    ordenes_pedido ||--o{ ordenes_historial_estado : "cambia de estado"

    espacios ||--o{ reservas_espacios : "se reserva"
    usuarios ||--o{ reservas_espacios : "reserva"
    espacios ||--o{ bloqueos_espacios : "se bloquea"

    usuarios |o--o{ comunicados : "publica"
    usuarios ||--o{ notificaciones : "recibe"
```

**Sede** no es una tabla: es el tipo `sede_enum` (`Ushuaia`, `Río Grande`), compartido por `usuarios`, `unidades_fisicas`, `ordenes_pedido`, `espacios`, `archivos` y `comunicados`. "Ambas sedes" se representa con `sede = NULL` y es exclusivo del `SUPERADMIN` (GLO-01).

## Identidad, archivos y configuración (Perfil 1)

```mermaid
erDiagram
    usuarios {
        int id PK
        varchar email UK "minúsculas"
        varchar password_hash "Argon2"
        varchar nombre
        varchar apellido
        varchar dni UK "7-8 dígitos"
        varchar telefono "nullable"
        rol_usuario_enum rol "SUPERADMIN, ADMIN_LOCAL, DOCENTE, ESTUDIANTE"
        sede_enum sede "NULL sólo si SUPERADMIN"
        estado_cuenta_enum estado "PENDIENTE_APROBACION por defecto"
        varchar motivo_estado
        timestamptz suspendido_hasta
        int token_version "revoca JWT"
        bool debe_cambiar_password
        timestamptz ultimo_login_en
        int aprobado_por_id FK
        timestamptz aprobado_en
        uuid foto_id FK
        timestamptz created_at
        timestamptz updated_at
    }
    usuarios_historial_estado {
        bigint id PK
        int usuario_id FK
        estado_cuenta_enum estado_anterior
        estado_cuenta_enum estado_nuevo
        varchar motivo
        int actor_id FK
        timestamptz created_at
    }
    usuarios_historial_cambios {
        bigint id PK
        int usuario_id FK
        int actor_id FK
        jsonb cambios "campo: antes, después"
        timestamptz created_at
    }
    archivos {
        uuid id PK
        int propietario_id FK
        proposito_archivo_enum proposito "FOTO_PERFIL, AVAL_PRESTAMO"
        sede_enum sede
        varchar tipo_mime
        int tamano_bytes
        char sha256
        varchar nombre_original
        timestamptz vinculado_en "NULL = huérfano"
        timestamptz created_at
    }
    archivos_contenido {
        uuid archivo_id PK, FK
        bytea datos
    }
    parametros_globales {
        varchar clave PK "ej. prestamo.general.max_dias"
        parametro_tipo_enum tipo
        jsonb valor
        varchar descripcion
        varchar unidad
        numeric valor_min
        numeric valor_max
        bool editable
        int version
        int actualizado_por_id FK
        timestamptz actualizado_en
    }
    parametros_globales_historial {
        bigint id PK
        varchar clave FK
        jsonb valor_anterior
        jsonb valor_nuevo
        int version
        varchar motivo
        int actor_id FK
        timestamptz created_at
    }
    tokens_recuperacion {
        bigint id PK
        int usuario_id FK
        char token_hash UK "SHA-256"
        timestamptz expira_en
        timestamptz usado_en
        timestamptz created_at
    }
    intentos_recuperacion {
        bigint id PK
        char email_hash "HMAC, sin FK"
        varchar ip
        timestamptz created_at
    }

    usuarios ||--o{ usuarios_historial_estado : ""
    usuarios ||--o{ usuarios_historial_cambios : ""
    usuarios |o--o{ usuarios : "aprobado_por"
    usuarios ||--o{ archivos : "propietario"
    usuarios |o--o| archivos : "foto_id"
    archivos ||--|| archivos_contenido : ""
    parametros_globales ||--o{ parametros_globales_historial : ""
    usuarios |o--o{ parametros_globales : "actualizado_por"
    usuarios ||--o{ tokens_recuperacion : ""
```

`tokens_recuperacion` e `intentos_recuperacion` (USR-02, migración `0015`) están **en revisión** (backend PR \#27).

## Catálogo, existencias y préstamos (Perfiles 2 y 3)

```mermaid
erDiagram
    categorias {
        varchar id PK "slug, ej. cameras"
        varchar nombre UK
        varchar color "hex"
    }
    equipamientos {
        int id PK
        varchar codigo UK
        varchar nombre
        varchar marca
        varchar modelo
        varchar categoria_id FK
        varchar descripcion
        int max_dias_prestamo "1 a 15"
        bool alta_gama "exige aval PDF"
        bool es_notebook
        bool activo "baja lógica"
        varchar imagen_url
        varchar video_url
        varchar_array reglas_cuidado
    }
    unidades_fisicas {
        int id PK
        int equipamiento_id FK
        varchar numero_serie UK
        varchar codigo_inventario UK
        sede_enum sede
        int locker "1 a 7"
        estado_unidad_enum estado "disponible, prestado, mantenimiento, baja"
    }
    ordenes_pedido {
        int id PK
        int solicitante_id FK
        sede_enum sede "de la sesión"
        int asignatura_id "sin FK, módulo pendiente"
        estado_orden_enum estado "pendiente, aprobada, rechazada, cancelada"
        timestamptz fecha_solicitud
        varchar observacion_docente
        varchar motivo_resolucion
        bool es_renovado
        int resuelto_por_id FK
        timestamptz resuelto_en
    }
    detalles_prestamo {
        int id PK
        int orden_id FK
        int equipamiento_id FK
        int unidad_fisica_id FK "se asigna al aprobar"
        estado_detalle_enum estado "pendiente, reservado, entregado, devuelto, ..."
        timestamptz retiro_pactado
        timestamptz devolucion_pactada
        timestamptz fin_ocupacion "se extiende si hay demora"
        tstzrange periodo "generada"
    }
    ordenes_historial_estado {
        bigint id PK
        int orden_id FK
        estado_orden_enum estado_anterior
        estado_orden_enum estado_nuevo
        varchar motivo
        int actor_id FK
        timestamptz created_at
    }

    categorias ||--o{ equipamientos : ""
    equipamientos ||--o{ unidades_fisicas : ""
    usuarios ||--o{ ordenes_pedido : "solicitante"
    ordenes_pedido ||--|{ detalles_prestamo : ""
    equipamientos ||--o{ detalles_prestamo : ""
    unidades_fisicas |o--o{ detalles_prestamo : ""
    ordenes_pedido ||--o{ ordenes_historial_estado : ""
```

Estados de una línea de préstamo: `pendiente`, `reservado`, `entregado`, `devuelto`, `rechazado`, `no_retirado`, `cancelado`. Sólo `reservado` y `entregado` ocupan la unidad. "Demorado" y "en curso / finalizada" no se guardan: se calculan al responder.

## Espacios y comunicaciones (Perfiles 4 y 5)

```mermaid
erDiagram
    espacios {
        int id_espacio PK
        varchar nombre "Aula-Estudio, Isla de Edición"
        sede_enum sede
        varchar tipo
    }
    reservas_espacios {
        int id_reserva PK
        int id_usuario FK
        int id_espacio FK
        date fecha_reserva
        time hora_inicio
        time hora_fin
        varchar estado_reserva "Pendiente, Aprobada, Rechazada, Cancelada, En_Uso, Finalizada"
        text motivo
        timestamptz created_at
    }
    bloqueos_espacios {
        int id_bloqueo PK
        int id_espacio FK
        date fecha_inicio
        date fecha_fin
        time hora_inicio "nullable: día completo"
        time hora_fin
        text motivo
        timestamptz created_at
    }
    comunicados {
        int id PK
        varchar titulo
        text contenido "hasta 5000"
        sede_enum sede "NULL si es global"
        bool es_global
        estado_comunicado_enum estado "PUBLICADO, ARCHIVADO"
        int autor_id FK
        timestamptz publicado_en
        timestamptz vence_en
        timestamptz actualizado_en
    }
    notificaciones {
        bigint id PK
        int usuario_id FK
        varchar tipo "ORDEN_APROBADA, RESERVA_RECHAZADA, ..."
        severidad_notificacion_enum severidad "NORMAL, CRITICA"
        varchar titulo
        varchar mensaje
        varchar referencia_modulo
        bigint referencia_id
        timestamptz creada_en
        timestamptz leida_en "NULL = no leída"
    }

    espacios ||--o{ reservas_espacios : ""
    usuarios ||--o{ reservas_espacios : ""
    espacios ||--o{ bloqueos_espacios : ""
    usuarios |o--o{ comunicados : "autor"
    usuarios ||--o{ notificaciones : "destinatario"
```

`notificaciones` ya tiene tabla (migración `0013`), pero sus endpoints y la campanita son la Fase B de SPEC-06, sin implementar.

## Invariantes garantizadas por PostgreSQL

| Tabla | Restricción | Qué impide |
| --- | --- | --- |
| `detalles_prestamo` | `EXCLUDE USING gist (unidad_fisica_id =, periodo &&)` sobre líneas `reservado` o `entregado` | Prestar la misma unidad dos veces en períodos que se pisan (PRE-17) |
| `reservas_espacios` | `EXCLUDE USING gist (id_espacio =, tsrange &&)` sobre reservas `Aprobada` o `En_Uso` | Dos reservas activas del mismo espacio en la misma franja (RES-02) |
| `usuarios` | `CHECK sede_segun_rol` | Un `SUPERADMIN` con sede o un no-superadmin sin sede (GLO-01) |
| `usuarios` | `CHECK dni_numerico`, `email_minusculas`, `suspension_coherente` | Datos de cuenta inconsistentes |
| `comunicados` | `CHECK alcance_coherente` | Un comunicado global con sede o uno local sin sede |
| `equipamientos` / `unidades_fisicas` | `CHECK max_dias_prestamo 1..15`, `locker 1..7` | Valores fuera del rango del laboratorio |
| `parametros_globales` | `CHECK clave_formato`, `rango_coherente` | Claves mal formadas o rangos invertidos (GLO-03) |

Las dos `EXCLUDE` requieren la extensión `btree_gist`.

## Del DER original al modelo actual

| DER v1 | Modelo actual | Cambio |
| --- | --- | --- |
| `usuario` con subtipos `estudiante`, `docente`, `administrador` | `usuarios.rol` | Una sola tabla con rol enumerado. Se suma la distinción `SUPERADMIN` / `ADMIN_LOCAL`; el rol "Administrador ICSE" se eliminó (ADR-001) |
| `sede` (entidad) y relación `pertenece_a` | `sede_enum` en cada tabla | Sin tabla: dos valores fijos. "Ambas" = `NULL`, sólo para el `SUPERADMIN` |
| `usuario.datos_contacto`, `foto`, `estado_cuenta` | `email`, `telefono`, `foto_id` → `archivos`, `estado` + `motivo_estado` + `suspendido_hasta` | Se suman `dni`, `token_version`, `debe_cambiar_password` y dos historiales inmutables (USR-08) |
| `modelo_equipamiento` | `equipamientos` | `tipo_gama` → `alta_gama` (bool); `estado_catálogo` → `activo`; `recursos_ayuda` → `imagen_url` y `video_url`. Se suman `codigo`, `marca`, `modelo`, `es_notebook`, `max_dias_prestamo` y `reglas_cuidado`. `manual_pdf` no se implementó |
| `categoria` | `categorias` | Clave textual (slug) y `color` |
| `unidad_fisica` | `unidades_fisicas` | `codigo_interno` → `codigo_inventario` + `numero_serie`; `estado_fisico` → `estado`; se suma `sede`. `observacion_fisica` no se implementó |
| `orden_prestamo` | `ordenes_pedido` | Las fechas pasaron a cada línea. `pdf_validacion` → archivo `AVAL_PRESTAMO` en `archivos` (integración en curso). `demorado` es derivado. Se suman `sede`, `resuelto_por_id` y `resuelto_en` |
| `detalle_prestamo` | `detalles_prestamo` | Cada línea tiene estado propio, unidad asignada al aprobar y período con exclusión temporal |
| `asignatura`, relaciones `dicta` y `justifica` | `ordenes_pedido.asignatura_id` sin FK | **Pendiente:** no hay módulo de asignaturas; bloquea el panel docente (PRE-20) |
| `orden_reserva_espacio` | `reservas_espacios` | `franja_horaria` → `fecha_reserva` + `hora_inicio` / `hora_fin`. No guarda quién aprobó o rechazó |
| `Espacio_fisico` y relación `posee` | `espacios.sede` | |
| `bloqueo_espacio` | `bloqueos_espacios` | Admite día completo o franja horaria. No guarda qué administrador lo registró |
| `comunicado` | `comunicados` | Se suman `estado` (archivado) y `vence_en` |
| `notificacion` | `notificaciones` | `tipo_alerta` → `tipo` + `severidad`; `leida (b)` → `leida_en`; referencia al recurso de origen |
| `chip_comportamiento` | — | **Pendiente** (USR-09) |
| `nota_administrativa` | — | **Pendiente** (GLO-05) |
| — | `parametros_globales` (+ historial) | Nuevo: reglas operativas editables sin tocar código (GLO-03) |
| — | `archivos` / `archivos_contenido` | Nuevo: foto de perfil y aval PDF (SPEC-03 B2) |
| — | `ordenes_historial_estado` | Nuevo: traza de cada transición de una orden |
| — | `tokens_recuperacion` / `intentos_recuperacion` | Nuevo, en revisión: recuperación de contraseña (USR-02) |

## Cómo actualizar este documento

Cada migración nueva que cree o altere tablas debe venir con su cambio acá: el diagrama del dominio, la vista general si cambia una relación y la línea de **Estado**. Mermaid `erDiagram` no admite paréntesis en los tipos: usar `varchar`, `timestamptz`, etc., y poner los detalles en el comentario entre comillas.
