from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import os
import sys
import time
import unittest
from unittest.mock import patch

from sdk.project import ProjectError
from sdk.stability_checks import StabilityCheckService, snapshot


class StabilityChecksTests(unittest.TestCase):
    def test_worker_exception_with_cancel_is_failure_and_withdraws_running_row(self):
        s=StabilityCheckService()
        def fail(*args):
            s.cancelled.set()
            raise ProjectError('tree cancellation unconfirmed')
        with patch('sdk.stability_checks.tool',return_value=__file__),patch('sdk.stability_checks.snapshot',return_value=[]),patch.object(s,'_execute',side_effect=fail):
            s.start();s.worker.join(5)
        self.assertEqual(s.status()['status'],'failed')
        self.assertEqual(s.status()['checks'][0]['status'],'failed')
        self.assertEqual(s.status()['error'],'tree cancellation unconfirmed')

    def test_real_owned_process_cancellation_finishes_promptly(self):
        s=StabilityCheckService();timer=threading.Timer(.3,s.cancelled.set)
        timer.start();before=time.monotonic()
        try:
            result,code,output=s._execute([sys.executable,'-c','import time; time.sleep(30)'],Path.cwd(),dict(os.environ))
        finally:timer.cancel()
        self.assertEqual(result,'cancelled');self.assertNotEqual(code,0)
        self.assertLess(time.monotonic()-before,8)

    def test_snapshot_is_detached_complete_and_refuses_missing(self):
        with tempfile.TemporaryDirectory() as raw:
            copied=Path(raw)/'copy'
            rows=snapshot(Path(__file__).resolve().parents[3],copied)
            self.assertGreater(len(rows),16)
            self.assertEqual(snapshot(copied),rows)
            (copied/'runtime/src/main.cpp').write_bytes(b'changed')
            self.assertNotEqual(snapshot(copied),rows)
            (copied/'runtime/src/main.cpp').unlink()
            with self.assertRaises(ProjectError):snapshot(copied)

    def test_aggregate_success_requires_all_checks_and_fresh_sources(self):
        for changed in (False,True):
            s=StabilityCheckService()
            rows=[dict(path='fixture.c',sha256='a'*64,size=1)]
            with patch('sdk.stability_checks.tool',return_value=__file__),patch('sdk.stability_checks.snapshot',side_effect=[rows,[] if changed else rows]),patch.object(s,'_execute',return_value=('passed',0,'fixture passed')) as execute:
                s.start();s.worker.join(5)
            self.assertFalse(s.worker.is_alive());self.assertEqual(execute.call_count,3)
            report=s.status();self.assertEqual(report['status'],'source_changed' if changed else 'passed')
            self.assertFalse(report['runtime_binary_verified']);self.assertFalse(report['gameplay_verified'])
            report['sources'].clear();self.assertEqual(s.status()['sources'],rows)

    def test_cancel_identity_single_worker_and_failure_do_not_claim_pass(self):
        s=StabilityCheckService();entered=threading.Event();release=threading.Event()
        def execute(*args):entered.set();release.wait(5);return 'cancelled',-1,''
        with patch('sdk.stability_checks.tool',return_value=__file__),patch('sdk.stability_checks.snapshot',return_value=[]),patch.object(s,'_execute',side_effect=execute):
            job=s.start();self.assertTrue(entered.wait(5))
            with self.assertRaises(ProjectError):s.start()
            with self.assertRaises(ProjectError):s.cancel('wrong')
            s.cancel(job['id']);release.set();s.worker.join(5)
        self.assertEqual(s.status()['status'],'cancelled')
        self.assertEqual(s.status()['checks'][1]['status'],'pending')
        with patch('sdk.stability_checks.tool',return_value=__file__),patch('sdk.stability_checks.snapshot',return_value=[]),patch.object(s,'_execute',return_value=('failed',1,'compile failed')):
            s.start();s.worker.join(5)
        self.assertEqual(s.status()['status'],'failed')
        self.assertEqual(s.status()['checks'][0]['exit_code'],1)


if __name__=='__main__':unittest.main()
