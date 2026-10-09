
from typing import Dict, Optional
from asset_docs_integration.asset_docs import AssetDocsPayload
from asset_docs_integration.log import logger


def buoy_retriever_callback( channel: str, identifier: str, payload: Dict ):
    logger.info( f"Handling event for channel {channel}, identifier: {identifier}" )

    adp: Optional[AssetDocsPayload] = None

    try:
        adp = AssetDocsPayload.from_dict( payload )
    except BaseException:
        logger.error(
            f"Could not deserialize payload for {AssetDocsPayload.__name__}",
            exc_info=True
        )

    logger.warning( repr( adp ))

    # TODO: Transform and submit to BR.

    return