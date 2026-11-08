# PLAN-04 — Catálogo y existencias (`inventory`)

> **Spec:** `specs/04-inventory-catalogo-existencias/spec.md` v1.2.0 (Fase B `APROBADO`) · **Estado del plan:** v2.0.0 `APROBADO` · **Fecha:** 2026-11-07 · **Perfil:** 2
> **Base verificada:** `origin/develop` del backend (`3ffed99`, incluye `loans.ocupacion_de_unidades`, PR \#21) y del frontend (`0a5ff37`).
> Tareas: `specs/04-inventory-catalogo-existencias/tasks.md`. **No se escribe código hasta que el spec v1.2.0 esté `APROBADO`.**

---

## 1. Principios de ejecución

- Sólo se tocan archivos de `inventory` (backend y frontend). Puntos de integración ajenos: ninguno en la Fase B; el cableado de `onAddToCart` en `App.tsx` lo hace el Perfil 3 (§6).
- Orden API-First: esquemas → servicio → router → tests → frontend.
- Cada tarea termina con tests en verde (`pytest -q` con `TEST_DATABASE_URL`) o con `npm run typecheck && npm run build && npm test`.
- Python 3.12 (validado). Con 3.13 falla un test de `users` ajeno al Perfil 2 (DT-30); no bloquea, pero se anota en el PR.
- Sin commits, push ni merge sin pedido explícito. Ramas sugeridas desde `develop`: `feat/inventory-disponibilidad` (backend) y `feat/inventory-detalle` (frontend). La Fase C, en ramas propias cuando se desbloquee.

## 2. Dependencias nuevas

Ninguna, ni en backend ni en frontend. El mini-calendario se arma con `Date` nativo y estilos en línea, como el resto de `inventory`; no se reutiliza `spaces/CalendarGrid.tsx` (es del Perfil 4).

## 3. Fase A (ejecutada)

Ejecutada el 2026-10-23 según la v1.0.0 de este plan (ver historial y la versión anterior en Git). Desviaciones registradas: categoría filtrada en la pantalla; `0010` con SQL directo por DT-26; `UnidadFormModal` para alta y edición de unidades desde el stock; ramas creadas al cierre. Después se sumaron `datos_equipamiento_por_ids` (PR \#19), "No disponible" (frontend PR \#11) y el test de concurrencia (PR \#20).

## 4. Fase B — Backend

### 4.1 Archivos

| Archivo | Acción | Contenido | Spec |
| :---- | :---- | :---- | :---- |
| `app/modules/inventory/service.py` | Modificar | Docstring del módulo con la lista de la API pública; docstring de `bloquear_unidad` con el contrato de §6.2; nueva `marcar_unidad_mantenimiento` | §6.2, C14, C17 |
| `app/modules/inventory/disponibilidad.py` | **Crear** | `MAX_DIAS_DISPONIBILIDAD`, `inicio_del_dia`, `validar_rango`, `contar_libres_por_dia` (pura) y `disponibilidad_por_dia` (la única que importa `loans`) | §5.4, RN-I14…I16, D-07 |
| `app/modules/inventory/schemas.py` | Modificar | `DiaDisponibilidad`, `DisponibilidadResponse` | §5.4 |
| `app/modules/inventory/router.py` | Modificar | `GET /equipamiento/{id}/disponibilidad`; RN-I13 en `editar_equipamiento`; extraer `_plazo_por_defecto(db, es_notebook)` de `crear_equipamiento` para reutilizarlo | §5.3, §5.4 |
| `tests/inventory/test_disponibilidad.py` | **Crear** | INV-26, INV-30, INV-31 | §9.2 |
| `tests/inventory/test_disponibilidad_unit.py` | **Crear** | `contar_libres_por_dia` y `validar_rango` sin base (rápidos) | RN-I15, D-07 |
| `tests/inventory/test_service.py` | Modificar | INV-28 | §6.2 |
| `tests/inventory/test_gestion.py` | Modificar | INV-29; agregar la ruta nueva a `test_exige_sesion` (o al test equivalente de INV-01) | RN-I13 |
| `Backend-PrestaMeDios/README.md` | Modificar | Endpoint de disponibilidad y funciones públicas nuevas | DoD |

Sin migración ni cambios en `alembic/env.py` (§7 del spec).

### 4.2 `service.py` (C14, C17)

```python
async def marcar_unidad_mantenimiento(db: AsyncSession, unidad_id: int) -> UnidadFisica:
    """Devolución con daño (C17 de SPEC-05, PRE-14): la unidad pasa a ``mantenimiento``.

    API pública. Sin ``commit`` ni ``flush``; no valida sede (autoriza quien llama).
    Idempotente si ya está en ``mantenimiento``; desde ``prestado`` o ``baja`` → 409.
    """
    unidad = await bloquear_unidad(db, unidad_id)
    if unidad is None:
        raise unidad_no_encontrada()
    if unidad.estado is E.MANTENIMIENTO:
        return unidad
    validar_transicion_admin(unidad.estado, E.MANTENIMIENTO)
    unidad.estado = E.MANTENIMIENTO
    return unidad
```

`bloquear_unidad` no cambia de código: sólo se documenta como pública (leer `id`, `equipamiento_id`, `sede`, `estado`; no asignar; bloquear varias en orden ascendente de id).

### 4.3 `disponibilidad.py` (§5.4)

Módulo aparte para que `service.py` no importe `loans` (RN-I16: `loans/service.py` ya importa `inventory/service.py`). Esquema de referencia:

```python
"""Disponibilidad por fechas del catálogo (SPEC-04 §5.4, PRE-01).

Único punto de `inventory` que usa `loans` (RN-I16). `inventory/service.py` no debe
importar este módulo ni `loans`, porque `loans/service.py` importa `inventory/service.py`.
"""

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timedelta

from app.core.errors import AppError
from app.core.settings import ZONA_HORARIA_LAB
from app.modules.inventory.service import unidades_asignables
from app.modules.loans.service import PeriodoOcupado, ocupacion_de_unidades

# D-07: tope técnico de la consulta (no es una regla del reglamento, P8 no aplica).
MAX_DIAS_DISPONIBILIDAD = 62


def inicio_del_dia(fecha: date) -> datetime:
    return datetime.combine(fecha, time.min, tzinfo=ZONA_HORARIA_LAB)


def validar_rango(desde: date, hasta: date, hoy: date) -> None:
    """422 RANGO_FECHAS_INVALIDO con un detalle por regla (§5.4)."""
    if hasta < desde: ...           # "La fecha final no puede ser anterior a la inicial."
    if desde < hoy: ...             # "El rango no puede empezar antes de hoy."
    if (hasta - desde).days + 1 > MAX_DIAS_DISPONIBILIDAD: ...  # "Como máximo 62 días."


def contar_libres_por_dia(
    desde: date, hasta: date, ocupacion: Mapping[int, Sequence[PeriodoOcupado]]
) -> list[tuple[date, int]]:
    """RN-I15: libre ese día si ningún período se solapa con [00:00, 24:00) local."""
    dias = []
    fecha = desde
    while fecha <= hasta:
        ini, fin = inicio_del_dia(fecha), inicio_del_dia(fecha + timedelta(days=1))
        libres = sum(
            1 for periodos in ocupacion.values()
            if not any(p.desde < fin and p.hasta > ini for p in periodos)
        )
        dias.append((fecha, libres))
        fecha += timedelta(days=1)
    return dias


async def disponibilidad_por_dia(db, equipamiento_id, sede, desde, hasta):
    """RN-I14: unidades asignables hoy menos las ocupadas, por día. Dos consultas."""
    ids = await unidades_asignables(db, equipamiento_id, sede)
    ocupacion = await ocupacion_de_unidades(
        db, ids, inicio_del_dia(desde), inicio_del_dia(hasta + timedelta(days=1))
    )  # con ids vacíos devuelve {} sin consultar
    return len(ids), contar_libres_por_dia(desde, hasta, ocupacion)
```

Notas:

- `ocupacion_de_unidades` devuelve una clave por unidad (lista vacía si está libre), así que `ocupacion.values()` recorre todas las asignables. Con `ids = []` devuelve `{}` y todos los días dan 0.
- La comparación `p.desde < fin and p.hasta > ini` es el solapamiento de intervalos semiabiertos `[)`, el mismo de `tstzrange` en `loans`. Los `datetime` que devuelve `loans` tienen zona (`timestamptz`), así que se comparan bien con los de `ZONA_HORARIA_LAB`.
- Costo: días × unidades × períodos, todo en memoria (62 × unas pocas unidades); no hace falta optimizar (P10).

### 4.4 Router

**`GET /equipamiento/{equipamiento_id}/disponibilidad`** (después de `obtener_equipamiento`):

```python
@router.get(
    "/equipamiento/{equipamiento_id}/disponibilidad",
    response_model=DisponibilidadResponse,
    summary="Disponibilidad por día de un ítem (mini-calendario)",
    responses=error_responses(401, 403, 404, 422),
)
async def obtener_disponibilidad(
    equipamiento_id: int,
    desde: date = Query(..., examples=["2026-11-09"]),
    hasta: date = Query(..., examples=["2026-11-30"]),
    sede: SedeEnum | None = Query(default=None),
    actor: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DisponibilidadResponse:
    """Unidades libres por día, sin identidad de solicitantes (PRE-01, RN-I14, RN-I15)."""
```

Orden de validación (fija qué error gana, y así se testea): 1) sesión (`401`); 2) sede con `sede_para_alta(actor, sede)` — mismas reglas que pide §5.4 (`403`/`422 SEDE_REQUERIDA`); 3) `validar_rango(desde, hasta, ahora_lab().date())` (`422`); 4) alcance del ítem con `_stmt_equipamiento_en_alcance(actor, sede_calculo, incluir_inactivos=True)` y la misma condición de `obtener_equipamiento` (`404`); 5) `disponibilidad_por_dia`.

`ahora_lab` se importa en el router desde `app.core.settings`, para que los tests puedan fijar "hoy" con `monkeypatch.setattr(router_module, "ahora_lab", ...)` si lo necesitan. Preferible: armar los datos de prueba con fechas relativas a hoy (`crear_linea(..., retiro=...)` ya lo admite) y no parchear.

**RN-I13 en `editar_equipamiento`:**

```python
cambios = payload.model_dump(exclude_unset=True)
if (
    "es_notebook" in cambios
    and cambios["es_notebook"] != equipamiento.es_notebook
    and "max_dias_prestamo" not in cambios
):
    cambios["max_dias_prestamo"] = await _plazo_por_defecto(db, cambios["es_notebook"])
```

`_plazo_por_defecto(db, es_notebook) -> int` sale de las líneas que hoy están en `crear_equipamiento` (`router.py:232-235` en `3ffed99`), que pasa a llamarla.

### 4.5 Esquemas

```python
class DiaDisponibilidad(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fecha: date = Field(..., examples=["2026-11-10"])
    unidades_libres: int = Field(..., ge=0, examples=[2])
    disponible: bool = Field(..., examples=[True])


class DisponibilidadResponse(BaseModel):
    equipamiento_id: int = Field(..., examples=[12])
    sede: SedeEnum = Field(..., examples=["Ushuaia"])
    desde: date = Field(..., examples=["2026-11-09"])
    hasta: date = Field(..., examples=["2026-11-30"])
    unidades_asignables: int = Field(..., ge=0, examples=[3])
    dias: list[DiaDisponibilidad]
```

`disponible` se calcula al construir (`unidades_libres > 0`), no se recibe de `loans`.

### 4.6 Tests (fixtures existentes: `client`, `db`, `crear_usuario`, `auth`, `crear_equipamiento`, `crear_linea`)

| Archivo | Casos |
| :---- | :---- |
| `test_disponibilidad_unit.py` | Día sin períodos; período que cubre el día entero; período que empieza antes del rango; período que termina a las 12:00 (ocupa) y a las 00:00 del día siguiente (no ocupa ese día siguiente); dos unidades en días alternados (`1` cada día); `validar_rango` con cada una de las tres fallas y con 62 días justos |
| `test_disponibilidad.py` (INV-26) | 3 unidades `disponible` + 1 `mantenimiento` + 1 `baja` + 1 `prestado` + 1 de la otra sede: `unidades_asignables = 3`; líneas `reservado` y `entregado` restan en sus días; `pendiente`, `devuelto` y `cancelado` no; el JSON no tiene claves `unidad`, `numero_serie`, `orden` ni `solicitante` (buscar en `response.text`) |
| `test_disponibilidad.py` (INV-30) | Matriz de errores en el orden de §4.4; admin con ítem inactivo → `200` en 0; estudiante → `404` |
| `test_disponibilidad.py` (INV-31) | Un ítem con 1 unidad y una línea `reservado` sobre el día D: el calendario da `0` en D y `POST /api/v1/loans/ordenes` con retiro y devolución en D (dentro de la franja y con la anticipación de `config`) → `409 EQUIPAMIENTO_NO_DISPONIBLE`; en D+5 da `1` y la orden se crea (`201`). Usar como payload el que ya arma `tests/loans/test_crear_orden.py` |
| `test_service.py` (INV-28) | Transiciones; idempotencia; `404`; sin `commit`: tras `marcar_unidad_mantenimiento` y `rollback`, la unidad sigue `disponible`; `liberar_unidad` + `marcar_unidad_mantenimiento` + `commit` → `mantenimiento`, y una segunda sesión que lee **antes** del `commit` obtiene `prestado` (nunca `disponible`) |
| `test_gestion.py` (INV-29) | General → notebook sin `max_dias_prestamo`: toma `prestamo.notebook.max_dias`; con `max_dias_prestamo=7`: 7; notebook → notebook (sin cambio real): no toca el plazo; editar sólo el nombre: no toca el plazo |

## 5. Fase B — Frontend (`src/features/inventory/`)

### 5.1 Archivos

| Archivo | Acción | Contenido |
| :---- | :---- | :---- |
| `types/index.ts` | Modificar | `DiaDisponibilidadDTO`, `DisponibilidadDTO` (espejo 1:1) y el modelo de vista `DiaCalendario` |
| `services/inventoryApi.ts` | Modificar | `obtenerDisponibilidad(id, {desde, hasta, sede?}, signal?)` → `GET /api/v1/inventory/equipamiento/{id}/disponibilidad?…` |
| `services/calendario.ts` | **Crear** | Funciones puras: `aIso(fecha)`, `ventana(hoy) → {min, max}` (62 días), `rangoDelMes(mes, hoy) → {desde, hasta} \| null`, `armarMes(mes, dias, hoy) → DiaCalendario[][]` (semanas de lunes a domingo, con `estado: "fuera" \| "libre" \| "sin-unidades" \| "cargando"` y `libres`), `puedeIrA(mes, hoy)` |
| `services/calendario.test.ts` | **Crear** | Mes que empieza en domingo, mes de 28 días, recorte por hoy y por la ventana, mes totalmente fuera de ventana (`null`), semanas completas de 7 |
| `services/carrito.ts` | **Crear** | `motivoNoAgregable(eq, role) → string \| null` ("Dado de baja", "En mantenimiento", "Sin unidades disponibles hoy"; `null` si se puede) y `muestraBotonAgregar(role, hayCallback)` |
| `services/carrito.test.ts` | **Crear** | Cada motivo y el caso habilitado; admin nunca ve el botón |
| `hooks/useDisponibilidad.ts` | **Crear** | `(equipamientoId, mes, sede?)` → `{dias, cargando, error}`, con `AbortController` al cambiar de mes o cerrar |
| `components/MiniCalendario.tsx` | **Crear** | Encabezado con mes y flechas (deshabilitadas fuera de ventana), grilla 7 × n, leyenda y aviso "Orientativo: la confirmación llega al enviar el pedido" |
| `components/EquipmentDetailModal.tsx` | **Crear** | Usa `Modal.tsx` existente. Datos de §8.2 del spec, `MiniCalendario` y el botón "Agregar al pedido" |
| `components/AgregarAlPedido.tsx` | **Crear** | Botón reutilizado en tarjeta, lista y detalle: deshabilitado con `title` = motivo; al pulsar llama al *callback* y muestra "Agregado" 2 s |
| `components/EquipmentCard.tsx` | Modificar | Reemplaza el botón actual por `AgregarAlPedido`; el clic de la tarjeta abre el detalle para todos los roles (hoy no hace nada para el admin y exige `canBook` para el resto) |
| `pages/CatalogPage.tsx` | Modificar | Estado `detalle: Equipment \| null` y `<EquipmentDetailModal>`; se quita la prop `onSelect`; la fila de la lista abre el detalle y suma `AgregarAlPedido`; "Disponibles" → "Disponibles hoy"; pasa la sede vista al detalle |
| `Frontend-PrestaMeDios/README.md` | Modificar | Detalle, calendario y el contrato `onAddToCart` |

### 5.2 Decisiones de diseño

- **Un pedido por mes.** `rangoDelMes` recorta a `[max(día 1, hoy), min(fin de mes, hoy + 61)]`; los días fuera de ese rango se pintan "fuera" sin pedirlos. Así nunca se dispara el `422` de rango desde la UI.
- **"Hoy"** es la fecha local del navegador. El backend usa la del laboratorio; si el navegador está en otra zona y el backend responde `422 RANGO_FECHAS_INVALIDO`, se muestra `ApiError.detail` (caso raro, no se compensa).
- **Sede del SUPERADMIN.** Se usa la sede vista de `useSede()`; si está en "ambas", el calendario muestra un selector de sede propio dentro del detalle en lugar de pedir.
- **Accesibilidad.** Cada celda lleva `aria-label` ("Martes 10 de noviembre: 2 unidades libres"); los colores se acompañan de la cantidad o de un guion, no sólo de color.
- **Contrato con el Perfil 3.** `inventory` exporta el tipo `Equipment` (ya existe) y no importa nada de `loans`. El carrito recibe el `Equipment` completo (`id`, `name`, `altaGama`, `esNotebook`, `maxDays`, `image`); si necesita otro campo, se agrega al mapper en una tarea de `inventory`.

## 6. Fase C (bloqueada por `loans`)

Se ejecuta cuando `loans` publique en `develop` `historial_de_unidad` y `reservas_futuras_de_unidad`. **Primer paso obligatorio:** comparar sus firmas con §5.3 y §5.5 del spec y, si difieren, actualizar el spec antes de programar.

| Archivo | Acción | Contenido |
| :---- | :---- | :---- |
| `inventory/schemas.py` | Modificar | `SolicitanteResumen`, `MovimientoUnidadResponse`, `UnidadEstadoResponse(UnidadFisicaResponse)` con `reservas_afectadas: int \| None` |
| `inventory/router.py` | Modificar | `GET /unidades/{id}/historial` (alcance con `puede_ver_sede` → `404`, luego `loans.historial_de_unidad`, recorte por `limit`/`offset`); `cambiar_estado_unidad` con `response_model=UnidadEstadoResponse` y, tras el `commit`, `reservas_futuras_de_unidad(db, unidad_id, desde=ahora_lab())` si el estado nuevo es `mantenimiento` o `baja` |
| `tests/inventory/test_historial.py` | Crear | INV-34 (con líneas creadas por `crear_linea` en varios estados) |
| `tests/inventory/test_gestion.py` | Modificar | INV-35 |
| Frontend `types`, `inventoryApi.ts`, `mappers.ts` | Modificar | DTOs del historial y `reservas_afectadas`; `listarHistorialUnidad` |
| `components/HistorialUnidadModal.tsx` | Crear | Lista paginada con "Cargar más" |
| `components/UnidadesRow.tsx`, `hooks/useGestion.ts`, `components/StockTable.tsx` | Modificar | Botón "Historial"; aviso persistente de reservas afectadas |

## 7. Verificación

| Qué | Cómo |
| :---- | :---- |
| Backend | `pytest -q` completo y `pytest --cov=app/modules/inventory` (mantener ≥ 90 %; hoy 98 %). Cada INV de la fase con test anotado (`# INV-NN`) |
| OpenAPI | `/docs`: el endpoint nuevo con ejemplos y `401/403/404/422` |
| Frontend | `npm run typecheck`, `npm run build`, `npm test` |
| Manual | Backend local con datos de demo: estudiante abre el detalle, navega dos meses, ve un día en rojo por una reserva aprobada (creada a mano o por la bandeja del Perfil 3); `SUPERADMIN` en "ambas sedes" elige sede en el detalle; con un *callback* de prueba (`onAddToCart={console.log}` sólo en local, sin commitear) el botón respeta los tres motivos |
| Trazabilidad | Tabla requisito → endpoint → test en la descripción del PR |

## 8. Puntos de contacto con otros perfiles

| Elemento | Dueño | Tratamiento |
| :---- | :---- | :---- |
| `loans.ocupacion_de_unidades`, `PeriodoOcupado` | Perfil 3 | Se usan tal cual (públicas, SPEC-05 §10.2). Si cambian de firma, se rompe `test_disponibilidad.py`: es la alarma buscada |
| Cableado `onAddToCart` en `App.tsx` | Perfil 3 (con conformidad del Perfil 1) | `inventory` no lo hace (D-12). Hasta entonces el botón no se muestra |
| `marcar_unidad_mantenimiento` | Perfil 2 → Perfil 3 | Avisar en `MEMORY.md` §5 al mergear: destraba AC-L59 |
| `historial_de_unidad`, `reservas_futuras_de_unidad` | Perfil 3 | Bloquean la Fase C |
| Datos de demo | Perfil 1 | Ítems con unidades en varios estados y alguna reserva aprobada para que el calendario muestre rojo |

## 9. Riesgos

| Riesgo | Mitigación |
| :---- | :---- |
| Import circular `inventory` ↔ `loans` | RN-I16: sólo `disponibilidad.py` importa `loans`; un test importa `app.main` desde cero (`python -c "import app.main"`) en la verificación de B-03 |
| El calendario y `POST /ordenes` divergen si `loans` cambia RN-L10 | INV-31 compara los dos con los mismos datos |
| Fechas: borde de medianoche y zona horaria | `contar_libres_por_dia` es pura y se testea con períodos que terminan a las 00:00 y a las 12:00 |
| El carrito del Perfil 3 se demora | El botón queda oculto sin *callback*; el detalle y el calendario se pueden mostrar igual en la demo |
| `crear_linea` usa diciembre de 2026 por defecto | En los tests de inventory usar siempre `retiro=` relativo a hoy, porque el endpoint rechaza fechas pasadas |

## 10. Historial

| Versión | Fecha | Cambio |
| :---- | :---- | :---- |
| 2.0.0 | 2026-11-07 | `BORRADOR` (Perfil 2, con asistencia de IA). Plan de las Fases B y C según el spec v1.2.0; la Fase A queda resumida en §3 |
| 1.0.0 | 2026-10-23 | Plan ejecutado (Fase A). Desviaciones: (1) la categoría se filtra en la pantalla y no en la API; (2) la migración `0010` usa SQL directo para los `CHECK` por el prefijo duplicado de `NAMING_CONVENTION`; (3) `UnidadFormModal` agrega alta y edición de unidades desde la tabla de stock; (4) las ramas de T-00 se crearon al cierre, con pedido explícito: `feat/inventory-gestion` (backend, `b93017f`) y `feat/inventory-catalogo` (frontend, `128b749`), publicadas por `Farvi-1986` |
| 0.1.0 | 2026-10-23 | Borrador inicial (Perfil 2) |
