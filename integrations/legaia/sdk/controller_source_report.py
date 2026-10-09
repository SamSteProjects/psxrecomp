"""Shared controller byte inspection with retained Retail instruction anchors."""
from importer.script_inspection import inspect_record


def controller_report(owner,man,offset,record,entry,source,selectors=None):
    if inspect_record(record,entry)['stops']:
        return inspect_record(man[offset:offset+len(record)],entry,semantic_id=owner.replace('scene://','script://',1),base_offset=offset)
    from importer.controller_branches import ControllerBranchAuthoringContext
    report=ControllerBranchAuthoringContext(source,system_selectors=selectors).inspect_owner(owner,man)
    for row in report['instructions']+report['dialogues']+report['unvisited_instructions']+report['unvisited_dialogues']:
        row['byte_offset']=offset+row['pc']
    report['semantic_id']=owner.replace('scene://','script://',1)
    return report
