#!/usr/bin/env python3

# Copyright Dansk Bibliotekscenter a/s. Licensed under GPLv3
# See license text in LICENSE.txt or at https://opensource.dbc.dk/licenses/gpl-3.0/

from setuptools import setup, find_packages

setup(name="deploymentutils",
    version="0.1.0",
    packages=find_packages(),
    description="",
    provides=["deploymentutils"],
    entry_points=
        {"console_scripts": [
            "templater = deploymentutils.templater:main"
        ]}
    )
