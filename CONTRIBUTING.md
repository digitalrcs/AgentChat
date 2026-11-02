# Help improve AgentChat

You do not need to write code to help. Clear bug reports, better instructions, accessible design feedback, and examples of useful agent collaboration all matter.

## Report a problem

Open an [issue](https://github.com/digitalrcs/AgentChat/issues). Tell us what you expected, what happened, and the steps that reproduce it. Include your operating system and AgentChat version if you know them.

Use a small made-up example rather than sharing private chat history, recordings, identity files, or your database. Crop screenshots to the relevant area. Follow [SECURITY.md](SECURITY.md) for security concerns.

## Suggest an improvement

Describe the problem you are trying to solve, who it would help, and what the experience should feel like. A sketch or short example conversation is useful. Please distinguish a requested feature from something that already works.

## Make a code or documentation change

1. Fork the repository and create a branch for one focused change.
2. Read [the installation guide](wiki/Installation.md) and use an isolated test database.
3. Keep credentials, runtime databases, uploaded media, generated logs, and personal endpoint settings out of commits.
4. Add meaningful tests for changed behavior. Run the backend tests and frontend build described below.
5. Open a pull request explaining the problem, the resulting behavior, and how you checked it. Include a screenshot for a visible UI change.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp data\pytest-contribution
npm.cmd run build
```

Documentation should be friendly to someone opening a terminal for the first time. Explain the result of a step before introducing the command. Avoid claiming that the app can automatically understand a file merely because it can store it.

Contributions are made under the project's [MIT license](LICENSE). Be respectful, keep feedback specific, and welcome different levels of experience.
