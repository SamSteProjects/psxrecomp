# Legend of Legaia debug-menu bridge

The external runtime overlay remains available with `F10`. Its `WARP` panel is
an intentionally small bridge to the retail Legaia developer menu rather than
a separate, host-side scene loader.

From a normal field/town state, press `F10`, press `Tab` until `WARP` is shown,
then press `Enter`. The runtime sets the documented debug gate at
`0x8007B98F` and pulses the game's documented `SELECT + TRIANGLE` input chord.
The external overlay closes and the game-owned debug menu opens. The runtime
keeps the gate asserted for the rest of the session, matching the documented
retail probe: it is the input dispatcher's master debug-mode gate and scene
initialisation can otherwise reset it mid-transition. The bridge supplies one
released pad sample followed by the actual `SELECT + TRIANGLE` chord on the
second PSX controller port, which is the retail dispatcher's developer-menu
binding. It deliberately does **not** force game mode 0: that path instead
loads PROT 0971's unrelated full-screen `DEBUG MODE` configuration tester.

Use the normal PSX controls inside that menu. Its `MAP CHANGE` facility performs
warps through the retail overlay, so it retains Legaia's own scene streaming,
entry position, event state, and overlay residency rules. This bridge refuses
to launch outside normal field mode; battle, ordinary menus, and FMV states are
intentionally excluded because they can own a different shared overlay.

The compact developer-menu routines, including the MAP CHANGE appliers, live
in field overlay PROT 0897. The bridge therefore complements the static
overlay and cache-generation fixes instead of bypassing them.

For a focused Fishing test, open the same `WARP` panel from a normal field/town
state and press `F`. This makes the retail mode-24 hand-off used by a fishing
pond door (`sub_id = 0`, `OTHER INIT = 0x18`), so the game takes its ordinary
scene-backup, overlay-load (PROT 0972), and return-to-field path. It is disabled
outside field/town mode because battle, menu, and FMV modes can own the shared
overlay window.
