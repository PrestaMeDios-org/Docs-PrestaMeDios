# Demo funcional — jueves 12/11/2026

> Presentación breve + demo en vivo de lo que hoy está en `develop`. Duración supuesta: **unos 20 minutos** (5 de láminas, 10 de demo, 5 de preguntas). Si la cátedra da otro tiempo, recortar la escena 4 primero.
> **Láminas:** artifact "PrestaMeDios — Demo funcional 12/11" (9 láminas, con notas para quien presenta).
> **Detalle de cada paso:** `docs/pruebas/recorrido-funcional.md`. **Estado y pendientes:** `../analisis-estado-y-produccion.md`.

## Antes del jueves (miércoles 11)

| # | Tarea | Responsable | Hecho |
| :-- | :-- | :-- | :-- |
| 1 | Completar el "Registro de la reunión" del recorrido del 10/11 con lo que dijo la cliente | Perfil 1 | |
| 2 | Si se puede: corregir DT-31 (mini-calendario sin estilos) y DT-32 (modo oscuro del detalle) | Perfil 2 | |
| 3 | Si se puede: mostrar el nombre del solicitante en las reservas pendientes (K1) | Perfil 4 | |
| 4 | Ensayo completo cronometrado, con la máquina que se va a usar | Todos | |
| 5 | Grabar un video del recorrido como plan B | [nombre] | |
| 6 | Base de datos recién cargada con `demo/seed_demo.py` la mañana del jueves (la reserva pendiente se crea a dos días hábiles de la carga) | [nombre] | |

## El día

- Backend: `uvicorn app.main:app` (sin `--reload`, para que no se reinicie si alguien guarda un archivo). Frontend: `npm run dev`.
- Dos ventanas del navegador (normal y privada), zoom al 125 % para que se lea desde el fondo, notificaciones del sistema silenciadas.
- Credenciales a mano en `demo/credenciales.md` (no se versiona, no se proyecta).
- Tema **claro** durante toda la demo (DT-32).

## Láminas (5 min)

| Lámina | Quién | Tiempo | Mensaje |
| :-- | :-- | :-- | :-- |
| 1. Portada | [Perfil 1] | 0:20 | Quiénes somos y qué vamos a mostrar |
| 2. El problema | [Perfil 1] | 0:40 | Correo y formularios, dos sedes aisladas |
| 3. Dónde estamos | [Perfil 1] | 0:50 | 22 de 47 de punta a punta, 32 con backend, 895 + 126 tests |
| 4. La demo | [Perfil 3] | 0:20 | Las cinco escenas |
| 5. Arquitectura | [Perfil 1] | 0:40 | Monolito modular, API primero, integridad en la base |
| 6. Cómo trabajamos | [Perfil 3 o 5] | 0:40 | SDD, 5 perfiles, IA con reglas |
| *(demo)* | | | |
| 7. Lo que falta | [Perfil 3] | 0:40 | El préstamo tiene backend; falta la pantalla |
| 8. Próximos pasos | [Perfil 3] | 0:30 | Préstamo, mostrador, avisos, piloto |
| 9. Preguntas | Todos | — | Pedir devoluciones concretas |

> Sugerencia: hacer la demo después de la lámina 6 y volver a las láminas 7–9 para cerrar.

## Demo (10 min)

Cada escena dice qué hacer y qué decir. Los números de paso son los de `docs/pruebas/recorrido-funcional.md`.

### Escena 1 — Cuenta nueva (2 min) · USR-01, USR-05
1. Ventana privada: intentar entrar como **Sofía** (pendiente) → no puede (paso 1.4).
2. Ventana normal: entrar como **Carla** (admin Ushuaia) → Gestión de Usuarios → Pendientes → **Aprobar** a Sofía (4.2, 4.3).
3. Ventana privada: Sofía ya entra.
> *Decir:* "Ninguna cuenta se activa sola; la aprueba un admin de su sede".

### Escena 2 — Estudiante (2 min) · PRE-01…03
1. Entrar como **Lucía**: catálogo con "7 disp. de 7", filtrar Cámaras, buscar "zoom" (2.2, 2.3).
2. Canon EOS M50: "2/3 uds." porque una está en mantenimiento (2.4).
3. Agregar Canon y trípode al **carrito** y abrirlo (2.7). Mostrar el botón deshabilitado y decir que el envío tiene backend y falta la pantalla.
> Evitar abrir el detalle de la Sony si DT-31 no se corrigió; si se abre, avisar que el calendario está sin estilos.

### Escena 3 — Espacios (2 min 30) · RES-01…05, GLO-02
1. Como Lucía: Reservas de Espacios → mañana antes de la hora actual → no deja (regla de 24 h) (2.10).
2. Reservar la **Isla de Edición 1** en un día válido → queda Pendiente (2.13).
3. Como Carla: Solicitudes pendientes → **Aprobar** la del docente y **Rechazar** la de Lucía con motivo (4.7, 4.8).
4. **Bloquear** el Aula-Estudio un día (4.9).
> *Decir:* "Dos aprobaciones de la misma franja no pueden convivir: lo impide la base de datos".

### Escena 4 — Admin (2 min) · PRE-12, PRE-14, NOV-02
1. Control de Stock → desplegar la Canon → pasar una unidad a mantenimiento → el catálogo baja una unidad (4.13, 4.14).
2. Novedades → publicar un comunicado **sólo para Ushuaia** (4.16).

### Escena 5 — Superadmin y sedes (1 min 30) · GLO-01, GLO-03
1. Entrar como **Superadmin**: selector de sede, Río Grande con 3 equipos (5.1, 5.2).
2. Parámetros → cambiar el cierre a 17:00 con motivo → Historial (5.6). **Volverlo a 16:00** (5.7).
3. Entrar como **Joaquín** (Río Grande): no ve el comunicado de Ushuaia ni sus espacios (6.2, 6.3).

### Si sobra tiempo (opcional)
Swagger en `http://localhost:8000/docs`: crear una orden con `POST /api/v1/loans/ordenes` como estudiante y aprobarla como admin con `PATCH /ordenes/{id}/estado`, para mostrar que el circuito existe en el backend. Ensayarlo antes: necesita fechas con 24 h de anticipación dentro del horario.

## Plan B

- Algo se rompe en vivo → no depurar delante del público: decir "lo mostramos en el video" y pasar al video grabado.
- Se cae el backend → reiniciarlo una vez (`uvicorn`); si no vuelve, video.
- Sin proyector o sin red → las láminas se pueden exportar a PDF desde el artifact y llevar en un pendrive.

## Preguntas que pueden hacer el jueves

| Pregunta | Respuesta corta | Quién |
| :-- | :-- | :-- |
| ¿Cuánto falta para el 80 %? | 32 de 47 con backend; el bloque grande es la pantalla del préstamo. Plan en la lámina 8 | Perfil 3 |
| ¿Por qué no se puede pedir un préstamo todavía? | El backend lo hace (crear, validar, aprobar asignando unidades); priorizamos las reglas y la concurrencia antes que la pantalla | Perfil 3 |
| ¿Cómo evitan que dos personas reserven lo mismo? | Restricción de exclusión en PostgreSQL y bloqueo de filas al asignar unidades, con tests de concurrencia | Perfil 4 / 2 |
| ¿Cómo usan la IA? | Para redactar specs e implementar, siempre bajo la Constitución, `AGENTS.md` y la revisión de PR | Perfil 1 |
| ¿Lo validaron con el Laboratorio? | Tres entrevistas y un recorrido el 10/11; hay reglas que todavía tenemos que confirmar (sanciones, asignaturas) | Perfil 1 |

**Preguntas para hacerle nosotros a la cátedra:** fecha y formato del final; si el asistente IA puede quedar como trabajo futuro; cómo se mide el 80 %; si el final tiene que estar desplegado en un servidor.

## Devoluciones

| Quién | Qué dijo | Acción | Responsable |
| :-- | :-- | :-- | :-- |
| | | | |
