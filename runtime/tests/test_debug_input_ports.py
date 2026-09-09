#!/usr/bin/env python3
"""Execute real command handlers and frontend samplers with synthetic devices.

No retail data, window, TCP listener or game build is required. CC/CXX may
select compilers; otherwise use gcc/g++ (including the local Windows UCRT kit).
"""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SERVER = (ROOT / "runtime/src/debug_server.c").read_text(encoding="utf-8")
MAIN = (ROOT / "runtime/src/main.cpp").read_text(encoding="utf-8")


def function(source, name):
    # The next function definition closes the slice; braces inside comments
    # and JSON string literals must not confuse source extraction.
    start = re.search(r"^(?:static )?(?:int|void|uint32_t|const char \*)\s*" +
                      re.escape(name) + r"\([^;]*?\)\s*\{", source, re.M)
    assert start, name
    end = source.index("\n}", start.end()) + 2
    return source[start.start():end]


def compiler(env, name):
    selected = os.environ.get(env) or shutil.which(name)
    fallback = Path("C:/msys64/ucrt64/bin") / (name + ".exe")
    if not selected and fallback.is_file():
        selected = str(fallback)
    if not selected:
        raise RuntimeError(f"Set {env} to a {name}-compatible compiler")
    return selected


def execute(name, code, cxx=False):
    cc = compiler("CXX" if cxx else "CC", "g++" if cxx else "gcc")
    with tempfile.TemporaryDirectory(prefix="debug-input-") as tmp:
        source = Path(tmp) / (name + (".cpp" if cxx else ".c"))
        binary = Path(tmp) / (name + ".exe")
        source.write_text(code, encoding="utf-8")
        env = dict(os.environ)
        env["PATH"] = str(Path(cc).parent) + os.pathsep + env.get("PATH", "")
        subprocess.run([cc, "-std=c++17" if cxx else "-std=c11", "-O0",
                        str(source), "-o", str(binary)], check=True, env=env)
        subprocess.run([str(binary)], check=True, env=env)


def test_handlers():
    state = SERVER.split("/* ---- Input override ---- */", 1)[1].split(
        "/* ---- Frontend turbo override ---- */", 1)[0]
    names = ["json_get_str", "json_get_int", "hex_to_u32", "input_command_port",
             "handle_set_input", "handle_press", "debug_server_reset_input", "handle_clear_input",
             "handle_input_route_clear", "handle_input_route_append",
             "handle_input_route_start", "handle_input_route_stop",
             "debug_server_get_input_override", "debug_server_get_axis_override",
             "debug_server_get_input_port"]
    code = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define PSX_BSS
#define PSX_MAX_PLAYERS 5
static int errors, oks;
static uint64_t s_frame_count;
static void send_err(int id, const char *message) { (void)id; (void)message; ++errors; }
static void send_ok(int id) { (void)id; ++oks; }
static void send_fmt(const char *fmt, ...) { (void)fmt; }
''' + state + "\n".join(function(SERVER, name) for name in names) + r'''
int main(void) {
    unsigned char axes[4];
    handle_set_input(1, "{\"buttons\":\"0xFFEF\"}");
    assert(!errors && debug_server_get_input_port() == 1);
    assert(debug_server_get_input_override() == 0xFFEF);
    handle_press(1, "{\"buttons\":65503,\"frames\":2,\"port\":2,\"lx\":20}");
    assert(!errors && debug_server_get_input_port() == 2);
    assert(debug_server_get_input_override() == 65503);
    assert(debug_server_get_input_override() == 65503);
    assert(debug_server_get_input_port() == 2); /* final sampled frame */
    assert(debug_server_get_axis_override(axes) && axes[0] == 20);
    assert(debug_server_get_input_override() == -1);
    const char *invalid[] = {"0", "3", "-1", "2.5", "null", "true",
                            "\"2junk\"", "4294967297", "\"\""};
    for (unsigned i = 0; i < sizeof(invalid)/sizeof(invalid[0]); ++i) {
        char command[128];
        snprintf(command, sizeof(command), "{\"buttons\":\"0xFFFF\",\"port\":%s}", invalid[i]);
        int before = errors;
        handle_set_input(1, command);
        assert(errors == before + 1 && s_input_port == 2 && s_input_override == -1);
    }
    handle_press(1, "{\"buttons\":65519,\"frames\":0,\"port\":1}");
    assert(s_input_port == 2 && s_input_override == -1);
    handle_clear_input(1, "{}");
    assert(debug_server_get_input_port() == 1 && !debug_server_get_axis_override(axes));
    handle_input_route_append(1, "{\"buttons\":65519,\"frames\":1}");
    handle_input_route_start(1, "{\"port\":2}");
    assert(debug_server_get_input_port() == 2);
    int before = errors;
    handle_set_input(1, "{\"buttons\":\"0xFFFF\",\"port\":1}");
    assert(errors == before + 1 && debug_server_get_input_port() == 2);
    assert(debug_server_get_input_override() == 65519);
    assert(debug_server_get_input_override() == -1);
    handle_input_route_start(1, "{}");
    assert(debug_server_get_input_port() == 1); /* no inherited port-2 route */
    handle_input_route_stop(1, "{}");
    assert(debug_server_get_input_override() == -1);
    puts("debug input handlers: passed");
}
'''
    execute("handlers", code)
    single = code[:code.index("int main(void)")].replace(
        "#define PSX_MAX_PLAYERS 5", "#define PSX_MAX_PLAYERS 1") + r'''
int main(void) {
    handle_press(1, "{\"buttons\":65519,\"port\":2}");
    assert(errors==1 && s_input_override==-1 && s_input_port==1);
    handle_set_input(1, "{\"buttons\":\"0xFFEF\"}");
    assert(s_input_override==65519 && s_input_port==1);
    debug_server_reset_input();
    assert(s_input_override==-1 && s_input_route_count==0 && s_input_port==1);
    puts("single-player debug input validation and session reset: passed");
}
'''
    execute("handlers-single", single)


def test_frontend():
    code = r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#define PSX_MAX_PLAYERS 5
namespace PSXRecompV4 { enum { PAD_MODE_ANALOG = 1 }; }
struct PlayerInput { int kind = 0; int mode = 0; };
struct PsxNetPad { uint16_t buttons = 0xFFFF; uint8_t lx=128,ly=128,rx=128,ry=128;
                  uint8_t analog=0,connected=0; };
static PlayerInput g_players[PSX_MAX_PLAYERS];
static PsxNetPad sio[PSX_MAX_PLAYERS], physical[PSX_MAX_PLAYERS];
static int port=1, g_offline_pad_count=2, policy_slot=-1;
static bool mash_on=false;
static int debug_server_get_input_port() { return port; }
static int debug_server_get_axis_override(unsigned char st[4]) { st[0]=20; return 1; }
static int effective_player_mode(PlayerInput& p) { return p.mode; }
static bool dev_any_input_enabled() { return false; }
static int controller_policy_resolve_override_mode(int s,int player,int mode,uint16_t,uint8_t*,bool,bool) {
    assert(player==s+1); policy_slot=s; return mode;
}
static int sio_get_pad_connected(int s) { return sio[s].connected; }
static int sio_get_pad_analog(int s) { return sio[s].analog; }
static uint16_t sio_get_pad_buttons_slot(int s) { return sio[s].buttons; }
static void sio_set_pad_connected(int s,int c) { sio[s].connected=c; }
static void sio_request_pad_type(int s,int a) { sio[s].analog=a; }
static void sio_set_pad_state_slot(int s,uint16_t w) { sio[s].buttons=w; }
static void sio_set_pad_sticks(int s,uint8_t a,uint8_t b,uint8_t c,uint8_t d) {
    sio[s].lx=a; sio[s].ly=b; sio[s].rx=c; sio[s].ry=d;
}
static void psx_selfcheck_note_pad(int,uint16_t,uint8_t,uint8_t,uint8_t,uint8_t,uint8_t) {}
static bool psx_selfcheck_mash_override(uint16_t *w) { *w=0xFFDF; return mash_on; }
static bool psx_start_consumer_enabled() { return false; }
static uint32_t psx_start_consumer_offline_frame() { return 0; }
static void psx_start_consumer_note(int,uint32_t,uint16_t) {}
static bool psx_start_bisect_enabled() { return false; }
static int netplay_sdl_start_held(int) { return 0; }
static void psx_start_bisect_log(const char*,uint32_t,int,int,int,int,int,int,int) {}
static int capture_pad_slot(int s,PsxNetPad *p) { *p=physical[s]; return p->connected; }
static void apply_pad_slot_to_sio(int s,const PsxNetPad& p) { sio[s]=p; }
''' + "\n".join(function(MAIN, name) for name in [
        "debug_input_override_slot", "prepare_input_override_slot",
        "apply_input_override_to_sio", "sample_pad_into_sio",
        "sample_headless_pad_into_sio"]) + r'''
int main() {
    physical[0].connected=1; physical[0].buttons=0xFFFE;
    g_players[1].mode=1; port=2;
    sample_pad_into_sio(0xFFEF);
    assert(sio[0].buttons==0xFFFE); /* P1 physical input still sampled */
    assert(sio[1].buttons==0xFFEF && sio[1].lx==20 && sio[1].connected==1);
    assert(policy_slot==1);
    physical[0].buttons=0xFFFD;
    sample_pad_into_sio(0xFFEF);
    assert(sio[0].buttons==0xFFFD);
    sample_pad_into_sio(-1);
    assert(sio[1].buttons==0xFFFF && sio[1].lx==128 && sio[1].connected==0);
    sample_pad_into_sio(0xFFEF); /* port-2 press then change to port 1 */
    port=1; sample_pad_into_sio(0xFFDF);
    assert(sio[1].buttons==0xFFFF && sio[1].lx==128 && sio[1].connected==0);
    assert(sio[0].buttons==0xFFDF);
    sample_pad_into_sio(-1);
    assert(sio[0].buttons==0xFFFD && sio[0].connected==1);
    g_offline_pad_count=1; port=2; sample_pad_into_sio(0xFFEF);
    assert(sio[1].buttons==0xFFEF); /* unassigned P2 still injectable */
    sample_headless_pad_into_sio(-1);
    assert(sio[1].buttons==0xFFFF && sio[1].lx==128 && sio[1].connected==0);
    sample_headless_pad_into_sio(0xFFEF);
    assert(sio[0].buttons==0xFFFF && sio[1].buttons==0xFFEF);
    sample_headless_pad_into_sio(-1);
    assert(sio[1].buttons==0xFFFF && sio[1].lx==128);
    mash_on=true; sample_pad_into_sio(-1);
    assert(sio[0].buttons==0xFFDF && sio[1].buttons==0xFFFF); /* mash remains P1 */
    mash_on=false; sample_pad_into_sio(-1);
    port=1; g_players[0].kind=1; sample_pad_into_sio(0xFFEF);
    g_players[0].kind=0; physical[0].connected=0; sio[0].connected=0;
    sample_pad_into_sio(-1); /* unplugged while overridden */
    assert(sio[0].connected==0 && sio[0].buttons==0xFFFF);
    puts("debug input frontend isolation and release: passed");
}
'''
    execute("frontend", code, cxx=True)
    single = code[:code.index("int main()")].replace(
        "#define PSX_MAX_PLAYERS 5", "#define PSX_MAX_PLAYERS 1") + r'''
int main() {
    g_offline_pad_count=1;
    port=2; assert(debug_input_override_slot()==0); /* defensive fallback */
    sample_headless_pad_into_sio(0xFFEF);
    assert(sio[0].buttons==0xFFEF);
    prepare_input_override_slot(-1); /* same order as the session init path */
    sio[0]=PsxNetPad{};
    sample_headless_pad_into_sio(0xFFDF);
    assert(sio[0].buttons==0xFFDF && sio[0].connected==1);
    sample_headless_pad_into_sio(-1);
    assert(sio[0].connected==0 && sio[0].buttons==0xFFFF);
    puts("single-player frontend bounds and fresh-session ownership: passed");
}
'''
    execute("frontend-single", single, cxx=True)
    init = MAIN[MAIN.index("session_reboot:"):MAIN.index("sio_init();", MAIN.index("session_reboot:"))]
    assert "prepare_input_override_slot(-1);" in init
    assert "debug_server_reset_input();" in init


def test_client():
    spec = importlib.util.spec_from_file_location("debug_client", ROOT / "tools/debug_client.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build_cmd(["input", "0xFFEF", "port=2"])[0]["port"] == 2
    assert module.build_cmd(["press", "0xFFEF", "3", "port=2"])[0] == {
        "cmd": "press", "buttons": 65519, "frames": 3, "port": 2}
    assert "port" not in module.build_cmd(["input", "0xFFEF"])[0]
    assert module.build_cmd(["press", "0xFFEF", "port=3"])[0] is None
    assert module.build_cmd(["input", "0xFFEF", "port=abc"])[0] is None
    print("debug input client: passed")


if __name__ == "__main__":
    test_handlers()
    test_frontend()
    test_client()
