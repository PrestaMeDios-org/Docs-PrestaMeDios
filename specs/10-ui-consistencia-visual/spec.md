# SPEC-10 — Consistencia visual de la interfaz

| Campo | Valor |
| --- | --- |
| **ID** | SPEC-10 |
| **Perfil responsable** | Perfil 1 — Identidad, Usuarios, Permisos, Configuración Global y Despliegue (transversal al frontend) |
| **Estado** | `EN REVISIÓN` — 2026-11-14. Entrega 1 enviada por PR (plan §2); falta el aval de los Perfiles 2 a 5 (U1…U4) y la aprobación. Lo que queda sin hacer está en §1.5 (entrega 2) |
| **Versión** | 0.23.1 |
| **Requisitos cubiertos** | GLO-06 (tema claro/oscuro, menú lateral colapsable y accesibilidad de la interfaz) y la parte de usabilidad del diagnóstico del ERS (§ problemática) |
| **Responde a** | Recorrido funcional con la cliente del 2026-11-10 (DT-31 y DT-32, ya resueltas, mostraron que faltaba una base visual común) |
| **Depende de** | Frontend `develop` (`6ae5db4`) y backend `develop` (`1c89c53`, cabeza `0019`). El backend sólo se toca por la portada MOMENTÁNEA M-02 (§4.7) |
| **Módulos afectados** | Frontend: `theme.ts`, `index.css`, `components/ui`, `components/layout` y, en la Fase B, las pantallas de cada `features/<dominio>` |
| **Módulos ajenos** | En la Fase B se tocan pantallas de los Perfiles 2, 3, 4 y 5 **sólo en su presentación** (sin cambiar servicios, tipos ni llamadas a la API). Va como coordinación (§11) y requiere el aval de cada perfil |
| **Constitución** | v1.1.0 |
| **Fuente de verdad funcional** | `docs/ERS.md` (GLO-06 y su caso de uso "Personalización de interfaz y accesibilidad") |
| **Plan y tareas** | `specs/10-ui-consistencia-visual/plan.md` y `tasks.md` (entrega 1) |

> **Modo de trabajo (Perfil 1, 2026-11-12 al 2026-11-14):** el spec se completó recorriendo la app, y los cambios se hicieron en la rama `feat/ui-consistencia` del frontend (y del backend, sólo para M-02), a pedido del Perfil 1. El 2026-11-14 se envía la **entrega 1** con lo hecho (V-01, V-02, V-04…V-21, M-01…M-04) en un PR por repositorio (plan §2). Los PR no se mergean a `develop` sin el aval de cada perfil sobre sus pantallas (§11, U1…U4). Lo que el spec prevé y todavía no está hecho queda en §1.5.

> **Desvío del flujo SDD (D-08).** `AGENTS.md` §4 pide el spec `APROBADO` antes de escribir código de aplicación. En esta entrega el código se escribió **durante** el relevamiento, con el spec en `BORRADOR` y luego `EN REVISIÓN`, a pedido del Perfil 1, para poder mostrar cada cambio funcionando. Es un desvío acordado para este spec, **no un precedente**: los PR quedan abiertos sin mergear hasta la aprobación del spec y los avales (§11), y si un perfil rechaza un cambio se saca del PR. La entrega 2 (§1.5) sigue el flujo normal: spec aprobado, plan y después código.

> **Numeración:** el 07 está reservado para `assistant` (Perfil 5) y el 09 es el último aprobado, así que este spec es el 10. Como es transversal, usa prefijos propios (como `AC-L…` de `loans` o `AC-S…` de `spaces`): `AC-U01…`, `RN-U01…`, `EC-U01…`, `NFR-U01…`. Los hallazgos del relevamiento son `V-01…`. Las decisiones empiezan en `D-01`.

---

## 0. Resumen ejecutivo

Cada perfil construyó sus pantallas por su cuenta y la interfaz quedó con piezas que resuelven lo mismo de formas distintas: calendarios diferentes en inventario, préstamos y espacios; modales propios; tarjetas, mensajes de validación y errores con estilos distintos. Este spec **pule la identidad actual** (bordó institucional, tipografía Outfit, tema claro/oscuro) sin cambiarla, y la vuelve consistente.

- **Fase A — Base visual común.** Se completan los tokens de `theme.ts` (espaciado, radios, sombras, tipografía) y se publican en `components/ui` los componentes que hoy están repetidos: tarjeta, modal, calendario, campo con mensaje de validación, aviso de error/éxito, insignia de estado, estado vacío y de carga.
- **Fase B — Adopción por pantalla.** Cada pantalla reemplaza sus piezas propias por las comunes y se corrigen los defectos visuales del relevamiento (§2.3). En la entrega 1 va en un solo PR de frontend con los cambios listados por dominio, y cada perfil avala los suyos (plan §2).

Se mantiene la técnica actual: **estilos inline con `useC()`** y tokens en `theme.ts`. No se adopta Tailwind (D-02).

---

## 1. Alcance

### 1.1 Dentro del alcance

| # | Capacidad | Requisitos | Fase |
| --- | --- | --- | --- |
| A1 | Tokens de diseño completos en `theme.ts`: colores (ya existen), espaciado, radios, sombras y escala tipográfica, iguales en claro y oscuro | GLO-06 | A |
| A2 | Componentes compartidos en `components/ui` (lista final según §2.3): `Card`, `Modal`, `Calendar`, `Field` (etiqueta + ayuda + error), `Alert`, `Badge` de estado, `EmptyState`, `Spinner` | GLO-06 | A |
| A3 | Mensajes de validación uniformes: dónde aparecen, color, ícono y momento (al salir del campo / al enviar) | GLO-06, P5 | A |
| A4 | Layout: sidebar colapsable, navbar y contenedor de página con márgenes y ancho máximo comunes; comportamiento en pantallas chicas | GLO-06 | A |
| A5 | **Manual de uso por rol (MOMENTÁNEO, M-01):** el botón "?" de la barra superior abre un modal con las tareas principales del rol de la sesión (§4.5). Primera entrega del spec | Sin requisito (RN-U02); cada tarea cita el suyo | A |
| B1 | Adopción de A1…A4 en cada pantalla y corrección de los hallazgos `V-NN` | GLO-06 | B |

### 1.2 Fuera del alcance

| Capacidad | Destino |
| --- | --- |
| Cambiar flujos, reglas de negocio, textos funcionales o llamadas a la API | Spec del perfil dueño de cada módulo |
| Cambio de identidad (paleta, tipografía o logo nuevos) | D-03: se pule la actual |
| Migrar a Tailwind u otra librería de estilos o componentes | D-02 |
| Pantallas que todavía no existen (mostrador de préstamos, asistente IA) | Las construye cada perfil ya con la base de la Fase A |

### 1.3 Regla de alcance: sin requisitos nuevos

Este spec es **estético**: no agrega requisitos funcionales ni casos de uso al ERS.

- **RN-U01.** Todo cambio que se vea como funcionalidad nueva se contrasta antes con los requisitos (`docs/ERS.md` §3) y los casos de uso. Si tiene respaldo, se cita el requisito.
- **RN-U02.** Si no tiene respaldo, se implementa como **MOMENTÁNEO**: aislado en sus propios archivos, conectado a la app en un único punto y marcado con el comentario `// MOMENTÁNEO (SPEC-10, RN-U02): <qué es>`, de modo que sacarlo sea borrar esos archivos y esa línea. Se lista en §1.4 y no se agrega al ERS.
- **RN-U03.** Un elemento MOMENTÁNEO no llama a la API ni guarda datos: sólo presenta información de lo que ya existe. **Excepción** sólo con aprobación explícita del Perfil 1, listada en §1.4 con su forma de sacarlo; el backend va aislado (tabla y archivo propios, migración que sólo crea y borra esa tabla) y no modifica tablas, esquemas ni enums existentes.

### 1.4 Elementos MOMENTÁNEOS

| # | Elemento | Por qué no tiene respaldo | Cómo se saca |
| --- | --- | --- | --- |
| M-02 | **Portada de comunicado** (§4.7): quien publica elige uno de los cuatro temas o sube una foto; si no elige, el color es automático (V-10). Excepción a RN-U03 aprobada por el Perfil 1 el 2026-11-12; **falta que la confirme el Perfil 5**, porque el backend queda dentro de su módulo (U5) | NOV-02 no habla de imágenes ni temas; es la propuesta U5 | Backend: `alembic downgrade` de `0020_notifications_portada` (borra sólo `comunicados_portada`), borrar `app/modules/notifications/portada.py`, `tests/notifications/test_portada.py` y las líneas marcadas en `main.py` y `alembic/env.py`. Front: borrar `features/notifications/portada/` y las líneas marcadas en `ComunicadoForm.tsx`, `ComunicadosList.tsx` y `NewsPage.tsx` |
| M-03 | Vista de Control de Stock por locker (V-17): selector "Ver por: Equipo / Locker" | PRE-12 guarda el locker de cada unidad, pero ningún requisito pide verlas agrupadas por locker | Borrar `features/inventory/components/LockerTable.tsx`, `agruparPorLocker` y lo que sólo usa ella en `services/stockVista.ts` (con sus tests), y el selector marcado en `StockPage.tsx` |
| M-04 | Texto del "Reglamento de uso" en el globo de Términos y Condiciones (V-19) | Sale del diseño de Figma, no del Reglamento (Resolución CICSE N° 056/2023), que no está cargado en el sistema. La casilla y "Acepto los Términos y Condiciones" sí tienen respaldo (PRE-03) | Reemplazar `REGLAMENTO_USO` en `features/loans/components/TerminosPrestamo.tsx` por los artículos del Reglamento cuando se tengan |
| M-01 | Manual de uso por rol (botón "?", §4.5) | Ningún requisito ni caso de uso lo pide. GLO-06 y su caso de uso cubren sólo el tema claro/oscuro y colapsar el menú lateral | Borrar `components/layout/manualDeUso.ts` y `ManualDeUsoModal.tsx`, y la línea marcada en `App.tsx`. El botón "?" ya existía en `Navbar.tsx` antes de este spec |

### 1.5 Pendiente para la entrega 2

<!-- PENDIENTE SPEC-10 (entrega 2): buscar "PENDIENTE SPEC-10" para encontrar cada punto. Revisar antes de aprobar la entrega 2. -->

> **Nota para revisar más adelante.** La entrega 1 (2026-11-14) lleva lo que se fue pidiendo al recorrer la app. Estos puntos del alcance (§1.1) **no están hechos** y quedan para una entrega 2, con su propio plan y PR. Cada sección afectada tiene un comentario `PENDIENTE SPEC-10` que apunta acá.

| # | Qué falta | Sección | Por qué quedó afuera |
| --- | --- | --- | --- |
| P-1 | Escala de espaciado, radios, sombras y tipografía en `theme.ts` (A1). Hoy cada pantalla los escribe a mano; sólo se agregaron `premium`/`premiumBg` | §4.1 | Conviene definirla mirando todas las pantallas ya pulidas, y aplicarla toca casi todos los archivos |
| P-2 | Mensajes de validación uniformes (A3, V-03): dónde, color, ícono y momento | §4.3 | No se relevó todavía; necesita recorrer los formularios de cada perfil |
| P-3 | Layout común (A4): contenedor de página con márgenes y ancho máximo, y pantallas chicas | §4.4 | Ídem |
| P-4 | Componentes de A2 que no existen: `Card`, `Field`, `Alert`, `EmptyState`, `Spinner`; y `Modal` a `components/ui` | §4.2 | `Modal` se adelantó en el frontend PR #29 (en revisión), que espera el aval U1 del Perfil 2 (D-06); el resto depende de P-1 |
| P-5 | `body` de `index.css` con colores fijos del tema claro (G-3) | §2.2 | Va con P-1 |
| P-6 | Paginación de pendientes de espacios en el backend (U7) | §11 | Es del Perfil 4; hoy el front pagina en memoria |
| P-7 | Administración de lockers con nombre (U6) y portada elegible en el ERS (U5) | §11 | Necesitan sumarse al ERS y un spec del perfil dueño |

---

## 2. Estado actual

### 2.1 Verificado en `develop` (frontend `6ae5db4`, 2026-11-12)

| Elemento | Estado |
| --- | --- |
| Tema | `src/theme.ts`: tokens de **color** claro y oscuro (`C_LIGHT`, `C_DARK`), `ThemeCtx` y `useC()`. No hay tokens de espaciado, radio, sombra ni tipografía: se escriben a mano en cada componente |
| Estilos | Casi todo con `style={{…}}` inline (p. ej. 84 en `SpacesPage.tsx`, 36 en `Navbar.tsx`). Tailwind 4 está instalado e importado en `index.css` pero ningún componente usa `className` |
| `index.css` | Importa Outfit e Inter de Google Fonts; `body` con colores fijos de tema claro (`#ECEAE7`, `#1A1A1A`) que no siguen el tema oscuro |
| `components/ui` | `Avatar`, `Badge`, `Button` (`primary`, `ghost`, `danger`), `Form`, `Input`, `icons` |
| Modal | `features/inventory/components/Modal.tsx` (del Perfil 2) lo reusan `loans`; `spaces` arma su propio overlay en `SpacesPage.tsx` |
| Calendarios | Tres resoluciones distintas: `inventory/components/MiniCalendario.tsx` (grilla mensual), `spaces/components/CalendarGrid.tsx` (grilla semanal) y `<input type="date">` nativo en `loans/SolicitudForm.tsx`, `loans/AprobarOrdenModal.tsx` y `spaces/SpacesPage.tsx` |

### 2.2 Brechas

| # | Brecha |
| --- | --- |
| G-1 | No hay tokens fuera del color: cada pantalla decide márgenes, radios y tamaños de letra |
| G-2 | Componentes repetidos con aspecto distinto (modal, calendario, tarjeta, mensajes) |
| G-3 | `body` no sigue el tema oscuro |
| G-4 | Pantallas armadas con piezas propias que no siguen el resto: confirmaciones nativas del navegador, listas planas sin filtros y datos que el admin necesita pero no veía (relevamiento §2.3) |

### 2.3 Relevamiento visual (app levantada, 2026-11-12)

> Se completa recorriendo cada pantalla con cada rol. Cada hallazgo indica pantalla, qué se ve, qué se espera y qué componente común lo resuelve.

| # | Pantalla / componente | Rol | Qué se ve | Qué se espera | Resuelve | Fase |
| --- | --- | --- | --- | --- | --- | --- |
| V-01 | Selección de fechas (inventario, préstamos, espacios, novedades) | Todos | Cuatro resoluciones distintas: mini-calendario propio en el detalle del equipo, `<input type="date">` nativo en Solicitar equipos y Aprobar orden, `date` + `time` nativos en el bloqueo de espacios y `datetime-local` en "Vence" de Novedades. Al solicitar no se ve la disponibilidad que mostraba el detalle (observación de la cliente) | Un único selector (`DatePicker`) sobre una grilla común (`GrillaMes`) que también usa el mini-calendario; en Solicitar equipos muestra la disponibilidad del pedido, el rango retiro→devolución y apaga lo que supera el plazo (§4.6) | A2 | **Hecho (local)** |
| V-02 | Botón "?" de la barra superior (`Navbar.tsx:275`) | Todos | El botón existe pero no hace nada: `App.tsx:184` le pasa `onHelp={() => {}}` | Abre el "Manual de uso" del rol de la sesión (capturas de referencia del Perfil 1, 2026-11-12) | A5 | A |
| V-04 | Tarjeta del catálogo (`EquipmentCard.tsx`) | Todos | El chip "Alta Gama" agrega una línea y desnivela "uds." y el carrito respecto de las otras tarjetas de la fila; la descripción no tiene tope de líneas; "5/5 uds." se lee poco; los botones editar/dar de baja (admin) flotan sin borde sobre la imagen | Tarjeta en columna de altura completa con el pie pegado abajo; descripción en 2 líneas con "…" (texto completo en `title`); "**5** de 5 disponibles"; "Alta Gama" en la línea del código; botones con fondo de tarjeta, borde y sombra suave. La imagen no cambia: siempre habrá una cargada (Perfil 1) | A2 | **Hecho (local)** |
| V-05 | Lista del catálogo (`CatalogPage.tsx`) | Todos | La fila no muestra que el equipo es de Alta Gama | Chip "Alta Gama" junto al nombre (mismo componente que la tarjeta) y "**5** de 5 disponibles" | A2 | **Hecho (local)** |
| V-06 | Violeta de Alta Gama fijo en el código | Estudiante, Docente | `#5A2D82` y `#EDE0FF` escritos a mano en `Navbar.tsx` (botón del carrito) y `loans/CarritoPanel.tsx`; no cambian en modo oscuro | Usan los tokens `premium`/`premiumBg`; el número del contador va con `C.card` sobre `premium` para leerse en oscuro | A1 | **Hecho (local)** |
| V-07 | Detalle del equipo (`EquipmentDetailModal.tsx`, `AgregarAlPedido.tsx`, `Modal.tsx`) | Todos | Una sola columna con párrafos sueltos ("todo volando"); la imagen al 100 % del ancho sin tope de alto alarga el modal; "Agregar al pedido" era un `<button>` sin estilos y quedaba fuera de la vista; "Tipo: Especial/Común" no coincide con "Alta Gama" de la tarjeta | Dos columnas (datos \| mini-calendario) que pasan a una en pantallas angostas; imagen entera con alto máximo de 220 px; "Ver video instructivo" como botón secundario, sólo si hay video; plazo, disponibles y locker en recuadros; chip "Alta Gama" en el encabezado; pie fijo con "Cerrar" y "Agregar al pedido" (bordó, verde al agregar). `Modal` suma props opcionales (`subtitulo`, `extraTitulo`, `conCerrar`, `pie`): sin ellas se ve igual que antes | A2 | **Hecho (local)** |
| V-08 | Sábados y domingos en los selectores de fecha | Todos | Nada los distingue; sólo aparece un aviso después de elegir | En Solicitar equipos y Aprobar orden se ven atenuados con la leyenda "El laboratorio normalmente no atiende sábados ni domingos", y se pueden seguir eligiendo (no es una regla nueva, §4.6) | A2 | **Hecho (local)** |
| V-09 | Calendario de Reservas de Espacios (`CalendarGrid.tsx`) | Todos | Botones ‹ › sin borde, días "Lun…Dom", el día elegido sólo con borde; distinto del resto | Mismo estilo que `GrillaMes`: botones con borde, iniciales L…D, día elegido en bordó lleno, ocupado/parcial con el color del texto. Se conserva su lógica (ocupación, bloqueos, motivo al pasar el mouse, GLO-04) | A2 | **Hecho (local)** |
| V-10 | Comunicados de Novedades (`ComunicadosList.tsx`) | Todos | Lista de recuadros blancos de ancho completo, todos iguales; el contenido largo se muestra entero | Grilla de tarjetas con una "foto" de patrón de circuito en SVG (`BannerComunicado.tsx`, sin imágenes externas); el color sale de datos que ya existen (`services/tema.ts`): rojo global, azul Ushuaia, verde Río Grande, amarillo si vence en 48 h. Chip de alcance y fecha, título destacado, contenido en 3 líneas con "Leer más", autor/vencimiento y acciones al pie. Elegir el tema o subir una imagen propia queda fuera (U5, §11) | A2 | **Hecho (local)** |
| V-11 | Confirmaciones y motivos (`window.confirm` / `window.prompt`) | Todos | Seis acciones usaban los cuadros nativos del navegador: Archivar comunicado (P5), Cancelar solicitud (P3), Cerrar todas mis sesiones (P1), Dar de baja equipo y cambiar estado de unidad (P2), motivo al rechazar/suspender una cuenta (P1) y motivo al rechazar una reserva (P4). Se ven fuera de estilo, y el panel embebido de la app de escritorio los bloquea y devuelve "Cancelar" sin mostrarlos: **la acción no hacía nada** (reportado con Archivar) | Diálogo propio en `components/ui/Dialogo.tsx` (`DialogoProvider`, `useConfirmar`, `usePedirTexto`), con título, mensaje, botón principal (rojo en acciones destructivas), `Esc` y clic fuera para cancelar. Mismos textos y mismas validaciones (p. ej. motivo de 3 caracteres) | A2 | **Hecho (local)** |
| V-12 | Turnos del día en Reservas de Espacios (`SpacesPage.tsx`) | Todos | Título "Franjas del 2026-11-12 (09:00–16:00)" y botoncitos chicos con un checkbox en una tarjeta grande: mucho espacio vacío; sin día elegido, un texto suelto | Título "Miércoles, 18 de noviembre" y subtítulo con el horario; turnos como tarjetas en grilla con la hora grande y su estado (Libre, Elegido, Con solicitud pendiente, Ocupado, Bloqueado); leyenda de colores; sin día, un estado vacío con ícono. Misma lógica de selección | A2 | **Hecho (local)** |
| V-13 | Confirmar solicitud de reserva (`SpacesPage.tsx`) | Estudiante, Docente | Sólo muestra espacio, fecha y horarios; el laboratorio no sabe para qué es la reserva | Campos **Materia** y **Descripción** (opcionales), guardados juntos en el `motivo` que la API ya acepta (RES-02, `ReservaEspacioCreate.motivo`, hasta 500; `services/motivo.ts`). El texto ("Taller — Rodaje") se ve en Mis reservas y en las solicitudes pendientes del admin. No cambia el backend ni agrega un campo nuevo | A2 | **Hecho (local)** |
| V-14 | Bandeja de Validaciones (`BandejaPage.tsx`) | Admin local, Superadmin | Una tarjeta por orden, con el texto en renglones sueltos | Formato del prototipo del equipo, mezclado con lo actual: tres tarjetas de resumen (pendientes, aprobadas hoy, con observación del docente), pestañas por estado (las de siempre) y por tipo (Estudiantes, Docentes, Especiales) y una tabla con solicitud, solicitante con iniciales, equipo con foto y código, asignatura, período con días, observación del docente ("Ver obs."), estado y acciones (`BandejaTabla.tsx`, `services/bandejaVista.ts`). El tipo se **deduce**: especial si lleva alta gama o aval; si no, estudiante con asignatura y docente sin ella. DNI y año del solicitante y el nombre de la materia no vienen en la orden: se muestran sede y fecha, y "Asignatura N". Mismas acciones y diálogos | A2 | **Hecho (local)** |
| V-15 | Alta y edición de equipo (`EquipmentFormModal.tsx`, `UnidadFormModal.tsx`) | Admin local, Superadmin | No se sabe qué campo cae dónde (código, nombre, marca, modelo); un clic fuera del diálogo lo cierra y se pierde lo cargado | Vista previa al costado, en vivo: la misma tarjeta del catálogo, la ficha (marca, modelo, categoría, plazo) y las unidades como se verían en Control de Stock. El diálogo tiene X arriba y sólo se cierra con la X, Cancelar o Crear; no con clic afuera ni con Escape (también el de unidad). Sin campos ni reglas nuevas (PRE-12, PRE-19) | A3 | Hecho en local |
| V-16 | Control de Stock (`StockTable.tsx`, `UnidadesRow.tsx`) y chips de tipo de la Bandeja | Admin local, Superadmin | Filas planas, sin imagen; las unidades desplegadas eran una tabla con botones grandes y rellenos | Miniatura de la imagen del equipo junto al nombre, categoría con su color, lockers en texto por rangos ("2–6"), Alta Gama con el chip violeta, barra de disponibles y acciones con íconos; la fila entera despliega. Unidades con resumen por estado, agrupadas por sede y ordenadas por código, locker en texto y acciones chicas. Chips de categoría arriba, como en el catálogo, que sólo filtran lo cargado. Los chips de tipo de la Bandeja (V-14) pasan al estilo de los filtros del catálogo. Mismas acciones y reglas (PRE-12, PRE-14) | A3 | Hecho en local |
| V-17 | Control de Stock, opción "Ver por: Equipo / Locker" (`StockPage.tsx`, `LockerTable.tsx`) | Admin local, Superadmin | Sólo había vista por equipo | **MOMENTÁNEO**: alternativa de vista que agrupa las mismas unidades por locker (1–7, PRE-12; los vacíos también y "Sin locker" si hay). Cada locker despliega sus unidades con equipo, código, serie, sede, estado y las mismas acciones de PRE-14. Respeta búsqueda, sede y chips de categoría. No hay requisito que pida esta agrupación; se borra quitando `LockerTable.tsx` y el selector | A3 | Hecho en local |
| V-18 | Mis Solicitudes (`loans/MisSolicitudesPage.tsx`, `loans/services/misSolicitudesVista.ts`) y Reservas de Espacios (`spaces/SpacesPage.tsx`, `spaces/components/MisReservas.tsx`) | Estudiante, Docente | "Mis reservas" de espacios estaba al pie del calendario de Reservas de Espacios, separada del panel de solicitudes; solicitudes y reservas en tarjetas grandes, y las reservas ocultaban las canceladas y rechazadas | Mis Solicitudes con pestañas "Equipamiento" y "Espacios" (con su cantidad), chips por estado (Todas, Pendientes, Aprobadas y Rechazadas de USR-06, más Canceladas) y una fila compacta por solicitud: qué se pidió, retiro → devolución o fecha y horario, estado y "Cancelar" con el diálogo propio (V-11). Las solicitudes con varios equipos o motivo se despliegan. Las reservas muestran también las canceladas y rechazadas, primero las próximas y al final, en gris, las que ya pasaron. Reservas de Espacios ya no muestra la lista y, al enviar, avisa que se siguen en Mis Solicitudes. Mismos datos y reglas de cancelación; es el panel de USR-06 | A3 | Hecho en local |
| V-19 | Casilla de Términos y Condiciones de la solicitud (`loans/components/SolicitudForm.tsx`, `loans/components/TerminosPrestamo.tsx`) | Estudiante, Docente | "Acepto la normativa de préstamos del laboratorio." sin ver qué se acepta | Según la opción del Figma con globo: "Acepto los **Términos y Condiciones**" (texto de PRE-03); el enlace muestra el "Reglamento de uso" numerado y la referencia a la Resolución CICSE N° 056/2023 al pasar el mouse o al tocarlo (se cierra con Escape o tocando afuera). Misma validación y mismo envío. **MOMENTÁNEO el texto** de las cuatro reglas (`REGLAMENTO_USO`): sale del diseño, no del Reglamento, que no está cargado en el sistema; se reemplaza cuando se tengan sus artículos | A3 | Hecho en local |
| V-20 | Directorio de Gestión de Usuarios (`users/pages/UsersPage.tsx`) | Admin local, Superadmin | Todas las cuentas mezcladas en una tabla plana; rol y estado en desplegables dentro de una tarjeta; sin forma de elegir el orden | Pestañas subrayadas (Pendientes, Directorio, Nueva cuenta) como en el resto. En Directorio: chips por rol con su cantidad (Todos, Estudiantes, Docentes, Administradores locales y, para el superadmin, Superadministradores), buscador, estado en un desplegable chico y "Ordenar" por apellido (A→Z o Z→A) o por fecha de alta, que el backend ya acepta (`ordenar_por`, `direccion`). Tabla con iniciales, rol y estado como chips de color. Mismos filtros de USR-04, mismo alcance de sede y mismas acciones | A3 | Hecho en local |
| V-21 | Reservas de Espacios, vista de administrador (`spaces/SpacesPage.tsx`, `spaces/components/SolicitudesPendientesEspacios.tsx`, `spaces/services/reservasDelDia.ts`, `spaces/services/pendientesVista.ts`, `spaces/components/CalendarGrid.tsx`) | Admin local, Superadmin | El admin veía "Ocupado" sin saber quién ni para qué; una solicitud pendiente de otra persona aparecía como "Libre"; "Solicitudes pendientes (aprobación manual)" era una lista de renglones chicos con el motivo pegado ("si — si") | Cada turno reservado muestra el apellido del solicitante y la materia. "Solicitudes pendientes" con su cantidad, agrupadas por día ("Jueves, 19 de noviembre · 5 solicitudes") y ordenadas por hora, con letra más grande: horario, solicitante y espacio, materia y descripción por separado, y Aprobar/Rechazar más grandes (RES-05). **Para muchas solicitudes:** cada día del calendario muestra cuántas pendientes tiene el espacio; al tocarlo, la lista muestra sólo las de ese día y espacio, con una barra "Mostrando las de … del … · Ver todas →". Sin día elegido, chips de período (Próximos 7 días · Próximos 14 días · Todas) y selector de espacio, y la lista se pagina de a 10 ("1–10 de 18", ‹ ›). Se probaron y descartaron días plegables, chips por espacio y un tope de 6 por día. Hoy filtra y pagina lo que ya devuelve `GET /reservas?estado=Pendiente` (ver U7). Se probó también una lista "Reservas del día" en el panel del día y se sacó por repetir esta. Los datos ya llegaban al admin (SPEC-08 AC-S14). **El estudiante no ve nada de esto** (RN-30: ni identidad ni materia de otros) | A3 | Hecho en local |
| V-03 | Mensajes de validación de formularios | Todos | Sin relevar | Ver §1.5, P-2 <!-- PENDIENTE SPEC-10 (P-2) --> | A3 | **Entrega 2** |

---

## 3. Actores

Todos los roles (`ESTUDIANTE`, `DOCENTE`, `ADMIN_LOCAL`, `SUPERADMIN`) y las pantallas públicas (login, registro, recuperación). No cambia ningún permiso.

---

## 4. Fase A — Base visual común

### 4.1 Tokens (`theme.ts`)

<!-- PENDIENTE SPEC-10 (P-1): escala de espaciado, radios, sombras y tipografía. -->
_Entrega 2 (§1.5, P-1): escala de espaciado, radios, sombras y tipografía._

**Agregados:** `premium` y `premiumBg` (Alta Gama, PRE-05), en claro (`#5A2D82` / `#EDE0FF`, los valores que ya se usaban) y oscuro (`#C4A0EC` / `#26173A`).

### 4.2 Componentes compartidos (`components/ui`)

Hechos en la entrega 1 (el resto, en §1.5 P-4): <!-- PENDIENTE SPEC-10 (P-4) -->

| Componente | Archivo | Contrato |
| --- | --- | --- |
| `DialogoProvider`, `useConfirmar`, `usePedirTexto` | `components/ui/Dialogo.tsx` | El proveedor envuelve la app. `confirmar({titulo, mensaje?, aceptar?, cancelar?, peligro?})` devuelve `Promise<boolean>`. `pedirTexto({titulo, etiqueta, aceptar?, minimo?, placeholder?})` devuelve el texto, o `null` si se cancela. `Esc` y clic fuera cancelan (V-11) |
| `GrillaMes` | `components/ui/calendario/GrillaMes.tsx` (+ `mes.ts`) | `mes`, `onMes`, `infoDia?(iso)` → `{estado, texto?, elegible?, ayuda?}`, `min?`, `max?`, `seleccionado?`, `rango?`, `onElegir?`, `atenuarFinDeSemana?`, `compacto?`. `estado`: `neutro`, `libre`, `sin`, `fuera`, `cargando` (§4.6) |
| `DatePicker` | `components/ui/DatePicker.tsx` | `value` (ISO), `onChange`, `min?`, `max?`, `infoDia?`, `rango?`, `invalido?`, `placeholder?`, `atenuarFinDeSemana?`, `borrable?`, `pie?` y atributos ARIA. Abre `GrillaMes` en un desplegable |
| `SelectorHora` y `horasEntre` | `components/ui/SelectorHora.tsx` | `value`, `onChange`, `opciones?` (por defecto `horasEntre()`, cada 30 min), `invalido?`, `vacio?` y atributos ARIA |
| Ícono `clock` | `components/ui/icons.tsx` | Se suma a `Ico` |

**Agregados:** `features/inventory/components/AltaGamaBadge.tsx` (sin props), que usan la tarjeta y la lista del catálogo. Está en `inventory` porque sólo lo usa ese módulo; pasa a `components/ui` si lo adopta `loans` (V-06).

### 4.3 Validación y mensajes

<!-- PENDIENTE SPEC-10 (P-2) -->
_Entrega 2 (§1.5, P-2)._

### 4.4 Layout

<!-- PENDIENTE SPEC-10 (P-3) -->
_Entrega 2 (§1.5, P-3)._

### 4.5 Manual de uso por rol (A5, V-02) — MOMENTÁNEO (M-01)

> No tiene requisito ni caso de uso propio (§1.4): se implementa aislado y marcado según RN-U02, y sólo describe lo que ya está en el ERS.

**Comportamiento.** El botón "?" (`title="Ayuda y manual de uso"`) abre un modal. El contenido depende del **rol de interfaz de la sesión** (`uiRole(rol)` de `features/auth/roles.ts`): no hay selector para cambiarlo. Se cierra con la X, con "Entendido", con `Esc` y al hacer clic fuera.

**Estructura del modal** (según las capturas de referencia):

1. Encabezado: título **"Manual de Uso"** y subtítulo "Vista activa: \<rol\>", con el botón X a la derecha; separador debajo.
2. Recuadro del rol, con fondo y borde del color del rol: título "Vista \<rol\>" y una lista numerada; cada número va en un cuadrado redondeado del color del rol, con el número en blanco.
3. Nota informativa en gris con ícono ⓘ (texto en D-04).
4. Botón principal "Entendido", de ancho completo, bordó (`Button` `primary`).

**Colores por rol** (tokens existentes de `theme.ts`, ya resueltos para claro y oscuro):

| Rol de UI | Roles del backend | Título y números | Fondo del recuadro |
| --- | --- | --- | --- |
| Estudiante | `ESTUDIANTE` | `C.mine` (azul) | `C.mineBg` |
| Docente | `DOCENTE` | `C.available` (verde) | `C.availableBg` |
| Admin | `ADMIN_LOCAL`, `SUPERADMIN` | `C.crimson` (bordó) | `C.crimsonLight` |

**Contenido.** Las tareas de referencia, cada una contrastada con el ERS (RN-U01) y con su estado en `develop`:

| Rol | # | Tarea (texto de referencia) | Requisito / caso de uso | Pantalla actual | Estado en `develop` |
| --- | --- | --- | --- | --- | --- |
| Estudiante | 1 | Explorar el catálogo de equipos disponibles | PRE-01, PRE-02 | Catálogo de Equipos | Implementado |
| | 2 | Ver ficha completa y specs de cada equipo | PRE-01 | Detalle del equipo | Implementado |
| | 3 | Solicitar préstamo con aprobación docente | PRE-03, PRE-06, PRE-20 | Carrito / solicitud | Implementado |
| | 4 | Reservar Isla de Edición | RES-01, RES-02 | Reservas de Espacios | Implementado |
| | 5 | Hacer seguimiento de tus solicitudes activas | USR-06 | Mis Solicitudes | Implementado |
| | 6 | Cancelar solicitudes pendientes o aprobadas | USR-06, RES-03 | Mis Solicitudes | Implementado |
| | 7 | Consultar novedades e información institucional | NOV-01, NOV-02 | Novedades | Implementado |
| Docente | 1 | Revisar solicitudes de estudiantes pendientes | PRE-20 | Validaciones Pendientes | Implementado |
| | 2 | Aprobar o rechazar préstamos de tu materia | PRE-20 | Validaciones Pendientes | Implementado |
| | 3 | Ver historial de solicitudes procesadas | PRE-20, USR-07 | Historial Solicitudes | Implementado |
| | 4 | Acceder al catálogo para referencia | PRE-01 | Catálogo de Equipos | Implementado |
| | 5 | Consultar reservas de espacios del instituto | RES-01 | Reservas de Espacios | Implementado |
| | 6 | Recibir notificaciones de nuevas solicitudes | NOV-04 (campanita) | — | **Pendiente** (Perfil 5) |
| Admin | 1 | Gestionar entregas y devoluciones en mostrador | PRE-13 | Gestión de Entregas | **Parcial** (Fase 3 de SPEC-05) |
| | 2 | Control de stock físico por sede y locker | PRE-12, PRE-14 | Control de Stock | Implementado |
| | 3 | Validar solicitudes de Alta Gama y docentes | PRE-05, PRE-09, PRE-10 | Bandeja de Validaciones | Implementado |
| | 4 | Gestionar comportamiento de alumnos con chips | USR-09 y CU de entrega y devolución ("chips contables de comportamiento") | — | **Pendiente** (Perfil 1) |
| | 5 | Calendario maestro de operaciones | PRE-16 | Calendario de Operaciones | Implementado |
| | 6 | Bloquear fechas en el calendario de espacios | RES-04, GLO-04 | Reservas de Espacios | Implementado |
| | 7 | Publicar y editar novedades institucionales | NOV-02 | Novedades | Implementado |

Ninguna tarea agrega funcionalidad: todas describen requisitos que ya están en el ERS. Las pendientes o parciales se muestran según D-05.

**Implementación.** El contenido vive en un solo archivo de datos (`components/layout/manualDeUso.ts`: rol → título, color y tareas), para que cada perfil actualice sus tareas sin tocar el componente. El modal (`components/layout/ManualDeUsoModal.tsx`) es **autocontenido**: el `Modal` de `inventory` no tiene subtítulo ni botón X, y depender de él ataría un elemento MOMENTÁNEO a un módulo del Perfil 2. Cuando exista el `Modal` común de A2 (D-06), se puede pasar a usarlo. `App.tsx` reemplaza `onHelp={() => {}}` por la apertura del modal. No hay llamadas a la API.

### 4.6 Calendario común (A2, V-01)

**Respaldo:** PRE-06 (elegir retiro y devolución "mediante un calendario", con la hora dentro de la franja operativa), PRE-07 (restringir las fechas seleccionables al plazo máximo), PRE-01 (disponibilidad por día), GLO-04 (bloqueos) y NOV-02 (vencimiento del comunicado). No agrega requisitos.

| Pieza | Dónde | Qué hace |
| --- | --- | --- |
| `GrillaMes` | `components/ui/calendario/GrillaMes.tsx` | Mes con ‹ ›, lunes primero, en español. Cada día recibe un estado (`neutro`, `libre`, `sin`, `fuera`, `cargando`), un texto opcional ("5 libres"), si está seleccionado, si está dentro del rango y si se puede elegir. Los colores salen del tema |
| `MiniCalendario` | `inventory` (Perfil 2) | Pasa a dibujarse con `GrillaMes`, sin cambiar lo que muestra |
| `DatePicker` | `components/ui/DatePicker.tsx` | Campo con el formato del resto de los inputs ("dd/mm/aaaa" + ícono); al hacer clic abre `GrillaMes` en un desplegable. `min`/`max`, `infoDia` opcional (disponibilidad), `rango` opcional, `invalido`. Cierra al elegir, con `Esc` y al hacer clic fuera |
| `SelectorHora` | `components/ui/SelectorHora.tsx` | Lista desplegable de horas con el estilo de los inputs, para reemplazar `type="time"` |
| Disponibilidad del pedido | `loans` (Perfil 3) | En Solicitar equipos, cada día muestra las unidades libres del modelo del carrito que menos tiene, considerando la cantidad pedida (mismo `GET /inventory/equipamiento/{id}/disponibilidad`, un pedido por modelo, ventana de 62 días). Los días sin unidades suficientes no se pueden elegir. La devolución marca el rango desde el retiro y apaga los días que superan el plazo del pedido (PRE-07) |

**Sábados y domingos:** se ven atenuados con la leyenda "El laboratorio normalmente no atiende", pero se pueden elegir, igual que hoy (aviso de `SolicitudForm`). Bloquearlos sería una regla de negocio nueva: los días de atención por sede quedaron fuera de SPEC-09 (D-09) y los cierres se cargan como bloqueos (GLO-04).

**Dónde se reemplaza:** Solicitar equipos y Aprobar orden (`loans`, Perfil 3); bloqueo de espacios (`spaces`, Perfil 4); "Vence" de Novedades (`notifications`, Perfil 5: fecha con `DatePicker` + hora con `SelectorHora`; los días anteriores a hoy van en gris y no se eligen, porque el vencimiento tiene que ser futuro, como ya valida `validarComunicado`). El calendario grande de Reservas de Espacios (`CalendarGrid`) no se reemplaza, porque es la grilla de turnos (RES-01); sólo se alinean sus colores con los de `GrillaMes` (V-09).

### 4.7 Portada de comunicado — MOMENTÁNEO (M-02)

> Sin requisito en el ERS (NOV-02 no habla de imágenes). Excepción a RN-U03: guarda datos, aislado según §1.3. Si el equipo lo adopta, pasa a un spec del Perfil 5 y se suma a NOV-02 (U5).

**Datos** (migración `0020_notifications_portada`, cuelga de `0019`): tabla nueva `comunicados_portada` — `comunicado_id` (PK, FK a `comunicados.id`, `ON DELETE CASCADE`), `tema` (`rojo`, `amarillo`, `azul`, `verde` o nulo), `imagen` (bytes, nulo), `tipo_mime`, `actualizado_en`. Un `CHECK` exige tema **o** imagen, nunca los dos. Sin fila = automático (V-10). No se modifican `comunicados` ni `files`.

**API** (`app/modules/notifications/portada.py`, montada en `/api/v1/notifications`):

| Método y ruta | Quién | Qué hace |
| --- | --- | --- |
| `GET /comunicados/portadas?ids=1,2,3` | Quien puede leer esos comunicados | `[{comunicado_id, tema, tiene_imagen, actualizado_en}]` de los que tienen portada (máx. 50 ids, entre 1 y 2³¹−1); los que no puede leer se omiten. Una sola consulta con las reglas de lectura de `notifications` |
| `PUT /comunicados/{id}/portada` `{tema}` | Quien puede editar el comunicado (RN-N5) | Fija el tema y borra la foto |
| `PUT /comunicados/{id}/portada/imagen` (multipart `archivo`) | Ídem | JPEG, PNG o WebP de hasta 5 MB (firma, no extensión); se vuelve a codificar como JPEG de hasta 1600 px, sin metadatos; borra el tema |
| `DELETE /comunicados/{id}/portada` | Ídem | Vuelve a automático |
| `GET /comunicados/{id}/portada/imagen` | Quien puede leer el comunicado | La foto, con los encabezados de `respuesta_descarga`; `404` si no hay |

Fuera de alcance o inexistente → `404` (P4.5); un estudiante o docente que intenta editar → `403`. Errores de la foto con los mismos códigos que `files`, todos `422`: `TIPO_ARCHIVO_NO_PERMITIDO`, `ARCHIVO_DEMASIADO_GRANDE`, `IMAGEN_INVALIDA`. `ids` mal formados o fuera del rango de `integer` → `422 IDS_INVALIDOS`. El router se monta **antes** que el de `notifications`, para que `/comunicados/portadas` no lo tome `/comunicados/{comunicado_id}`.

**Dependencia de funciones privadas del Perfil 5.** Para aplicar exactamente las mismas reglas que los comunicados, `portada.py` reusa `_filtro_lectura` (lectura, RN-N3) y `_bloquear_para_editar` (edición, RN-N5) de `notifications/service.py`. Están reunidas en un único bloque al principio del archivo: si el Perfil 5 las renombra o cambia su firma, se ajusta ahí. Se le pide que las exponga como públicas (U4/U5). Observación de la revisión del backend PR #39.

**Tests:** `tests/notifications/test_portada.py` (permisos, alcance, foto, `ids`) y `tests/notifications/test_migracion_0020.py` (cadena con `0019`, el `downgrade` borra sólo `comunicados_portada` y el `upgrade` la recrea con sus restricciones).

**Front** (`features/notifications/portada/`): en el formulario, "Portada" con cinco opciones — Automática, los cuatro colores y "Subir foto" (vista previa antes de publicar). Se aplica después de crear o editar el comunicado. La tarjeta muestra la foto, si no el tema elegido, si no el automático.

---

## 5. Fase B — Adopción por pantalla

Todo cambio en pantallas ajenas es **de presentación**: no cambia servicios, tipos ni llamadas a la API, salvo lo indicado en la última columna. Cada perfil revisa sus archivos en el PR de frontend (plan §2) y da su aval (§11).

| Dominio | Perfil que avala | Hallazgos | Archivos principales | Fuera de lo visual |
| --- | --- | --- | --- | --- |
| Base común y layout | 1 | V-01, V-02, V-06, V-08, V-11 | `components/ui/{Dialogo,DatePicker,SelectorHora}.tsx`, `components/ui/calendario/`, `components/layout/{Navbar,ManualDeUsoModal}.tsx`, `App.tsx`, `theme.ts` | — |
| `inventory` | 2 (U1) | V-01, V-04, V-05, V-07, V-15, V-16, V-17 (M-03) | `EquipmentCard`, `EquipmentDetailModal`, `AgregarAlPedido`, `Modal` (props opcionales), `MiniCalendario`, `EquipmentFormModal`, `UnidadFormModal`, `StockTable`, `UnidadesRow`, `LockerTable`, `VistaPreviaEquipo`, `AltaGamaBadge`, `CatalogPage`, `StockPage`, `services/{stockVista,vistaPrevia}.ts` | — |
| `loans` | 3 (U2) | V-01, V-06, V-08, V-11, V-14, V-18, V-19 (M-04) | `SolicitudForm`, `TerminosPrestamo`, `AprobarOrdenModal`, `CarritoPanel`, `BandejaPage`, `BandejaTabla`, `MisSolicitudesPage`, `hooks/`, `services/{bandejaVista,calendarioPedido,misSolicitudesVista}.ts` | La disponibilidad del pedido usa el `GET` de disponibilidad de `inventory` que ya existe (§4.6) |
| `spaces` | 4 (U3) | V-01, V-09, V-11, V-12, V-13, V-18, V-21 | `SpacesPage`, `CalendarGrid`, `MisReservas`, `SolicitudesPendientesEspacios`, `services/{motivo,reservasDelDia,pendientesVista}.ts` | Materia y descripción se guardan en el `motivo` existente (V-13) |
| `notifications` | 5 (U4) | V-01, V-10, V-11, M-02 | `ComunicadosList`, `ComunicadoForm`, `BannerComunicado`, `NewsPage`, `services/tema.ts`, `portada/` | M-02: tabla y endpoints propios, aislados (§4.7) |
| `users` | 1 | V-11, V-20 | `UsersPage`, `ProfilePage`, `types/index.ts` (`ordenar_por` y `direccion`, que el backend ya acepta) | — |

---

## 6. Códigos de error

No se cambian códigos existentes. Sólo la portada MOMENTÁNEA (M-02) usa los de `files` y suma `IDS_INVALIDOS` (§4.7).

---

## 7. Criterios de aceptación

Se verifican con `npm run typecheck`, `npm run build`, Vitest y capturas antes/después en claro y oscuro.

### 7.1 Manual de uso (A5, M-01) — `components/layout/manualDeUso.test.ts` y verificación manual

| # | Criterio |
| --- | --- |
| AC-U01 | El botón "?" abre el modal "Manual de Uso"; la X, "Entendido", `Esc` y el clic fuera lo cierran |
| AC-U02 | El subtítulo dice "Vista activa: \<rol\>" según la sesión: Estudiante, Docente, Administrador local o Superadministrador (D-07) |
| AC-U03 | Cada rol ve sus tareas de §4.5 en orden, con el color de su rol; el `SUPERADMIN` ve las de Admin más gestión de usuarios (USR-04) y parámetros (GLO-03) (D-07) |
| AC-U04 | Las tareas pendientes o parciales llevan la marca "Próximamente" (D-05) |
| AC-U05 | La nota al pie dice el texto de D-04 y no menciona un selector de vista |
| AC-U06 | Se lee bien en tema claro y oscuro (texto sobre fondo del recuadro) |
| AC-U07 | No hace llamadas a la API (RN-U03) y está marcado como MOMENTÁNEO en sus archivos y en la línea de `App.tsx` (RN-U02) |

---

### 7.2 Entrega 1 — Vitest, pytest y verificación en el navegador

| # | Criterio | Hallazgo | Verificación |
| --- | --- | --- | --- |
| AC-U08 | Solicitar equipos, Aprobar orden, el bloqueo de espacios y "Vence" usan `DatePicker`/`SelectorHora`; en Solicitar equipos no se eligen los días sin unidades suficientes ni los que superan el plazo | V-01, V-08 | `calendarioPedido.test.ts`, `mes.test.ts` y manual |
| AC-U09 | La tarjeta y la lista del catálogo muestran "N de M disponibles" y "Alta Gama" con los tokens `premium`, alineadas en la fila | V-04…V-06 | Manual, claro y oscuro |
| AC-U10 | El detalle del equipo se ve en dos columnas con el pie fijo; `Modal` sin las props nuevas se ve igual que antes | V-07 | Manual |
| AC-U11 | Ninguna acción usa `window.confirm` ni `window.prompt`; las seis acciones de V-11 funcionan en el panel embebido | V-11 | Búsqueda en el código y manual |
| AC-U12 | Turnos del día con la fecha en palabras, estados y leyenda; materia y descripción viajan en `motivo` ("Materia — Descripción"; sólo descripción, "— Descripción", para que no se lea como materia) | V-12, V-13 | `motivo.test.ts` y manual |
| AC-U13 | La Bandeja deduce el tipo y filtra por estado y tipo; "+N más" lista todos los equipos; si una lista llega al límite de 100, la cifra se muestra como "100+" y se avisa que el filtro por tipo se aplica sobre esas 100 | V-14 | `bandejaVista.test.ts` y manual |
| AC-U14 | El alta de equipo muestra la vista previa en vivo y no se cierra con clic fuera ni con `Esc` | V-15 | `vistaPrevia.test.ts` y manual |
| AC-U15 | Control de Stock filtra por categoría y, en la vista por locker, agrupa las mismas unidades del 1 al 7 | V-16, V-17 | `stockVista.test.ts` y manual |
| AC-U16 | Mis Solicitudes separa equipamiento y espacios, filtra por estado y cancela con el diálogo propio | V-18 | `misSolicitudesVista.test.ts` y manual |
| AC-U17 | La casilla de Términos y Condiciones muestra el reglamento y sigue siendo obligatoria | V-19 | Manual |
| AC-U18 | El directorio filtra por rol con su cantidad y ordena con `ordenar_por`/`direccion` | V-20 | Manual |
| AC-U19 | El admin ve quién y para qué en cada turno, las pendientes por día en el calendario, el filtro por día, período ("Próximos N días" desde hoy; "Todas" incluye las pasadas sin resolver) y espacio, y la paginación de a 10. **El estudiante no ve identidad ni materia de otros** (RN-30) | V-21 | `reservasDelDia.test.ts`, `pendientesVista.test.ts` y manual con los dos roles |
| AC-U20 | La portada elegida (tema o foto) se guarda y se ve; sin elección, el color automático; un estudiante o docente que intenta editarla recibe `403`; un admin fuera de alcance (otra sede o un comunicado global para un `ADMIN_LOCAL`), `404` (P4.5) | M-02 | `tests/notifications/test_portada.py` y `test_migracion_0020.py` |
| AC-U21 | `npm run typecheck`, `npm run build` y `npm test` en verde; `pytest -q` en verde y una sola cabeza de Alembic | Todos | Plan §6 |

---

## 8. Casos de borde

| # | Caso | Comportamiento |
| --- | --- | --- |
| EC-U01 | Lista vacía (pendientes, solicitudes, stock, directorio) | Mensaje de estado vacío propio; con filtros, "con estos filtros" |
| EC-U02 | Texto largo (descripción, motivo, nombre) | Una o dos líneas con "…" y el texto completo en `title` |
| EC-U03 | Equipo sin imagen | Miniatura con las letras del código |
| EC-U04 | Muchas pendientes de espacios | Paginación de a 10 y filtros (V-21); en el backend, U7 |
| EC-U05 | Tema oscuro | Todos los colores salen de `useC()`; cada pantalla se verificó en los dos temas |
| EC-U06 | Teclado | Desplegables y diálogos se cierran con `Esc`; chips y filas desplegables son botones |

---

## 9. Requisitos no funcionales

| # | Requisito |
| --- | --- |
| NFR-U01 | Sin dependencias nuevas en el frontend ni en el backend |
| NFR-U02 | Los filtros, la paginación y las agrupaciones nuevas trabajan sobre lo que la API ya devuelve: no agregan pedidos por fila |
| NFR-U03 | Texto legible en claro y oscuro (colores del tema, sin valores fijos nuevos) |
| NFR-U04 | La lógica de las vistas va en `services/*.ts` con tests, separada de los componentes |

---

## 10. Decisiones

| # | Decisión | Opciones | Recomendación | Estado |
| --- | --- | --- | --- | --- |
| D-01 | Numeración propia (`AC-U…`) | Propia / seguir la del Perfil 1 | Propia, por ser transversal | Propuesta |
| D-02 | Técnica de estilos | Inline + tokens / Tailwind | Inline + tokens (menor diff sobre módulos ajenos) | Acordada con el Perfil 1 (2026-11-12) |
| D-03 | Dirección visual | Pulir la identidad actual / cambio fuerte | Pulir la actual | Acordada con el Perfil 1 (2026-11-12) |
| D-04 | Nota al pie del manual. La referencia dice "Para cambiar de rol usá el selector Vista:", pero ese selector era del prototipo y ya no existe: el rol sale de la sesión | (a) Quitarla · (b) Reemplazarla por "Lo que ves depende de tu rol. Si necesitás otro acceso, consultá con el laboratorio de tu sede." | (b) | Aceptada por el Perfil 1 (2026-11-12) |
| D-05 | Tareas que todavía no existen (docente 6, admin 4; admin 1 parcial) | (a) Mostrarlas igual · (b) Ocultarlas hasta que existan · (c) Mostrarlas con la marca "Próximamente" | (c): el manual queda completo y no promete algo que hoy no funciona | Aceptada por el Perfil 1 (2026-11-12) |
| D-06 | Modal del manual | (a) Reusar `features/inventory/components/Modal.tsx` (Perfil 2) · (b) Llevarlo antes a `components/ui/Modal.tsx` (A2) | (b), con el aval U1 del Perfil 2; mientras tanto, (a) | Aceptada por el Perfil 1 (2026-11-12). (b) está en el frontend PR #29 (2026-11-18, en revisión): `components/ui/Modal.tsx`, con los imports de `inventory` y `loans` actualizados; se mergea con el aval U1 |
| D-08 | Código de la entrega 1 antes de aprobar el spec | (a) Esperar la aprobación para escribir código · (b) Escribirlo durante el relevamiento y no mergear hasta aprobar | (b) sólo para la entrega 1, como desvío explícito de `AGENTS.md` §4 (nota de modo de trabajo); la entrega 2 vuelve a (a) | Decidida por el Perfil 1; observada en la revisión del Docs PR #40 y pendiente de que el equipo la acepte |
| D-07 | El `SUPERADMIN` ve el manual de Admin | (a) Igual al de Admin · (b) Admin + tareas propias: gestión de usuarios de ambas sedes (USR-04) y parámetros (GLO-03) | (b), con un subtítulo "Vista activa: Superadministrador" | Aceptada por el Perfil 1 (2026-11-12) |

---

## 11. Coordinación con otros perfiles (se registra en `MEMORY.md` §5 al aprobar)

| # | Perfil | Pedido |
| --- | --- | --- |
| U1 | Perfil 2 | Aval para los cambios de presentación en `inventory` de la entrega 1 (§5): props opcionales en `Modal` y `MiniCalendario` dibujado con `GrillaMes`, **sin moverlos de carpeta**. Pasarlos a `components/ui` queda para la entrega 2 (§1.5, P-4) y se pedirá entonces. **`Modal` se adelantó** en el frontend PR #29 (2026-11-18): se pide el aval para ese movimiento antes de mergearlo. `MiniCalendario` sigue en `inventory` |
| U2 | Perfil 3 | Aval para la Fase B en `loans` (formularios de solicitud y bandeja) |
| U3 | Perfil 4 | Aval para la Fase B en `spaces` (`SpacesPage`, `CalendarGrid`) |
| U4 | Perfil 5 | Aval para la Fase B en `notifications`. Además, exponer como públicas `_filtro_lectura` y `_bloquear_para_editar` de `notifications/service.py`, que usa la portada M-02 (§4.7) |
| U5 | Perfil 5 | **Confirmar la excepción M-02 y decidir si se adopta.** La portada elegible ya está implementada como MOMENTÁNEO (§4.7): tabla aislada `comunicados_portada` (migración `0020`) y router propio `notifications/portada.py`, sin tocar `comunicados`, sus esquemas ni `files`. Se le pide al Perfil 5: (1) confirmar la excepción a RN-U03, ya que el backend queda dentro de su módulo; (2) decidir si la adopta tal como está, la reescribe dentro de su spec o se saca (§1.4). Si se adopta, hay que sumarla a NOV-02 en el ERS con el equipo o la referente. Sin la portada, el color sale del alcance y el vencimiento (V-10) |
| U7 | Perfil 4 | **Propuesta, sin implementar:** paginar en el backend `GET /spaces/reservas?estado=Pendiente` (`limit`/`offset`, y opcionalmente `desde`/`hasta` e `id_espacio`), para que la lista de pendientes del admin (V-21) no traiga todas de una vez cuando sean cientos. Hoy el frontend pagina en memoria; el cambio no altera qué datos ve cada rol |
| U6 | Perfil 2 | **Propuesta, sin implementar:** administrar los lockers desde la vista por locker (V-17): alta pidiendo sólo el nombre, edición y baja. Hoy PRE-12 fija el locker como un número del 1 al 7 dentro de cada unidad (`unidades_fisicas.locker`), así que esto necesita una tabla `lockers` por sede, una migración que convierta los números actuales, endpoints en `inventory` y decidir qué pasa al borrar un locker con unidades (impedirlo o pedir a dónde moverlas). No está en el ERS: requiere sumarlo con el equipo o la referente y un spec del Perfil 2. Mientras tanto la vista por locker sigue mostrando los lockers 1 a 7 |

---

## 12. Trazabilidad

| Requisito | Hallazgos | Componentes | Criterio |
| --- | --- | --- | --- |
| GLO-06 | V-01…V-21 | Toda la entrega | AC-U01…AC-U21 |
| PRE-01, PRE-02, PRE-05 | V-04…V-07 | `EquipmentCard`, `EquipmentDetailModal`, `AltaGamaBadge` | AC-U09, AC-U10 |
| PRE-03, PRE-06, PRE-07 | V-01, V-08, V-19 | `DatePicker`, `GrillaMes`, `SolicitudForm`, `TerminosPrestamo` | AC-U08, AC-U17 |
| PRE-09, PRE-10, PRE-20 | V-14 | `BandejaTabla`, `bandejaVista.ts` | AC-U13 |
| PRE-12, PRE-14, PRE-19 | V-15…V-17 | `VistaPreviaEquipo`, `StockTable`, `LockerTable` | AC-U14, AC-U15 |
| USR-04 | V-20 | `UsersPage` | AC-U18 |
| USR-06, RES-03 | V-18 | `MisSolicitudesPage`, `MisReservas` | AC-U16 |
| RES-01, RES-02, RES-05, GLO-04 | V-09, V-12, V-13, V-21 | `CalendarGrid`, `SpacesPage`, `SolicitudesPendientesEspacios` | AC-U12, AC-U19 |
| NOV-02 | V-10, M-02 | `ComunicadosList`, `BannerComunicado`, `portada/` | AC-U20 |
| Sin requisito (RN-U02) | M-01…M-04 | Ver §1.4 | AC-U01…AC-U07 |

---

## 13. Historial de cambios

| Versión | Fecha | Autor | Cambio |
| --- | --- | --- | --- |
| 0.23.1 | 2026-11-21 | Perfil 1 (con asistencia de IA) | `Modal` a `components/ui` adelantado de la entrega 2 en el frontend PR #29 (en revisión): P-4, D-06 y U1 lo registran; el merge espera el aval U1 del Perfil 2. Sin cambios de alcance |
| 0.23.0 | 2026-11-17 | Perfil 1 (con asistencia de IA) | Revisión del Docs PR #40: U5 describe la portada tal como está implementada y pide al Perfil 5 confirmar la excepción M-02; U1 pide sólo lo de la entrega 1; AC-U20 distingue `403` y `404`; desvío del flujo SDD explícito (nota de modo de trabajo y D-08); el ciclo de la migración `0020` se probó a mano en 0.11.1 y tiene test desde 0.22.1. Ajustes del frontend PR #28 por su revisión: motivo con sólo descripción, `Dialogo` con dos pedidos, portada al editar, portadas en tandas de 50, "100+" en la Bandeja, conteo del directorio aparte y "Próximos N días" desde hoy |
| 0.22.1 | 2026-11-17 | Perfil 1 (con asistencia de IA) | Revisión del backend PR #39 (M-02): `ids` fuera del rango de `integer` → `422`; `GET /comunicados/portadas` en una sola consulta; dependencia de funciones privadas del Perfil 5 documentada en §4.7 y pedida en U4; test de la migración `0020`; se saca un chequeo de `content-length` que no protegía nada |
| 0.22.0 | 2026-11-14 | Perfil 1 (con asistencia de IA) | Preparado para enviar la entrega 1: estado `EN REVISIÓN`, M-03 y M-04 en §1.4, lo pendiente en §1.5 (marcado `PENDIENTE SPEC-10`), contratos de §4.2, Fase B por dominio (§5), criterios AC-U08…AC-U21, casos de borde, no funcionales y trazabilidad. Plan y tareas redactados. Historial ordenado |
| 0.21.0 | 2026-11-14 | Perfil 1 (con asistencia de IA) | V-21: pendientes del admin preparadas para muchas solicitudes: número por día en el calendario, filtro por día, período y espacio, y paginación de a 10. Ítem de coordinación U7 (paginación en backend, Perfil 4). Placeholders de "Cargar nuevo espacio" con el acento escapado (`ó`) corregidos. 257 tests y `typecheck` en verde; verificado con el superadmin |
| 0.20.1 | 2026-11-14 | Perfil 1 (con asistencia de IA) | V-21: se saca "Reservas del día" (repetía las pendientes) y se rediseñan las "Solicitudes pendientes" del admin, agrupadas por día y más legibles. 252 tests y `typecheck` en verde; verificado con el superadmin |
| 0.20.0 | 2026-11-14 | Perfil 1 (con asistencia de IA) | Quién reservó y para qué en los turnos del día y lista "Reservas del día" para el admin (V-21). 252 tests y `typecheck` en verde; verificado con el superadmin en Ushuaia sin aprobar ni rechazar |
| 0.19.0 | 2026-11-14 | Perfil 1 (con asistencia de IA) | Directorio de usuarios con chips por rol, orden y chips de rol y estado (V-20). 249 tests y `typecheck` en verde; verificado con el superadmin en Ushuaia |
| 0.18.3 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Se deshace 0.18.2 a pedido del usuario: las reservas vuelven a la pestaña "Espacios" de Mis Solicitudes (V-18) |
| 0.18.2 | 2026-11-13 | Perfil 1 (con asistencia de IA) | "Mis reservas" vuelve a Reservas de Espacios con las filas compactas y los chips; Mis Solicitudes queda sólo con equipamiento (V-18). 249 tests y `typecheck` en verde; verificado con la estudiante de Ushuaia |
| 0.18.1 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Bandeja (V-14): "+N más" en la columna Equipo abre la lista de todos los equipos de la solicitud, con miniatura, código y cantidad (se cierra con Escape o tocando afuera); las miniaturas sin imagen muestran las letras del código. Verificado con el superadmin en la solicitud #3 |
| 0.18.0 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Términos y Condiciones con el reglamento en un globo en la solicitud de equipos (V-19), con el texto de las reglas MOMENTÁNEO. 249 tests y `typecheck` en verde; verificado con la estudiante de Ushuaia sin enviar la solicitud |
| 0.17.0 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Tarjetas de Novedades al mismo alto con el pie igual; Mis Solicitudes separada en equipamiento y espacios, con "Mis reservas" movida desde Reservas de Espacios (V-18). 247 tests y `typecheck` en verde; verificado con el estudiante de Ushuaia; luego pestañas, chips por estado y filas compactas. 249 tests |
| 0.16.1 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Vista por locker agrupada por equipo (V-17). Propuesta U6 al Perfil 2: alta, edición y baja de lockers con nombre, sin implementar por no estar en el ERS |
| 0.16.0 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Chips de categoría y lockers en texto en Control de Stock (V-16); vista por locker MOMENTÁNEA (V-17). 247 tests y `typecheck` en verde; verificado con el superadmin |
| 0.15.0 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Control de Stock rediseñado (V-16), formulario de equipo más compacto y chips de la Bandeja con el estilo del catálogo, en la rama local. 244 tests, `typecheck` y `build` en verde; verificado con el admin de Ushuaia |
| 0.14.0 | 2026-11-13 | Perfil 1 (con asistencia de IA) | Vista previa en vivo y cierre protegido en el alta/edición de equipo (V-15) en la rama local. 244 tests, `typecheck` y `build` en verde; verificado con el superadmin sin guardar datos |
| 0.13.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Bandeja de Validaciones en tabla (V-14) en la rama local. 240 tests, `typecheck` y `build` en verde; verificado con el admin de Río Grande y la solicitud #1, a 1400 px de ancho sin desplazamiento horizontal |
| 0.12.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Reservas de Espacios: turnos del día rediseñados (V-12) y materia y descripción en la confirmación, sobre el `motivo` existente (V-13). 235 tests, `typecheck` y `build` en verde; verificado con estudiante y admin de Río Grande |
| 0.11.1 | 2026-11-12 | Perfil 1 (con asistencia de IA) | M-02 implementado en las ramas locales `feat/ui-consistencia` (backend y frontend): migración `0020` (upgrade → downgrade → upgrade probado **a mano**; el test automático se sumó en 0.22.1), una cabeza, 8 tests nuevos (62 de `notifications` en verde), selector en el formulario y portada en la tarjeta. Verificado en el navegador: tema elegido, foto subida y vista de un estudiante. Códigos de error alineados con `files` |
| 0.11.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | M-02: portada de comunicado elegible (tema o foto), MOMENTÁNEO con backend aislado (§4.7). RN-U03 admite excepciones aprobadas por el Perfil 1 |
| 0.10.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | V-11: diálogos propios en lugar de `window.confirm`/`window.prompt` en seis acciones (Archivar no funcionaba en el panel embebido). 232 tests, `typecheck` y `build` en verde; Archivar verificado de punta a punta con el comunicado de prueba #4 |
| 0.9.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Tarjetas de comunicados (V-10) en la rama local: banner SVG tipo circuito en cuatro colores asignados por alcance y vencimiento, grilla y "Leer más". Propuesta U5 al Perfil 5 (tema elegible e imagen propia). 232 tests, `typecheck` y `build` en verde; verificado con los cuatro colores en claro y oscuro |
| 0.8.1 | 2026-11-12 | Perfil 1 (con asistencia de IA) | "Vence" de Novedades: días anteriores a hoy en gris (mínimo = hoy en la zona del laboratorio). Verificado en el navegador |
| 0.8.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Calendario común (§4.6, V-01, V-08, V-09) en la rama local: `GrillaMes`, `DatePicker` y `SelectorHora` en `components/ui`; `MiniCalendario` sobre la grilla común; Solicitar equipos con disponibilidad del pedido, rango y plazo (`calendarioPedido.ts`, `useDisponibilidadPedido`); reemplazados los selectores nativos de Aprobar orden, bloqueo de espacios y "Vence" de Novedades; `CalendarGrid` alineado. 229 tests, `typecheck` y `build` en verde. Verificado en el navegador, incluida Aprobar orden con una solicitud de prueba (#1, base local) |
| 0.7.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Detalle del equipo rediseñado en la rama local (V-07). `Modal` de `inventory` con props opcionales; los otros diálogos que lo usan (formularios de inventario, carrito, aprobación, motivo y solicitud de `loans`) no cambian. Verificado con Canon (imagen y video) y Sony (Alta Gama, sin imagen), en claro y oscuro; `typecheck`, 219 tests y `build` en verde |
| 0.6.1 | 2026-11-12 | Perfil 1 (con asistencia de IA) | V-06 hecho en la rama local: `Navbar.tsx` y `loans/CarritoPanel.tsx` (Perfil 3, coordinación U2) usan los tokens `premium`/`premiumBg`. Verificado con el carrito de Alta Gama en claro y oscuro |
| 0.6.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Tarjeta y lista del catálogo (V-04, V-05) hechas en la rama local: pie alineado, descripción en 2 líneas, "N de M disponibles", chip `AltaGamaBadge`, botones de admin con borde; tokens `premium`/`premiumBg`. Nuevo hallazgo V-06. `typecheck`, 219 tests y `build` en verde; verificado con Estudiante y Admin local, en claro y oscuro |
| 0.5.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Modo de trabajo en rama local. **Manual de uso implementado** en `feat/ui-consistencia` (local, sin push): `manualDeUso.ts`, `ManualDeUsoModal.tsx`, `manualDeUso.test.ts` (AC-U02…AC-U06) y 4 líneas marcadas en `App.tsx`. `typecheck`, 219 tests y `build` en verde; verificado en el navegador con Admin local (claro y oscuro) y Estudiante; AC-U01 (X, Entendido, Esc, clic fuera) |
| 0.4.0 | 2026-11-12 | Perfil 1 | D-04…D-07 aceptadas con la recomendación |
| 0.3.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Regla de alcance sin requisitos nuevos (§1.3, RN-U01…RN-U03) y elementos MOMENTÁNEOS (§1.4). El manual de uso pasa a M-01: no tiene requisito ni caso de uso. Cada tarea del manual cita su requisito del ERS |
| 0.2.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Manual de uso por rol (A5, §4.5, V-02) a partir de las capturas de referencia; primer hallazgo de la tarjeta del catálogo (V-04); decisiones D-04…D-07 |
| 0.1.0 | 2026-11-12 | Perfil 1 (con asistencia de IA) | Borrador inicial: alcance en dos fases, estado actual verificado y esqueleto del relevamiento |
