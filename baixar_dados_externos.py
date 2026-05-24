"""
Baixa datasets externos para apoio ao fine-tuning/avaliação.

Uso:
  python baixar_dados_externos.py --dataset all
  python baixar_dados_externos.py --dataset medquad
  python baixar_dados_externos.py --dataset pubmedqa --force
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
EXTERNOS_DIR = BASE_DIR / "dados" / "externos"
RAW_DIR = EXTERNOS_DIR / "raw"
DOCS_DIR = EXTERNOS_DIR / "docs"
MANIFEST_PATH = RAW_DIR / "download_manifest.json"

URL_MEDQUAD_ZIP = "https://github.com/abachaa/MedQuAD/archive/refs/heads/master.zip"
URL_PUBMEDQA_JSON = "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json"


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, destination: Path, force: bool = False) -> dict:
    if destination.exists() and not force:
        return {
            "status": "skipped_exists",
            "path": str(destination),
            "size_bytes": destination.stat().st_size,
            "url": url,
        }

    req = Request(url, headers={"User-Agent": "fiap-fase3-downloader/1.0"})
    with urlopen(req, timeout=120) as response:  # nosec - URL fixa e pública
        data = response.read()

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return {
        "status": "downloaded",
        "path": str(destination),
        "size_bytes": destination.stat().st_size,
        "url": url,
    }


def maybe_download_medmcqa(force: bool = False) -> dict:
    """
    Tenta baixar MedMCQA via Hugging Face datasets (opcional).
    Se datasets não estiver instalado, registra instrução e segue sem falhar.
    """
    medmcqa_dir = RAW_DIR / "medmcqa"
    if medmcqa_dir.exists() and not force:
        return {
            "status": "skipped_exists",
            "path": str(medmcqa_dir),
            "note": "diretório já existe",
        }

    try:
        from datasets import load_dataset  # type: ignore
    except Exception:
        return {
            "status": "skipped_missing_dependency",
            "path": str(medmcqa_dir),
            "note": "instale com: pip install datasets",
        }

    for candidate in ("medmcqa", "openlifescienceai/medmcqa"):
        try:
            ds = load_dataset(candidate)
            medmcqa_dir.mkdir(parents=True, exist_ok=True)
            for split_name in ds.keys():
                out_file = medmcqa_dir / f"{split_name}.jsonl"
                ds[split_name].to_json(str(out_file), orient="records", lines=True)
            return {
                "status": "downloaded",
                "path": str(medmcqa_dir),
                "source": candidate,
            }
        except Exception:
            continue

    return {
        "status": "error",
        "path": str(medmcqa_dir),
        "note": "não foi possível baixar MedMCQA via datasets",
    }


def write_manifest(entries: list[dict]) -> None:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixar dados externos do projeto.")
    parser.add_argument(
        "--dataset",
        choices=["all", "medquad", "pubmedqa", "medmcqa"],
        default="all",
        help="Dataset a baixar (default: all).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Força re-download mesmo se o arquivo já existir.",
    )
    args = parser.parse_args()

    ensure_dirs()
    entries: list[dict] = []

    if args.dataset in ("all", "medquad"):
        entries.append(
            download_file(
                URL_MEDQUAD_ZIP,
                RAW_DIR / "medquad.zip",
                force=args.force,
            )
        )

    if args.dataset in ("all", "pubmedqa"):
        entries.append(
            download_file(
                URL_PUBMEDQA_JSON,
                RAW_DIR / "pubmedqa_ori_pqal.json",
                force=args.force,
            )
        )

    if args.dataset in ("all", "medmcqa"):
        entries.append(maybe_download_medmcqa(force=args.force))

    write_manifest(entries)

    print("\nDownload concluído.")
    print(f"Manifesto: {MANIFEST_PATH}")
    for item in entries:
        print(
            f"- {item.get('status')}: {item.get('path')}"
            + (f" ({item.get('note')})" if item.get("note") else "")
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
