
from typing import Dict
from asset_docs_integration.log import logger


def buoy_retriever_callback( channel: str, identifier: str, payload: Dict ):
    logger.info( f"Handling event for channel {channel}, identifier: {identifier}" )
