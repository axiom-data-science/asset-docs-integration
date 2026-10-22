#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Listener for LISTEN/NOTIFY events, shuttling to IOOS Buoy Retriever."""

import argparse
import os
import pathlib
import sys
from typing import Optional
from urllib.parse import ParseResult, urlparse

from asset_docs_integration.buoy_retriever import buoy_retriever_callback
from asset_docs_integration.log import logger, setup_logging
from asset_docs_integration.pg_event import pg_event_listen_with_callback

DEFAULT_PGSQL_CHANNEL_NAME = "asset_doc_insert_or_update"

ENV_NAME_API_TOKEN = "API_TOKEN"
ENV_NAME_PG_URI = "PG_URI"


def main():
    """Console script for submission to DataCite to update URL redirect for a DOI."""

    setup_logging()

    parser = argparse.ArgumentParser(
        description="Listen on a Postgres events channel and push to IOOS Buoy Retriever"
    )

    parser.add_argument(
        "--api-token-path",
        "--api-token",
        type=pathlib.Path,
        required=False,
        help=(
            "Path to a file containing your Buoy Retrieve API token (reads from"
            "environment variable API_TOKEN if not set)"
        ),
    )

    parser.add_argument(
        "--buoy-retriever-base-url",
        "--buoy-retriever-url",
        type=str,
        help="The base URL against which to make IOOS Buoy Retriever REST API calls",
    )

    parser.add_argument(
        "--pgsql-channel-name",
        type=str,
        help=f"The Postgres event channel to listen on (default: {DEFAULT_PGSQL_CHANNEL_NAME})",
        default=DEFAULT_PGSQL_CHANNEL_NAME,
    )

    args = parser.parse_args()

    return listen_and_handle_asset_doc_events(args)


def listen_and_handle_asset_doc_events(args: argparse.Namespace) -> int:
    """main cli implementation for listen_and_handle_asset_doc_events"""

    assert args.pgsql_channel_name and isinstance(args.pgsql_channel_name, str)
    assert args.buoy_retriever_base_url and isinstance(args.buoy_retriever_base_url, str)

    api_token: Optional[str] = None

    api_token_found_path = False
    api_token_found_env = False

    if args.api_token_path is not None:
        assert args.api_token_path and isinstance(args.api_token_path, pathlib.Path)

        the_api_token_path: pathlib.Path = args.api_token_path

        assert the_api_token_path.is_file()
        assert the_api_token_path.stat().st_size > 0

        api_token = the_api_token_path.read_text()
        api_token_found_path = True

    else:
        env_api_token = os.environ.get(ENV_NAME_API_TOKEN, None)

        if env_api_token is not None and env_api_token:
            api_token = env_api_token
            api_token_found_env = True

    if api_token is None:
        logger.warning(
            "Unable to determine API token via command line arg (--api-token-path) "
            "or environment variable (export API_TOKEN=...)"
        )
        return 1

    if api_token_found_env is True:
        logger.info(f"{ENV_NAME_API_TOKEN}: (from environment)")
    if api_token_found_path is True:
        logger.info(f"{ENV_NAME_API_TOKEN}: (from path: {str(the_api_token_path)})")

    pg_uri: Optional[str] = None

    env_pg_uri = os.environ.get(ENV_NAME_PG_URI, "")

    parsed_pg_uri: Optional[ParseResult] = None

    if env_pg_uri:
        try:
            parsed_pg_uri = urlparse(env_pg_uri)
            pg_uri = env_pg_uri

        except BaseException:
            pass

    if not pg_uri or not parsed_pg_uri:
        logger.error(
            f"Invalid value for Postgres URI in environment variable {ENV_NAME_PG_URI}: '{env_pg_uri}'"
        )
        return 1

    logger.info(
        (
            # Don't print password...
            f"Using {ENV_NAME_PG_URI} to connect to "
            f"{parsed_pg_uri.username}:***@"
            f"{parsed_pg_uri.hostname}:{parsed_pg_uri.port}{parsed_pg_uri.path}"
        )
    )

    # Forever listen + callback loop
    pg_event_listen_with_callback(
        pg_uri,
        args.pgsql_channel_name,
        buoy_retriever_callback,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
