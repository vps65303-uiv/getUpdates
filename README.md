# Shellndrod (safe Telegram status monitor)

This Android app accepts only three Telegram commands:
- `/help`
- `/status`
- `/exit`

It does not run shell commands, read files, capture the screen, or collect contacts/messages.

## Build
1. Put `main.py` and `buildozer.spec` in the repository root.
2. Put `build.yml` at `.github/workflows/build.yml`.
3. Push to `main` or `master`, or start the workflow manually from GitHub Actions.
4. Download the APK from the workflow's Artifacts section.

## Use
Open the app, enter your Telegram bot token and your own chat ID, then tap Start monitoring.
The token is kept only in the app's memory while it runs; do not share it.
