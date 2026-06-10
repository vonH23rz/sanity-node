# Installing Sanity Node

This guide describes the supported public Docker Compose installation
path for Sanity Node.

The installation starts with a credential-free, collector-only
configuration. Add remote systems and optional monitoring features only
after the first dashboard is healthy.

## Supported installation path

The supported general-purpose installation uses:

- a Linux collector host;
- Docker Engine;
- Docker Compose;
- the repository `docker-compose.yml`;
- the safe first-run bootstrap;
- the configuration validator;
- the fail-closed container startup path.

The default browser endpoint is:

```text
http://<collector-ip>:8099
```

The public container installation is the recommended starting point for
new users.

The host-native systemd deployment is an advanced integration path. It
is intended for installations that need direct access to the collector
host's Docker engine, filesystems, backup markers, systemd state,
persistent SSH host trust, or other host-local resources.

## Qualification status

The complete public Docker installation journey was qualified before
the `v0.3.0` release.

The qualified environment used:

- Docker Engine `29.5.3`;
- Docker Compose `v5.1.4`;
- a completely fresh repository clone;
- a clean bootstrap workspace;
- isolated container, image, network, port, and output resources.

The qualification covered the supported clean bootstrap, collector-only
starter configuration, dashboard generation, HTTP serving, restart,
scheduled refresh protection, automatic recovery, and complete cleanup.

It did not qualify every optional SSH-backed or collector-host-integrated
check through the unmodified Compose boundary. Those features require
additional deployment-specific access and trust configuration.

Sanity Node does not currently declare a formal minimum Docker Engine or
Compose version.

The installation requires a modern Docker Compose implementation that
supports:

```bash
docker compose up --build --wait
```

The qualification evidence is recorded in:

```text
docs/v0.3.0-installation-qualification.md
```

## Prerequisites

Prepare an always-on Linux machine that can act as the Sanity Node
collector.

The collector needs:

- Git;
- Docker Engine;
- the Docker Compose plugin;
- permission to run Docker commands;
- outbound access to clone the repository and build the image;
- a free TCP port, `8099` by default;
- enough disk space for the repository, image, logs, and generated
  dashboard;
- network access to every remote host or HTTP endpoint that will be
  monitored.

Verify the required commands:

```bash
git --version
docker --version
docker compose version
```

Verify that Docker is usable by the current account:

```bash
docker info
```

If this command requires `sudo`, either use `sudo` consistently for
Docker commands or configure the account according to the operating
system's Docker guidance.

Adding an account to the Docker group grants powerful host-level access.
Treat Docker access as administrative access.

## Clone the repository

Clone Sanity Node and enter the repository:

```bash
git clone https://github.com/vonH23rz/sanity-node.git
cd sanity-node
```

For an official release, check out the desired release tag before
bootstrapping:

```bash
git checkout v0.3.0
```

Confirm the working tree:

```bash
git status --short --branch
```

## Create the first-run workspace

Run the safe bootstrap from the repository root:

```bash
./scripts/bootstrap-workspace.py --create-env
```

The bootstrap creates:

```text
config/
html/
logs/
ssh/
config/config.yaml
.env
```

The generated `config/config.yaml` comes from
`examples/config.starter.yaml`.

The starter configuration:

- selects `dashboard.runtime_mode: public`;
- defines one enabled collector;
- enables collector-local system information;
- requires no SSH credentials;
- enables no remote systems;
- enables no service, storage, backup, protection, or image-update
  checks.

Existing files are preserved by default.

The bootstrap does not overwrite an existing configuration or `.env`
unless `--force` is supplied.

Use `--force` only when intentionally replacing bootstrap-managed
files:

```bash
./scripts/bootstrap-workspace.py --create-env --force
```

This can replace:

- `config/config.yaml`;
- `.env`, when `--create-env` is also supplied.

It does not delete SSH keys, generated dashboards, logs, or unrelated
workspace files.

The `--root` option is intended for tests and advanced alternate
workspace preparation. Normal installations should omit it.

## Review `.env`

The bootstrap copies `.env.example` to `.env` and sets `PUID` and
`PGID` to the current account.

Review it:

```bash
cat .env
```

The standard values are:

```text
SANITY_NODE_PORT=8099
TZ=Europe/Berlin
PUID=1000
PGID=1000
SANITY_NODE_REFRESH_SECONDS=300
SANITY_NODE_CONFIG=/app/config/config.yaml
SANITY_NODE_OUTPUT=/app/html/index.html
SANITY_NODE_LOG=/app/logs/generator.log
SANITY_NODE_SSH_USER=truenas_admin
SANITY_NODE_SSH_KEY=/app/ssh/id_ed25519
```

Adjust at least:

- `TZ` for the collector's timezone;
- `SANITY_NODE_PORT` if host port `8099` is already in use;
- `PUID` and `PGID` only when the bootstrap did not create them for the
  correct account;
- `SANITY_NODE_REFRESH_SECONDS` when a refresh interval other than five
  minutes is required.

The Compose deployment always serves port `8099` inside the container.
`SANITY_NODE_PORT` in `.env` controls the host-side published port.

For example:

```text
SANITY_NODE_PORT=18099
```

would make the dashboard available at:

```text
http://<collector-ip>:18099
```

Do not change the `/app/...` runtime paths for a normal installation.

## Validate the starter configuration

Validate the generated configuration before starting Docker:

```bash
./scripts/validate-config.py config/config.yaml
```

A valid starter configuration ends with:

```text
Validation result: 0 error(s), 0 warning(s)
Configuration validation passed.
```

Validation errors return a nonzero exit code.

The validator reads the configuration only. It does not generate or
replace the dashboard.

## Validate Docker Compose configuration

Render the effective Compose configuration:

```bash
docker compose --env-file .env config
```

This catches invalid environment substitutions and Compose syntax
problems before the image is built.

The command prints the resolved configuration and should exit
successfully.

## Start Sanity Node

Build and start the container:

```bash
docker compose up --build --wait
```

Then inspect its state:

```bash
docker compose ps
```

The service should report healthy.

The initial startup is fail-closed. Before the web server starts, the
container must:

1. validate `config/config.yaml`;
2. run startup preflight;
3. remove any stale generated `index.html`;
4. generate a nonempty dashboard successfully;
5. start the scheduled refresh loop;
6. start the HTTP server.

A running HTTP process without a valid generated dashboard is not
considered healthy.

## Open the dashboard

Open:

```text
http://<collector-ip>:8099
```

Replace `<collector-ip>` with the IP address or DNS name of the Linux
collector.

When a custom host port is configured in `.env`, use that port instead.

From the collector itself, verify HTTP directly:

```bash
curl --fail http://127.0.0.1:8099/
```

Verify that the generated file exists:

```bash
test -s html/index.html
```

## Inspect logs

Follow container output:

```bash
docker compose logs --follow sanity-node
```

Inspect recent output without following:

```bash
docker compose logs --tail 200 sanity-node
```

The generator log is stored on the host at:

```text
logs/generator.log
```

Inspect it with:

```bash
tail -n 200 logs/generator.log
```

## Customize the collector identity

Edit:

```text
config/config.yaml
```

The collector definition and collector host should use the same ID.

A basic example is:

```yaml
collector:
  id: collector
  display_name: Utility Node
  hostname: utility-node
  type: linux

hosts:
  - id: collector
    enabled: true
    display_name: Utility Node
    hostname: utility-node
    type: linux

    modules:
      system_info: true
      local_storage: false
      docker: false
      backup_status: false
      services: false
```

Set `display_name` and `hostname` to values appropriate for the
installation.

In the standard container deployment, collector-local checks run inside
the container boundary. They do not automatically gain access to the
collector host's Docker socket, host filesystems, backup markers, or
systemd state.

Start with system information and HTTP checks. Add host-integrated checks
only when their deployment requirements are understood.

## Add the first HTTP service

HTTP checks are the simplest optional checks because they require no SSH
credentials and no access to the collector's Docker engine.

Add a service under `services`:

```yaml
services:
  - enabled: true
    host: collector
    name: Example Service
    type: app
    check: http
    url: http://example-service:8080/
```

The `host` value must reference an enabled host ID.

Supported service classifications are:

```text
app
helper
```

An HTTP check reports reachability of the configured URL. It does not
inspect the application's internal health.

After editing the configuration:

```bash
./scripts/validate-config.py config/config.yaml
docker compose restart sanity-node
docker compose ps
```

## Add a remote Linux host

A remote Linux host can provide:

- system information;
- Docker container checks;
- filesystem checks;
- backup marker and optional timer checks.

An enabled remote Linux host requires:

- `type: linux`;
- an address;
- explicit SSH settings;
- a usable SSH key;
- the relevant module enabled.

Example:

```yaml
hosts:
  - id: linux-server
    enabled: true
    display_name: Linux Server
    hostname: linux-server
    address: linux-server.example.internal
    type: linux

    ssh:
      enabled: true
      user: sanity-node-monitor
      key_file: /app/ssh/id_ed25519_linux_server

    modules:
      system_info: true
      local_storage: false
      docker: false
      backup_status: false
      services: true
```

Enable only the modules for which the remote account has the required
permissions.

## Add a TrueNAS SCALE host

An enabled TrueNAS host can provide:

- system information;
- pool capacity and health;
- disk temperatures;
- SMART health;
- snapshot task and freshness information;
- replication task state;
- application status;
- native application update information.

Example:

```yaml
hosts:
  - id: storage-server
    enabled: true
    display_name: Storage Server
    hostname: storage-server
    address: storage-server.example.internal
    type: truenas
    web_url: https://storage-server.example.internal

    ssh:
      enabled: true
      user: truenas_admin
      key_file: /app/ssh/id_ed25519_storage_server

    modules:
      system_info: true
      pools: true
      temperatures: false
      smart: false
      snapshots: false
      replications: false
      apps: true
      services: true
```

Enable one additional module at a time and validate after every change.

Temperature and SMART collection can require additional remote command
permissions. Do not grant broader administrative access than required.

## Install SSH credentials

Place private keys in the repository's ignored `ssh/` directory.

Example:

```bash
install -m 600 ~/.ssh/id_ed25519_sanity_node ssh/id_ed25519_storage_server
```

The key path inside `config/config.yaml` must use the container path:

```text
/app/ssh/id_ed25519_storage_server
```

Do not use the host-side repository path in `config/config.yaml`.

The Compose volume mounts:

```text
./ssh -> /app/ssh
```

read-only.

Private keys should normally use mode `600`:

```bash
chmod 600 ssh/id_ed25519_storage_server
```

The container runs with the UID and GID configured in `.env`. Ensure
that account can read the key:

```bash
ls -ln ssh/
```

Test the key and remote account from the collector host before enabling
the check:

```bash
ssh -i ssh/id_ed25519_storage_server -o IdentitiesOnly=yes monitoring-user@storage-server.example.internal
```

Accept and verify the correct SSH host fingerprint deliberately.

The committed Compose file mounts `./ssh` only at `/app/ssh` for
configured key files.

The runtime SSH command uses normal OpenSSH host-key verification, but
the base Compose file does not mount a persistent verified
`known_hosts` location for the runtime account.

A private key alone is therefore not sufficient for a new SSH target.
Before enabling SSH-backed monitoring, add an explicit deployment
integration that provides verified host trust to the container, or use
the advanced host-native deployment path.

Do not work around this requirement with
`StrictHostKeyChecking=no`, an empty host-key database, or automatic
acceptance of unverified fingerprints.

## Validate SSH-backed changes

After adding an SSH-backed host, run:

```bash
./scripts/validate-config.py config/config.yaml
```

The container runs startup preflight automatically during initial
startup and before every scheduled refresh.

Do not run the host-side preflight against a Docker configuration that
contains `/app/...` key paths. Those paths exist inside the container,
not on the collector host.

The host-side preflight is intended for host-native execution or for an
alternate configuration whose paths are valid on the host.

After the SSH key, verified host trust, and remote permissions are in
place, restart:

```bash
docker compose restart sanity-node
docker compose ps
```

## Add optional checks carefully

The full configuration reference is:

```text
examples/config.example.yaml
```

Use it as a reference. Do not copy it unchanged as a production
configuration.

Its enabled TrueNAS example deliberately demonstrates SSH-backed
features and will fail when its example host and key do not exist.

Optional areas include:

- `services`;
- `local_storage`;
- `backup_checks`;
- `protection`;
- `image_updates`;
- `summary_cards`.

Enable one small change at a time:

1. edit `config/config.yaml`;
2. validate it;
3. restart or wait for the next refresh;
4. inspect the dashboard and logs;
5. continue only after the result is understood.

## Local storage checks

Example:

```yaml
local_storage:
  - enabled: true
    host: collector
    mount: /
    label: System Disk
    warning_percent: 80
    critical_percent: 90
```

In the standard container deployment, `/` refers to the container
filesystem, not automatically to the collector host's root filesystem.

Remote Linux storage checks operate over SSH when:

- the host is enabled;
- `modules.local_storage: true`;
- the host has an address;
- explicit SSH configuration is usable.

## Docker container checks

Example:

```yaml
services:
  - enabled: true
    host: collector
    name: Example Container
    type: app
    check: docker
    container: example-container
```

Collector-local Docker checks require Docker command and daemon access
inside the Sanity Node runtime.

The standard Docker Compose installation does not mount the collector
host's Docker socket and does not provide host-Docker access by default.

Prefer an HTTP check where possible.

Remote Linux Docker checks use SSH when:

- `modules.docker: true`;
- the host address and SSH settings are configured;
- the remote account can execute the required Docker inspection.

Do not expose a Docker socket or grant remote Docker access without
understanding that it provides powerful control over the monitored host.

## Backup checks

Example:

```yaml
backup_checks:
  - enabled: true
    host: linux-server
    name: Server Backup
    marker_file: /var/backups/server/last-successful-backup.txt
    systemd_timer: server-backup.timer
    max_age_hours: 36
```

Collector-local backup checks inside Docker cannot automatically inspect
the collector host's marker files or systemd state.

Remote Linux backup checks use SSH and require permission to read the
marker file and query the optional timer.

## Image-update checks

Supported providers are:

```text
diun
truenas
```

A Diun source reads a Prometheus metrics endpoint:

```yaml
image_updates:
  enabled: true

  sources:
    - id: linux-server-diun
      host: linux-server
      provider: diun
      url: http://diun.example.internal:8080/metrics
```

Inside a container, `127.0.0.1` refers to the Sanity Node container
itself. Do not use a collector-host loopback URL unless the endpoint is
also available inside the same container.

A TrueNAS source uses the configured TrueNAS SSH connection:

```yaml
image_updates:
  enabled: true

  sources:
    - id: storage-server-apps
      host: storage-server
      provider: truenas
```

## Configuration refresh behavior

The default refresh interval is 300 seconds.

Every scheduled refresh performs:

```text
configuration validation
→ startup preflight
→ dashboard generation
```

When validation, preflight, or generation fails:

- the generator does not publish invalid output;
- the last successful dashboard remains served;
- the container remains running;
- logs record the failure;
- a later valid configuration recovers automatically.

The initial startup behaves differently by design: it requires one
successful dashboard generation before starting the web server.

## Apply configuration changes

For ordinary configuration changes, first validate:

```bash
./scripts/validate-config.py config/config.yaml
```

Sanity Node will detect the valid configuration on the next scheduled
refresh.

To apply it immediately:

```bash
docker compose restart sanity-node
docker compose ps
```

A restart removes the previously generated dashboard before requiring a
new successful initial render. Keep a copy of important configuration
before making large changes.

## File ownership and permissions

The container writes to:

```text
html/
logs/
```

It reads:

```text
config/
ssh/
```

The runtime process uses `PUID` and `PGID` from `.env`.

Inspect ownership numerically:

```bash
ls -lnd config html logs ssh
ls -ln config html logs ssh
```

Correct ownership for the current account when necessary:

```bash
sudo chown -R "$(id -u):$(id -g)" config html logs ssh
```

Apply restrictive key permissions:

```bash
find ssh -type f -name 'id_*' -exec chmod 600 {} +
```

Do not make private keys world-readable.

## Change the browser port

Edit `.env`:

```text
SANITY_NODE_PORT=8099
```

Choose an unused host port between `1` and `65535`.

Recreate the container after changing published ports:

```bash
docker compose up --detach --force-recreate
docker compose ps
```

Then open the new port in the local firewall when required.

## Firewall and reverse proxy

For direct LAN access, allow the selected host TCP port only from the
networks that should reach Sanity Node.

A reverse proxy can forward to:

```text
http://<collector-ip>:8099
```

TLS termination, authentication, DNS, and public exposure remain the
responsibility of the reverse proxy and network administrator.

Sanity Node does not require public Internet exposure.

Avoid exposing the dashboard publicly unless the monitoring information
is appropriate for public access and the proxy provides suitable
protection.

## Update Sanity Node

Before updating:

1. back up `config/`, `.env`, and `ssh/`;
2. confirm the current container is healthy;
3. record the current release tag or commit;
4. read the release notes.

Stop at a clean repository state:

```bash
git status --short --branch
```

Fetch release information:

```bash
git fetch --tags origin
```

Check out the desired release:

```bash
git checkout v0.3.0
```

Revalidate local configuration:

```bash
./scripts/validate-config.py config/config.yaml
docker compose --env-file .env config
```

Rebuild and recreate:

```bash
docker compose up --detach --build --wait
docker compose ps
```

Inspect logs and verify the dashboard before deleting any previous
backup.

Do not use `git pull` blindly when the repository contains local tracked
changes.

Runtime configuration, keys, logs, and dashboard output are ignored by
Git and should remain outside commits.

## Back up an installation

At minimum, back up:

```text
config/config.yaml
.env
ssh/
```

Optionally retain:

```text
logs/
html/index.html
```

The dashboard can be regenerated. Configuration and SSH credentials are
the essential installation state.

Protect backups containing private keys with appropriate encryption and
permissions.

## Stop Sanity Node

Stop the container while preserving generated files and configuration:

```bash
docker compose down
```

Start it again with:

```bash
docker compose up --detach --wait
```

## Uninstall Sanity Node

Stop and remove the Compose container and network:

```bash
docker compose down
```

Remove the locally built image when desired:

```bash
docker compose down --rmi local
```

The Compose commands do not remove the bind-mounted runtime directories.

To remove the installation completely, first back up anything needed,
leave the repository directory, and delete the clone manually.

For example:

```bash
cd ..
rm -rf sanity-node
```

Confirm the path carefully before running a recursive removal command.

## Troubleshooting

### The container does not become healthy

Inspect:

```bash
docker compose ps
docker compose logs --tail 300 sanity-node
```

Common causes include:

- invalid YAML;
- a configuration validation error;
- missing write access to `html/` or `logs/`;
- a missing or unreadable SSH key;
- an unreachable required SSH host;
- an invalid UID or GID;
- a conflicting host port;
- failed initial dashboard generation.

### Configuration validation fails

Run:

```bash
./scripts/validate-config.py config/config.yaml
```

Correct every reported error before restarting.

Check YAML indentation carefully. Use spaces, not tabs.

Compare the relevant section with:

```text
examples/config.example.yaml
```

### Startup preflight fails

Inspect the container log for the exact path or credential failure.

Confirm:

```bash
ls -ld config html logs ssh
ls -l config/config.yaml
ls -l ssh/
```

Verify that configured container key paths begin with:

```text
/app/ssh/
```

### Port `8099` is already in use

Find the listener:

```bash
sudo ss -ltnp | grep ':8099'
```

Select another `SANITY_NODE_PORT` in `.env` and recreate the container.

### The dashboard still shows the previous state

The default refresh interval is five minutes.

Inspect timestamps:

```bash
stat html/index.html
tail -n 100 logs/generator.log
```

Apply a valid change immediately with:

```bash
docker compose restart sanity-node
```

### Invalid configuration did not replace the dashboard

This is expected.

Scheduled refreshes fail closed and continue serving the last successful
dashboard.

Correct the configuration. The next scheduled refresh will recover
automatically.

### An HTTP service is DOWN

Test the exact URL from the collector host:

```bash
curl --fail --show-error --verbose http://example-service:8080/
```

Also consider the container network boundary. A hostname or loopback
address that works on the collector host may not resolve to the same
destination inside the container.

### SSH checks are UNKNOWN

Test the same identity from the collector host:

```bash
ssh -i ssh/id_ed25519_remote -o IdentitiesOnly=yes monitoring-user@remote-host
```

A successful host-side SSH test proves the key and remote account, but
it does not prove that the container has persistent verified host trust.

Confirm:

- DNS or IP reachability;
- the remote username;
- private-key permissions;
- host-key trust inside the deployed runtime;
- remote command permissions;
- the `/app/ssh/...` path in `config/config.yaml`;
- the deployment-specific persistent `known_hosts` integration.

### Collector-local Docker checks fail

The standard Compose installation does not provide host Docker access by
default.

Use HTTP checks, remote SSH checks, or an explicitly designed advanced
deployment rather than weakening the installation casually.

### Collector-local filesystem or systemd checks are misleading

Inside Docker, local paths and process state belong to the container
boundary.

Use remote SSH checks or an advanced host-native deployment for
collector-host filesystem, backup marker, and systemd monitoring.

## Security notes

- Keep `config/`, `.env`, `ssh/`, `logs/`, and `html/` out of Git.
- Never commit private keys.
- Use dedicated monitoring accounts where practical.
- Grant only the remote command permissions required by enabled modules.
- Preserve SSH host-key verification.
- Never disable `StrictHostKeyChecking` to bypass deployment setup.
- Treat Docker access as administrative access.
- Keep the dashboard on trusted networks unless protected deliberately.
- Review configuration before enabling checks that reveal infrastructure
  names, addresses, storage layouts, or service inventory.

## Recommended installation sequence

Use this sequence for a controlled first deployment:

```bash
git clone https://github.com/vonH23rz/sanity-node.git
cd sanity-node
git checkout v0.3.0

./scripts/bootstrap-workspace.py --create-env
./scripts/validate-config.py config/config.yaml
docker compose --env-file .env config
docker compose up --build --wait
docker compose ps
```

Open:

```text
http://<collector-ip>:8099
```

Then:

1. customize the collector identity;
2. add one HTTP service;
3. validate;
4. observe one refresh;
5. add one remote host if required;
6. install and verify its SSH key;
7. enable one monitoring module at a time.

Start small, validate every change, and preserve the last known-good
configuration.
