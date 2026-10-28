# Building the executable

LineBackupToDiscord.exe is built with [PyInstaller](https://pyinstaller.org/). PyInstaller can only build for the
OS it runs on, so the Windows `.exe` has to be built on Windows.

## Building it yourself

1. Install the dependencies, PyInstaller included (it's in the `dev` dependency group).

   If using uv, simply run:
   ```bash
   uv sync
   ```

   Or, if using regular pip with requirements.txt, run:
   ```bash
   pip install -r requirements.txt pyinstaller
   ```

2. Run this command in the project root directory (with `uv run` in front if you use uv):
   ```bash
   pyinstaller --onefile --name=LineBackupToDiscord --icon=./readme_imgs/logo.ico --additional-hooks-dir ./build_executable/extra_hooks main.py
   ```
   `extra_hooks` makes sure every part of uvicorn, the webhook server, is bundled into the executable.

3. Done! The executable will be created in the `dist` folder.

## Publishing a release

Releases are built and published by the [Release](../.github/workflows/release.yml) GitHub Actions workflow, on a
Windows runner:

1. Update `VERSION` in `utilities.py` and `version` in `pyproject.toml`, then run `uv lock`
2. Add a section for the new version at the top of [CHANGELOG.md](../CHANGELOG.md). The heading is the release title,
   e.g. `## v0.1.2 - Some Title`, and everything under it until the next `## ` heading is the release notes
3. Push to `master`, then start the workflow in one of two ways:
    - **Actions** tab → **Release** → **Run workflow**. It creates a draft release by default, so you can check it and
      click **Publish release** when it's ready
    - Push a tag that matches `VERSION`, e.g. `git tag v0.1.2 && git push origin v0.1.2`. The release is published
      right away

The workflow builds the executable, runs it once to generate `config.yml` (which also makes sure it starts), and
uploads `LineBackupToDiscord-<version>.zip` with the executable and `config.yml` inside to the release.
