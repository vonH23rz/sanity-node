# Deploying Sanity Node

This guide describes the advanced host-native systemd deployment
contract included with Sanity Node.

New users should normally start with the supported Docker Compose
installation documented in:

```text
docs/installation.md
```

The host-native path is intended for operators who need direct access to
collector-host resources and are prepared to manage a Linux service
account, systemd units, filesystem permissions, SSH trust, local command
access, updates, and rollback.

## Deployment choices

Sanity Node provides two distinct deployment models.

### Docker Compose

Use Docker Compose when the required monitoring can operate through:

- collector-only starter telemetry;
- HTTP checks;
- network-reachable endpoints;
- explicitly integrated remote access;
- the standard container filesystem and network boundary.

The default Docker browser port is:

```text
8099
```

The complete first-run procedure is in `docs/installation.md`.

### Host-native systemd

Use the host-native path when the collector must directly inspect:

- the collector's Docker engine;
- collector-host filesystems;
- backup marker files;
- local systemd timer state;
- collector-local monitoring endpoints;
- persistent SSH identities and verified host trust;
- other host-local resources that are intentionally not exposed to the
  standard container.

The committed production systemd templates use:

```text
User=sanity-node
Group=sanity-node
/opt/sanity-node
TCP port 8088
```

These values form the generic host-native deployment contract.

A private deployment can use a carefully reviewed systemd drop-in when
a different account or environment is required. Do not silently edit
the operational contract without recording and testing the change.

## Host-native qualification boundary

The permanent host-native runtime completed production migration,
scheduled generation, lifecycle, rollback, and cutover rehearsals during
Phase 3C.

The repository provides:

- `scripts/run-public-production.sh`;
- `systemd/sanity-node-generate.service`;
- `systemd/sanity-node-generate.timer`;
- `systemd/sanity-node-web.service`;
- deterministic runner and unit-contract tests;
- the production and rollback contract documented in
  `docs/phase3c-reference-retirement-decision.md`.

This is advanced deployment guidance, not a universal host installer.

Linux distributions, package names, Docker access, SSH permissions,
filesystem layouts, reverse proxies, and local security policy vary.
The operator remains responsible for integrating those host-specific
requirements safely.

## Permanent workspace layout

The default production root is:

```text
/opt/sanity-node
```

The required layout is:

```text
/opt/sanity-node/
├── app/
├── config/
│   └── config.yaml
├── html/
│   └── index.html
├── logs/
│   └── generator.log
├── run/
│   └── generator.lock
├── ssh/
└── .ssh/
    └── known_hosts
```

The intended roles are:

- `app/`: an immutable application snapshot from a known release;
- `config/`: private runtime configuration;
- `html/`: the last successfully published dashboard;
- `logs/`: persistent generation log;
- `run/`: non-blocking generation lock;
- `ssh/`: private monitoring keys referenced by configuration;
- `.ssh/known_hosts`: verified SSH host trust for the service account.

Private configuration and credentials must remain outside Git.

## Runtime path contract

The production runner defaults to:

```text
SANITY_NODE_PRODUCTION_ROOT=/opt/sanity-node
SANITY_NODE_APP_ROOT=/opt/sanity-node/app
SANITY_NODE_CONFIG=/opt/sanity-node/config/config.yaml
SANITY_NODE_OUTPUT=/opt/sanity-node/html/index.html
SANITY_NODE_LOG=/opt/sanity-node/logs/generator.log
```

The non-blocking execution lock is stored at:

```text
/opt/sanity-node/run/generator.lock
```

It also protects these retained-runtime defaults from overlap:

```text
SANITY_NODE_REFERENCE_ROOT=/opt/homelab-dashboard
SANITY_NODE_REHEARSAL_ROOT=/opt/sanity-node-public-rehearsal
```

The runner rejects:

- `/` as the production root;
- application, configuration, output, log, or run paths that escape the
  production root;
- overlap with protected reference or rehearsal roots;
- missing configuration;
- missing required executables;
- non-public runtime mode;
- overlapping generation.

Keep the standard paths unless there is a documented operational reason
to override them.

## Operating-system prerequisites

The collector requires:

- a systemd-based Linux distribution;
- Python 3;
- PyYAML for the same Python interpreter used by the scripts;
- Bash;
- OpenSSH client tools;
- `curl`;
- `flock`;
- standard core utilities including `awk`, `grep`, `sha256sum`, `stat`,
  `mv`, `chmod`, and `date`;
- network access to monitored endpoints;
- any optional local tools required by enabled checks.

On Debian- or Ubuntu-derived systems, the core runtime is commonly
provided by packages similar to:

```text
python3
python3-yaml
openssh-client
curl
util-linux
coreutils
```

Package names vary by distribution. Verify commands rather than assuming
a package name.

Check the required base commands:

```bash
python3 --version
python3 -c 'import yaml; print(yaml.__version__)'
bash --version
ssh -V
curl --version
flock --version
systemctl --version
```

Optional local features may additionally require:

- Docker CLI and access to the Docker daemon;
- permission to read selected mountpoints;
- permission to read backup marker files;
- permission to query local systemd units;
- network access to a Diun metrics endpoint;
- other commands explicitly required by the enabled collector module.

Do not grant optional privileges until the corresponding check is
enabled and understood.

## Create the service account

The committed units use the generic account:

```text
sanity-node
```

Create a system account whose home directory is the production root:

```bash
sudo useradd     --system     --home-dir /opt/sanity-node     --shell /usr/sbin/nologin     --user-group     sanity-node
```

If the account already exists, inspect it instead of recreating it:

```bash
getent passwd sanity-node
getent group sanity-node
```

The service account needs:

- read and execute access to `app/`;
- read access to `config/config.yaml`;
- read access to private keys under `ssh/`;
- read access to `.ssh/known_hosts`;
- write access to `html/`, `logs/`, and `run/`;
- network access to configured hosts and endpoints;
- only the local command permissions required by enabled modules.

Do not give the account an interactive shell merely for convenience.

## Create the production workspace

Create the default layout:

```bash
sudo install -d -o root -g root -m 0755 /opt/sanity-node
sudo install -d -o root -g root -m 0755 /opt/sanity-node/app
sudo install -d -o root -g sanity-node -m 0750 /opt/sanity-node/config
sudo install -d -o sanity-node -g sanity-node -m 0775 /opt/sanity-node/html
sudo install -d -o sanity-node -g sanity-node -m 0775 /opt/sanity-node/logs
sudo install -d -o sanity-node -g sanity-node -m 0775 /opt/sanity-node/run
sudo install -d -o root -g sanity-node -m 0750 /opt/sanity-node/ssh
sudo install -d -o sanity-node -g sanity-node -m 0700 /opt/sanity-node/.ssh
```

The application snapshot should normally be root-owned and not writable
by the runtime account.

The private configuration and key directories should be readable only
by the intended administrative and service identities.

## Install an immutable application snapshot

Use a clean temporary clone:

```bash
git clone https://github.com/vonH23rz/sanity-node.git /tmp/sanity-node-release
cd /tmp/sanity-node-release
git checkout v0.3.0
```

Confirm the checked-out revision:

```bash
git status --short --branch
git rev-parse --verify HEAD
```

Install only tracked release content into the application directory:

```bash
git archive v0.3.0     | sudo tar -x -C /opt/sanity-node/app
```

Ensure the required scripts are executable:

```bash
sudo chmod 0755     /opt/sanity-node/app/scripts/generate-dashboard.py     /opt/sanity-node/app/scripts/run-public-production.sh     /opt/sanity-node/app/scripts/startup-preflight.py     /opt/sanity-node/app/scripts/validate-config.py
```

Keep the installed application snapshot root-owned:

```bash
sudo chown -R root:root /opt/sanity-node/app
```

Do not run production directly from a mutable development checkout.

## Install the production configuration

Start from the credential-free template:

```bash
sudo install     -o root     -g sanity-node     -m 0640     /opt/sanity-node/app/examples/config.starter.yaml     /opt/sanity-node/config/config.yaml
```

Edit the private file:

```bash
sudoedit /opt/sanity-node/config/config.yaml
```

The production configuration must contain:

```yaml
dashboard:
  runtime_mode: public
```

For host-native SSH keys, use host paths rather than container paths.

Example:

```yaml
ssh:
  enabled: true
  user: monitoring-user
  key_file: /opt/sanity-node/ssh/storage-server
```

Do not use `/app/ssh/...` in the host-native configuration.

Use `examples/config.example.yaml` as a schema reference, not as a file
to copy unchanged.

## Install SSH identities

Install a dedicated private key as the runtime account:

```bash
sudo install -o sanity-node -g sanity-node -m 0600 /secure/source/storage-server-key /opt/sanity-node/ssh/storage-server
```

OpenSSH rejects private keys that are readable by another user or group.
A root-owned, group-readable `0640` key is therefore not a valid model
for a service running as `sanity-node`.

The private key should be:

```text
owner: sanity-node
group: sanity-node
mode: 0600
```

Root can still replace or back up the file administratively.

Verify ownership and mode:

```bash
stat --printf='MODE=%a OWNER=%U GROUP=%G\n' /opt/sanity-node/ssh/storage-server
```

Test the identity deliberately as the runtime account:

```bash
sudo -u sanity-node ssh -i /opt/sanity-node/ssh/storage-server -o IdentitiesOnly=yes monitoring-user@storage-server.example.internal
```

Do not disable host-key verification.

## Establish verified SSH host trust

The service account's home is `/opt/sanity-node`, so normal OpenSSH host
trust is stored at:

```text
/opt/sanity-node/.ssh/known_hosts
```

Obtain the expected host key through a trusted channel.

A candidate key can be collected for comparison:

```bash
ssh-keyscan storage-server.example.internal     > /tmp/storage-server.known-hosts
```

Display its fingerprint:

```bash
ssh-keygen -lf /tmp/storage-server.known-hosts
```

Compare the fingerprint through an independent trusted source before
installing it.

After verification:

```bash
sudo install     -o sanity-node     -g sanity-node     -m 0600     /tmp/storage-server.known-hosts     /opt/sanity-node/.ssh/known_hosts
```

For multiple hosts, build and verify the complete file before installing
it.

Never use `StrictHostKeyChecking=no` as a deployment shortcut.

## Validate service-account access

Verify filesystem access as the service account:

```bash
sudo -u sanity-node     test -r /opt/sanity-node/config/config.yaml

sudo -u sanity-node     test -x /opt/sanity-node/app/scripts/run-public-production.sh

sudo -u sanity-node     test -w /opt/sanity-node/html

sudo -u sanity-node     test -w /opt/sanity-node/logs

sudo -u sanity-node     test -w /opt/sanity-node/run
```

Inspect the complete path ownership:

```bash
namei -l /opt/sanity-node/config/config.yaml
namei -l /opt/sanity-node/ssh/storage-server
namei -l /opt/sanity-node/.ssh/known_hosts
```

## Validate configuration

Run the validator as the runtime account:

```bash
sudo -u sanity-node     /opt/sanity-node/app/scripts/validate-config.py     /opt/sanity-node/config/config.yaml
```

Every validation error must be corrected before activation.

The host-native configuration should use host-valid paths for keys,
marker files, output, and logs.

## Run startup preflight

Run preflight with the permanent paths:

```bash
sudo -u sanity-node     /opt/sanity-node/app/scripts/startup-preflight.py     --config /opt/sanity-node/config/config.yaml     --output /opt/sanity-node/html/index.html     --log /opt/sanity-node/logs/generator.log
```

Preflight checks:

- configuration readability and YAML mapping structure;
- output and log parent writability;
- required SSH sections;
- required SSH usernames;
- required key paths;
- key existence, file type, and readability.

Preflight does not prove that every remote command is authorized. Test
enabled remote capabilities separately.

## Local collector integration

Host-native execution makes collector-local checks possible, but it does
not grant their permissions automatically.

### Collector-local Docker

Collector-local Docker checks execute:

```text
docker inspect
docker ps
```

The `sanity-node` account therefore needs Docker daemon access.

On many systems this means membership in the Docker group:

```bash
sudo usermod -aG docker sanity-node
```

Docker daemon access is effectively administrative host access.

Use it only after deliberate risk acceptance. Restart the relevant
service process after changing group membership.

An alternative is to avoid collector-local Docker checks and use HTTP
checks or remote least-privilege integration.

### Collector-local storage

Local storage checks execute `df -P` against configured paths.

The service account needs search and read access through every parent
directory of the monitored mountpoint.

Do not loosen unrelated filesystem permissions just to make a dashboard
check pass.

### Collector-local backup state

Local backup checks may need to:

- read a marker file;
- inspect a log directory;
- query `systemctl is-active` for a timer.

Grant only the required read and query access.

### Collector-local metrics endpoints

A Diun or similar endpoint configured with `127.0.0.1` is accessed from
the host-native collector itself.

Confirm the endpoint is actually listening on the expected host
interface and port.

## Remote Linux integration

Remote Linux modules use SSH and can collect:

- system information;
- Docker container state;
- filesystem capacity;
- backup marker freshness;
- optional timer state.

The remote monitoring account needs only the commands required by the
enabled modules.

Examples can include:

```text
uname
hostname
uptime
nproc
free
df
stat
systemctl is-active
docker inspect
docker ps
```

Do not provide unrestricted sudo when a narrow command allowlist is
sufficient.

## TrueNAS SCALE integration

TrueNAS monitoring uses SSH-backed commands such as:

```text
midclt call app.query
midclt call pool.query
midclt call pool.snapshottask.query
midclt call replication.query
midclt call disk.temperatures
zpool status -P
zfs list
smartctl -H
```

The exact command set depends on enabled modules.

Temperature and SMART collection may require a narrowly scoped
passwordless sudo rule for `smartctl`.

Review the generated commands and grant only the required operations.

Do not disable SSH host-key verification or broadly elevate the remote
account solely to avoid permission analysis.

## Optional environment overrides

The generation service reads:

```text
/etc/default/sanity-node
```

The file is optional.

Use it only for reviewed environment overrides, such as alternate
protected roots or locale settings.

Example:

```text
LC_ALL=C
LANG=C
```

Protect the file:

```bash
sudo install     -o root     -g root     -m 0644     /dev/null     /etc/default/sanity-node
```

Do not place private SSH keys or multiline configuration in the
environment file.

The committed service template already defines the standard runtime
paths.

## Install the systemd units

Install the committed production units:

```bash
sudo install     -o root     -g root     -m 0644     /opt/sanity-node/app/systemd/sanity-node-generate.service     /etc/systemd/system/sanity-node-generate.service

sudo install     -o root     -g root     -m 0644     /opt/sanity-node/app/systemd/sanity-node-generate.timer     /etc/systemd/system/sanity-node-generate.timer

sudo install     -o root     -g root     -m 0644     /opt/sanity-node/app/systemd/sanity-node-web.service     /etc/systemd/system/sanity-node-web.service
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Inspect the installed units:

```bash
systemctl cat sanity-node-generate.service
systemctl cat sanity-node-generate.timer
systemctl cat sanity-node-web.service
```

The committed templates require the standard account, paths, and port.

## Generation service contract

`sanity-node-generate.service` is a hardened oneshot service.

It:

- waits for `network-online.target`;
- runs as `sanity-node:sanity-node`;
- uses `/opt/sanity-node/app` as its working directory;
- invokes `scripts/run-public-production.sh`;
- allows writes only below `/opt/sanity-node`;
- treats retained reference and rehearsal roots as read-only when they
  exist;
- uses no-new-privileges;
- uses private temporary storage;
- applies read-only system protection;
- restricts SUID and SGID creation;
- locks process personality.

The service is expected to be inactive between successful runs because
it is `Type=oneshot`.

## Fail-closed generation contract

Every production generation:

1. validates all runtime paths;
2. rejects protected-root overlap;
3. acquires a non-blocking lock;
4. validates configuration;
5. requires `dashboard.runtime_mode: public`;
6. runs startup preflight;
7. renders to a process-specific temporary file;
8. requires nonempty output;
9. requires `Utility Node Services`;
10. requires `public-systems-section`;
11. rejects obsolete `Config Preview` wording;
12. applies output mode `0664`;
13. atomically replaces the previous successful output;
14. records the output SHA-256 and duration.

A failed generation does not replace the last successful dashboard.

## Run the first manual generation

Do not enable the timer before a successful manual generation.

Start the oneshot:

```bash
sudo systemctl start sanity-node-generate.service
```

Inspect its result:

```bash
systemctl status sanity-node-generate.service --no-pager
systemctl show sanity-node-generate.service     --property=Result     --value
journalctl -u sanity-node-generate.service -n 200 --no-pager
```

Verify the permanent output:

```bash
sudo -u sanity-node     test -s /opt/sanity-node/html/index.html

grep -F "Dashboard Summary"     /opt/sanity-node/html/index.html

grep -F "Runtime Detail"     /opt/sanity-node/html/index.html

! grep -F "Config Preview"     /opt/sanity-node/html/index.html
```

Inspect ownership and mode:

```bash
stat     --printf='MODE=%a UID=%u GID=%g SIZE=%s MTIME=%Y\n'     /opt/sanity-node/html/index.html
```

The expected output mode is `0664`.

## Start the web service

The web service serves only:

```text
/opt/sanity-node/html
```

It listens on:

```text
TCP port 8088
```

Enable and start it after a successful dashboard exists:

```bash
sudo systemctl enable --now sanity-node-web.service
```

Verify:

```bash
systemctl is-active sanity-node-web.service
systemctl is-enabled sanity-node-web.service
curl --fail http://127.0.0.1:8088/
```

Confirm the served response matches the file:

```bash
curl --fail --silent http://127.0.0.1:8088/     > /tmp/sanity-node-response.html

cmp     /opt/sanity-node/html/index.html     /tmp/sanity-node-response.html
```

The web service starts independently from the generator. It continues
serving the last successful dashboard while a scheduled generation runs
or fails.

## Enable scheduled generation

The committed timer uses:

```text
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=1s
RandomizedDelaySec=0
Persistent=true
```

Enable it only after manual generation and web validation:

```bash
sudo systemctl enable --now sanity-node-generate.timer
```

Verify:

```bash
systemctl is-active sanity-node-generate.timer
systemctl is-enabled sanity-node-generate.timer
systemctl list-timers sanity-node-generate.timer --all
```

Observe at least one scheduled generation:

```bash
journalctl     -u sanity-node-generate.service     --since '-10 minutes'     --no-pager
```

## Port differences

The two deployment models intentionally use different default ports:

```text
Docker Compose host port: 8099
Host-native systemd port: 8088
```

Do not confuse the Docker `.env` setting with the host-native systemd
web service.

The host-native port is encoded directly in:

```text
systemd/sanity-node-web.service
```

Keeping port `8088` is recommended when using the committed production
contract.

A reverse proxy can forward to:

```text
http://127.0.0.1:8088
```

## Changing the host-native port

Changing the systemd port is an explicit deployment customization.

Use a drop-in that clears and replaces `ExecStart`:

```bash
sudo systemctl edit sanity-node-web.service
```

Example:

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 -m http.server 8090 --directory /opt/sanity-node/html
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart sanity-node-web.service
```

Record the custom port in deployment documentation and update firewall
and reverse-proxy configuration.

## Reverse proxy integration

The host-native web service provides plain HTTP.

TLS, authentication, DNS, access control, and Internet exposure remain
the responsibility of the reverse proxy and network administrator.

Recommended proxy target:

```text
http://127.0.0.1:8088
```

Keep direct port access restricted to trusted networks or localhost when
the reverse proxy is the intended entry point.

The dashboard can reveal infrastructure names, services, storage, and
operational status. Do not expose it publicly without deliberate access
controls.

## Service-account drop-ins

A deployment may need a different runtime account for collector-local
access.

The generic templates intentionally use `sanity-node`.

A private override can change the account:

```bash
sudo systemctl edit sanity-node-generate.service
```

Example:

```ini
[Service]
User=collector-account
Group=collector-account
```

Any override must preserve:

- read access to application and configuration;
- write access to output, logs, and lock directory;
- verified SSH trust;
- required local command access;
- the unit hardening contract where possible.

Account overrides are deployment-specific and must not publish private
usernames or credentials into the repository.

The web service normally does not need collector privileges and should
remain on the restricted `sanity-node` account.

## Monitoring the deployment

Useful commands include:

```bash
systemctl status sanity-node-web.service --no-pager
systemctl status sanity-node-generate.timer --no-pager
systemctl status sanity-node-generate.service --no-pager
systemctl list-timers sanity-node-generate.timer --all
journalctl -u sanity-node-generate.service -n 200 --no-pager
journalctl -u sanity-node-web.service -n 100 --no-pager
tail -n 200 /opt/sanity-node/logs/generator.log
stat /opt/sanity-node/html/index.html
curl --fail http://127.0.0.1:8088/
```

A healthy permanent state normally means:

- web service active and enabled;
- generation timer active and enabled;
- generation service inactive between runs with last result `success`;
- nonempty output;
- local HTTP response matching the output file.

## Update the host-native deployment

Treat updates as controlled application-snapshot replacement.

Before updating:

1. record the current release and application hash;
2. back up configuration, SSH material, environment overrides, units,
   and output;
3. confirm the web service is healthy;
4. stop the generation timer;
5. ensure no generation is running;
6. prepare the new application snapshot separately.

Stop scheduled generation:

```bash
sudo systemctl stop sanity-node-generate.timer
```

Confirm the oneshot is not running:

```bash
systemctl is-active sanity-node-generate.service
```

Prepare a new snapshot under a temporary directory:

```bash
sudo install -d -o root -g root -m 0755 /opt/sanity-node/app.next

git -C /tmp/sanity-node-release fetch --tags origin
git -C /tmp/sanity-node-release checkout v0.3.0

git -C /tmp/sanity-node-release archive v0.3.0     | sudo tar -x -C /opt/sanity-node/app.next
```

Validate the new scripts:

```bash
sudo chmod 0755     /opt/sanity-node/app.next/scripts/generate-dashboard.py     /opt/sanity-node/app.next/scripts/run-public-production.sh     /opt/sanity-node/app.next/scripts/startup-preflight.py     /opt/sanity-node/app.next/scripts/validate-config.py

sudo chown -R root:root /opt/sanity-node/app.next
```

Preserve the previous snapshot and activate the new one:

```bash
sudo mv /opt/sanity-node/app /opt/sanity-node/app.previous
sudo mv /opt/sanity-node/app.next /opt/sanity-node/app
```

Install any updated unit templates, then reload systemd:

```bash
sudo install -o root -g root -m 0644     /opt/sanity-node/app/systemd/sanity-node-generate.service     /etc/systemd/system/sanity-node-generate.service

sudo install -o root -g root -m 0644     /opt/sanity-node/app/systemd/sanity-node-generate.timer     /etc/systemd/system/sanity-node-generate.timer

sudo install -o root -g root -m 0644     /opt/sanity-node/app/systemd/sanity-node-web.service     /etc/systemd/system/sanity-node-web.service

sudo systemctl daemon-reload
```

Validate configuration and run one manual generation.

Only after success:

```bash
sudo systemctl restart sanity-node-web.service
sudo systemctl start sanity-node-generate.timer
```

Keep `app.previous` until the new release has completed sufficient
scheduled observation.

## Roll back an application update

Stop scheduled generation:

```bash
sudo systemctl stop sanity-node-generate.timer
```

Preserve the failed snapshot and restore the previous one:

```bash
sudo mv /opt/sanity-node/app /opt/sanity-node/app.failed
sudo mv /opt/sanity-node/app.previous /opt/sanity-node/app
```

Restore previous unit files when they changed, then:

```bash
sudo systemctl daemon-reload
sudo systemctl start sanity-node-generate.service
sudo systemctl restart sanity-node-web.service
sudo systemctl start sanity-node-generate.timer
```

Verify output, HTTP, timer state, and logs.

Do not delete the failed snapshot until the regression is understood.

## Configuration rollback

Keep versioned private backups outside the served and application
directories.

Before a significant configuration change:

```bash
sudo cp -a     /opt/sanity-node/config/config.yaml     /opt/sanity-node/config/config.yaml.backup
```

Validate before manual generation.

If a change fails:

```bash
sudo cp -a     /opt/sanity-node/config/config.yaml.backup     /opt/sanity-node/config/config.yaml
```

Run validation and manual generation again.

Scheduled generation protects the previous dashboard from failed output,
but it does not version the configuration for you.

## Back up the host-native deployment

Essential state includes:

```text
/opt/sanity-node/config/
/opt/sanity-node/ssh/
/opt/sanity-node/.ssh/known_hosts
/etc/default/sanity-node
/etc/systemd/system/sanity-node-generate.service
/etc/systemd/system/sanity-node-generate.timer
/etc/systemd/system/sanity-node-web.service
```

Also consider retaining:

```text
/opt/sanity-node/logs/
/opt/sanity-node/html/index.html
/opt/sanity-node/app/
```

Protect backups that contain private keys or infrastructure inventory.

## Stop the deployment

Stop scheduled generation first:

```bash
sudo systemctl stop sanity-node-generate.timer
```

Stop the web service:

```bash
sudo systemctl stop sanity-node-web.service
```

Disable both when the stop is intended to persist across reboot:

```bash
sudo systemctl disable sanity-node-generate.timer
sudo systemctl disable sanity-node-web.service
```

The oneshot generation service is normally inactive between runs.

## Uninstall the host-native deployment

Back up required state first.

Disable and stop units:

```bash
sudo systemctl disable --now sanity-node-generate.timer
sudo systemctl disable --now sanity-node-web.service
sudo systemctl stop sanity-node-generate.service
```

Remove installed units:

```bash
sudo rm -f     /etc/systemd/system/sanity-node-generate.service     /etc/systemd/system/sanity-node-generate.timer     /etc/systemd/system/sanity-node-web.service

sudo systemctl daemon-reload
sudo systemctl reset-failed
```

Remove the workspace only after confirming the path and backups:

```bash
sudo rm -rf /opt/sanity-node
```

Optionally remove the service account when no other resource uses it:

```bash
sudo userdel sanity-node
sudo groupdel sanity-node
```

Do not remove retained reference or rehearsal runtimes as part of a
generic uninstall unless a separate retirement decision authorizes it.

## Troubleshooting

### Generation service fails

Inspect:

```bash
systemctl status sanity-node-generate.service --no-pager
journalctl -u sanity-node-generate.service -n 300 --no-pager
tail -n 300 /opt/sanity-node/logs/generator.log
```

Common causes include:

- invalid configuration;
- non-public runtime mode;
- unreadable configuration or key;
- missing verified host trust;
- unwritable output, log, or run directory;
- missing runtime dependency;
- remote command permission failure;
- another generation holding the lock;
- path overlap with a protected runtime;
- missing expected dashboard markers.

### Web service fails

Inspect:

```bash
systemctl status sanity-node-web.service --no-pager
journalctl -u sanity-node-web.service -n 200 --no-pager
sudo ss -ltnp | grep ':8088'
```

The web service requires a nonempty
`/opt/sanity-node/html/index.html`.

It does not invoke the generator automatically.

Run and validate the generation service first.

### Timer is active but output is stale

Inspect the timer and recent oneshot results:

```bash
systemctl list-timers sanity-node-generate.timer --all
systemctl show sanity-node-generate.service     --property=Result     --value
journalctl     -u sanity-node-generate.service     --since '-30 minutes'     --no-pager
```

A failed generation intentionally preserves the previous dashboard.

### SSH checks fail

Test as the actual runtime account:

```bash
sudo -u sanity-node     ssh     -i /opt/sanity-node/ssh/storage-server     -o IdentitiesOnly=yes     monitoring-user@storage-server.example.internal
```

Check:

- key readability;
- verified `known_hosts`;
- remote username;
- network reachability;
- remote command permissions;
- configuration key path;
- service-account home directory.

### Collector-local Docker checks fail

Test:

```bash
sudo -u sanity-node docker ps
```

If access is denied, either grant deliberate Docker daemon access or
disable collector-local Docker checks.

Do not weaken the Docker socket permissions globally.

### Local backup or storage checks fail

Test the exact marker or mount path as the service account.

Examples:

```bash
sudo -u sanity-node test -r /var/lib/example-backup/last-successful
sudo -u sanity-node df -P /srv/example-storage
```

Grant only the narrow filesystem access required.

## Security checklist

Before activation, confirm:

- application files are root-owned;
- configuration is not world-readable;
- private keys are not world-readable;
- SSH fingerprints were verified independently;
- `StrictHostKeyChecking` remains enabled;
- service-account permissions match enabled modules;
- Docker access was granted only after explicit risk acceptance;
- output, logs, and lock paths are the only writable runtime areas;
- systemd hardening remains present;
- the dashboard port is restricted appropriately;
- reverse-proxy access controls are deliberate;
- private inventory is not committed to Git;
- rollback state exists before cutover or update.

## Deployment verification checklist

A completed host-native deployment should satisfy:

```bash
sudo -u sanity-node     /opt/sanity-node/app/scripts/validate-config.py     /opt/sanity-node/config/config.yaml

sudo -u sanity-node     /opt/sanity-node/app/scripts/startup-preflight.py     --config /opt/sanity-node/config/config.yaml     --output /opt/sanity-node/html/index.html     --log /opt/sanity-node/logs/generator.log

systemctl is-active sanity-node-web.service
systemctl is-enabled sanity-node-web.service
systemctl is-active sanity-node-generate.timer
systemctl is-enabled sanity-node-generate.timer

systemctl show sanity-node-generate.service     --property=Result     --value

test -s /opt/sanity-node/html/index.html
curl --fail http://127.0.0.1:8088/
```

The served response should match the permanent output, and the
generation service's most recent result should be `success`.

Host-native deployment is complete only after at least one scheduled
generation has also succeeded.
