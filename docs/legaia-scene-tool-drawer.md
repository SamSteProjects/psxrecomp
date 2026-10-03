# Collapsible scene tools

**Scene tools** opens the existing animation, transformation, selection and wall/group controls in a scrollable drawer. It starts closed to give the3D scene more room. Collapsing/reopening retains the same DOM controls, callbacks and local drafts; it does not recreate or reset them. Toggle layout changes cancel an active viewport gesture and refresh the viewport dimensions through existing handlers.

Runtime notices, field-map notes, proposed-scene restore controls, active actor-group controls and script-target controls remain outside the drawer. The open drawer limits its height using the workspace, toolbar and visible notices, reserving180px for the scene when space permits. A zero minimum height on the scene panel prevents an expanded drawer from stretching the panel below the window. The drawer has a native keyboard-focusable disclosure summary and ordinary scrolling.

At narrow widths use **Scene** for the viewport and tools, **Hierarchy & assets** for the library, and **Inspector** for properties. These panel tabs already existed. The prior hierarchy proof observed only the hidden sidebar in the Scene tab; it did not establish that narrow keyboard hierarchy browsing was unavailable. The current proof verifies arrow browsing through the Library tab.

Six actual private-retail browser checks pass with no page errors: default collapse/unique controls, bounded expansion and existing snap handlers, retained snap settings after collapse/reopen, narrow Library keyboard access, narrow Scene drawer access and unchanged files/history/selection. At1280x950 the scene is640px tall collapsed and279px expanded. At540x840 the collapsed scene is389px tall; the open drawer check retains at least175px. Desktop and narrow screenshots were visually inspected. The focused hierarchy Node suite remains green. No authoring, Build or game request runs.

Private proof: `local-output/sdk-20260909/scene-tool-drawer-20261003/parent/`. Owned browser/server handles are terminal. These workspace changes require no immediate gameplay verification; source transforms, runtime identity and gameplay acceptance remain separate.
