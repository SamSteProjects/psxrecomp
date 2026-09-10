"""Socket failures must not trigger a second HTTP response."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.server import EditorHandler


class ResponseDisconnectTests(unittest.TestCase):
    def handler(self):
        handler = object.__new__(EditorHandler)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.close_connection = False
        return handler

    def test_disconnect_during_headers_or_body_closes_without_retry(self):
        for stage in ('headers', 'body'):
            for error in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
                with self.subTest(stage=stage, error=error):
                    handler = self.handler()
                    target = handler.end_headers if stage == 'headers' else handler.wfile.write
                    target.side_effect = error('client disconnected')
                    handler._json(200, {'ready': True})
                    self.assertTrue(handler.close_connection)
                    handler.send_response.assert_called_once_with(200)
                    if stage == 'headers':
                        handler.wfile.write.assert_not_called()

    def test_unrelated_failure_is_not_silenced(self):
        handler = self.handler()
        handler.wfile.write.side_effect = OSError('unrelated failure')
        with self.assertRaises(OSError):
            handler._json(200, {})
        self.assertFalse(handler.close_connection)


if __name__ == '__main__':
    unittest.main()
