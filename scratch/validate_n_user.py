# ###################################################################################
# VALIDATION SCRIPT
# ###################################################################################
import subprocess
import sys
import py_compile

def run_command(cmd, shell=False):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED (code {res.returncode}):")
        print(res.stdout)
        print(res.stderr)
        return False, res.stdout, res.stderr
    print("SUCCESS")
    return True, res.stdout, res.stderr

def main():
    # 1. Compile Python files
    py_files = [
        "appverbo/menu_settings.py",
        "appverbo/routes/profile/profile_handlers.py"
    ]
    for pf in py_files:
        print(f"Compiling {pf}...")
        try:
            py_compile.compile(pf, doraise=True)
            print("SUCCESS")
        except Exception as e:
            print(f"Compilation failed for {pf}: {e}")
            sys.exit(1)
            
    # 2. Node syntax checks
    js_files = [
        "static/js/modules/dynamic_process_runtime_core_v1.js",
        "static/js/modules/dynamic_process_history_renderer_v1.js"
    ]
    for jf in js_files:
        ok, out, err = run_command(["node", "--check", jf])
        if not ok:
            print("Javascript syntax check failed!")
            sys.exit(1)

    # 3. git diff --check
    ok, out, err = run_command(["git", "diff", "--check"])
    if not ok:
        print("Git whitespace check failed!")
        sys.exit(1)

    print("\n--- ALL STATIC CHECKS PASSED SUCCESSFULLY ---")

if __name__ == "__main__":
    main()
