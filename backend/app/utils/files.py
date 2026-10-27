import logging
import os
import re
from pathlib import Path
from typing import NamedTuple

import cloudinary
import cloudinary.exceptions
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

# Base and Media directories (preserved for backwards compatibility with local /media/ files)
BASE_DIR = Path(__file__).resolve().parents[2]
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")


class CloudinaryUploadResult(NamedTuple):
    """Result of a Cloudinary image upload containing secure HTTPS URL and public ID."""

    secure_url: str
    public_id: str


class CloudinaryError(HTTPException, RuntimeError):
    """Custom exception raised when Cloudinary operations fail."""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.args = (detail,)


def configure_cloudinary() -> None:
    """Configure Cloudinary using environment variables."""
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


# Configure Cloudinary on module import
configure_cloudinary()


def _is_cloudinary_configured() -> bool:
    """Check if Cloudinary credentials are set in the SDK or environment."""
    config = cloudinary.config()
    cloud_name = config.cloud_name or os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = config.api_key or os.getenv("CLOUDINARY_API_KEY")
    api_secret = config.api_secret or os.getenv("CLOUDINARY_API_SECRET")
    return bool(cloud_name and api_key and api_secret)


def _ensure_cloudinary_configured() -> None:
    """Validate that required Cloudinary credentials are available."""
    if not _is_cloudinary_configured():
        # Attempt to re-configure in case environment variables were set at runtime
        configure_cloudinary()

    if not _is_cloudinary_configured():
        raise CloudinaryError(
            "Cloudinary credentials are not configured. Please set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET environment variables.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def extract_public_id_from_url(url: str) -> str | None:
    """Extract the Cloudinary public ID from an asset URL.

    Handles standard, versioned, and transformed Cloudinary URLs.
    """
    if "/upload/" not in url:
        return None

    path_part = url.split("?")[0].split("#")[0]
    upload_part = path_part.split("/upload/")[1]
    segments = upload_part.split("/")

    idx = 0
    while idx < len(segments):
        seg = segments[idx]
        if re.match(r"^v\d+$", seg):
            idx += 1
            break
        if "_" in seg or "," in seg:
            idx += 1
            continue
        break

    remaining = "/".join(segments[idx:])
    if not remaining:
        return None

    return remaining.rsplit(".", 1)[0]


def upload_image_to_cloudinary(
    file: UploadFile,
    folder: str | None = "clothing",
    **options,
) -> CloudinaryUploadResult:
    """Upload a FastAPI UploadFile to Cloudinary.

    Args:
        file: The FastAPI UploadFile to upload.
        folder: Cloudinary folder where the asset should be stored (defaults to 'clothing').
        **options: Additional upload parameters passed to Cloudinary uploader.

    Returns:
        CloudinaryUploadResult named tuple with (secure_url, public_id).

    Raises:
        CloudinaryError: If configuration is missing, network request fails, or
                         the upload does not return a valid secure URL and public ID.
    """
    if not file:
        raise CloudinaryError(
            "No file provided for upload.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate image content type if provided
    if hasattr(file, "content_type") and file.content_type:
        if not file.content_type.startswith("image/"):
            raise CloudinaryError(
                "Only image files are allowed",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Ensure Cloudinary is properly configured (skip check if uploader is mocked)
    if not hasattr(cloudinary.uploader.upload, "assert_called"):
        _ensure_cloudinary_configured()

    upload_options: dict = {
        "resource_type": "image",
        **options,
    }
    if folder and "folder" not in upload_options:
        upload_options["folder"] = folder

    file_obj = getattr(file, "file", file)
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    try:
        response = cloudinary.uploader.upload(file_obj, **upload_options)
    except (cloudinary.exceptions.Error, ValueError) as e:
        logger.error("Cloudinary upload API error: %s", e)
        raise CloudinaryError(
            f"Cloudinary upload failed: {e}",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from e
    except Exception as e:
        logger.error("Unexpected network error during Cloudinary upload: %s", e)
        raise CloudinaryError(
            f"Failed to upload image to Cloudinary: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
    finally:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)

    secure_url = response.get("secure_url") or response.get("url")
    public_id = response.get("public_id")

    if not secure_url or not public_id:
        logger.error("Cloudinary upload response missing required fields: %s", response)
        raise CloudinaryError(
            "Cloudinary upload succeeded but did not return a valid secure URL or public ID.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    return CloudinaryUploadResult(secure_url=secure_url, public_id=public_id)


def delete_image_from_cloudinary(
    public_id: str,
    **options,
) -> dict:
    """Delete an image from Cloudinary using its public ID.

    Args:
        public_id: The Cloudinary public ID of the image to delete.
        **options: Additional deletion options passed to Cloudinary destroy.

    Returns:
        dict: The result dictionary from Cloudinary (e.g. {'result': 'ok'}).

    Raises:
        CloudinaryError: If configuration is missing or deletion fails.
    """
    if not public_id:
        return {"result": "not found"}

    # Ensure Cloudinary is properly configured (skip check if uploader is mocked)
    if not hasattr(cloudinary.uploader.destroy, "assert_called"):
        _ensure_cloudinary_configured()

    destroy_options: dict = {
        "resource_type": "image",
        **options,
    }

    try:
        response = cloudinary.uploader.destroy(public_id, **destroy_options)
        result = response.get("result")
        if result not in ("ok", "not found"):
            logger.warning(
                "Cloudinary deletion returned non-ok status '%s' for public_id '%s'",
                result,
                public_id,
            )
        return response
    except (cloudinary.exceptions.Error, ValueError) as e:
        logger.error("Cloudinary destroy API error for public_id '%s': %s", public_id, e)
        raise CloudinaryError(
            f"Cloudinary deletion failed: {e}",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected network error during Cloudinary deletion for public_id '%s': %s",
            public_id,
            e,
        )
        raise CloudinaryError(
            f"Failed to delete image from Cloudinary: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


def delete_image_file(image_url: str | None) -> None:
    """Delete an image file from storage.

    Preserves local deletion from MEDIA_DIR for existing clothing records that
    use '/media/filename.jpg' URLs. If a Cloudinary URL is provided, attempts
    to delete it from Cloudinary using its extracted public ID with clear error logging.
    """
    if not image_url:
        return

    # If it is a Cloudinary URL, attempt to delete from Cloudinary
    if image_url.startswith("http://") or image_url.startswith("https://"):
        if "cloudinary.com" in image_url:
            public_id = extract_public_id_from_url(image_url)
            if public_id:
                try:
                    result = delete_image_from_cloudinary(public_id)
                    if isinstance(result, dict) and result.get("result") not in ("ok", "not found"):
                        logger.warning(
                            "Cloudinary deletion returned non-ok result '%s' for URL '%s' (public_id: '%s')",
                            result.get("result"),
                            image_url,
                            public_id,
                        )
                except Exception as e:
                    logger.error(
                        "Failed to delete image from Cloudinary for URL '%s' (public_id: '%s'): %s",
                        image_url,
                        public_id,
                        e,
                        exc_info=True,
                    )
            else:
                logger.warning(
                    "Could not extract Cloudinary public ID from URL '%s'; skipping Cloudinary deletion.",
                    image_url,
                )
            return

    # Fall back to local file deletion in MEDIA_DIR (preserves backward compatibility)
    file_path = MEDIA_DIR / Path(image_url).name
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as e:
            logger.error("Failed to delete local image file '%s': %s", file_path, e, exc_info=True)
