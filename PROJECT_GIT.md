# zcprotobuf Git Project Setup

`zcprotobuf` currently lives inside a larger workspace.  
To use it as a standalone git project:

```bash
cd zcprotobuf
git init
git add .
git commit -m "init zcprotobuf project"
git branch -M main
```

Add GitHub remote and push:

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

Recommended repo name: `zcprotobuf`

Before pushing, verify:
- `README.md`
- `TESTING.md`
- `native/build.sh`
- `internal.py`, `_zigcodec.py`, `plugin.py`
