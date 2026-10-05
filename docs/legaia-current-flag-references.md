# Current flag reference inspection

Open a flag source-group asset or its source script in Asset Database, choose
**Inspect references**, then select **Effective / Current**. A saved operand edit
appears as `effective_script_flag_reference`; **Derived source** retains the original
`script_flag_reference`. Search accepts the exact operand ID or recorded hashes.
Following the source instruction uses its source-record hash as a qualifier.

A Current edge targets the same Retail source-group asset. Its target is an encoded
reference group within one source script, not a globally resolved runtime flag.
The label and evidence separately display the Retail index and Current index so an
edit never silently changes the meaning of the stable group identity. Only authored
sites add Current edges; unchanged sites continue to inherit their Retail references.

`flag_binding_evidence` contains exactly `operand_id`, `retail_index`,
`effective_index`, `source_record_sha256` and `component_sha256`. The edge also retains
the original bank, operation, mnemonic, scope and extended target, plus scene import
and resource-catalog hashes. Native source validation precedes catalog annotation;
graph assembly rejects annotations that differ from the saved ScriptFlags binding or
its unique source script record. Browser qualification rejects unqualified source
sites, incompatible layers, unsupported widths and context side-effect selectors,
invalid hashes and attempts to attach runtime values.

This is read-only inspection through the existing graph and authoring serializer.
Undo removes an authored relationship; Redo and Save/Open restore it. Project scope
uses the same per-scene source checks. No runtime values, story names, execution,
branch reachability or cross-script shared-variable identities are inferred.

Validation on 2026-10-04: 28 focused Python checks with private-disc fixtures and no
skips, JavaScript source/Current reference guards, and a native dolk2 CFLAG_SET edit
from 24 to 25. Native evidence includes unchanged Retail relationships, exact operand
and inverse/project queries, Save/Open, Undo/Redo, styled desktop/narrow screenshots,
source-script navigation, unchanged inspection history/data/selection and zero browser
errors. No gameplay or game launch was required; execution remains unverified.
