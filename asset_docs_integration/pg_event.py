

from typing import Callable, Dict, Optional, Any, Tuple

import psycopg2
import psycopg2.extensions
import select
import json

from asset_docs_integration.log import logger





def pg_event_listen_with_callback(
    pg_uri: str,
    pg_channel_name: str,
    event_callback: Optional[Callable[[str, Any], None]] = None
):
        """
        https://www.psycopg.org/docs/advanced.html#asynchronous-notifications
        https://gist.github.com/pkese/2790749
        """

        assert pg_uri
        assert pg_channel_name

        pg_con = psycopg2.connect( pg_uri )
        pg_con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        crs = pg_con.cursor()

        try:
            channel = pg_channel_name
            pg_con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            crs.execute(f'LISTEN {channel};')
            logger.info(f"Listening on channel: {channel}")

            while True:
                if select.select([pg_con],[],[],5) == ([],[],[]):  # noqa
                    pass
                else:
                    pg_con.poll()

                    dedup: Dict[Tuple[str,str],bool] = {}

                    while pg_con.notifies:
                        notify = pg_con.notifies.pop()
                        if not notify:
                            logger.info(f"NOTIFY payload not correct: {notify}.")
                        else:

                            dedup[ ( notify.channel, notify.payload ) ] = True

                    logger.warning( repr( dedup ) )
                    for ( ( notify_channel, notify_payload ), _ ) in dedup.items():

                        try:

                            payload = json.loads(notify_payload)

                            logger.info(
                                f"Received event on channel {notify_channel}"
                            )

                            if not event_callback:
                                continue

                            event_callback(
                                notify_channel,
                                payload
                            )

                        except BaseException as e:
                            logger.info(
                                f"Could not parse {notify_channel} / {notify_payload}: {e}"
                            )

                    dedup.clear()


        except KeyboardInterrupt:
            pass
        finally:
            if pg_con:
                logger.warning("Closing PG connection...")
                pg_con.close()
                logger.warning("Connection closed")
