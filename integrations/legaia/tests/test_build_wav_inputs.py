"""Frozen input receipt qualification without claiming native ZIP verification."""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
import base64,json,os,threading,unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import test_audio_sample_sources as source_tests
from sdk.project import ProjectError,canonical
from sdk.build import authored_state_key
from sdk.build_history import _load
from sdk.audio_sample_sources import preserve_build_inputs,source_path
from sdk.build_wav_inputs import snapshots,inputs,download
from sdk.server import EditorServer,EditorHandler

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class BuildWavs(unittest.TestCase):
    setUpClass=classmethod(source_tests.WavInputs.setUpClass.__func__)
    setUp=source_tests.WavInputs.setUp
    tearDown=source_tests.WavInputs.tearDown
    args=source_tests.WavInputs.args
    retain=source_tests.WavInputs.retain

    def frozen(self):
        record,wav=self.retain();key=authored_state_key(self.project)
        audit=dict(schema_version='legaia.build-audit.v1',disc_sha256=record['source_record']['disc_sha256'],build_kind='authored',edits=[],overlays=[])
        raw=canonical(audit);audit_hash=sha256(raw).hexdigest();identifier=audit_hash[:16];root=self.project.root/'Builds'/identifier;root.mkdir(parents=True)
        package='legaia.sdk.'+'1'*12;version='0.1.0-'+identifier
        receipt=dict(schema_version='legaia.build-receipt.v1',authored_state_key=key,audit_sha256=audit_hash,manifest_sha256='2'*64,archive_sha256='3'*64,source_disc_sha256=audit['disc_sha256'],runtime_status='package_built_not_launched',feature_id='placements',build_kind='authored',archive_bytes=1,package_id=package,version=version,archive_file=package+'-'+version+'.psxmod')
        (root/'build-audit.json').write_bytes(raw);(root/'build-receipt.json').write_bytes(canonical(receipt));preserve_build_inputs(self.project,root,key,self.project.root)
        return record,wav,key,dict(id=identifier,expected_archive_sha256=receipt['archive_sha256'],expected_project_key=key),root

    def test_frozen_recovery_independent_of_current_and_different_input_receipts(self):
        record,wav,key,args,root=self.frozen();self.project.undo();source_path(self.project,record).write_bytes(b'changed unregistered Current file');args['expected_project_key']=authored_state_key(self.project)
        listing=snapshots(self.project,**args);self.assertEqual(listing['snapshots'],[dict(input_key=key,matches_current_inputs=False,integrity='not_checked')])
        options=inputs(self.project,**args,input_key=key);self.assertEqual(options['sources'],[record]);self.assertEqual(options['package_integrity'],'not_checked')
        recovered=download(self.project,**args,input_key=key,expected_manifest_key=options['manifest_key'],receipt_key=record['receipt_key']);self.assertEqual(base64.b64decode(recovered['wav_base64']),wav)
        # An unrelated bad Current-input receipt cannot replace this historical receipt.
        path=root/'input-receipts';path.mkdir();(path/(args['expected_project_key']+'.json')).write_text('{}')
        with self.assertRaises(ProjectError):_load(self.project,args['id'])
        self.assertEqual(inputs(self.project,**args,input_key=key)['sources'],[record])

    def test_stale_unknown_receipt_and_modified_manifest_or_wav_reject(self):
        record,wav,key,args,root=self.frozen();options=inputs(self.project,**args,input_key=key);base=dict(**args,input_key=key,expected_manifest_key=options['manifest_key'],receipt_key=record['receipt_key'])
        for extra in ({'expected_project_key':'f'*64},{'expected_archive_sha256':'f'*64},{'expected_manifest_key':'f'*64},{'receipt_key':'f'*64},{'input_key':'f'*64}):
            with self.assertRaises(ProjectError):download(self.project,**{**base,**extra})
        path=root/'wav-inputs'/key/(record['wav_sha256']+'.wav');path.write_bytes(wav[:-1]+bytes([wav[-1]^1]))
        with self.assertRaises(ProjectError):inputs(self.project,**args,input_key=key)
        path.write_bytes(wav);manifest=root/'wav-inputs'/key/'manifest.json';value=json.loads(manifest.read_text());value['files'][0]['byte_length']+=1;manifest.write_text(json.dumps(value))
        with self.assertRaises(ProjectError):inputs(self.project,**args,input_key=key)

    def test_http_exact_snapshot_inspection_and_frozen_download(self):
        record,wav,key,args,_=self.frozen();before=deepcopy(self.project._document());server=EditorServer(('127.0.0.1',0),self.project);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,value):
            request=Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=30) as response:return json.load(response)
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                self.assertEqual(len(post('/api/builds/wav-snapshots',args)['snapshots']),1)
                options=post('/api/builds/wav-inputs',dict(**args,input_key=key));value=post('/api/builds/wav-download',dict(**args,input_key=key,expected_manifest_key=options['manifest_key'],receipt_key=record['receipt_key']))
                self.assertEqual(base64.b64decode(value['wav_base64']),wav)
                with self.assertRaises(HTTPError) as error:post('/api/builds/wav-snapshots',{**args,'extra':1})
                error.exception.close();self.assertEqual(self.project._document(),before)
            finally:server.shutdown();server.server_close();worker.join(timeout=10)

if __name__=='__main__':unittest.main()
