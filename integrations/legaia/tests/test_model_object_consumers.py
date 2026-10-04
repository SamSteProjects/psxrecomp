"""V7 authored objects have Current packet/vector ownership and no Retail alias."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import unittest
from unittest.mock import patch
from sdk import model_object_allocation,model_vertex_users,model_normal_users
from test_model_object_ledger import clone_request
import test_model_editors_allocated_vectors as fixtures


class ObjectConsumerTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.AllocatedEditorTests();self.addCleanup(helper.doCleanups)
        p,asset=helper.fixture()
        self.enterContext(patch('sdk.model_object_allocation.source_key',return_value='a'*64))
        source=model_object_allocation.source(p,asset,'a'*64)
        requests=[clone_request(source['topology'],source['object_identities'][0],100)]
        report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
        p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
        return p,asset

    def test_primitive_and_vector_reference_sources_and_browser_adapters(self):
        from urllib.request import urlopen
        from test_model_primitive_workflow import http_server
        p,asset=self.fixture();source=p.model_primitive_source(asset)
        with http_server(p) as (server,_):
            with urlopen(f'http://127.0.0.1:{server.server_port}/model-object-ownership.js') as response:
                self.assertEqual(response.status,200)
                self.assertIn(b'export function validateObjectOwnership',response.read())
        self.assertEqual(source['schema_version'],'legaia.model-primitives.v6')
        self.assertEqual(source['face_mappings'][1],[])
        self.assertEqual(source['vector_growth'],[dict(object_index=0,vertices=3,normals=3),dict(object_index=1,vertices=8,normals=7)])
        self.assertIsNone(source['object_mappings'][1]['retail_index'])
        reports=[]
        for module,field in ((model_vertex_users,'vertex'),(model_normal_users,'normal')):
            for owner,index in ((0,0),(0,5),(1,0)):
                report=module.inspect(p,asset,owner,index,source['effective_sha256'],'a'*64)
                self.assertEqual(report['schema_version'],f'legaia.model-{field}-users.v4')
                if owner==1:
                    self.assertEqual(report['retail_vector_count'],0);self.assertEqual(report['face_mapping'],[])
                    self.assertIsNone(report['retail_coordinates']);self.assertEqual(report['retail_users'],[])
                    self.assertEqual(report['vector_origin'],'allocated')
                reports.append(dict(noun=field,report=report,binding=dict(asset_id=asset,object_index=owner,**{field+'_index':index},expected_sha256=source['effective_sha256'],source_key='a'*64)))
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        script="""import {decodeModelPrimitives} from './integrations/legaia/editor/model-primitives.js';
import {decodeVertexUsers} from './integrations/legaia/editor/model-vertex-users.js';
import {decodeNormalUsers} from './integrations/legaia/editor/model-normal-users.js';
import assert from 'node:assert/strict';let text='';for await(const chunk of process.stdin)text+=chunk;
const {source,reports}=JSON.parse(text),context={projectPath:'C:/private/project',sceneId:'scene://fixture',mode:'edit',sourceKey:source.project_source_key};
const decode=s=>decodeModelPrimitives(s,s.asset_id,context);decode(source);
for(const mutate of [s=>s.object_mappings[1].retail_index=0,s=>s.object_mappings[1].object_id='bad',s=>s.object_mappings[1].donor_object_id=s.object_mappings[1].object_id,s=>s.object_mappings[0].object_index=1,s=>s.vector_growth[1].vertices--,s=>s.face_mappings[1]=s.face_mappings[0]]){const bad=structuredClone(source);mutate(bad);assert.throws(()=>decode(bad));}
for(const {noun,report,binding} of reports){const fn=noun==='vertex'?decodeVertexUsers:decodeNormalUsers;fn(report,binding);const bad=structuredClone(report);bad.object_mappings[1].retail_index=0;assert.throws(()=>fn(bad,binding));}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,reports=reports)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_packet_edit_history_keeps_authored_object_identity(self):
        p,asset=self.fixture();source=p.model_primitive_source(asset)
        before=p.read_model_replacement(asset,p.model_overrides[asset]);identities=deepcopy(source['object_mappings'])
        edits=[dict(object_index=1,primitive_index=0,vertices=[7,6,5,0],normal_indices=[6,5,4,0])]
        for field in ('uvs','colors'):
            if source['objects'][1]['primitives'][0][field] is not None:
                edits[0][field]=source['objects'][1]['primitives'][0][field]
        review=p.preview_model_primitives(asset,edits,source['effective_sha256'],'a'*64)
        node=shutil.which('node')
        if node:
            for key in ('preview','current_preview'):review[key]['semantic_id']=asset
            script="""import {decodeModelPrimitives,decodeModelPrimitivePreview} from './integrations/legaia/editor/model-primitives.js';
let text='';for await(const chunk of process.stdin)text+=chunk;
const {source,review,edits}=JSON.parse(text),context={projectPath:'C:/private/project',sceneId:'scene://fixture',mode:'edit',sourceKey:source.project_source_key};
decodeModelPrimitivePreview(review,decodeModelPrimitives(source,source.asset_id,context),context,edits);
"""
            result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,review=review,edits=edits)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
            self.assertEqual(result.returncode,0,result.stderr)
        p.set_model_primitives(asset,edits,source['effective_sha256'],'a'*64,review['proposed_sha256'])
        after=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertNotEqual(after,before)
        self.assertEqual(p.model_overrides[asset]['ledger']['schema_version'],'legaia.model-face-addition-ledger.v7')
        self.assertEqual(p.model_primitive_source(asset)['object_mappings'],identities)
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),after)

    def test_shared_face_and_group_donors_qualify_copied_object_ancestry(self):
        from sdk import model_face_addition,model_group_allocation
        p,asset=self.fixture();source=model_face_addition.source(p,asset,'a'*64)
        self.enterContext(patch('sdk.model_group_allocation.source_key',return_value='a'*64))
        groups=model_group_allocation.source(p,asset,'a'*64)
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        script="""import {decodeFaceAdditionSource} from './integrations/legaia/editor/model-face-addition.js';
import {decodeGroupAllocationSource} from './integrations/legaia/editor/model-group-allocation.js';
import assert from 'node:assert/strict';let text='';for await(const chunk of process.stdin)text+=chunk;
const {source,groups}=JSON.parse(text),decode=s=>decodeFaceAdditionSource(s,s.asset_id,s.project_source_key);
decode(source);decodeGroupAllocationSource(groups,groups.asset_id,groups.project_source_key);
for(const mutate of [s=>s.topology.objects[1].donor_object_id=s.topology.objects[1].object_id,s=>s.topology.allocated_object_count++,s=>s.topology.objects[0].source_object_index=1,s=>s.topology.faces.find(f=>f.object_index===1).donor_face_id=s.topology.faces.find(f=>f.object_index===1).face_id]){const bad=structuredClone(source);mutate(bad);assert.throws(()=>decode(bad));}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(dict(source=source,groups=groups)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
