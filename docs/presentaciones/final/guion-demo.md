# Presentación final — guion de la demo (20 minutos)

> **Provisorio.** Supone que el circuito de préstamo completo (solicitud, aprobación, entrega y devolución), las notificaciones y el horario por sede ya tienen pantalla. Si al final algo no está, se reemplaza por la escena equivalente de `docs/pruebas/recorrido-funcional.md` y se dice en voz alta qué falta.
> **Hilo conductor:** un solo préstamo, de punta a punta, contado como una historia: *Lucía necesita una cámara para un rodaje de la materia [asignatura]*.

## Preparación

- Base cargada con un script de datos de demostración (como `demo/seed_demo.py`, ampliado con asignaturas, un préstamo ya entregado y uno demorado). Usuarios ficticios `@example.com`; credenciales fuera del repo.
- Fechas: correr el script la mañana de la presentación, porque las reglas de 24 h y del horario dependen del día.
- Tres ventanas: **estudiante** (normal), **admin** (privada), **docente** (otro navegador). Zoom 125 %, tema claro.
- Correo: usar un servidor de prueba local (Mailpit o similar) en una pestaña, para mostrar que el aviso llega.
- Video de respaldo grabado con exactamente este recorrido.

## Escenas

| # | Min. | Quién maneja | Escena | Requisitos |
| :-- | :-- | :-- | :-- | :-- |
| 1 | 20:00 → 23:00 | P1 | Cuenta nueva | USR-01, USR-05 |
| 2 | 23:00 → 28:00 | P2 + P3 | La solicitud | PRE-01…07, PRE-05 |
| 3 | 28:00 → 33:00 | P3 | Aprobación y mostrador | PRE-10, PRE-13, PRE-15, PRE-18, PRE-20, NOV-04 |
| 4 | 33:00 → 37:00 | P4 + P5 | Espacios y avisos | RES-01…05, NOV-02, NOV-03 |
| 5 | 37:00 → 40:00 | P1 | Superadmin y sedes | GLO-01…03 |

### 1. Cuenta nueva (3 min)
1. Registro de una estudiante nueva con teléfono obligatorio → "Pendiente de aprobación"; intenta entrar y no puede.
2. La admin de Ushuaia la aprueba desde Pendientes.
> *Mensaje:* validación manual y jurisdicción por sede.

### 2. La solicitud (5 min)
1. Lucía busca "cámara" y filtra por categoría; abre el detalle de una cámara con el mini-calendario de disponibilidad.
2. Agrega cámara y trípode al carrito → **Continuar con la solicitud**.
3. Formulario: deja vacía la asignatura → el formulario la marca en rojo (PRE-04). Elige fechas: intenta 6 días → no deja (PRE-07). Elige retiro mañana dentro del horario y devolución a 3 días; acepta términos; envía.
4. *(Si hay tiempo)* Agrega un equipo de alta gama → pide el PDF de la resolución (PRE-05).
5. Mis Solicitudes: la orden figura **Pendiente**.

### 3. Aprobación y mostrador (5 min)
1. Docente: ve la solicitud de su asignatura y deja un comentario, sin botones de aprobar (PRE-20).
2. Admin: Bandeja de validaciones → abre la orden, ve el comentario del docente, **ajusta la hora de retiro** y aprueba; el sistema asigna unidades físicas (PRE-18, PRE-10).
3. Lucía: la campanita muestra el cambio de horario como aviso crítico (NOV-04).
4. Admin: Gestión de entregas → **entrega** (la unidad pasa a "En uso") → **devolución** con observación "lente con polvo" (PRE-13).
5. Control de stock → historial de esa unidad con la observación (PRE-12). Mostrar un préstamo **demorado en rojo** precargado.

### 4. Espacios y avisos (4 min)
1. Docente reserva el Aula-Estudio; con menos de 24 h aparece el aviso con el correo del laboratorio.
2. Dos estudiantes piden la misma franja; la admin aprueba una y la otra se descarta (RES-05).
3. Comunicado de sede (NOV-02) y aviso de vencimiento en el correo de prueba (NOV-03).

### 5. Superadmin y sedes (3 min)
1. Superadmin: cambia de sede, ve los dos inventarios.
2. Parámetros: horario por sede, cambio con motivo e historial.
3. Estudiante de Río Grande: no ve nada de Ushuaia.
> *Cierre:* "Todo lo que vieron respeta la sede del usuario, y cada regla se puede cambiar sin programar".

## Plan B

| Si pasa… | Hacemos… |
| :-- | :-- |
| Un error en una escena | Se cuenta qué debería pasar y se sigue con la próxima; nada de depurar en vivo |
| Se cae el backend o la base | Un reinicio; si no vuelve en 30 s, video |
| Falla la red o el proyector | Video desde el pendrive o la notebook de respaldo |
| Se acaba el tiempo | La escena 4 se reduce a un solo paso (aprobación de espacio) |

## Lista de control (30 minutos antes)

- [ ] Backend sin `--reload`, frontend levantado, base recién cargada.
- [ ] Tres sesiones abiertas en las ventanas correctas.
- [ ] Servidor de correo de prueba abierto.
- [ ] Notificaciones del sistema operativo silenciadas; batería conectada.
- [ ] Video de respaldo abierto y pausado.
