import json
import select
from typing import Any, Callable, Dict, Optional, Tuple

import psycopg2
import psycopg2.extensions

from asset_docs_integration.log import logger


def pg_event_listen_with_callback(
    pg_uri: str, pg_channel_name: str, event_callback: Optional[Callable[[str, str, Any], None]] = None
):
    """
    https://www.psycopg.org/docs/advanced.html#asynchronous-notifications
    https://gist.github.com/pkese/2790749
    """

    assert pg_uri
    assert pg_channel_name

    pg_con = psycopg2.connect(pg_uri)
    pg_con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    crs = pg_con.cursor()

    try:
        channel = pg_channel_name
        pg_con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        crs.execute(f"LISTEN {channel};")
        logger.info(f"Listening on channel: {channel}")

        while True:
            if select.select([pg_con], [], [], 5) == ([], [], []):  # noqa
                pass
            else:
                pg_con.poll()

                dedup: Dict[Tuple[str, str], Dict] = {}

                # drain all pending async notifications, deduplicating
                # potential back-to-back events on the same object.
                while pg_con.notifies:
                    notify = pg_con.notifies.pop()
                    if not notify:
                        logger.info(f"NOTIFY payload not correct: {notify}.")
                    else:
                        payload = json.loads(notify.payload)

                        # remove diagnostic fields (when unused)
                        # for tg in ( 'TG_OP', 'TG_NAME', ):
                        #     if tg in payload:
                        #         del payload[tg]

                        # TODO: this likely needs a revisit to support a
                        # more generic consideration for 'keys' for an
                        # incoming notification.

                        identifier = None

                        if "uuid" in payload and payload["uuid"]:
                            identifier = payload["uuid"]
                        else:
                            identifier = notify.payload

                        dedup[(notify.channel, identifier)] = payload

                # Callback for each of the deduplicated document events
                for (notify_channel, notify_identifier), notify_payload in dedup.items():
                    try:
                        logger.debug(f"Received event on channel {notify_channel}")

                        if not event_callback:
                            continue

                        event_callback(notify_channel, notify_identifier, notify_payload)

                    except BaseException as e:
                        logger.info(
                            (
                                f"Could not handle {notify_channel} event / "
                                f"{notify_payload}"
                            ),
                            exc_info=True
                        )

                dedup.clear()

    except KeyboardInterrupt:
        pass
    finally:
        if pg_con:
            logger.warning("Closing PG connection...")
            pg_con.close()
            logger.warning("Connection closed")
