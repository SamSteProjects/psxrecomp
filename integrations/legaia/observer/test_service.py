"""Small synthetic regressions for the restored read-only service boundary."""

import unittest
from unittest.mock import patch

from .client import ProtocolClient
from .errors import ProtocolError
from .service import ObserverService


class UnavailableClient:
    calls = []

    def __init__(self, *args, **kwargs):
        self.request_count = 0

    def negotiate(self):
        self.calls.append("protocol_info")
        raise ProtocolError("unknown command: protocol_info")

    def close(self):
        pass


class ObserverServiceTests(unittest.TestCase):
    def test_discovery_never_falls_back_to_raw_ram(self):
        UnavailableClient.calls = []
        service = ObserverService(client_factory=UnavailableClient)
        result = service.discover()
        self.assertFalse(result["available"])
        self.assertIsNone(result["observation"])
        self.assertEqual(result["reason"]["code"], "unsupported_protocol")
        self.assertEqual(UnavailableClient.calls, ["protocol_info"])
        self.assertEqual({p["scene"] for p in result["profiles"]}, {"town01", "town0c"})

    def test_old_epoch_does_not_start_new_observation(self):
        UnavailableClient.calls = []
        service = ObserverService(client_factory=UnavailableClient)
        result = service.observe(expected_epoch_id="epoch-obsolete")
        self.assertEqual(result["reason"]["code"], "stale_epoch")
        self.assertEqual(UnavailableClient.calls, [])
        self.assertIsNone(result["observation"])

    def test_read_only_command_cannot_be_replaced_in_params(self):
        client = ProtocolClient(startup_attempts=1)
        for fields in ({"cmd": "write"}, {"id": 99}):
            with self.assertRaises(ProtocolError):
                client.request("read_regions", **fields)
        with self.assertRaises(ProtocolError):
            client.request("set_input", buttons="0xFFEF")
        self.assertEqual(client.request_count, 0)

    def test_slow_partial_response_cannot_renew_timeout(self):
        class Socket:
            def settimeout(self, timeout):
                pass

            def recv(self, size):
                return b'{"id":'

        client = ProtocolClient(request_timeout=0.5)
        with patch("integrations.legaia.observer.client.time.monotonic", side_effect=[0.0, 0.1, 0.6]):
            with self.assertRaisesRegex(ProtocolError, "timed out"):
                client._receive_line(Socket())


if __name__ == "__main__":
    unittest.main()
