# from_zero

`from_zero` is a standalone documentation project for building and validating `zcprotobuf` from a clean machine.

## Contents

- `README.md`: project overview and quick start
- `ZCPROTOBUF_FROM_ZERO.md`: full step-by-step guide
- `publish_github.sh`: helper script to push this project to GitHub

## Quick Start

```bash
cd from_zero
./publish_github.sh
```

Optional:

```bash
./publish_github.sh your-repo-name
./publish_github.sh your-account/your-repo-name
VISIBILITY=private ./publish_github.sh
```

## Notes

- The script initializes git if needed.
- It creates branch `main` and pushes to GitHub.
- If no changes are detected, it skips commit and only pushes.
