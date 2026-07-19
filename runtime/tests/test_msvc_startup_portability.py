"""Structural guards for the MSVC startup and build portability contract."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / "runtime" / "src" / "main.cpp").read_text(encoding="utf-8")
RUNTIME_CMAKE = (ROOT / "runtime" / "runtime.cmake").read_text(encoding="utf-8")


class MsvcStartupPortabilityTests(unittest.TestCase):
    def test_windows_stdio_setup_avoids_ucrt_invalid_parameter_fail_fast(self):
        main_start = MAIN.index("int main(int argc, char** argv)")
        first_marker = MAIN.index('"psxrecomp: main() entered\\n"', main_start)
        startup = MAIN[main_start:first_marker]

        windows_branch = re.search(
            r"#ifdef _WIN32(?P<body>.*?)#else", startup, re.DOTALL
        )
        self.assertIsNotNone(windows_branch)
        body = windows_branch.group("body")
        self.assertEqual(body.count("_IONBF"), 2)
        self.assertNotIn("_IOLBF", body)
        self.assertNotRegex(body, r"_IOLBF\s*,\s*0")

    def test_idle_skip_uses_the_shared_c_linkage_declaration(self):
        self.assertIn('#include "psx_cycles.h"', MAIN)
        self.assertNotIn("extern int g_idle_skip_enabled;", MAIN)

    def test_msvc_workarounds_are_target_scoped(self):
        msvc = RUNTIME_CMAKE[RUNTIME_CMAKE.index("elseif(MSVC)") :]
        self.assertIn("target_compile_definitions(${target} PRIVATE NOMINMAX)", msvc)
        self.assertIn("target_compile_options(${target} PRIVATE /experimental:c11atomics)", msvc)
        self.assertIn("/STACK:67108864,67108864", msvc)


if __name__ == "__main__":
    unittest.main()
