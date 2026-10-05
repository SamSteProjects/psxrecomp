# Actor Inspector component layout

Click a component header to collapse or expand it. The existing component filter
continues to search all values, including collapsed contents. **Collapse visible
components** and **Expand visible components** affect only sections matching the
current filter. Clearing a filter retains the other sections' layout choices.

With a component header focused:

- Left collapses; Right expands.
- Up/Down move to the previous/next visible header.
- Home/End focus the first/last visible header.
- Enter/Space toggle through normal button activation.

The layout is remembered across actors in the same project during this editor
session. Opening another project resets it; reloading the editor starts expanded.
Focus returns to the same header after a same-actor rerender when it remains
visible. Changing actors does not transfer header focus. Inputs and buttons inside
an expanded component keep their existing keyboard behavior.

These are display controls. Collapsing retains the existing input values and
action handlers; it does not submit, discard or author an override. Retail,
authored, effective and runtime observations remain separate. Unknown components
retain their read-only fallback. Scene-resource and NPC draft Inspectors keep
their specialized layouts.

Verification used imported Town01 actors and a private browser fixture. Component
navigation, filters, stale callbacks, project isolation and rerender focus passed;
the complete project document and Authored files stayed unchanged. No game was
launched and no new gameplay verification is required for this layout feature.
