#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console script for asset-docs-integration."""

import argparse
import sys


def main():
    """Console script for asset-docs-integration."""
    parser = argparse.ArgumentParser()
    parser.add_argument("_", nargs="*")
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    print("Replace this message by putting your code into asset_docs_integration.cli.main")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
