from typing import Any, Dict, Optional, List
from copy import deepcopy
from urllib.parse import urljoin
import psycopg2
from psycopg2.sql import Identifier, SQL
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
# 'api/configs/{id}/'
BR_PATH_POST_DATASET_CONFIGS='api/configs/'

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
    user_can_view: Optional[bool] = None
    user_can_publish: Optional[bool] = None

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

def _post_dataset_configs(
    br_base_url: str ,
    br_api_token: str,
    dataset_config_id: str,
    config_payload: Dict
) -> Any:

    assert dataset_config_id
    assert config_payload and isinstance( config_payload, Dict )

    # api/configs/{id}
    _url = urljoin( br_base_url, BR_PATH_POST_DATASET_CONFIGS )
    _url = urljoin( _url, f"{dataset_config_id}/" )

    resp = requests.post(
        _url,
        headers={
            'Accept': 'application/json',
            BR_X_API_TOKEN: br_api_token,
        },
        json={
            'config': config_payload,
        }
    )

    resp.raise_for_status()

    return resp.json()

@dataclass
class BRCallbackConfig(object):
    ad_document_slug: str
    ad_schema: str
    ad_ncojson_view: str
    br_base_url: str
    br_api_token: str
    br_pipeline_slug: str
    br_dataset_slug: str
    br_dataset_config_slug: str
    br_dataset_config_id: Optional[str]


def buoy_retriever_callback(
    cfg: BRCallbackConfig,
    pg_con: psycopg2.extensions.connection,
    channel: str,
    identifier: str,
    payload: Dict
):

    assert cfg.ad_document_slug is not None
    assert cfg.br_base_url is not None
    assert cfg.br_api_token is not None
    assert cfg.br_pipeline_slug is not None
    assert cfg.br_dataset_slug is not None
    assert cfg.br_dataset_config_slug is not None

    assert isinstance( pg_con, psycopg2.extensions.connection )

    tg_op: Optional[str] = payload.get("TG_OP", None)

    logger.info(f"Handling {tg_op} event for channel {channel}, identifier: {identifier}")

    adp: Optional[AssetDocsPayload] = None

    try:
        adp = AssetDocsPayload.from_dict(payload)
        assert isinstance( adp, AssetDocsPayload )
    except BaseException:
        logger.error(
            f"Could not deserialize payload for {AssetDocsPayload.__name__}",
            exc_info=True
        )
        return

    # logger.warning(repr(adp))
    adp_slug = getattr( adp, 'slug', None )

    if not adp_slug:
        logger.warning( "Unable to determine slug from payload, skipping" )
        return

    if adp_slug != cfg.ad_document_slug:
        logger.warning( f"Skipping slug ({adp_slug})" )
        return

    logger.info(
        f"{identifier} has slug {cfg.ad_document_slug}, proceed with handling."
    )

    list_pipelines = _get_pipelines( cfg.br_base_url, cfg.br_api_token )

    assert isinstance( list_pipelines, List )

    found_pipeline: Optional[BRPipeline] = None

    for p in list_pipelines:
        br_pipeline = BRPipeline.from_dict( p )

        if br_pipeline.slug == cfg.br_pipeline_slug:
            found_pipeline = br_pipeline
            break

    if found_pipeline is None:
        logger.warning(
            f"Could not find pipeline slug {cfg.br_pipeline_slug}"
        )
        return

    logger.info(
        f"Found {cfg.br_pipeline_slug}, {repr(found_pipeline)}"
    )

    found_dataset: Optional[BRPipeline] = None

    list_pipeline_datasets = _get_datasets_by_pipeline_slug(
        cfg.br_base_url,
        cfg.br_api_token,
        found_pipeline.slug,
    )

    for ds in list_pipeline_datasets:
        br_dataset = BRDataset.from_dict( ds )

        if br_dataset.slug == cfg.br_dataset_slug:
            found_dataset = br_dataset
            break

    if found_dataset is None:
        logger.warning(
            f"Could not find dataset slug {cfg.br_dataset_slug}, "
            f"existing for pipeline {cfg.br_pipeline_slug}: {repr(list_pipeline_datasets)}"
        )
        return

    logger.debug(
        f"Found {cfg.br_dataset_slug}, {repr(found_dataset)}"
    )

    found_dataset_config: Optional[BRDatasetConfig] = None

    list_pipeline_dataset_configs = _get_dataset_configs_by_pipeline_slug(
        cfg.br_base_url,
        cfg.br_api_token,
        found_pipeline.slug,
    )

    for dsc in list_pipeline_dataset_configs:
        br_dataset_config = BRDatasetConfig.from_dict( dsc )

        if (
            br_dataset_config.slug == cfg.br_dataset_config_slug or
            # the API returns something like my_slug_testing when a config is
            # marked with the 'testing' status. So we check for both equality
            # as well as startwith conditions
            str( br_dataset_config.slug ).startswith( cfg.br_dataset_config_slug )
        ):
            found_dataset_config = br_dataset_config
            break

    if found_dataset_config is None:
        logger.warning(
            f"Could not find dataset config slug {cfg.br_dataset_config_slug}, "
            f"for existing pipeline {cfg.br_pipeline_slug}: {repr(list_pipeline_dataset_configs)}"
        )
        return

    logger.debug(
        f"Found {cfg.br_dataset_config_slug}, {repr(found_dataset_config)}"
    )

    passed_config_id = cfg.br_dataset_config_id

    found_dataset_config_id: str = str( found_dataset_config.id or '' )

    if not passed_config_id and not found_dataset_config_id:
        logger.error( "Unable to determine config ID" )
        return

    if (
        passed_config_id and
        found_dataset_config_id and
        passed_config_id != found_dataset_config_id
    ):
        logger.error(
            (
                "Mismatch between passed dataset config ID and found dataset "
                f"config ID: {passed_config_id} != {found_dataset_config.id}"
            )
        )
        return

    target_config_id: Optional[str] = ( passed_config_id or found_dataset_config_id )

    assert target_config_id, \
        "Unable to determine usable dataset config target ID."

    crs = pg_con.cursor()

    # TODO: parameterize?
    _uuid = 'uuid'

    crs.execute(
        SQL(
            """
            SELECT
                v.{idcol},
                v.slug,
                v.dataset_id,
                v.nco_json
            FROM {schema}.{view} v
            WHERE v.{idcol} = %s
            """
        ).format(
            schema=Identifier( cfg.ad_schema ),
            view=Identifier( cfg.ad_ncojson_view ),
            idcol=Identifier( _uuid ),
        ),
        ( adp.uuid, )
    )

    (res_uuid, res_slug, res_dataset_id, res_nco_json ) = crs.fetchone()

    assert res_uuid == adp.uuid, \
        f"Unexpected ncoJSON query result"

    logger.info(
        f"Retrieved ncoJSON for doc {res_slug}, dataset_id: {res_dataset_id}"
    )

    # TODO: Parameterize
    _top_level_cfg_nco_json_property_name = 'ncojson'

    # Do our best to merge the existing dataset config's config field with our
    # NCO-JSON by inserting the NCO-JSON at a known top-level property name
    merged_config = deepcopy( found_dataset_config.config )

    if merged_config is None:
        merged_config = {}

    assert (
        isinstance( merged_config, dict )
    ), (
        "Expected dataset_config.config field to be a dict (JSON object), "
        f"got: {repr(merged_config)}"
    )

    if _top_level_cfg_nco_json_property_name not in merged_config:
        merged_config[_top_level_cfg_nco_json_property_name] = {}

    assert isinstance(
        merged_config[_top_level_cfg_nco_json_property_name],
        dict
    )

    # Set the nco-json fields in the merged valuec (variables, attributes)
    for ( k, v ) in res_nco_json.items():
        merged_config[_top_level_cfg_nco_json_property_name][k] = v

    post_config_resp = _post_dataset_configs(
        cfg.br_base_url,
        cfg.br_api_token,
        target_config_id,
        merged_config
    )

    assert str( post_config_resp['id'] ) == str( target_config_id ), \
        f"Unexpected config update response: {repr(post_config_resp)}"

    logger.info(
        (
            f"Updated dataset config {target_config_id} with document payload "
            f"from document ({identifier} / {adp_slug}), affecting "
            f"pipeline: {found_pipeline.slug} / {found_dataset.slug} / "
            f"{found_dataset_config.slug}"
        )
    )

    return
