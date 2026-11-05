from typing import Any, Dict, Optional, List
from urllib.parse import urljoin
import requests

from asset_docs_integration.asset_docs import AssetDocsPayload
from asset_docs_integration.log import logger
from dataclasses import dataclass
from dataclasses_json import dataclass_json


BR_X_API_TOKEN='X-API-KEY'
BR_PATH_GET_PIPELINE='api/pipelines/'
# 'api/datasets/by-pipeline/{pipeline_slug}/'
BR_PATH_GET_DATASETS_BY_PIPELINE_SLUG='api/datasets/by-pipeline/'
# 'api/configs/by-pipeline/{pipeline_slug}/'
BR_PATH_GET_DATASET_CONFIGS_BY_PIPELINE_SLUG='api/configs/by-pipeline/'

@dataclass_json
@dataclass
class BRPipeline:
    slug: Optional[str] = None
    name: Optional[str] = None

@dataclass_json
@dataclass
class BRDataset:
    slug: Optional[str] = None
    state: Optional[str] = None

@dataclass_json
@dataclass
class BRDatasetConfig:
    id: Optional[int] = None
    slug: Optional[str] = None
    state: Optional[str] = None
    config: Optional[Any] = None


def _get_pipelines( br_base_url: str , br_api_token: str) -> Any:

    _url = urljoin( br_base_url, BR_PATH_GET_PIPELINE )

    resp = requests.get(
        _url,
        headers={
            'Accept': 'application/json',
            BR_X_API_TOKEN: br_api_token,
        }
    )

    resp.raise_for_status()

    return resp.json()


def _get_dataset_configs_by_pipeline_slug( br_base_url: str , br_api_token: str, pipeline_slug: str ) -> Any:

    # api/configs/by-pipeline/{pipeline_slug}/
    _url = urljoin( br_base_url, BR_PATH_GET_DATASET_CONFIGS_BY_PIPELINE_SLUG )
    _url = urljoin( _url, f"{pipeline_slug}/" )

    resp = requests.get(
        _url,
        headers={
            'Accept': 'application/json',
            BR_X_API_TOKEN: br_api_token,
        }
    )

    resp.raise_for_status()

    return resp.json()


def _get_datasets_by_pipeline_slug( br_base_url: str , br_api_token: str, pipeline_slug: str ) -> Any:

    # api/datasets/by-pipeline/{pipeline_slug}/
    _url = urljoin( br_base_url, BR_PATH_GET_DATASETS_BY_PIPELINE_SLUG )
    _url = urljoin( _url, f"{pipeline_slug}/" )

    resp = requests.get(
        _url,
        headers={
            'Accept': 'application/json',
            BR_X_API_TOKEN: br_api_token,
        }
    )

    resp.raise_for_status()

    return resp.json()



def buoy_retriever_callback(
    br_base_url: str,
    br_api_token: str,
    br_pipeline_slug: str,
    br_dataset_slug: str,
    br_dataset_config_slug: str,
    channel: str,
    identifier: str,
    payload: Dict
):

    assert br_base_url is not None
    assert br_api_token is not None
    assert br_pipeline_slug is not None
    assert br_dataset_slug is not None
    assert br_dataset_config_slug is not None

    tg_op: Optional[str] = payload.get("TG_OP", None)
    logger.info(f"Handling {tg_op} event for channel {channel}, identifier: {identifier}")

    adp: Optional[AssetDocsPayload] = None

    try:
        adp = AssetDocsPayload.from_dict(payload)
    except BaseException:
        logger.error(
            f"Could not deserialize payload for {AssetDocsPayload.__name__}",
            exc_info=True
        )

    # logger.warning(repr(adp))

    list_pipelines = _get_pipelines( br_base_url, br_api_token )

    assert isinstance( list_pipelines, List )

    found_pipeline: Optional[BRPipeline] = None

    for p in list_pipelines:
        br_pipeline = BRPipeline.from_dict( p )

        if br_pipeline.slug == br_pipeline_slug:
            found_pipeline = br_pipeline
            break

    if found_pipeline is None:
        logger.warning(
            f"Could not find pipeline slug {br_pipeline_slug}"
        )
        return

    logger.info(
        f"Found {br_pipeline_slug}, {repr(found_pipeline)}"
    )

    found_dataset: Optional[BRPipeline] = None

    list_pipeline_datasets = _get_datasets_by_pipeline_slug(
        br_base_url,
        br_api_token,
        found_pipeline.slug,
    )

    for ds in list_pipeline_datasets:
        br_dataset = BRDataset.from_dict( ds )

        if br_dataset.slug == br_dataset_slug:
            found_dataset = br_dataset
            break

    if found_dataset is None:
        logger.warning(
            f"Could not find dataset slug {br_dataset_slug}, "
            f"existing for pipeline {br_pipeline_slug}: {repr(list_pipeline_datasets)}"
        )
        return

    logger.info(
        f"Found {br_dataset_slug}, {repr(found_dataset)}"
    )

    found_dataset_config: Optional[BRDatasetConfig] = None

    list_pipeline_dataset_configs = _get_dataset_configs_by_pipeline_slug(
        br_base_url,
        br_api_token,
        found_pipeline.slug,
    )

    for dsc in list_pipeline_dataset_configs:
        br_dataset_config = BRDatasetConfig.from_dict( dsc )

        if br_dataset_config.slug == br_dataset_config_slug:
            found_dataset_config = br_dataset_config
            break

    if found_dataset_config is None:
        logger.warning(
            f"Could not find dataset config slug {br_dataset_config_slug}, "
            f"for existing pipeline {br_pipeline_slug}: {repr(list_pipeline_dataset_configs)}"
        )
        return

    logger.info(
        f"Found {br_dataset_config_slug}, {repr(found_dataset_config)}"
   )


    # TODO: Create dataset / dataset config from current document

    return
