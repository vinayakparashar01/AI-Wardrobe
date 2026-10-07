from pathlib import Path

MEDIA_DIR = Path(__file__).resolve().parents[2] / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def delete_image_file(image_url: str | None) -> None:
    if not image_url:
        return

    file_path = MEDIA_DIR / Path(image_url).name

    if file_path.exists():
        file_path.unlink()
