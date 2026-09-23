import sys
import json
import logging
from pathlib import Path


# ---------------------------------------------------------
# Make backend/app importable when running from scripts/
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


from app.services.legal_update_service import update_legal_sources


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Legal sources registry
# ---------------------------------------------------------

SOURCES_FILE = BACKEND_DIR / "data" / "legal_sources.json"


def load_legal_sources() -> list[dict]:
    """
    Load enabled official legal sources from the registry.
    """

    if not SOURCES_FILE.exists():
        raise FileNotFoundError(
            f"Legal sources registry not found: {SOURCES_FILE}"
        )

    with SOURCES_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    sources = data.get("sources", [])

    enabled_sources = []

    for source in sources:

        if not source.get("enabled", True):
            continue

        enabled_sources.append(
            {
                "document_id": source["document_id"],
                "source_name": source["source_name"],
                "category": source["category"],
                "source_url": source["source_url"],
            }
        )

    return enabled_sources


# ---------------------------------------------------------
# Main updater runner
# ---------------------------------------------------------

def main():

    print(
        "\n=== NyayaSaathi Legal Knowledge Updater ===\n"
    )

    try:
        sources = load_legal_sources()

    except Exception as exc:
        print(
            f"Could not load legal sources: {exc}"
        )
        return

    if not sources:
        print(
            "No enabled legal sources found."
        )
        return

    print(
        f"Checking {len(sources)} "
        f"official legal source(s)...\n"
    )

    # update_legal_sources() returns:
    #
    # {
    #     "success": bool,
    #     "total": int,
    #     "results": [...]
    # }

    batch_result = update_legal_sources(
        sources
    )

    results = batch_result.get(
        "results",
        [],
    )

    added = 0
    updated = 0
    unchanged = 0
    failed = 0

    for result in results:

        status = result.get(
            "status",
            "failed",
        )

        source_name = result.get(
            "sourceName",
            result.get(
                "documentId",
                "Unknown source",
            ),
        )

        if status == "added":
            added += 1
            symbol = "+"

        elif status == "updated":
            updated += 1
            symbol = "~"

        elif status == "unchanged":
            unchanged += 1
            symbol = "="

        else:
            failed += 1
            symbol = "!"

        print(
            f"[{symbol}] "
            f"{source_name}: "
            f"{status}"
        )

        if not result.get(
            "success",
            False,
        ):
            error = result.get(
                "message",
                "Unknown error",
            )

            print(
                f"    Error: {error}"
            )

    print(
        "\n=== Update Summary ==="
    )

    print(
        f"Total:     {batch_result.get('total', len(results))}"
    )

    print(
        f"Added:     {added}"
    )

    print(
        f"Updated:   {updated}"
    )

    print(
        f"Unchanged: {unchanged}"
    )

    print(
        f"Failed:    {failed}"
    )

    print(
        "======================\n"
    )


if __name__ == "__main__":
    main()