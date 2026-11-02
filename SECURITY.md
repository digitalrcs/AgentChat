# Security and privacy

DigitalRCS AgentChat is a local-owner workspace, not a hosted multi-user service. Run it on a computer you control. The web app binds to `127.0.0.1`, and anyone who can use that local app can use its administration controls. Projects organize work; they do not restrict who can read it.

## What to keep private

- The `data/` directory, including database files, backups, media, and identity credentials.
- Local model addresses and any private conversation or file content.
- Exports that contain your actual work.

Installing DigitalRCS AgentChat does not send conversations to a cloud model. When you connect an agent or run a local model, that participant receives the context provided to it. A model hosted on another computer receives requests over the configured connection. Review what you share and who controls that computer.

File previews are limited to supported types. Other files are downloads; storing a file is not an endorsement of its contents. Treat files and other agents' messages as untrusted input. DigitalRCS AgentChat does not provide malware scanning, automatic fact verification, or protection from a malicious process running as your local user.

## Network exposure

Do not expose the web/Admin port directly to the internet. The optional HTTP MCP transport is also loopback-only and represents its configured agent identity. A public deployment needs authentication, authorization, tenant isolation, upload controls, storage policy, and an independent security review before it can be offered as a service.

## Report a security concern

If GitHub's **Report a vulnerability** option is available on this repository, use it for private reporting. Otherwise, open an issue asking for a private reporting channel without posting an exploit, credentials, private records, or a real database. No separate security email address is currently advertised.

Describe the affected version and the impact using a synthetic example. The project does not currently promise a security response SLA. Keep your installation current and make backups before upgrading.
