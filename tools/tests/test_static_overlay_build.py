"""Build generated split overlays from an empty tree and after inventory changes.

Requires CMake and a C compiler. Run with Python unittest or directly.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StaticOverlayBuildTests(unittest.TestCase):
    def test_clean_and_incremental_generated_inventory(self):
        cmake = shutil.which('cmake')
        cc = os.environ.get('CC') or shutil.which('gcc') or shutil.which('clang')
        ninja = shutil.which('ninja')
        if not (cmake and cc and ninja):
            self.skipTest('CMake, Ninja and a C compiler are required')
        with tempfile.TemporaryDirectory(prefix='overlay build ') as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            build = root / 'build'
            recipe = source / 'recipe.txt'
            recipe.write_text('2 10 0', encoding='utf-8')
            (source / 'psx_runtime.h').write_text(
                '#ifndef TEST_PSX_RUNTIME_H\n#define TEST_PSX_RUNTIME_H\n'
                'typedef struct CPUState { int unused; } CPUState;\n#endif\n',
                encoding='utf-8')
            (source / 'generate.py').write_text(textwrap.dedent(f'''
                import sys
                from pathlib import Path
                sys.path.insert(0, {str(ROOT / 'tools')!r})
                import compile_overlays
                count, value, single = map(int, Path(sys.argv[1]).read_text().split())
                output = Path(sys.argv[2])
                output.parent.mkdir(parents=True, exist_ok=True)
                parts = []
                for i in range(count):
                    # The real generated prologue repeats these helper names
                    # across images, including images at the same guest PC.
                    raw = '#include "psx_runtime.h"\\n'
                    raw += ''.join('static int ' + helper + '(void) {{ return 0; }}\\n'
                                   for helper in ('psx_lwl', 'psx_lwr', 'psx_swl', 'psx_swr'))
                    raw += ('static int psx_alias_body_80100000(void) {{ return ' +
                            str(value + i) + '; }}\\n')
                    raw += ('int func_80100000(void) {{ return psx_alias_body_80100000() + '
                            'psx_lwl() + psx_lwr() + psx_swl() + psx_swr(); }}\\n')
                    renamed, symbols = compile_overlays.namespace_generated_static(
                        raw, f'ov_{{i}}', [0x80100000])
                    parts.append({{'namespace': f'ov_{{i}}', 'src': renamed}})
                dispatch = ''.join(f'int ov_{{i}}_func_80100000(void);\\n' for i in range(count))
                dispatch += 'int result(void) {{ return ' + '+'.join(
                    f'ov_{{i}}_func_80100000()' for i in range(count)) + '; }}\\n'
                compile_overlays.write_static_outputs(str(output), parts, [], dispatch,
                                                      single_file=bool(single))
            '''), encoding='utf-8')
            (source / 'main.c').write_text(
                '#include <stdio.h>\nint result(void);\n'
                'int main(void) { printf("%d\\n", result()); return 0; }\n',
                encoding='utf-8')
            (source / 'CMakeLists.txt').write_text(textwrap.dedent(f'''
                cmake_minimum_required(VERSION 3.20)
                project(StaticOverlayFixture C)
                include("{(ROOT / 'runtime/psx_static_overlay_parts.cmake').as_posix()}")
                set(out_dir "${{CMAKE_CURRENT_BINARY_DIR}}/generated")
                set(dispatch "${{out_dir}}/overlays_static.c")
                add_custom_command(OUTPUT "${{dispatch}}"
                    COMMAND "{Path(sys.executable).as_posix()}" "${{CMAKE_CURRENT_SOURCE_DIR}}/generate.py"
                        "${{CMAKE_CURRENT_SOURCE_DIR}}/recipe.txt" "${{dispatch}}"
                    DEPENDS "${{CMAKE_CURRENT_SOURCE_DIR}}/recipe.txt"
                    VERBATIM)
                add_custom_target(fixture_codegen DEPENDS "${{dispatch}}")
                psxrecomp_static_overlay_parts(parts fixture "${{dispatch}}")
                add_executable(fixture main.c "${{dispatch}}" ${{parts}})
                target_include_directories(fixture PRIVATE "${{CMAKE_CURRENT_SOURCE_DIR}}")
                add_dependencies(fixture fixture_codegen)
            '''), encoding='utf-8')

            def run(*args):
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout.strip()

            run(cmake, '-S', str(source), '-B', str(build), '-G', 'Ninja',
                f'-DCMAKE_C_COMPILER={Path(cc).as_posix()}')
            exe = build / ('fixture.exe' if os.name == 'nt' else 'fixture')
            for count, value, single in [(2, 10, 0), (5, 20, 0), (1, 30, 0),
                                          (1, 40, 0), (3, 50, 1), (35, 60, 0),
                                          (4, 70, 0)]:
                with self.subTest(count=count, value=value, single=single):
                    recipe.write_text(f'{count} {value} {single}', encoding='utf-8')
                    run(cmake, '--build', str(build), '--parallel', '2')
                    self.assertEqual(run(str(exe)),
                                     str(count * value + count * (count - 1) // 2))
            run(cmake, '--build', str(build), '--parallel', '2')


if __name__ == '__main__':
    unittest.main()
