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

## Property category filter

Choose **Property category** to show whole components containing a displayed SDK
property-state category, such as Retail, Authored, Derived, Unresolved or Unsupported.
Categories come from the current Inspector labels; no property value or runtime identity
is inferred. Multiple authored workflows share the Authored category. Combine the
category with text search and **Authored only**. Authored only still requires actual
SDK override membership, including when an empty Authored layer is displayed.

Selection persists across actor rerenders in this editor session; a remembered category
absent from another entity yields zero results. **Reset filter** clears category, query
and authored-only membership together. All rows/actions in matching components remain
available. Collapsing/filtering submits no edit, preserves values, and leaves saved
project data/history unchanged. Visible-component collapse and keyboard navigation keep
their existing scope. Specialized scenery/resource/draft layouts retain their own tools.

Three Node suites, syntax and actual private retail browser checks passed with unchanged
project/history/files and no authoring/Save/Build/Run requests. Evidence/screenshots:
`local-output/sdk-20260909/inspector-property-category-20261005/`.
No manual gameplay check is added for this display workflow.
