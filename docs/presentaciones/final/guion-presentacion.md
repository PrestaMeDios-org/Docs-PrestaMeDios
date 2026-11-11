# Presentación final — guion de la hora

> **Provisorio.** Pensado para cuando la aplicación esté al 100 % o cerca. Lo que dice `[__]` se completa la semana del final.
> **Formato:** 60 minutos frente a profesores, jurado y público: **20 de presentación, 20 de demo, 20 de preguntas y devoluciones**.
> **Láminas:** artifact "PrestaMeDios — Presentación final" (16 láminas + 2 de anexo; cada una tiene en el pie el bloque y el minuto, y en las notas quién presenta y qué decir).
> **Documentos que acompañan:** `guion-demo.md` (bloque 2), `preguntas-y-devoluciones.md` (bloque 3), `../analisis-estado-y-produccion.md` (respaldo de cifras y del camino a producción).

## Reparto

Cada integrante presenta lo de su dominio, para que el jurado vea quién hizo qué. Reemplazar `[nombre]` en la tabla.

| Perfil | Dominio | Integrante | Habla en |
| :-- | :-- | :-- | :-- |
| 1 | Identidad, usuarios, configuración, despliegue | [nombre] | Portada, agenda, relevamiento, cobertura, arquitectura, producción, moderación |
| 2 | Catálogo y stock | [nombre] | Solución, calidad; escena 2 de la demo |
| 3 | Préstamos | [nombre] | Método o iteraciones; conduce la demo (escenas 2 y 3) |
| 4 | Espacios | [nombre] | Problema, decisiones (exclusión); escena 4 |
| 5 | Comunicaciones e IA | [nombre] | Aprendizajes, futuro; escena 4 (avisos) |

## Bloque 1 — Presentación (00:00 → 20:00)

| Min. | Lámina | Quién | Dur. | Idea fuerza |
| :-- | :-- | :-- | :-- | :-- |
| 00:00 | 1. Portada | P1 | 0:30 | Qué es y para quién |
| 00:30 | 2. Tres bloques | P1 | 0:30 | Cómo usamos la hora y quién es quién |
| 01:00 | 3. El problema | P4 | 1:30 | Correo y formularios; dos sedes, cuatro roles |
| 02:30 | 4. Relevamiento | P1 | 1:30 | Reglamento, tres entrevistas, validación con software funcionando |
| 04:00 | 5. Seis subsistemas | P2 | 1:30 | Qué hace la aplicación |
| 05:30 | 6. Cobertura | P1 | 1:30 | `[__]` de 47 requisitos; qué quedó afuera a propósito |
| 07:00 | 7. Arquitectura | P1 | 1:30 | Monolito modular, API primero |
| 08:30 | 8. Decisiones | P4 + P1 | 2:00 | Reglas donde no se pueden saltear |
| 10:30 | 9. Cómo trabajamos | P3 o P5 | 2:30 | Spec-Driven Development e IA con reglas escritas |
| 13:00 | 10. Calidad | P2 | 1:30 | Un test por criterio; concurrencia probada |
| 14:30 | 11. Iteraciones | P3 | 2:00 | Lo que cada entrevista corrigió |
| 16:30 | 12. Aprendizajes | P5 | 2:30 | Qué repetiríamos, qué cambiaríamos, cuánto nos equivocamos al estimar |
| 19:00 | — | — | 1:00 | Margen y pase a la demo |

**Reglas del bloque:** nadie lee las láminas; las notas son ayuda, no texto. Si el bloque se atrasa, la lámina 10 (calidad) se dice en 30 segundos y la 5 se salta: la demo la cubre.

## Bloque 2 — Demo (20:00 → 40:00)

Lámina 13 en pantalla mientras se cambia al navegador. Ver `guion-demo.md`. Conduce el Perfil 3; cada escena la maneja su dueño. A los 38:00 se cierra la escena en curso.

## Bloque 3 — Preguntas y devoluciones (40:00 → 60:00)

| Min. | Qué | Quién |
| :-- | :-- | :-- |
| 40:00 | Lámina 14, camino a producción | P1 (3 min) |
| 43:00 | Lámina 15, trabajo futuro | P5 (1:30) |
| 44:30 | Lámina 16, gracias + preguntas | Modera P1 |
| 44:30–58:00 | Preguntas del jurado y del público | El dueño de cada dominio (ver `preguntas-y-devoluciones.md`) |
| 58:00 | Cierre y agradecimiento | P1 |

**Durante las preguntas:** repetir la pregunta en voz alta, responder en menos de un minuto, ofrecer el anexo si piden detalle. Una persona que no esté respondiendo anota las devoluciones.

## Lo que hay que tener listo

**Una semana antes**
- [ ] Completar `[__]` de las láminas 1, 6, 10 y 12 y del anexo con los números reales (tabla §4.1 del análisis, corrida de tests, PR, ClickUp).
- [ ] Completar en el ERS las secciones que pide la cátedra (§6 del análisis): cronograma por requerimientos, adecuación de la metodología, error de estimaciones, sobre los entregables, presentación visual.
- [ ] Dos ensayos completos cronometrados, uno con alguien de afuera haciendo preguntas.
- [ ] Video de respaldo de la demo completa (≤ 15 min).
- [ ] Invitar a la referente del Laboratorio; si puede, que diga dos minutos sobre su experiencia (preguntarle antes, no improvisar).

**El día**
- [ ] Notebook principal y una de respaldo con todo instalado y la base cargada.
- [ ] Láminas exportadas a PDF en un pendrive.
- [ ] Reloj visible para quien presenta (o alguien que muestre carteles 5′ / 1′).
- [ ] Agua.

## Entregables que acompañan la presentación

| Documento | Dónde | Estado |
| :-- | :-- | :-- |
| ERS (IEEE 830) completo | `docs/ERS.md` | Faltan las secciones de §6 del análisis |
| Specs, planes y tareas con trazabilidad | `specs/` | Aprobar los que están en `BORRADOR` |
| Arquitectura y modelo de datos | `docs/diseno/` | Al día al 09/11 |
| Guía de instalación | `README.md` de Backend y Frontend | Sumar despliegue con Docker |
| Manual de usuario (admin y estudiante) | `[a crear]` | Pendiente |
| Código fuente | Repos de `PrestaMeDios-org` | Llevar `develop` a `main` antes del final |
| Estas láminas y guiones | `docs/presentaciones/final/` | Provisorio |
