"""Validate saved editor tree state without native scene authoring."""
import re
from copy import deepcopy
from .project import ProjectError

GROUPS={'actors','npc-drafts','environment','transition','trigger','region','collision','script'}
FIELDS={'name','id','type','component','authored','visibility'}
SPACE=re.compile(r'[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]')


def query(value):
    if not isinstance(value,str) or len(value.encode('utf-16-le',errors='surrogatepass'))//2>2048:
        raise ProjectError('Saved hierarchy search is limited to 2048 characters')
    token='';quoted=False;escaped=False;started=False;literal=False;terms=0
    def finish():
        nonlocal token,started,literal,terms
        if not started:return
        text=token
        if not literal and text.startswith('-'):text=text[1:]
        if not text:raise ProjectError('Saved hierarchy search requires a nonempty term')
        colon=text.find(':')
        if not literal and colon>0 and text[colon+1:colon+3]!='//':
            prefix=text[:colon].lower()
            if prefix in FIELDS:text=text[colon+1:]
            elif '://' not in text:raise ProjectError('Saved hierarchy search has an unknown field')
        if not text:raise ProjectError('Saved hierarchy field requires a value')
        terms+=1
        if terms>32:raise ProjectError('Saved hierarchy search is limited to 32 terms')
        token='';started=False;literal=False
    for char in value:
        if escaped:token+=char;escaped=False;started=True
        elif char=='\\' and quoted:escaped=True
        elif char=='"':
            if not started:literal=True
            quoted=not quoted;started=True
        elif SPACE.fullmatch(char) and not quoted:finish()
        else:token+=char;started=True
    if quoted or escaped:raise ProjectError('Close the quoted saved hierarchy search phrase')
    finish()
    return value


def hierarchy(value):
    if not isinstance(value,dict) or set(value)!={'query','collapsed_groups'}:
        raise ProjectError('Saved hierarchy requires search and collapsed groups only')
    query(value['query']);groups=value['collapsed_groups']
    if (not isinstance(groups,list) or len(groups)>len(GROUPS) or any(not isinstance(group,str) or group not in GROUPS for group in groups)
            or groups!=sorted(set(groups))):
        raise ProjectError('Saved hierarchy requires canonical supported collapsed groups')
    return deepcopy(value)
