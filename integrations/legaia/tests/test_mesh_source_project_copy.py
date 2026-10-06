"""Copies and saved export inputs retain qualified original mesh dependencies."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,shutil,subprocess,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError,canonical
from sdk import project_copy,project_copy_history,export_snapshot,export_history,model_mesh_sources
import test_model_mesh_source_retention as source_fixtures
import test_model_mesh_append as fixtures

class MeshSourceCopyTests(unittest.TestCase):
    def fixture(self):
        helper=source_fixtures.MeshSourceTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();content=fixtures.glb()
        helper.apply(p,asset,donor,content,new_group=True);p.save()
        helper.apply(p,asset,donor,content,new_group=True,source_offset=[10,20,30])
        return p,asset,content

    def test_deduplicated_current_sources_copy_reopen_and_editor_inventory(self):
        p,asset,content=self.fixture();glb_hash=sha256(content).hexdigest();relative=f'Authored/Models/Sources/{glb_hash}.glb'
        orphan=p.root/'Authored/Models/Sources'/('f'*64+'.glb');orphan.write_bytes(b'unreferenced')
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.saved_digest));metadata=(p.root/'project.legaia.json').read_bytes()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            report=project_copy.review(p);self.assertEqual([x['path'] for x in report['files'] if '/Sources/' in x['path']],[relative])
            created=project_copy.create_copy(p,'Mesh branch',report['review_key']);clone=ProjectService.open(Path(created['copied_project']))
            self.assertEqual(clone.read_model_replacement(asset,clone.model_overrides[asset]),p.read_model_replacement(asset,p.model_overrides[asset]))
            self.assertEqual((clone.root/relative).read_bytes(),content);self.assertFalse((clone.root/relative).with_name(orphan.name).exists())
            key=model_mesh_sources.catalog(clone,asset,'a'*64)['project_source_key'];receipt=clone.model_overrides[asset]['mesh_imports'][1]
            self.assertEqual(model_mesh_sources.download(clone,asset,key,receipt['receipt_key'])['selected'],receipt)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack,p.saved_digest),before);self.assertEqual((p.root/'project.legaia.json').read_bytes(),metadata)
        self.assertEqual(project_copy_history.list_copies(p)['copies'][0]['status'],'recorded_copy')
        script="""import {decodeCopyReview,decodeCreatedCopy} from './integrations/legaia/editor/project-copy.js';import assert from 'node:assert/strict';let text='';for await(const c of process.stdin)text+=c;const {review,created}=JSON.parse(text);decodeCopyReview(review,review.project_source_key,review.source_project);decodeCreatedCopy(created,created.project_source_key,created.source_project);for(const path of ['Authored/Models/Sources/../outside.glb','Authored/Models/Sources/not-a-hash.glb','Authored/Models/Sources/'+ 'f'.repeat(64)+'.png']){const r=structuredClone(review);r.files[0].path=path;assert.throws(()=>decodeCopyReview(r,r.project_source_key,r.source_project));}const r=structuredClone(review);r.files.push({path:'Authored/TextureSources/'+'f'.repeat(64)+'.png',sha256:'f'.repeat(64),byte_length:1});r.file_count++;r.byte_length++;decodeCopyReview(r,r.project_source_key,r.source_project);"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(review=report,created=created)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3]);self.assertEqual(result.returncode,0,result.stderr)

    def test_snapshot_recovery_copies_sources_without_exporting_disc(self):
        p,asset,content=self.fixture();key,files=export_snapshot.capture_export_inputs(p)
        identifier='experimental-drafts-'+'c'*32;directory=p.root/'Builds'/identifier;directory.mkdir(parents=True)
        snapshot=export_snapshot.write_export_inputs(directory,key,files)
        # Synthetic completion metadata exercises input recovery without any disc export.
        report=dict(schema_version='legaia.experimental-draft-export.v1',archive={},disc=dict(output_sha256='a'*64,output_bytes=1,reopened_prot_verified=True),input_snapshot=snapshot)
        (directory/'report.json').write_bytes(canonical(report));held={str(f.relative_to(directory)):f.read_bytes() for f in directory.rglob('*') if f.is_file()}
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            destination=export_history.copy_export_inputs(p,identifier);clone=ProjectService.open(destination)
            clone.read_model_replacement(asset,clone.model_overrides[asset])
            self.assertEqual((clone.root/'Authored/Models/Sources'/(sha256(content).hexdigest()+'.glb')).read_bytes(),content)
        self.assertEqual({str(f.relative_to(directory)):f.read_bytes() for f in directory.rglob('*') if f.is_file()},held)

    def test_retained_texture_pngs_are_copyable_and_listed(self):
        import test_texture_slot_sources as texture_fixtures
        from sdk import texture_slot_sources
        from sdk.scene_preview import source_key
        self.enterContext(patch('sdk.texture_slots.source_key',side_effect=source_key))
        self.enterContext(patch('sdk.texture_slot_sources.source_key',side_effect=source_key))
        helper=texture_fixtures.SlotSources();self.addCleanup(helper.doCleanups)
        p,identifier,png,stp,options,native=helper.setup_project()
        args=(p,identifier,sha256(native).hexdigest(),source_key(p),png,options,stp)
        reviewed=texture_slot_sources.review(*args);texture_slot_sources.apply(*args,reviewed['review_key'])
        reviewed=project_copy.review(p);created=project_copy.create_copy(p,'Texture source branch',reviewed['review_key'])
        clone=ProjectService.open(Path(created['copied_project']))
        original_png,original_stp,_=texture_slot_sources.read_sources(clone,clone.texture_additions[identifier])
        self.assertEqual((original_png,original_stp),(png,stp))
        self.assertEqual(project_copy_history.list_copies(p)['copies'][0]['status'],'recorded_copy')

    def test_missing_changed_sources_and_input_limits_reject_before_copy(self):
        p,asset,content=self.fixture();report=project_copy.review(p);path=p.root/'Authored/Models/Sources'/(sha256(content).hexdigest()+'.glb')
        path.write_bytes(content[:-1]+b'x')
        with self.assertRaises(ProjectError):project_copy.create_copy(p,'Reject',report['review_key'])
        self.assertFalse((p.root/'ProjectCopies').exists());path.unlink()
        with self.assertRaises(ProjectError):project_copy.review(p)
        path.write_bytes(content)
        _,files=export_snapshot.capture_export_inputs(p)
        with self.assertRaisesRegex(ProjectError,'file limit'):export_snapshot.capture_export_inputs(p,max_files=len(files)-1)
        with self.assertRaisesRegex(ProjectError,'byte limit'):export_snapshot.capture_export_inputs(p,max_bytes=sum(map(len,files.values()))-1)

if __name__=='__main__':unittest.main()
