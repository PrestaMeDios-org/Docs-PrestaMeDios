# Demo funcional — jueves 12/11/2026

> Presentación breve y demo en vivo de lo que hoy está en `develop` (backend `1c89c53`, frontend `6ae5db4`, los dos del 11/11). Duración supuesta: **unos 20 minutos** (5 de láminas, 10 de demo y 5 de preguntas). Si la cátedra da menos tiempo, recortar primero la escena 4.
> **Láminas:** artifact "PrestaMeDios — Demo funcional 12/11" (9 láminas, con notas para quien presenta). Actualizadas el 12/11 con lo que se mergeó el 11/11.
> **Detalle de cada paso:** `docs/pruebas/recorrido-funcional.md` (escrito el 10/11: el préstamo y lo nuevo de espacios no figuran ahí, están en este guion). **Estado y pendientes:** `../analisis-estado-y-produccion.md`.

## Qué cambió desde el 10/11

El 11/11 entraron 14 PR (backend #32…#37, frontend #19…#26). Para la demo importan:

- **Préstamos en pantalla:** formulario de solicitud desde el carrito, "Mis solicitudes" y "Bandeja de Validaciones" (aprobar eligiendo unidades, ajustar horario, rechazar y cancelar con motivo). Frontend PR #24.
- **Aval de alta gama:** el formulario pide el PDF y la admin lo descarga desde la bandeja. Backend PR #34.
- **Horario y correo de contacto por sede** en Parámetros (SPEC-09 Fase A). Backend PR #35 y frontend PR #26. *Espacios y préstamos todavía leen el horario global.*
- **Espacios:** confirmación antes de reservar, franjas contiguas en una sola reserva, nombre del solicitante para la admin, la estudiante cancela una reserva aprobada, y los bloqueos se pueden deshacer y muestran el motivo al pasar el mouse. Backend PR #32 y #36, frontend PR #20.
- **Catálogo:** mini-calendario con estilos y detalle legible en modo oscuro (DT-31 y DT-32 resueltas, frontend PR #23); categorías base cargadas por la migración `0019` (backend PR #37).
- **Sin mergear:** teléfono obligatorio (SPEC-09 Fase B, rama `feat/users-telefono`). **No usar esa rama para la demo:** levantar `develop`.

## Antes de la demo (hoy)

| # | Tarea | Responsable | Hecho |
| :-- | :-- | :-- | :-- |
| 1 | Poner backend y frontend en `develop` actualizado (`git pull`) y correr `alembic upgrade head` (llega hasta la `0019`) | [nombre] | |
| 2 | Cargar la base con `demo/seed_demo.py`. Las categorías ya las crea la `0019`: el script marca "ya existía" y sigue. Desde el 12/11 también carga una foto por equipo (Wikimedia Commons, licencias CC) | [nombre] | |
| 2b | **Abrir el catálogo una vez con internet** antes de presentar: las fotos se cargan desde Wikimedia y quedan en la caché del navegador. Sin internet las tarjetas se ven sin foto, pero todo lo demás funciona | [nombre] | |
| 3 | **Ensayar el préstamo de punta a punta** (escenas 2 y 3) en la máquina de la demo, con las fechas de hoy | Perfil 3 | |
| 4 | En Parámetros, cargar el correo de contacto de cada sede (arranca vacío) | Superadmin | |
| 5 | Grabar un video del recorrido como plan B | [nombre] | |
| 6 | Completar el "Registro de la reunión" del recorrido del 10/11 | Perfil 1 | |

## El día

- Backend: `uvicorn app.main:app` (sin `--reload`, para que no se reinicie si alguien guarda un archivo). Frontend: `npm run dev`.
- Dos ventanas del navegador (normal y privada), zoom al 125 % para que se lea desde el fondo, notificaciones del sistema silenciadas.
- Credenciales a mano en `demo/credenciales.md` (no se versiona, no se proyecta).
- Un PDF cualquiera a mano en el escritorio, por si se muestra el aval de alta gama.

## Láminas (5 min)

| Lámina | Quién | Tiempo | Mensaje |
| :-- | :-- | :-- | :-- |
| 1. Portada | [Perfil 1] | 0:20 | Quiénes somos y qué vamos a mostrar |
| 2. El problema | [Perfil 1] | 0:40 | Correo y formularios, dos sedes aisladas |
| 3. Dónde estamos | [Perfil 1] | 0:50 | 34 de 47 requisitos desde la pantalla (72 %), 961 tests de backend y 213 de frontend, todos en verde |
| 4. La demo | [Perfil 3] | 0:20 | Las cinco escenas |
| 5. Arquitectura | [Perfil 1] | 0:40 | Monolito modular, API primero, integridad en la base |
| 6. Cómo trabajamos | [Perfil 3 o 5] | 0:40 | SDD, 5 perfiles, 8 specs aprobados, IA con reglas |
| *(demo)* | | | |
| 7. Lo que falta | [Perfil 3] | 0:40 | El préstamo se pide y se aprueba; falta el mostrador |
| 8. Próximos pasos | [Perfil 3] | 0:30 | Mostrador, avisos, docente y sede, piloto |
| 9. Preguntas | Todos | — | Pedir devoluciones concretas |

> Sugerencia: hacer la demo después de la lámina 6 y volver a las láminas 7–9 para cerrar.

## Demo (10 min)

Cada escena dice qué hacer y qué decir. Los números entre paréntesis son los pasos de `docs/pruebas/recorrido-funcional.md`.

### Escena 1 — Cuenta nueva (1 min 30) · USR-01, USR-05
1. Ventana privada: intentar entrar como **Sofía** (pendiente) → no puede (1.4).
2. Ventana normal: entrar como **Carla** (admin Ushuaia) → Gestión de Usuarios → Pendientes → **Aprobar** a Sofía (4.2, 4.3).
3. Ventana privada: Sofía ya entra. Cerrar su sesión.
> *Decir:* "Ninguna cuenta se activa sola; la aprueba un admin de su sede".

### Escena 2 — La estudiante pide un préstamo (3 min) · PRE-01…07
1. Ventana privada: entrar como **Lucía**. Catálogo, filtrar Cámaras (2.2, 2.3).
2. Abrir el detalle de la **Canon EOS M50**: la tarjeta cuenta sólo las unidades disponibles (la que está en mantenimiento no suma), y el detalle muestra el mini-calendario con la disponibilidad por día (2.4, 2.5). Los números dependen de lo que quedó en la base: revisarlos en el ensayo.
3. **Agregar al pedido** la Canon y el trípode → abrir el **Carrito** → **Continuar con la solicitud**.
4. Formulario: enviar sin completar para mostrar los errores en rojo (PRE-04). Completar:
   - **Retiro:** mañana viernes 13/11, a una hora **posterior a la hora actual** (24 h de anticipación) y dentro del horario.
   - **Devolución:** lunes 16/11 a las 10:00 (el plazo general es de 4 días; elegir más muestra el error de PRE-07).
   - **Código de asignatura:** cualquiera, por ejemplo `[código]`.
   - Tildar **Acepto la normativa de préstamos del laboratorio** y enviar.
5. **Ver mis solicitudes:** la orden figura **Pendiente**.
> *Decir:* "El estudiante ve la disponibilidad real antes de pedir; el sistema aplica los plazos y la anticipación del reglamento, y esos valores se cambian desde Parámetros".
> Opcional: agregar la **Sony A7 III** (alta gama) para mostrar que el formulario exige el PDF del aval.

### Escena 3 — La admin valida (2 min 30) · PRE-10, PRE-15, PRE-18
1. Ventana normal (Carla): **Bandeja de Validaciones** → aparece la orden de Lucía, con su nombre.
2. **Revisar y aprobar:** elegir la unidad física de cada equipo entre las libres para ese período; mostrar que se puede **ajustar el horario** de retiro antes de aprobar. Aprobar.
3. Ventana privada (Lucía): recargar Mis solicitudes → **Aprobada**, con las fechas finales.
> *Decir:* "La aprobación asigna unidades concretas. Si dos admins intentan dar la misma cámara al mismo tiempo, la base de datos lo impide: lo probamos con tests de concurrencia".
> Si sobra tiempo: crear otra orden y **Rechazarla** con motivo.

### Escena 4 — Espacios (1 min 30) · RES-01…05, GLO-04
1. Lucía: Reservas de Espacios → Isla de Edición 1 → elegir dos franjas seguidas de un día válido → confirmar → queda **Pendiente** como una sola reserva.
2. Carla: Solicitudes pendientes → se ve **el nombre de quien reservó** → **Aprobar**.
3. Carla: **Bloquear** el Aula-Estudio un día con motivo "Mantenimiento" → pasar el mouse sobre el día para ver el motivo → **deshacer** el bloqueo.
> *Decir:* "Dos aprobaciones de la misma franja no pueden convivir: lo impide la base de datos".

### Escena 5 — Superadmin y sedes (1 min 30) · GLO-01, GLO-03
1. Entrar como **Superadmin**: selector de sede, Río Grande con 3 equipos (5.1, 5.2).
2. **Parámetros:** horario y correo de contacto **por sede**. Cambiar el cierre de Ushuaia con un motivo y abrir el **Historial**; después volverlo a su valor.
3. Entrar como **Joaquín** (Río Grande): no ve los equipos, espacios ni comunicados de Ushuaia (6.1–6.3).
> No prometer que el cambio de horario mueve las franjas de espacios: todavía leen el horario global.

## Plan B

- Algo se rompe en vivo → no depurar delante del público: decir "lo mostramos en el video" y pasar al video grabado.
- El formulario rechaza la fecha → revisar que el retiro sea al menos 24 h después de la hora actual y dentro del horario; si no sale al primer intento, pasar a la escena 4.
- Se cae el backend → reiniciarlo una vez (`uvicorn`); si no vuelve, video.
- Sin proyector o sin red → las láminas se pueden exportar a PDF desde el artifact y llevar en un pendrive.

## Preguntas que pueden hacer hoy

| Pregunta | Respuesta corta | Quién |
| :-- | :-- | :-- |
| ¿Cuánto falta para el 80 %? | 34 de 47 desde la pantalla (72 %); faltan 4. Mostrador, campanita, correo de vencimiento y panel docente alcanzan. Plan en la lámina 8 | Perfil 3 |
| ¿Qué pasa después de aprobar un préstamo? | Falta el mostrador: registrar la entrega y la devolución con observaciones (PRE-13). El backend ya guarda las unidades asignadas | Perfil 3 |
| ¿Cómo evitan que dos personas reserven lo mismo? | Restricción de exclusión en PostgreSQL para espacios y bloqueo de filas al asignar unidades, con tests de concurrencia | Perfil 4 / 3 |
| ¿El docente aprueba? | No: según la referente, el docente sólo observa y comenta. Su panel de lectura (PRE-20) está pendiente | Perfil 3 |
| ¿Cómo usan la IA? | Para redactar specs e implementar, siempre bajo la Constitución, `AGENTS.md` y la revisión de PR | Perfil 1 |
| ¿Lo validaron con el Laboratorio? | Tres entrevistas y un recorrido el 10/11; hay reglas que todavía tenemos que confirmar (sanciones, asignaturas) | Perfil 1 |

**Preguntas para hacerle nosotros a la cátedra:** fecha y formato del final; si el asistente IA puede quedar como trabajo futuro; cómo se mide el 80 %; si el final tiene que estar desplegado en un servidor.

## Devoluciones

| Quién | Qué dijo | Acción | Responsable |
| :-- | :-- | :-- | :-- |
| | | | |
