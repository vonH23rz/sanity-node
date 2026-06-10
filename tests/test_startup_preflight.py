#!/usr/bin/env python3

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = REPO_ROOT / "scripts" / "startup-preflight.py"
ENTRYPOINT_PATH = REPO_ROOT / "scripts" / "docker-entrypoint.sh"
DOCKERFILE_PATH = REPO_ROOT / "Dockerfile"
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"

SPEC = importlib.util.spec_from_file_location(
    "startup_preflight",
    PREFLIGHT_PATH,
)
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


class StartupPreflightTests(unittest.TestCase):
    def make_runtime(self, config):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)

        config_dir = root / "config"
        output_dir = root / "html"
        log_dir = root / "logs"

        config_dir.mkdir()
        output_dir.mkdir()
        log_dir.mkdir()

        config_path = config_dir / "config.yaml"
        output_path = output_dir / "index.html"
        log_path = log_dir / "generator.log"

        config_path.write_text(yaml.safe_dump(config))

        return (
            temporary,
            config_path,
            output_path,
            log_path,
        )

    @staticmethod
    def minimal_config():
        return {
            "dashboard": {
                "title": "Sanity Node",
                "subtitle": "Test",
                "refresh_minutes": 5,
            },
            "collector": {
                "id": "collector",
                "display_name": "Collector",
                "hostname": "collector",
                "type": "linux",
            },
            "hosts": [
                {
                    "id": "collector",
                    "enabled": True,
                    "display_name": "Collector",
                    "hostname": "collector",
                    "type": "linux",
                    "modules": {
                        "docker": True,
                    },
                }
            ],
            "services": [],
            "local_storage": [],
            "backup_checks": [],
            "protection": [],
            "image_updates": {
                "enabled": False,
                "sources": [],
            },
        }

    def test_minimal_collector_configuration_passes_without_ssh_key(self):
        runtime = self.make_runtime(self.minimal_config())
        temporary, config_path, output_path, log_path = runtime

        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(requirements, {})
        self.assertEqual(errors, [])

    def test_missing_configuration_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "html").mkdir()
            (root / "logs").mkdir()

            requirements, errors = PREFLIGHT.run_preflight(
                root / "config" / "config.yaml",
                root / "html" / "index.html",
                root / "logs" / "generator.log",
            )

        self.assertEqual(requirements, {})
        self.assertTrue(
            any(
                "configuration file does not exist" in error
                for error in errors
            )
        )

    def test_invalid_yaml_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "html").mkdir()
            (root / "logs").mkdir()

            config_path = root / "config" / "config.yaml"
            config_path.write_text("hosts: [\n")

            _, errors = PREFLIGHT.run_preflight(
                config_path,
                root / "html" / "index.html",
                root / "logs" / "generator.log",
            )

        self.assertTrue(
            any(
                "contains invalid YAML" in error
                for error in errors
            )
        )

    def test_missing_output_directory_fails(self):
        runtime = self.make_runtime(self.minimal_config())
        temporary, config_path, output_path, log_path = runtime

        self.addCleanup(temporary.cleanup)
        output_path.parent.rmdir()

        _, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertIn(
            f"dashboard output directory does not exist: "
            f"{output_path.parent}",
            errors,
        )

    def test_enabled_truenas_snapshots_require_existing_key(self):
        config = self.minimal_config()
        config["hosts"].append(
            {
                "id": "nas",
                "enabled": True,
                "display_name": "NAS",
                "hostname": "nas",
                "address": "192.0.2.10",
                "type": "truenas",
                "ssh": {
                    "enabled": True,
                    "user": "monitor",
                    "key_file": "/missing/id_ed25519",
                },
                "modules": {
                    "snapshots": True,
                    "replications": False,
                },
            }
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(
            requirements["nas"],
            ["TrueNAS snapshot monitoring"],
        )
        self.assertTrue(
            any(
                "does not exist: /missing/id_ed25519" in error
                for error in errors
            )
        )

    def test_required_ssh_host_without_ssh_section_fails_clearly(self):
        config = self.minimal_config()
        config["hosts"].append(
            {
                "id": "nas",
                "enabled": True,
                "display_name": "NAS",
                "hostname": "nas",
                "address": "192.0.2.10",
                "type": "truenas",
                "modules": {
                    "snapshots": True,
                    "replications": False,
                },
            }
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(
            requirements["nas"],
            ["TrueNAS snapshot monitoring"],
        )
        self.assertIn(
            "host 'NAS' requires SSH for TrueNAS snapshot monitoring, "
            "but its ssh section is missing or disabled",
            errors,
        )

    def test_disabled_truenas_modules_do_not_require_key(self):
        config = self.minimal_config()
        config["hosts"].append(
            {
                "id": "nas",
                "enabled": True,
                "display_name": "NAS",
                "hostname": "nas",
                "address": "192.0.2.10",
                "type": "truenas",
                "ssh": {
                    "enabled": True,
                    "user": "monitor",
                    "key_file": "/missing/id_ed25519",
                },
                "modules": {
                    "snapshots": False,
                    "replications": False,
                },
            }
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertNotIn("nas", requirements)
        self.assertEqual(errors, [])

    def test_remote_linux_docker_check_requires_key(self):
        config = self.minimal_config()
        config["hosts"].append(
            {
                "id": "remote",
                "enabled": True,
                "display_name": "Remote Linux",
                "hostname": "remote",
                "address": "192.0.2.20",
                "type": "linux",
                "ssh": {
                    "enabled": True,
                    "user": "monitor",
                    "key_file": "/missing/remote-key",
                },
                "modules": {
                    "docker": True,
                },
            }
        )
        config["services"].append(
            {
                "id": "remote-app",
                "enabled": True,
                "name": "Remote App",
                "host": "remote",
                "type": "app",
                "check": "docker",
                "container": "remote-app",
            }
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(
            requirements["remote"],
            ["remote Linux Docker monitoring"],
        )
        self.assertTrue(
            any(
                "does not exist: /missing/remote-key" in error
                for error in errors
            )
        )

    def test_collector_local_docker_check_does_not_require_key(self):
        config = self.minimal_config()
        config["services"].append(
            {
                "id": "local-app",
                "enabled": True,
                "name": "Local App",
                "host": "collector",
                "type": "app",
                "check": "docker",
                "container": "local-app",
            }
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(requirements, {})
        self.assertEqual(errors, [])

    def test_collector_system_info_does_not_require_ssh(self):
        config = self.minimal_config()
        config["hosts"][0]["modules"]["system_info"] = True

        requirements = PREFLIGHT.collect_ssh_requirements(
            config
        )

        self.assertEqual(requirements, {})

    def test_remote_system_info_modules_require_ssh(self):
        config = self.minimal_config()
        config["hosts"].extend(
            [
                {
                    "id": "remote-linux",
                    "enabled": True,
                    "display_name": "Remote Linux",
                    "hostname": "remote-linux",
                    "address": "192.0.2.20",
                    "type": "linux",
                    "modules": {
                        "system_info": True,
                    },
                },
                {
                    "id": "remote-truenas",
                    "enabled": True,
                    "display_name": "Remote TrueNAS",
                    "hostname": "remote-truenas",
                    "address": "192.0.2.30",
                    "type": "truenas",
                    "modules": {
                        "system_info": True,
                    },
                },
                {
                    "id": "module-disabled",
                    "enabled": True,
                    "display_name": "Module Disabled",
                    "hostname": "module-disabled",
                    "address": "192.0.2.40",
                    "type": "linux",
                    "modules": {
                        "system_info": False,
                    },
                },
            ]
        )

        requirements = PREFLIGHT.collect_ssh_requirements(
            config
        )

        self.assertEqual(
            requirements["remote-linux"],
            ["remote Linux system information"],
        )
        self.assertEqual(
            requirements["remote-truenas"],
            ["TrueNAS system information"],
        )
        self.assertNotIn(
            "module-disabled",
            requirements,
        )

    def test_remote_system_info_without_ssh_fails_clearly(self):
        config = self.minimal_config()
        config["hosts"].append(
            {
                "id": "remote-linux",
                "enabled": True,
                "display_name": "Remote Linux",
                "hostname": "remote-linux",
                "address": "192.0.2.20",
                "type": "linux",
                "modules": {
                    "system_info": True,
                },
            }
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(
            requirements["remote-linux"],
            ["remote Linux system information"],
        )
        self.assertIn(
            "host 'Remote Linux' requires SSH for "
            "remote Linux system information, "
            "but its ssh section is missing or disabled",
            errors,
        )

    def test_truenas_pool_module_requires_ssh(self):
        config = self.minimal_config()
        config["hosts"].extend(
            [
                {
                    "id": "pool-host",
                    "enabled": True,
                    "display_name": "Pool Host",
                    "hostname": "pool-host",
                    "address": "192.0.2.30",
                    "type": "truenas",
                    "modules": {
                        "pools": True,
                    },
                },
                {
                    "id": "pool-disabled",
                    "enabled": True,
                    "display_name": "Pool Disabled",
                    "hostname": "pool-disabled",
                    "address": "192.0.2.31",
                    "type": "truenas",
                    "modules": {
                        "pools": False,
                    },
                },
            ]
        )

        requirements = PREFLIGHT.collect_ssh_requirements(
            config
        )

        self.assertEqual(
            requirements["pool-host"],
            ["TrueNAS pool monitoring"],
        )
        self.assertNotIn(
            "pool-disabled",
            requirements,
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(
            requirements["pool-host"],
            ["TrueNAS pool monitoring"],
        )
        self.assertIn(
            "host 'Pool Host' requires SSH for "
            "TrueNAS pool monitoring, "
            "but its ssh section is missing or disabled",
            errors,
        )

    def test_cli_returns_nonzero_for_missing_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "html").mkdir()
            (root / "logs").mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(PREFLIGHT_PATH),
                    "--config",
                    str(root / "missing.yaml"),
                    "--output",
                    str(root / "html" / "index.html"),
                    "--log",
                    str(root / "logs" / "generator.log"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "configuration file does not exist",
            result.stderr,
        )


    def make_fake_entrypoint_runtime(
        self,
        generator_exit=0,
        validator_fail_after=None,
        refresh_seconds=3600,
        serve_seconds=0,
    ):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        app_root = root / "app"
        scripts_dir = app_root / "scripts"
        html_dir = app_root / "html"
        logs_dir = app_root / "logs"
        config_dir = app_root / "config"
        fake_bin = root / "bin"
        trace_path = root / "trace.log"

        for directory in (
            scripts_dir,
            html_dir,
            logs_dir,
            config_dir,
            fake_bin,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        config_path = config_dir / "config.yaml"
        output_path = html_dir / "index.html"
        log_path = logs_dir / "generator.log"
        config_path.write_text("{}\n")

        def write_executable(path, content):
            path.write_text(content)
            path.chmod(0o755)

        validator_script = (
            "#!/usr/bin/env sh\n"
            f"echo validate >> {trace_path}\n"
        )

        if validator_fail_after is not None:
            validator_count_path = root / "validator.count"
            validator_script += (
                f'count="$(cat {validator_count_path} '
                '2>/dev/null || echo 0)"\n'
                'count=$((count + 1))\n'
                f'printf "%s\\n" "$count" > '
                f"{validator_count_path}\n"
                f'if [ "$count" -gt {validator_fail_after} ]; '
                "then exit 9; fi\n"
            )

        write_executable(
            scripts_dir / "validate-config.py",
            validator_script,
        )
        write_executable(
            scripts_dir / "startup-preflight.py",
            "#!/usr/bin/env sh\n"
            f"echo preflight >> {trace_path}\n",
        )
        write_executable(
            scripts_dir / "generate-dashboard.py",
            "#!/usr/bin/env sh\n"
            f"echo generate >> {trace_path}\n"
            f"if [ {generator_exit} -ne 0 ]; then exit {generator_exit}; fi\n"
            'printf "dashboard\\n" > "$SANITY_NODE_OUTPUT"\n',
        )
        write_executable(
            fake_bin / "python3",
            "#!/usr/bin/env sh\n"
            f"echo serve >> {trace_path}\n"
            f"sleep {serve_seconds}\n",
        )

        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{fake_bin}:{environment['PATH']}",
                "SANITY_NODE_APP_ROOT": str(app_root),
                "SANITY_NODE_CONFIG": str(config_path),
                "SANITY_NODE_OUTPUT": str(output_path),
                "SANITY_NODE_LOG": str(log_path),
                "SANITY_NODE_PORT": "8099",
                "SANITY_NODE_REFRESH_SECONDS": str(
                    refresh_seconds
                ),
                "PUID": str(os.getuid()),
                "PGID": str(os.getgid()),
            }
        )

        result = subprocess.run(
            [str(ENTRYPOINT_PATH), "run"],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
            timeout=10,
        )

        return (
            temporary,
            trace_path,
            output_path,
            result,
        )

    def test_entrypoint_validates_preflights_generates_then_serves(self):
        runtime = self.make_fake_entrypoint_runtime()
        temporary, trace_path, output_path, result = runtime
        self.addCleanup(temporary.cleanup)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            trace_path.read_text().splitlines(),
            ["validate", "preflight", "generate", "serve"],
        )
        self.assertEqual(output_path.read_text(), "dashboard\n")

    def test_entrypoint_does_not_serve_when_initial_generation_fails(self):
        runtime = self.make_fake_entrypoint_runtime(generator_exit=7)
        temporary, trace_path, output_path, result = runtime
        self.addCleanup(temporary.cleanup)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            trace_path.read_text().splitlines(),
            ["validate", "preflight", "generate"],
        )
        self.assertFalse(output_path.exists())
        self.assertIn(
            "initial dashboard generation failed",
            result.stderr,
        )

    def test_entrypoint_revalidates_before_scheduled_refresh(self):
        runtime = self.make_fake_entrypoint_runtime(
            validator_fail_after=1,
            refresh_seconds=1,
            serve_seconds=3,
        )
        temporary, trace_path, output_path, result = runtime
        self.addCleanup(temporary.cleanup)

        self.assertEqual(result.returncode, 0, result.stderr)

        trace = trace_path.read_text().splitlines()

        self.assertEqual(
            trace[:4],
            ["validate", "preflight", "generate", "serve"],
        )
        self.assertGreaterEqual(trace.count("validate"), 2)
        self.assertEqual(trace.count("preflight"), 1)
        self.assertEqual(trace.count("generate"), 1)
        self.assertEqual(trace.count("serve"), 1)
        self.assertEqual(output_path.read_text(), "dashboard\n")
        self.assertIn(
            "Configuration validation failed; generator was not run",
            result.stderr,
        )
        self.assertIn(
            "Keeping the last successfully generated dashboard",
            result.stderr,
        )

    def test_container_healthchecks_require_generated_dashboard(self):
        dockerfile = DOCKERFILE_PATH.read_text()
        compose = COMPOSE_PATH.read_text()

        self.assertIn(
            'CMD test -s "$SANITY_NODE_OUTPUT"',
            dockerfile,
        )
        self.assertNotIn(
            "CMD-SHELL",
            dockerfile,
        )
        self.assertIn(
            'test -s "$${SANITY_NODE_OUTPUT:-/app/html/index.html}"',
            compose,
        )
        self.assertIn(
            "/app/scripts/startup-preflight.py",
            dockerfile,
        )

    def test_truenas_disk_health_modules_require_ssh(self):
        config = self.minimal_config()
        config["hosts"].extend(
            [
                {
                    "id": "temperature-host",
                    "enabled": True,
                    "display_name": "Temperature Host",
                    "hostname": "temperature-host",
                    "address": "192.0.2.31",
                    "type": "truenas",
                    "modules": {
                        "temperatures": True,
                        "smart": False,
                    },
                },
                {
                    "id": "smart-host",
                    "enabled": True,
                    "display_name": "SMART Host",
                    "hostname": "smart-host",
                    "address": "192.0.2.32",
                    "type": "truenas",
                    "modules": {
                        "temperatures": False,
                        "smart": True,
                    },
                },
                {
                    "id": "both-host",
                    "enabled": True,
                    "display_name": "Both Host",
                    "hostname": "both-host",
                    "address": "192.0.2.33",
                    "type": "truenas",
                    "modules": {
                        "temperatures": True,
                        "smart": True,
                    },
                },
                {
                    "id": "disabled-disk-health",
                    "enabled": True,
                    "display_name": "Disabled Disk Health",
                    "hostname": "disabled-disk-health",
                    "address": "192.0.2.34",
                    "type": "truenas",
                    "modules": {
                        "temperatures": False,
                        "smart": False,
                    },
                },
            ]
        )

        requirements = PREFLIGHT.collect_ssh_requirements(
            config
        )

        self.assertEqual(
            requirements["temperature-host"],
            ["TrueNAS temperature monitoring"],
        )
        self.assertEqual(
            requirements["smart-host"],
            ["TrueNAS SMART monitoring"],
        )
        self.assertEqual(
            requirements["both-host"],
            [
                "TrueNAS SMART monitoring",
                "TrueNAS temperature monitoring",
            ],
        )
        self.assertNotIn(
            "disabled-disk-health",
            requirements,
        )

        runtime = self.make_runtime(config)
        temporary, config_path, output_path, log_path = runtime
        self.addCleanup(temporary.cleanup)

        requirements, errors = PREFLIGHT.run_preflight(
            config_path,
            output_path,
            log_path,
        )

        self.assertEqual(
            requirements["both-host"],
            [
                "TrueNAS SMART monitoring",
                "TrueNAS temperature monitoring",
            ],
        )
        self.assertIn(
            "host 'Temperature Host' requires SSH for "
            "TrueNAS temperature monitoring, "
            "but its ssh section is missing or disabled",
            errors,
        )
        self.assertIn(
            "host 'SMART Host' requires SSH for "
            "TrueNAS SMART monitoring, "
            "but its ssh section is missing or disabled",
            errors,
        )
        self.assertIn(
            "host 'Both Host' requires SSH for "
            "TrueNAS SMART monitoring, "
            "TrueNAS temperature monitoring, "
            "but its ssh section is missing or disabled",
            errors,
        )



if __name__ == "__main__":
    unittest.main()
