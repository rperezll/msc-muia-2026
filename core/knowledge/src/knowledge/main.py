import uvicorn

from knowledge.app import create_app
from shared_lib.config import config


def main() -> None:
    cfg = config.knowledge
    uvicorn.run(
        create_app(),
        host=cfg.host,
        port=cfg.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
