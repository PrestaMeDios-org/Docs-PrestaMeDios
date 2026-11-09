# Docs-PrestaMeDios

Documentación compartida del proyecto PrestaMeDios: ERS, Constitución, reglas para agentes de IA, memoria del proyecto, perfiles y specs SDD. El código vive en `Backend-PrestaMeDios` y `Frontend-PrestaMeDios`.

| Archivo | Contenido |
| --- | --- |
| `docs/ERS.md` | ERS (IEEE 830): requisitos, casos de uso, diseño e iteraciones. Fuente de verdad funcional |
| `docs/diseno/` | Arquitectura, modelo de datos y casos de uso: originales presentados a la cátedra y versiones actualizadas al código |
| `docs/constitution.md` | Principios no negociables del proyecto |
| `AGENTS.md` | Guía operativa para agentes de IA |
| `docs/perfiles.md` | División del trabajo en 5 perfiles y prompts de arranque |
| `MEMORY.md` | Estado, decisiones (ADR), deuda técnica y coordinación entre perfiles |
| `specs/NN-<slug>/` | `spec.md`, `plan.md` y `tasks.md` de cada spec |
| `workspace/` | Plantillas para la raíz del workspace: `CLAUDE.md`, `opencode.json` y `AGENTS.md` |

## Armar el workspace

Los tres repos se clonan uno al lado del otro en una carpeta común, que no es un repo:

```sh
mkdir Proyecto-PrestaMeDios && cd Proyecto-PrestaMeDios
git clone https://github.com/PrestaMeDios-org/Docs-PrestaMeDios.git
git clone https://github.com/PrestaMeDios-org/Backend-PrestaMeDios.git
git clone https://github.com/PrestaMeDios-org/Frontend-PrestaMeDios.git
cp Docs-PrestaMeDios/workspace/CLAUDE.md Docs-PrestaMeDios/workspace/opencode.json Docs-PrestaMeDios/workspace/AGENTS.md .
```

El último paso copia a la raíz los archivos que hacen que el agente, abierto ahí, cargue `Docs-PrestaMeDios/AGENTS.md` al iniciar, sin tener que ir a buscarlo:

| Archivo | Herramienta | Qué hace |
| --- | --- | --- |
| `CLAUDE.md` | Claude Code | Incluye `Docs-PrestaMeDios/AGENTS.md` con `@` |
| `opencode.json` | OpenCode | Lo declara en `instructions` |
| `AGENTS.md` | Copilot y otras | Puntero de respaldo: le pide al agente que lo lea |

Si alguna plantilla cambia en este repo, volvé a copiarla. Abrí el agente siempre en la raíz: dentro de Backend o Frontend no ve la documentación.

```
Proyecto-PrestaMeDios/
├── CLAUDE.md · opencode.json · AGENTS.md   ← copias locales (no versionadas)
├── Docs-PrestaMeDios/
├── Backend-PrestaMeDios/
└── Frontend-PrestaMeDios/
```

## Trabajo diario

- Antes de empezar, `git pull` en los tres repos.
- Los cambios a specs, `MEMORY.md` y demás documentos se commitean y se publican **en este repo**, no en Backend ni Frontend.
- Commits con *Conventional Commits* en español, por ejemplo `docs(spec-05): …` o `docs(memory): …`.
