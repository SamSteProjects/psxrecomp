"""Small synthetic regressions for the restored read-only service boundary."""

import unittest
from copy import deepcopy
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
    def compatible_service(self, *, profile_id=None, wrong_identity=False, statuses=None, transform=None):
        calls = []
        service = None

        class Client:
            request_count = 0

            def __init__(self, *args, **kwargs):
                pass

            def negotiate(self):
                calls.append("protocol_info")
                wanted = service._select(profile_id).document["supported_runtime_protocol"]
                return {"protocol": {"name": wanted["name"], "major": wanted["minimum_major"],
                                     "minor": wanted["minimum_minor"]},
                        "capabilities": wanted["required_capabilities"], "server": {"kind": "native"}}

            def runtime_identity(self):
                calls.append("runtime_identity")
                expected = service._select(profile_id).document["executable_identity"]
                source = deepcopy(expected["runtime_source_identity"])
                if wrong_identity:
                    source["sha256"] = "0" * 64
                return {"runtime": {"implementation": "psxrecomp", "process_instance_id": "proc-fixture"},
                        "main_executable": {"serial": expected["serial"], "source_identity": source,
                                            "canonical_length": source["length"], "guest_base": source["guest_base"]}}

            def execution_witness(self, pc):
                calls.append(("execution_witness", pc))
                status = (statuses or {}).get(pc, "missing")
                witness = None if status == "missing" else {
                    "resolved_pc": pc, "observation_current": status == "current",
                    "range": {"kind": "executed-instruction", "guest_base": pc, "length": 4,
                              "instruction_count": 1, "block_range_available": False}}
                response = {"requested_pc": pc, "status": status, "witness": witness}
                return transform(response) if transform else response

            def close(self):
                calls.append("close")

        service = ObserverService(client_factory=Client)
        self.addCleanup(service.close)
        return service, calls

    def test_discovery_primes_every_selected_pc_but_does_not_verify_scene(self):
        for selected in (None, "legaia-na-scus94254-field-v1"):
            with self.subTest(profile=selected):
                service, calls = self.compatible_service(profile_id=selected)
                pcs = [w["pc"] for w in service._select(selected).document["execution_identity"]["required_witnesses"]]
                result = service.discover(selected)
                self.assertTrue(result["available"])
                self.assertEqual(result["state"], "compatible_runtime")
                self.assertFalse(result["scene_verified"])
                self.assertIsNone(result["observation"])
                self.assertEqual(result["ram_writes"], 0)
                self.assertEqual(result["witness_tracking"], {"status": "primed", "requested_pcs": pcs,
                                 "initial_statuses": [{"pc": pc, "status": "missing"} for pc in pcs]})
                self.assertEqual(calls, ["protocol_info", "runtime_identity"] + [("execution_witness", pc) for pc in pcs])
                self.assertIsNone(service._last_epoch)

    def test_identity_failure_never_arms_a_witness(self):
        service, calls = self.compatible_service(wrong_identity=True)
        result = service.discover()
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"]["code"], "profile_rejected")
        self.assertNotIn("witness_tracking", result)
        self.assertEqual(calls, ["protocol_info", "runtime_identity", "close"])

    def test_initial_current_stale_and_ambiguous_are_not_scene_acceptance(self):
        statuses = {"0x801CF754": "current", "0x801DE840": "stale", "0x801D79E8": "ambiguous"}
        service, _ = self.compatible_service(statuses=statuses)
        result = service.discover()
        self.assertTrue(result["available"])
        self.assertFalse(result["scene_verified"])
        self.assertIsNone(result["observation"])
        self.assertEqual(result["witness_tracking"]["initial_statuses"],
                         [{"pc": pc, "status": status} for pc, status in statuses.items()])

    def test_malformed_or_partial_priming_never_reports_success(self):
        def current_bad_range(response):
            response.update(status="current", witness={"resolved_pc": response["requested_pc"],
                            "observation_current": True, "range": {"length": 4096}})
            return response

        def fail_second(response):
            if response["requested_pc"] == "0x801DE840":
                raise ProtocolError("request interrupted")
            return response

        transforms = (lambda r: None, lambda r: dict(r, requested_pc="0x80000000"),
                      lambda r: dict(r, status="ready"), lambda r: dict(r, witness={}),
                      current_bad_range, fail_second)
        for transform in transforms:
            with self.subTest(transform=transform):
                service, calls = self.compatible_service(transform=transform)
                result = service.discover()
                self.assertFalse(result["available"])
                self.assertNotIn("witness_tracking", result)
                self.assertIsNone(result["observation"])
                self.assertEqual(calls[-1], "close")

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
