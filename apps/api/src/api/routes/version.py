import subprocess

from fastapi import APIRouter

from api.settings import settings

router = APIRouter(tags=["meta"])


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


@router.get("/version")
async def version() -> dict[str, str | None]:
    return {
        "version": settings.app_version,
        "git_sha": _git_sha(),
    }
