"""Carga datos de prueba para la demo y el recorrido funcional.

Pasa por la API real (in-process, httpx + ASGITransport) para respetar las
validaciones. Las altas administrativas se firman como el Superadministrador
(id más bajo con rol SUPERADMIN). Es idempotente: lo que ya existe se saltea.

Uso, desde la carpeta Backend-PrestaMeDios con el .venv activo y después de
``pip install -r requirements-dev.txt`` (el script usa httpx):
    python <ruta>/seed_demo.py <contraseña-de-la-demo>
La contraseña es la de todas las cuentas de prueba: 8 o más caracteres, con
letras y números.
"""

import asyncio
import os
import sys
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

# Sin PYTHONPATH: el paquete `app` se toma de la carpeta desde la que se corre
# (así funciona igual en Linux, macOS y Windows).
sys.path.insert(0, os.getcwd())
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")


def _salir(mensaje: str) -> None:
    raise SystemExit(f"\n✗ {mensaje}\n")


if len(sys.argv) != 2:
    _salir("Falta la contraseña de las cuentas de prueba. Uso: python seed_demo.py <contraseña>")
PASSWORD = sys.argv[1]
if len(PASSWORD) < 8 or not any(c.isalpha() for c in PASSWORD) or not any(c.isdigit() for c in PASSWORD):
    _salir("La contraseña tiene que tener 8 o más caracteres, con letras y números (por ejemplo Demo2026x).")

try:
    import httpx
except ModuleNotFoundError:
    _salir("Falta httpx. Con el .venv activo: pip install -r requirements-dev.txt")

if not os.path.isdir(os.path.join(os.getcwd(), "app", "modules")):
    _salir("Hay que correrlo desde la carpeta Backend-PrestaMeDios (cd Backend-PrestaMeDios).")

from sqlalchemy import select, update  # noqa: E402

try:
    from app.core.enums import RolUsuario
    from app.core.security import crear_access_token
    from app.database import AsyncSessionLocal
    from app.main import app
    from app.modules.users.models import Usuario
except ModuleNotFoundError as e:
    _salir(f"Falta el paquete {e.name!r}. Con el .venv activo: pip install -r requirements-dev.txt")
except Exception as e:  # p. ej. el .env sin JWT_SECRET_KEY o sin DATABASE_URL
    _salir(f"El backend no arranca: {e}\n  Revisar el .env (DATABASE_URL y JWT_SECRET_KEY, ver .env.example).")

API = "/api/v1"

USUARIOS = [
    # email, nombre, apellido, dni, rol, sede, telefono
    ("estudiante.demo@example.com", "Lucía", "Prueba", "90000001", "ESTUDIANTE", "Ushuaia", "+54 2901 400001"),
    ("docente.demo@example.com", "Martín", "Prueba", "90000002", "DOCENTE", "Ushuaia", "+54 2901 400002"),
    ("admin.ushuaia.demo@example.com", "Carla", "Prueba", "90000003", "ADMIN_LOCAL", "Ushuaia", "+54 2901 400003"),
    ("estudiante.rg.demo@example.com", "Joaquín", "Prueba", "90000004", "ESTUDIANTE", "Río Grande", "+54 2964 400004"),
]
# Se registra sola (autorregistro) y queda PENDIENTE_APROBACION para aprobarla en vivo.
ASPIRANTE = ("aspirante.demo@example.com", "Sofía", "Prueba", "90000005", "ESTUDIANTE", "Ushuaia", "+54 2901 400005")

# Mismos ids y nombres que las categorías base de la migración 0019 (en una base
# nueva ya existen y el script sólo avisa "ya existía").
CATEGORIAS = [
    ("cameras", "Cámaras", "#1A4A7A"),
    ("audio", "Audio", "#1A7A4A"),
    ("lighting", "Iluminación", "#A0620D"),
    ("tripods", "Trípodes", "#5A2D82"),
    ("notebooks", "Notebooks", "#6E6E73"),
]


# Fotos libres de Wikimedia Commons (miniaturas de 960 px), por código de equipo.
# Se cargan desde internet: abrir el catálogo una vez antes de la demo para que
# queden en la caché del navegador. Autores y licencias en cada página de Commons:
#   CAM-001 File:Sony Alpha7 III 20 apr 2018b.jpg (CC BY-SA 4.0)
#   CAM-002 File:Canon EOS M50 black 01.jpg (CC BY-SA 4.0)
#   AUD-001 File:Zoom H5.jpg (CC BY 4.0)
#   AUD-002 File:Rode Wireless Go II Set.jpg (CC BY-SA 4.0)
#   ILU-001 File:Softbox.jpg (CC BY-SA 3.0; softbox genérico, no es el Godox)
#   TRI-001 File:123 365 Manfrotto 190XB + 804RC2 (5685134538).jpg (CC BY-SA 2.0)
#   NB-001  File:Lenovo ThinkPad E14 G7 14 WUXGA.jpg (CC0)
_COMMONS = "https://thumb.wikimedia.org/wikipedia/commons/thumb"
IMAGENES = {
    "CAM-001": f"{_COMMONS}/0/04/Sony_Alpha7_III_20_apr_2018b.jpg/960px-Sony_Alpha7_III_20_apr_2018b.jpg",
    "CAM-002": f"{_COMMONS}/4/4e/Canon_EOS_M50_black_01.jpg/960px-Canon_EOS_M50_black_01.jpg",
    "AUD-001": f"{_COMMONS}/3/3c/Zoom_H5.jpg/960px-Zoom_H5.jpg",
    "AUD-002": f"{_COMMONS}/b/b7/Rode_Wireless_Go_II_Set.jpg/960px-Rode_Wireless_Go_II_Set.jpg",
    "ILU-001": "https://upload.wikimedia.org/wikipedia/commons/4/41/Softbox.jpg",
    "TRI-001": f"{_COMMONS}/4/42/123_365_Manfrotto_190XB_%2B_804RC2_%285685134538%29.jpg"
               "/960px-123_365_Manfrotto_190XB_%2B_804RC2_%285685134538%29.jpg",
    "NB-001": f"{_COMMONS}/c/c5/Lenovo_ThinkPad_E14_G7_14_WUXGA.jpg/960px-Lenovo_ThinkPad_E14_G7_14_WUXGA.jpg",
}


def u(serie, codigo, sede, locker=None, estado="disponible"):
    return {"numero_serie": serie, "codigo_inventario": codigo, "sede": sede, "locker": locker, "estado": estado}


EQUIPOS = [
    {
        "codigo": "CAM-001", "nombre": "Cámara Sony A7 III", "marca": "Sony", "modelo": "ILCE-7M3",
        "categoria_id": "cameras", "alta_gama": True,
        "descripcion": "Cámara full frame mirrorless. Equipo de alta gama: requiere aval docente.",
        "unidades": [u("DEMO-A7-01", "CAM-U-01", "Ushuaia", 1), u("DEMO-A7-02", "CAM-U-02", "Ushuaia", 1)],
    },
    {
        "codigo": "CAM-002", "nombre": "Cámara Canon EOS M50", "marca": "Canon", "modelo": "EOS M50 Mark II",
        "categoria_id": "cameras", "descripcion": "Cámara mirrorless APS-C para prácticas generales.",
        "unidades": [
            u("DEMO-M50-01", "CAM-U-03", "Ushuaia", 2), u("DEMO-M50-02", "CAM-U-04", "Ushuaia", 2),
            u("DEMO-M50-03", "CAM-U-05", "Ushuaia", 2, "mantenimiento"), u("DEMO-M50-04", "CAM-R-01", "Río Grande", 1),
        ],
    },
    {
        "codigo": "AUD-001", "nombre": "Grabador Zoom H5", "marca": "Zoom", "modelo": "H5",
        "categoria_id": "audio", "descripcion": "Grabador de audio portátil de 4 pistas.",
        "unidades": [u("DEMO-H5-01", "AUD-U-01", "Ushuaia", 3), u("DEMO-H5-02", "AUD-U-02", "Ushuaia", 3)],
    },
    {
        "codigo": "AUD-002", "nombre": "Micrófono inalámbrico Rode Wireless GO II", "marca": "Rode",
        "modelo": "Wireless GO II", "categoria_id": "audio", "descripcion": "Kit de dos transmisores y un receptor.",
        "unidades": [u("DEMO-RGO-01", "AUD-U-03", "Ushuaia", 3), u("DEMO-RGO-02", "AUD-R-01", "Río Grande", 2)],
    },
    {
        "codigo": "ILU-001", "nombre": "Panel LED Godox SL60W", "marca": "Godox", "modelo": "SL60W",
        "categoria_id": "lighting", "descripcion": "Luz continua LED de 60 W con softbox.",
        "unidades": [u("DEMO-SL60-01", "ILU-U-01", "Ushuaia", 4), u("DEMO-SL60-02", "ILU-U-02", "Ushuaia", 4)],
    },
    {
        "codigo": "TRI-001", "nombre": "Trípode Manfrotto 190X", "marca": "Manfrotto", "modelo": "MK190X3",
        "categoria_id": "tripods", "descripcion": "Trípode de aluminio con cabezal de bola.",
        "unidades": [
            u("DEMO-190X-01", "TRI-U-01", "Ushuaia", 5), u("DEMO-190X-02", "TRI-U-02", "Ushuaia", 5),
            u("DEMO-190X-03", "TRI-R-01", "Río Grande", 3),
        ],
    },
    {
        "codigo": "NB-001", "nombre": "Notebook Lenovo ThinkPad E14", "marca": "Lenovo", "modelo": "ThinkPad E14 Gen 5",
        "categoria_id": "notebooks", "es_notebook": True, "descripcion": "Notebook para edición liviana.",
        "unidades": [u("DEMO-E14-01", "NB-U-01", "Ushuaia", 6), u("DEMO-E14-02", "NB-U-02", "Ushuaia", 6)],
    },
]

for _eq in EQUIPOS:
    _eq["imagen_url"] = IMAGENES[_eq["codigo"]]

ESPACIOS = [
    ("Aula-Estudio", "Aula-Estudio", "Ushuaia"),
    ("Isla de Edición 1", "Isla de Edición", "Ushuaia"),
    ("Aula-Estudio Río Grande", "Aula-Estudio", "Río Grande"),
]


# Fechas de los ejemplos: días hábiles a partir de pasado mañana, en hora del laboratorio.
# Los préstamos usan equipos distintos de los que pide Lucía en vivo (Canon y trípode)
# para no quitarle unidades a la escena 2.
ZONA_LAB = ZoneInfo("America/Argentina/Ushuaia")


def habil(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


DIA_1 = habil(date.today() + timedelta(days=2))
DIA_2 = habil(DIA_1 + timedelta(days=1))


def a_las(dia: date, hora: int) -> str:
    return datetime.combine(dia, time(hora), ZONA_LAB).isoformat()


def ok(r: httpx.Response, que: str) -> dict | None:
    if r.status_code in (200, 201):
        print(f"  ✓ {que}")
        return r.json()
    if r.status_code == 409:
        print(f"  · {que} (ya existía)")
        return None
    _salir(f"{que}: la API respondió {r.status_code} {r.text}\n"
           "  Lo que se cargó hasta acá queda; corregir y volver a correr el script (saltea lo que ya existe).")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        sa = (
            await db.execute(select(Usuario).where(Usuario.rol == RolUsuario.SUPERADMIN).order_by(Usuario.id))
        ).scalars().first()
        if sa is None:
            raise SystemExit("No hay Superadministrador: correr crear-superadmin primero.")
        token, _ = crear_access_token(usuario_id=sa.id, rol=sa.rol, sede=sa.sede, token_version=sa.token_version)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://demo") as c:
        H = {"Authorization": f"Bearer {token}"}

        print("Usuarios")
        for email, nombre, apellido, dni, rol, sede, tel in USUARIOS:
            ok(await c.post(f"{API}/users", headers=H, json={
                "email": email, "password": PASSWORD, "nombre": nombre, "apellido": apellido,
                "dni": dni, "telefono": tel, "rol": rol, "sede": sede,
            }), f"{rol} {sede}: {email}")
        email, nombre, apellido, dni, rol, sede, tel = ASPIRANTE
        ok(await c.post(f"{API}/auth/register", json={
            "email": email, "password": PASSWORD, "nombre": nombre, "apellido": apellido,
            "dni": dni, "telefono": tel, "rol": rol, "sede": sede,
        }), f"autorregistro pendiente: {email}")

        # El alta directa fuerza el cambio de contraseña (SPEC-02 A9); para la demo se omite.
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Usuario)
                .where(Usuario.email.in_([x[0] for x in USUARIOS]))
                .values(debe_cambiar_password=False)
            )
            await db.commit()

        print("Categorías")
        for cid, nombre, color in CATEGORIAS:
            ok(await c.post(f"{API}/inventory/categorias", headers=H,
                            json={"id": cid, "nombre": nombre, "color": color}), nombre)

        print("Equipamiento")
        for eq in EQUIPOS:
            ok(await c.post(f"{API}/inventory/equipamiento", headers=H, json=eq), f"{eq['codigo']} {eq['nombre']}")

        print("Imágenes del equipamiento")
        por_codigo = {}
        for sede in ("Ushuaia", "Río Grande"):
            r = await c.get(f"{API}/inventory/equipamiento", headers=H, params={"sede": sede})
            por_codigo |= {e["codigo"]: e for e in r.json()}
        for codigo, url in IMAGENES.items():
            e = por_codigo.get(codigo)
            if e is None:
                print(f"  · {codigo} (no está en el catálogo)")
            elif e.get("imagen_url") == url:
                print(f"  · {codigo} (ya tenía la imagen)")
            else:
                ok(await c.patch(f"{API}/inventory/equipamiento/{e['id']}", headers=H,
                                 json={"imagen_url": url}), f"imagen de {codigo}")

        print("Espacios")
        existentes = set()
        for sede in ("Ushuaia", "Río Grande"):
            r = await c.get(f"{API}/spaces/espacios", headers=H, params={"sede": sede})
            existentes |= {e["nombre"] for e in r.json()}
        espacio_ids = {}
        for nombre, tipo, sede in ESPACIOS:
            if nombre in existentes:
                print(f"  · {nombre} (ya existía)")
                continue
            e = ok(await c.post(f"{API}/spaces/espacios", headers=H,
                                json={"nombre": nombre, "tipo": tipo, "sede": sede}), f"{nombre} ({sede})")
            espacio_ids[nombre] = e["id_espacio"]

        print("Comunicado")
        r = await c.get(f"{API}/notifications/comunicados", headers=H)
        if r.json()["total"] == 0:
            ok(await c.post(f"{API}/notifications/comunicados", headers=H, json={
                "titulo": "Bienvenida al sistema de préstamos",
                "contenido": "Desde este portal pueden consultar el catálogo, reservar el Aula-Estudio "
                             "y la Isla de Edición, y seguir sus solicitudes. (Comunicado de prueba)",
                "es_global": True,
            }), "comunicado global")
        else:
            print("  · ya hay comunicados")

        async def sesion(email: str) -> dict:
            r = await c.post(f"{API}/auth/login", json={"email": email, "password": PASSWORD})
            if r.status_code != 200:
                raise SystemExit(f"  ✗ login {email}: {r.status_code} {r.text}")
            return {"Authorization": f"Bearer {r.json()['access_token']}"}

        print("Reservas de espacios de ejemplo")
        if "Aula-Estudio" in espacio_ids:
            martin = await sesion("docente.demo@example.com")
            joaquin = await sesion("estudiante.rg.demo@example.com")
            carla = await sesion("admin.ushuaia.demo@example.com")
            ok(await c.post(f"{API}/spaces/reservas", headers=martin, json={
                "id_espacio": espacio_ids["Aula-Estudio"], "fecha_reserva": DIA_1.isoformat(),
                "hora_inicio": "10:00:00", "hora_fin": "12:00:00", "motivo": "Clase práctica de iluminación (prueba)",
            }), f"pendiente: Martín, Aula-Estudio {DIA_1.isoformat()} 10–12")
            r = ok(await c.post(f"{API}/spaces/reservas", headers=martin, json={
                "id_espacio": espacio_ids["Isla de Edición 1"], "fecha_reserva": DIA_2.isoformat(),
                "hora_inicio": "09:00:00", "hora_fin": "11:00:00", "motivo": "Edición del corto de la cátedra (prueba)",
            }), f"Martín, Isla de Edición 1 {DIA_2.isoformat()} 9–11")
            ok(await c.patch(f"{API}/spaces/reservas/{r['id_reserva']}/estado", headers=carla,
                             json={"nuevo_estado": "Aprobada"}), "  aprobada por Carla")
            ok(await c.post(f"{API}/spaces/reservas", headers=joaquin, json={
                "id_espacio": espacio_ids["Aula-Estudio Río Grande"], "fecha_reserva": DIA_2.isoformat(),
                "hora_inicio": "10:00:00", "hora_fin": "12:00:00", "motivo": "Grabación de entrevistas (prueba)",
            }), f"pendiente: Joaquín, Aula-Estudio Río Grande {DIA_2.isoformat()} 10–12")
        else:
            print("  · se saltea (los espacios ya existían)")

        print("Préstamos de ejemplo")
        martin = await sesion("docente.demo@example.com")
        r = await c.get(f"{API}/loans/ordenes/mias", headers=martin)
        if r.json():
            print("  · se saltea (Martín ya tiene órdenes)")
            return
        lucia = await sesion("estudiante.demo@example.com")
        joaquin = await sesion("estudiante.rg.demo@example.com")
        carla = await sesion("admin.ushuaia.demo@example.com")
        eq = {codigo: e["id"] for codigo, e in por_codigo.items()}

        def orden(items: list[str], retiro: str, devolucion: str, asignatura: int | None = None) -> dict:
            o = {"retiro": retiro, "devolucion": devolucion, "acepta_normativa": True,
                 "items": [{"equipamiento_id": eq[x]} for x in items]}
            if asignatura is not None:
                o["asignatura_id"] = asignatura
            return o

        ok(await c.post(f"{API}/loans/ordenes", headers=martin, json=orden(
            ["ILU-001", "AUD-002"], a_las(DIA_1, 10), a_las(DIA_2, 15),
        )), f"pendiente: Martín, panel LED + Rode, {DIA_1.isoformat()} → {DIA_2.isoformat()}")

        o = ok(await c.post(f"{API}/loans/ordenes", headers=lucia, json=orden(
            ["AUD-001"], a_las(DIA_2, 10), a_las(DIA_2, 15), asignatura=101,
        )), f"Lucía, Zoom H5, {DIA_2.isoformat()} 10–15")
        libres = (await c.get(f"{API}/loans/ordenes/{o['id']}/unidades-libres", headers=carla)).json()
        ok(await c.patch(f"{API}/loans/ordenes/{o['id']}/estado", headers=carla, json={
            "estado": "aprobada",
            "asignaciones": [{"detalle_id": x["detalle_id"], "unidad_fisica_id": x["unidades"][0]} for x in libres],
        }), "  aprobada por Carla, con unidad asignada")

        ok(await c.post(f"{API}/loans/ordenes", headers=joaquin, json=orden(
            ["CAM-002"], a_las(DIA_1, 10), a_las(DIA_2, 12), asignatura=201,
        )), f"pendiente: Joaquín (Río Grande), Canon, {DIA_1.isoformat()} → {DIA_2.isoformat()}")


try:
    asyncio.run(main())
except (OSError, ConnectionError) as e:
    _salir(f"No se pudo conectar con PostgreSQL: {e}\n  Revisar que esté corriendo y el DATABASE_URL del .env.")
except Exception as e:
    if type(e).__module__.startswith(("asyncpg", "sqlalchemy")):
        _salir(f"Error de base de datos: {str(e).splitlines()[0]}\n"
               "  ¿Existe la base del DATABASE_URL? ¿Se corrió `alembic upgrade head`?")
    raise
