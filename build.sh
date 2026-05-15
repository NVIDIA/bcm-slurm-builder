#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

function distro_version {
    echo $VERSION_ID
}

function get_distro_family {
    # only parameter is the distro
    case $1 in
    rocky)
        DISTRO=rhel
        ;;
    *)
        # if not defined, we return the same distro
        DISTRO=$1
        ;;
    esac
    echo $DISTRO
}

if [ $# -lt 1 ]; then
    echo Need to provide a slurm version to build. Ex: 25.11.3.
    echo Additionally, you can optionally provide a tarball path "(in tar.bz2 format)" after the version.
    exit 1
fi

echo $1 | grep '^\([0-9]*.\)\{2\}[0-9]*$' &> /dev/null
if [ $? -ne 0 ]; then
    echo The provided slurm version does not match the expected pattern.
    echo It should be something like 25.11.3
    exit 1
fi

set -x

. /etc/os-release
FULL_VERSION=$1
SLURM_MAJOR="${FULL_VERSION%.*}"
if [ $# -lt 2 ]; then TARBALL=slurm-${FULL_VERSION}.tar.bz2; else TARBALL=$2; fi
PKG_BUILD_DIR=slurm-${FULL_VERSION}
DISTRO=$ID
DISTRO_VERSION=$( distro_version )
DISTRO_MAJOR=${DISTRO_VERSION%.*}
PRS_PATCH=${PKG_BUILD_DIR}/slurm-${SLURM_MAJOR}-prs.patch
DISTRO_FAMILY=$( get_distro_family $DISTRO )

if [ ! -e "${TARBALL}" ]; then
    echo Downloading package to build slurm $FULL_VERSION
    URL=https://download.schedmd.com/slurm/"${TARBALL}"
    wget "$URL"
    if [ ! -e "${TARBALL}" ]; then
        echo Could not download slurm tarball: $URL
        exit 1
    fi
fi

CM_VERSION=$( ./scripts/bc-branch-dependency-name )
BC_RELEASE_TAG=$( ./scripts/bc-release-tag $TARBALL $CM_VERSION )

packages=$( jq -r .${DISTRO_FAMILY}${DISTRO_MAJOR}.slurm$( echo $SLURM_MAJOR | sed 's/\.//' ).packages dependencies.json )
if [ ! -z "$packages" ] && [ "$packages" != "null" ]; then
    case $DISTRO_FAMILY in
    rhel)
        yum install -y $packages
        if [ $? -ne 0 ]; then
            echo There was a problem installing dependencies
            exit 1
        fi
        ;;
    sles)
        zypper -n install $packages
        if [ $? -ne 0 ]; then
            echo There was a problem installing dependencies
            exit 1
        fi
        ;;
    ubuntu)
        apt update && DEBIAN_FRONTEND=noninteractive apt-get install -y $packages
        if [ $? -ne 0 ]; then
            echo There was a problem installing dependencies
            exit 1
        fi
        ;;
    *)
        echo Unsupported distro to custom-build slurm.
        exit 1
    esac
fi

# loading modules
modules=$( jq -r .${DISTRO_FAMILY}${DISTRO_MAJOR}.slurm$( echo $SLURM_MAJOR | sed 's/\.//' ).modules dependencies.json )
if [ ! -z "$modules" -a "$modules" != "null" ]; then
    echo Loading modules
    module load $modules
fi

if [ -e $PKG_BUILD_DIR ]; then
    rm -fR $PKG_BUILD_DIR
fi

tar jxf $TARBALL

# distro-specific packaging files
case $DISTRO_FAMILY in
ubuntu)
    rm -fR $PKG_BUILD_DIR/debian

    cp -r deb/debian${SLURM_MAJOR} $PKG_BUILD_DIR/debian
    extra_control=debian/control.ubuntu${DISTRO_MAJOR}
    if [ -f $extra_control ]; then
        cp -f $extra_control $PKG_BUILD_DIR/debian/control
    fi
    ;;
rhel|sles)
    rm -fR $PKG_BUILD_DIR/rpm

    cp -rv rpm $PKG_BUILD_DIR/rpm
    ;;
esac

cp -r slurm_files/* ${PKG_BUILD_DIR}
if [ -f ${PKG_BUILD_DIR}/scontrol_${SLURM_MAJOR}.patch ]; then
    echo Copying scontrol patch
    cp -f ${PKG_BUILD_DIR}/scontrol_${SLURM_MAJOR}.patch ${PKG_BUILD_DIR}/scontrol.patch
fi
if [ -f ${PRS_PATCH} ]; then
    echo Copying PRS patch file
    mv ${PRS_PATCH} ${PKG_BUILD_DIR}/prs-select.patch
else
    echo No PRS patch provided for slurm ${SLURM_MAJOR}
fi
cp -r pyxis/* ${PKG_BUILD_DIR}


case $DISTRO_FAMILY in
ubuntu)
    PKG_VERSION=${FULL_VERSION}-$( ./scripts/bc-revision-number )-${BC_RELEASE_TAG}

    if [ "$DISTRO_MAJOR" == "24" ];then
        JWT_LIB=libjwt2
        JWT_LIB_DEV=libjwt-dev
    else
        JWT_LIB=libjwt0
        JWT_LIB_DEV=libjwt-dev
    fi

    if [ ! -e "$PKG_BUILD_DIR" ]; then
        echo Directory where slurm will be built is missing: $PKG_BUILD_DIR
        exit 1
    fi
    cd $PKG_BUILD_DIR

    sed -i -e s/PKG_VERSION/${PKG_VERSION}/g debian/changelog
    sed -i -e s/SLURM_MAJOR_VERSION/${SLURM_MAJOR}/g debian/{control,rules,slurm${SLURM_MAJOR}*}
    sed -i -e s/SLURM_FULL_VERSION/${FULL_VERSION}/g debian/control
    sed -i -e s/CM_CONFIG_CM_VERSION/${CM_VERSION}/g debian/control
    sed -i -e s/JWT_LIB_DEV/${JWT_LIB_DEV}/g debian/control
    sed -i -e s/JWT_LIB/${JWT_LIB}/g debian/control
    # adjust paths for ucx/pmix/hwloc
    sed -i 's/--with-hwloc=.*/--with-hwloc=\/cm\/shared\/apps\/hwloc2\/current \\/' debian/rules
    sed -i 's/--with-ucx=.*/--with-ucx=\/cm\/shared\/apps\/ucx\/current \\/' debian/rules
    sed -i 's/--with-pmix=.*/--with-pmix=\/cm\/shared\/apps\/cm-pmix3\/current:\/cm\/shared\/apps\/cm-pmix4\/current \\/' debian/rules

    # build is done by hand from the slurm directory
    debian/rules binary
    if [ $? -ne 0 ]; then
        echo Failed to build slurm.
        exit 1
    fi

    cd -
    ;;
rhel|sles)
    ARCH=$( uname -p )
    [ -d temp1 ] && rm -rf temp1
    mkdir temp1
    [ -d temp2 ] && rm -rf temp2
    mkdir temp2
    cp pyxis/* temp1
    cp slurm_files/cm-* temp1
    cp slurm_files/copyright.* temp1
    cp slurm_files/slurm-backup temp1
    cp -r slurm_files/power temp1
    diff -ruN temp2 temp1 > slurm-modules.patch || true
    rm -fR temp1 temp2

    if [ ! -e rpmbuild ]; then
        mkdir -p rpmbuild
    fi
    rm -fR rpmbuild/*
    ln -s $PWD/${PKG_BUILD_DIR} rpmbuild/SOURCES
    ln $TARBALL "rpmbuild/SOURCES/$TARBALL"
    cp rpm/slurm${SLURM_MAJOR}.spec rpmbuild/SOURCES/slurm.spec
    sed -i 's/test -f \/root\//test -f /' rpmbuild/SOURCES/slurm.spec
    sed -i "s/^Version:.*/Version: ${FULL_VERSION}/g" rpmbuild/SOURCES/slurm.spec
    sed -i "s/%(bc-release-tag)/${BC_RELEASE_TAG}/g" rpmbuild/SOURCES/slurm.spec
    # adjust paths for ucx/pmix/hwloc
    sed -i 's/--with-hwloc=.*/--with-hwloc=\/cm\/shared\/apps\/hwloc2\/current \\/' rpmbuild/SOURCES/slurm.spec
    sed -i 's/--with-ucx=.*/--with-ucx=\/cm\/shared\/apps\/ucx\/current \\/' rpmbuild/SOURCES/slurm.spec
    sed -i 's/--with-pmix=.*/--with-pmix=\/cm\/shared\/apps\/cm-pmix3\/current:\/cm\/shared\/apps\/cm-pmix4\/current \\/' rpmbuild/SOURCES/slurm.spec
    # adjust names of packages to what is available on a BCM cluster
    sed -i 's/BuildRequires: cm-pmix3.*/BuildRequires: cm-pmix3/' -i rpmbuild/SOURCES/slurm.spec
    sed -i 's/BuildRequires: cm-pmix4.*/BuildRequires: cm-pmix4/' -i rpmbuild/SOURCES/slurm.spec
    sed -i 's/BuildRequires: cm-ucx.*/BuildRequires: cm-ucx/' -i rpmbuild/SOURCES/slurm.spec

    mv slurm-modules.patch rpmbuild/SOURCES
    PATH="$PWD"/scripts:"$PATH" rpmbuild -bb --target ${ARCH} --define "_topdir $PWD/rpmbuild" rpmbuild/SOURCES/slurm.spec
    if [ $? -ne 0 ]; then
        echo Failed to build slurm.
        exit 1
    fi

    cp rpmbuild/RPMS/${ARCH}/*.rpm .
    ;;
*)
    echo Unsupported distro to custom-build slurm.
    exit 1
esac

set +x

echo Packages built:
if [ "$DISTRO" == "ubuntu" ]; then
    ls -1 *.deb
else
    ls -1 *.rpm
fi
