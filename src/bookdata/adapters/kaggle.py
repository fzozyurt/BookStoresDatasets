"""Kaggle yayıncı port'u: veri setini Kaggle'a yükler.

Veri seti kimliği (`BOOKDATA_KAGGLE_DATASET`) ve kimlik bilgileri
(`KAGGLE_USERNAME`, `KAGGLE_KEY`) kodda gömülü değildir; ENV'den alınır.
Böylece repo başkası tarafından fork edilince kendi veri setine yükler.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class KagglePublisher:
    def __init__(self, dataset_id: str | None, credentials_env_ok: bool = True) -> None:
        self.dataset_id = dataset_id
        self.credentials_env_ok = credentials_env_ok

    def can_publish(self) -> bool:
        return bool(self.dataset_id)

    def publish(self, csv_path: Path, store: str, note: str) -> None:
        from kaggle.api.kaggle_api_extended import KaggleApi  # yalnızca yayınlarken yüklenir

        if not self.dataset_id:
            logger.warning(
                "Kaggle veri seti kimliği tanımlı değil (BOOKDATA_KAGGLE_DATASET). Yayın atlandı."
            )
            return

        owner, slug = self.dataset_id.split("/", 1)
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            (workdir / "dataset-metadata.json").write_text(
                json.dumps(
                    {
                        "title": slug,
                        "id": self.dataset_id,
                        "licenses": [{"name": "CC0-1.0"}],
                        "resources": [{"path": csv_path.name, "description": f"{store} veri seti"}],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workdir / csv_path.name).write_bytes(csv_path.read_bytes())

            api = KaggleApi()
            api.authenticate()
            api.dataset_create_version(folder=str(workdir), version_notes=note)
        logger.info("Kaggle yayını tamamlandı: %s (%s)", self.dataset_id, note)
