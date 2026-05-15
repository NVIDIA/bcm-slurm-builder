#!/bin/bash
#
# SPDX-FileCopyrightText: Copyright (c) 2023-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Description: compiles and copies the pyxis plugin to a specified directory 
#

SPANK_PLUGIN=spank_pyxis.so
PROG_NAME=$0

DEFAULT_DST_DIR=/cm/local/apps/slurm/current/lib64/slurm
PYXIS_DIR=/cm/local/apps/slurm/var/pyxis
DEFAULT_TARBALL=pyxis-sources.tar.gz
DEFAULT_TARBALL_PATH=$PYXIS_DIR/$DEFAULT_TARBALL

usage() {
    echo "The script compiles and copies the pyxis plugin to a specified directory"
    echo "Usage:"
    echo "  module load slurm && $PROG_NAME [-d /path/to/slurm/libs/] [-f /file/to/tarball]"
    echo "Defaults:"
    echo "  * destination directory: $DEFAULT_DST_DIR"
    echo "  * tarball path: $DEFAULT_TARBALL_PATH"
}

while getopts d:f:h flag
do
    case "${flag}" in
        d) DST_DIR=${OPTARG};;
        f) TARBALL_FILE_PATH=${OPTARG};;
        h)
           usage
           exit 0
           ;;
        *)
           echo "Unknown option: -${OPTARG}" >&2
           usage
           exit 1
           ;;
    esac
done

DST_DIR="${DST_DIR:-$DEFAULT_DST_DIR}"
TARBALL_FILE_PATH="${TARBALL_FILE_PATH:-$DEFAULT_TARBALL_PATH}"
SRC_PARENT_DIR="$(mktemp -d -t pyxis-XXXXXX)"
SRC_DIR="${SRC_PARENT_DIR}/pyxis-sources"

echo "Using paths:"
echo "  Destination directory: $DST_DIR"
echo "  Pyxis directory: $PYXIS_DIR"
echo "  Sources directory: $SRC_DIR"
echo "  Tarball path: $TARBALL_FILE_PATH"

set -e

if [ ! -f "$TARBALL_FILE_PATH" ]; then
    echo "File $TARBALL_FILE_PATH not found: ensure pyxis-sources package is installed" >&2
    exit 1
fi

echo "Unpack $TARBALL_FILE_PATH into ${SRC_PARENT_DIR}"
tar zfx "$TARBALL_FILE_PATH" --directory="${SRC_PARENT_DIR}"

pushd "$SRC_DIR"

echo "Compilation:"
CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null)
export CPATH="${SRC_DIR}:${CPATH}"
make -j "$CORES"

echo "Copy $SPANK_PLUGIN to ${DST_DIR}"
install -m 644 "$SPANK_PLUGIN" "${DST_DIR}"

popd  # SRC_DIR

echo "Remove temporary directory: $SRC_PARENT_DIR"
rm -fr "$SRC_PARENT_DIR"

exit 0
