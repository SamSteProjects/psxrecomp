# Compare a transition arrival in its destination scene

Import both the source scene and named destination. Refresh source resources, open a
transition's Asset Details, choose **Inspect transition entry and source**, then
**Compare arrival in destination scene**. The action opens the central viewport in the
destination scene. It previews saved Current entry operands alongside Retail; it does
not stage or Apply edits and does not import an unknown destination automatically.

Blue marks Retail; gold marks Current. Labels retain X/Z and the static encoded facing
angle out of4096. **Frame arrival comparison** fits both points. **Arrival reference Y**
changes only the inspection plane (default0); true source elevation and runtime pose
are unknown. **Return to source scene** uses ordinary scene navigation; **Clear arrival
comparison** removes the local overlay. Neither changes authored operands or history.
Active scene is existing saved view state, so navigation can affect dirty status.

`/api/transition-arrival-preview` accepts exactly `asset_id` and the active source's
`source_key`. It requires Edit mode, requalifies the source catalog/transition resource
and imported destination, and returns `legaia.transition-arrival-preview.v1`. The report
contains source/destination scene IDs and preview keys, a project-state key, the validated
transition resource and its separate Retail/Current arrival layers, and explicit unknown
height/unverified runtime qualifiers. Inspection never changes the active scene itself.
The editor navigates afterward and requires the destination and project keys to match
before installing the overlay. Changing the scene, project, mode or keyed saved state
withdraws it. Closed/stale source-dialog responses cannot install a preview.

The source instruction's destination label remains immutable. These are destination
arrival points, not source trigger locations, observed player positions, or proof that
the transition executes. Facing is the existing source interpretation, not an observed
runtime pose. An unchanged Current point remains separately labeled even when it
coincides with Retail. No terrain height, branch reachability or story state is inferred.

Validation: 10 focused Python checks with private-disc coverage and no skips; JavaScript
source/destination layer, reference-height, stale key, navigation, pending/closed and mode
guards; editor syntax checks. Native Town01 -> map01 compared Retail12352/3264 and
Current128/3264 over loaded map geometry, inspected desktop/narrow screenshots, exercised
reference Y, Frame, Return, Clear and actual flag/transition Inspector actions, with
unchanged authored data/history and zero browser errors. The pass repaired out-of-scope
lookup references in both dialog guards and kept the temporary overlay controls outside
the closed Scene tools drawer. No game was launched; gameplay remains deferred.
