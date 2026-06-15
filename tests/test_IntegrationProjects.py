"""
Integration tests: clone small GitHub projects and run MediumDarwin
against them in 4 configurations per project, in parallel.

3 build systems (Maven, Gradle, Ant) × 4 configs = 12 runs total.

Configurations:
  plain    – mutation + build
  testsel  – code-coverage-backed test selection + subsumption
  schemata – mutant schemata generation
  full     – coverage + subsumption + schemata

Projects are cloned fresh from GitHub at runtime.
No build-file modifications are required — every project works OOTB.
"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------------------------------
# Paths  (all relative – no absolute paths)
# ------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_MD_SCRIPT = os.path.join(_REPO_ROOT, "MediumDarwin.py")

# ------------------------------------------------------------------------
# Project definitions  (real GitHub repos, no modifications needed)
# ------------------------------------------------------------------------
_PROJECTS = {
    "maven": {
        "url": "https://github.com/swharden/Java-Boilerplate.git",
        "commit": "98489276301d3512fd0d908a36a60249a298ed51",
        "source_dir": "src/main/java",
        "build_cmd": "mvn,compile",
        "test_cmd": "mvn,test",
    },
    "gradle": {
        "url": "https://github.com/MihranGalstyan/Gradle-JUnit.git",
        "commit": "1803cd3952bb5a63637b432691f1d99252337cb1",
        "source_dir": "src/main/java",
        "build_cmd": "./gradlew,compileJava",
        "test_cmd": "./gradlew,test",
    },
    "ant": {
        "url": "https://github.com/victordion/AllAboutAnt.git",
        "commit": "0673521a487fa36ef3c3d461f6854f0469beaeba",
        "source_dir": "src",
        "build_cmd": "ant,compile",
        "test_cmd": "ant,junit",
        "test_target_name": "junit",
        "junit_target_name": "junit",
    },
}

# ------------------------------------------------------------------------
# 4 configurations  (flags appended after -m -b --all)
# ------------------------------------------------------------------------
_CONFIGS = {
    "plain":    [],
    "testsel":  ["-q", "-s"],
    "schemata": ["-e"],
    "full":     ["-q", "-s", "-e"],
}


class TestIntegrationProjects(unittest.TestCase):
    """Clone & run MediumDarwin on 3 build-systems × 4 configs in parallel."""

    @staticmethod
    def _chmod_x(path):
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    @staticmethod
    def _git_clone(url, dest, commit=None):
        subprocess.run(
            ["git", "clone", "--quiet", url, dest],
            capture_output=True, text=True, timeout=120, check=True,
        )
        if commit:
            subprocess.run(
                ["git", "-C", dest, "checkout", commit],
                capture_output=True, text=True, timeout=30, check=True,
            )

    @staticmethod
    def _keep():
        val = os.environ.get("KEEP_TEST_PROJECTS", "1").lower()
        return val not in ("0", "false", "no", "off")

    @classmethod
    def _run_one(cls, proj_cfg, config_flags, clone_dir):
        """Execute MediumDarwin on *clone_dir*; return (ok, stderr_tail)."""
        extra = []
        if proj_cfg.get("test_target_name"):
            extra += ["--test_target_name", proj_cfg["test_target_name"]]
        if proj_cfg.get("junit_target_name"):
            extra += ["--junit_target_name", proj_cfg["junit_target_name"]]

        args = (
            [sys.executable, _MD_SCRIPT]
            + ["-m", "-b", "--all"]
            + config_flags
            + [
                "-p", os.path.join(clone_dir, proj_cfg["source_dir"]),
                "-t", clone_dir,
                "-c", proj_cfg["build_cmd"],
                "--test-command", proj_cfg["test_cmd"],
                "--timeout", "180",
                "--initial-timeout", "360",
            ]
            + extra
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = _REPO_ROOT

        try:
            proc = subprocess.run(
                args, cwd=clone_dir, env=env,
                capture_output=True, text=True, timeout=900,
            )
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT after 900 s"

        ok = proc.returncode == 0 and os.path.isdir(
            os.path.join(clone_dir, "LittleDarwinResults")
        )
        tail = "\n".join(proc.stderr.strip().splitlines()[-8:])
        return ok, tail

    def test_all_configs_parallel(self):
        """Clone 3 projects × 4 configs, run all in parallel, assert success.

        By default, cloned projects & results are kept on disk at
        tests/integration_runs/.  Set KEEP_TEST_PROJECTS=0 to use a
        temporary directory instead.
        """
        persist = self._keep()
        test_dir = os.path.join(
            _REPO_ROOT, "tests", "integration_runs",
        ) if persist else tempfile.mkdtemp(prefix="md_int_")
        if persist:
            shutil.rmtree(test_dir, ignore_errors=True)
            os.makedirs(test_dir, exist_ok=True)

        try:
            # ---- clone ----
            print("\n=== Phase 1: Cloning projects ===")
            for pn, pc in _PROJECTS.items():
                for cn in _CONFIGS:
                    label = f"{pn}/{cn}"
                    cdir = os.path.join(test_dir, label.replace("/", "_"))
                    if os.path.isdir(os.path.join(cdir, ".git")):
                        print(f"  skip {label}")
                        continue
                    print(f"  cloning {label}")
                    self._git_clone(pc["url"], cdir, commit=pc.get("commit"))

            # ---- submit all ----
            print(f"\n=== Phase 2: Running 12 configs in parallel (this will take a few minutes) ===\n")
            futures = {}
            exec_info = {}
            with ThreadPoolExecutor(max_workers=12) as ex:
                for pn, pc in _PROJECTS.items():
                    for cn, cf in _CONFIGS.items():
                        label = f"{pn}/{cn}"
                        cdir = os.path.join(test_dir, label.replace("/", "_"))
                        if pn == "gradle":
                            self._chmod_x(os.path.join(cdir, "gradlew"))
                        fut = ex.submit(self._run_one, pc, cf, cdir)
                        futures[fut] = label

            # ---- collect ----
            results = {}
            for fut in as_completed(futures):
                label = futures[fut]
                ok, tail = fut.result()
                results[label] = (ok, tail)

            # ---- report ----
            print(f"\n{'='*60}")
            print(f"  Results")
            print(f"{'='*60}")
            failures = []
            for label in sorted(results):
                ok, tail = results[label]
                status = "OK" if ok else "FAIL"
                print(f"  [{status}] {label}")
                if not ok:
                    failures.append(label)
                    for line in tail.strip().splitlines():
                        print(f"         {line}")

            print(f"\n{len(futures) - len(failures)}/{len(futures)} passed")
            self.assertEqual(
                len(failures), 0,
                f"Failed: {failures}",
            )
        finally:
            if persist:
                print(f"\n[KEPT] projects & results at: {test_dir}")
            else:
                shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
