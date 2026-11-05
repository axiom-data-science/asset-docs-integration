from typing import Any, Dict, Optional
from urllib.parse import urljoin
import requests

from asset_docs_integration.asset_docs import AssetDocsPayload
from asset_docs_integration.log import logger


BR_PATH_GET_PIPELINE='/pipelines/'

def _get_pipelines( br_base_url: str ) -> Any:

    resp = requests.get(
        urljoin( br_base_url, BR_PATH_GET_PIPELINE ),
        headers={
            'Accept': 'application/json',
        }
    )

    resp.raise_for_status()

    return resp.json()



def buoy_retriever_callback(
    br_base_url: str,
    br_api_token: str,
    br_pipeline_slug: str,
    br_datset_slug: str,
    br_datset_config_slug: str,
    channel: str,
    identifier: str,
    payload: Dict
):

    assert br_base_url is not None
    assert br_api_token is not None
    assert br_pipeline_slug is not None
    assert br_datset_slug is not None
    assert br_datset_config_slug is not None

    logger.info(f"Handling event for channel {channel}, identifier: {identifier}")

    adp: Optional[AssetDocsPayload] = None

    try:
        adp = AssetDocsPayload.from_dict(payload)
    except BaseException:
        logger.error(
            f"Could not deserialize payload for {AssetDocsPayload.__name__}",
            exc_info=True
        )

    # logger.warning(repr(adp))

    list_pipelines = _get_pipelines( br_base_url )

    logger.warning( list_pipelines )


    # TODO: Transform and submit to BR.

    return
