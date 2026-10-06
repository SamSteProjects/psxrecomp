# Author source effect color operands

Open a qualified script through the Asset Database or its source owner inspector. Find **Script effect color operands**, or use **Open operand editor** on an EFFECT_COLOR_INTENSITY instruction row. Authored script assets may open directly in the source editor.

Enter the encoded red, green and blue bytes (0–255) and signed intensity (-32768–32767). **Apply effect color operands** creates one Undo entry; Save persists it. **Clear effect color override** returns this instruction to retail values. Discard removes an uncommitted form draft. Retail, authored and effective values stay visible separately. Invalid widths/fractions are rejected. The complete selector byte and any extended actor context remain unchanged.

**Download operand JSON** retains `ScriptEffectColors` entries under stable `script://<scene>/<source-owner>/effect-color/<hex-pc>` identities. Existing reviewed operand-file and bundle workflows support this family. Files remain bound to their imported source/owner. Normal Build reports the typed before/after values and delivers qualified native bytes; readback acceptance is recorded in the SDK status report.

Only reached sub0 instructions in uniquely owned records without decoder stops qualify. Unknown/aliased paths remain unsupported. RGB bytes and intensity do not establish host rendering, visual color space, effect target identity, story reachability or runtime timing. There is no initial actor-color override, simulated renderer, runtime write or allocated-NPC-specific color editor in this workflow. Gameplay verification remains separate.
