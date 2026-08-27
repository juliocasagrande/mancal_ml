"""Baixa os arquivos brutos do dataset e confere o hash de cada um.

Uso:
    .\\.venv\\Scripts\\python.exe backend\\scripts\\download_dataset.py

Lê `data/dataset_manifest.json`, baixa cada arquivo listado para
`data/raw/` e verifica o SHA-256 contra o valor registrado no manifesto.
Falha (sem gravar o arquivo final) se o hash não conferir.
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "data" / "dataset_manifest.json"
RAW_DIR = ROOT / "data" / "raw"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)  # noqa: S310 - fonte fixa e documentada
    tmp.replace(dest)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    failures = []
    for entry in manifest["files"]:
        dest = RAW_DIR / entry["local_name"]
        expected_hash = entry["sha256"]

        if dest.exists() and sha256_of(dest) == expected_hash:
            print(f"OK (já presente): {entry['local_name']}")
            continue

        print(f"Baixando {entry['local_name']} ...")
        download_file(entry["download_url"], dest)

        actual_hash = sha256_of(dest)
        if actual_hash != expected_hash:
            print(
                f"ERRO: hash divergente para {entry['local_name']}: "
                f"esperado {expected_hash}, obtido {actual_hash}",
                file=sys.stderr,
            )
            dest.unlink(missing_ok=True)
            failures.append(entry["local_name"])
        else:
            print(f"OK: {entry['local_name']}")

    if failures:
        print(f"\nFalha ao validar {len(failures)} arquivo(s): {failures}", file=sys.stderr)
        return 1

    print(f"\nDataset verificado com sucesso em {RAW_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
