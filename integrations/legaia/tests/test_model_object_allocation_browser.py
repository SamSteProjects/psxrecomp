"""Browser object allocation review qualifies real SDK reports and native geometry."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import subprocess
import unittest
from sdk import model_object_allocation
from test_model_object_ledger import clone_request
import test_model_object_project as fixtures


class ObjectAllocationBrowserTests(unittest.TestCase):
    def test_actual_source_and_multi_object_review(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        helper=fixtures.ObjectProjectTests();self.addCleanup(helper.doCleanups);p,asset=helper.fixture()
        source=model_object_allocation.source(p,asset,'a'*64)
        requests=[clone_request(source['topology'],source['object_identities'][0],100),clone_request(source['topology'],source['object_identities'][0],200)]
        report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        cases=[dict(source=source,requests=requests,report=report)]
        p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        source=model_object_allocation.source(p,asset,'a'*64)
        requests=[clone_request(source['topology'],source['object_identities'][-1],300)]
        report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        cases.append(dict(source=source,requests=requests,report=report))
        script="""import {decodeObjectAllocationSource,decodeObjectAllocationReview,objectAllocationRequest} from './integrations/legaia/editor/model-object-allocation.js';
import assert from 'node:assert/strict';let text='';for await(const chunk of process.stdin)text+=chunk;
for(const {source,requests,report} of JSON.parse(text)){const decode=s=>decodeObjectAllocationSource(s,s.asset_id,s.project_source_key);
decode(source);decodeObjectAllocationReview(report,source,requests);let next=1000;
assert.equal(objectAllocationRequest(source,source.object_identities[0].object_id,()=>`00000000-0000-4000-8000-${(next++).toString(16).padStart(12,'0')}`).groups.length,source.native_objects[0].groups.length);
for(const mutate of [s=>s.remaining_vector_budget--,s=>s.normal_vectors.push([]),s=>s.preview.triangles[0][0]++,s=>s.native_objects[0].primitive_byte_length++,s=>s.object_identities[0].object_id='bad']){const bad=structuredClone(source);mutate(bad);assert.throws(()=>decode(bad));}
for(const mutate of [r=>r.allocation.new_objects[0].spans[0].byte_offset++,r=>r.allocation.pointer_relocations[0].current_offset++,r=>r.topology.objects.at(-1).donor_object_id='bad',r=>r.preview.triangles.at(-1)[0]++,r=>r.topology.faces.at(-1).donor_face_id='bad',r=>r.allocation.new_objects[0].opaque_metadata++,r=>r.allocation.growth_bytes++,r=>r.requests[0].object_id='bad']){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeObjectAllocationReview(bad,source,requests));}
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(cases),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
