"""Saved inspection tree metadata composes with camera history, never game data."""
from copy import deepcopy
import json,subprocess,unittest
from sdk.hierarchy_views import hierarchy,query
from sdk.project import ProjectError,ProjectService
from sdk.build import authored_state_key
from sdk.scene_preview import source_key
import test_scene_views as fixtures


class HierarchyViewTests(unittest.TestCase):
    def test_server_client_query_acceptance_parity(self):
        corpus=['','Actor','type:actor -authored:true','name:"Actor One"','"name:literal"','scene://town01/actors','id:scene://town01','-"actor one"','name:"escaped \\" word"','""','name:','-','unknown:x','"unclosed','"escape\\','x'*2048,'x'*2049,'😀'*1024,'😀'*1025,' '.join(['a']*32),' '.join(['a']*33),'type:actor\ufeff-authored:true','name:"Actor\nOne"']
        expected=[]
        corpus+=['attached:ModelRenderer','model:asset://fixture/models/0001','retail_model:0001 current_model:0002','animation:scene-anm','retail_animation:0001 -current_animation:authored-record','current_animation:','retail_model:']
        for text in corpus:
            try:query(text);expected.append(True)
            except ProjectError:expected.append(False)
        script="""import {parseHierarchyQuery} from './integrations/legaia/editor/hierarchy-query.js';let text='';for await(const c of process.stdin)text+=c;console.log(JSON.stringify(JSON.parse(text).map(q=>{try{parseHierarchyQuery(q);return true;}catch{return false;}})));"""
        run=subprocess.run(['C:/Program Files/nodejs/node.exe','--input-type=module','-e',script],input=json.dumps(corpus),capture_output=True,text=True,encoding='utf-8');self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout),expected)

    def test_metadata_crud_review_history_save_open_and_native_inputs(self):
        helper=fixtures.SceneViewTests();helper.setUp();self.addCleanup(helper.doCleanups);p=helper.p
        before=deepcopy(p._document());inputs=deepcopy((p.imports,p.overrides,authored_state_key(p),source_key(p)));display=deepcopy(fixtures.DISPLAY);display['hierarchy']=dict(query='type:actor -authored:true',collapsed_groups=['actors','script'])
        row=helper.create('Actor inspection',display);self.assertEqual(row['display'],display);stale=helper.cmd('delete_scene_view',row)
        replacement=deepcopy(display);replacement['hierarchy']=dict(query='type:actor attached:ActorAnimation retail_animation:scene-anm current_animation:authored-record',collapsed_groups=[])
        p.command(helper.cmd('update_scene_view',row,display=replacement));self.assertEqual(p.scene_views[row['id']]['display'],replacement)
        with self.assertRaises(ProjectError):p.command(stale)
        opened=ProjectService.open(p.save());self.assertEqual(opened.scene_views,p.scene_views);self.assertEqual((p.imports,p.overrides,authored_state_key(p),source_key(p)),inputs)
        p.undo();self.assertEqual(p.scene_views[row['id']]['display'],display);p.undo();self.assertEqual(p._document(),before);p.redo();p.redo();self.assertEqual(p.scene_views,opened.scene_views)

    def test_invalid_queries_folds_and_metadata_reject_atomically(self):
        helper=fixtures.SceneViewTests();helper.setUp();self.addCleanup(helper.doCleanups);p=helper.p;held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        for value in [dict(query='name:',collapsed_groups=[]),dict(query=True,collapsed_groups=[]),dict(query='x',collapsed_groups=['script','actors']),dict(query='x',collapsed_groups=['unknown']),dict(query='x',collapsed_groups=['actors','actors']),dict(query='x',collapsed_groups=[None]),dict(query='x',collapsed_groups=[] ,runtime={})]:
            d=deepcopy(fixtures.DISPLAY);d['hierarchy']=value
            with self.subTest(value=value),self.assertRaises(ProjectError):helper.create('Invalid',d)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
        value=dict(query='',collapsed_groups=[]);decoded=hierarchy(value);decoded['collapsed_groups'].append('actors');self.assertEqual(value,dict(query='',collapsed_groups=[]))


if __name__=='__main__':unittest.main()
