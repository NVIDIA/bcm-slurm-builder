#!/cm/local/apps/python3/bin/python

# SPDX-FileCopyrightText: Copyright (c) 2004-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import argparse
import errno
import logging
import os
import sys
from urllib.parse import urlsplit

from pkg_resources import resource_isdir, resource_filename

import pythoncm
from pythoncm.cluster import Cluster
from pythoncm.settings import Settings
from pythoncm.entity import Node
from pythoncm.entity import PowerOperation
from pythoncm.entity_converter import EntityConverter
from pythoncm.entity.metadata.poweroperation import PowerOperation as Power
from pythoncm.namerange import bracket_expand
from pythoncm.rpc.rpc import RPC


PEM = '/cm/shared/licenses/cm/slurm/power/powerslurm.pem'
KEY = '/cm/shared/licenses/cm/slurm/power/powerslurm.key'
LOG_FILE = '/cm/local/apps/slurm/var/spool/powersave.log'
LOGGER = logging.getLogger(__name__)
CA = None

if resource_isdir("pythoncm", "etc"):
    CA = resource_filename("pythoncm", "etc/cacert.pem")

if CA is None or not os.path.exists(CA):
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), CA)


bracket_expand = bracket_expand.BracketExpand.expand

def get_settings() -> Settings | None:
    try:
        with open('/var/run/cmd.url') as f:
            url: str = f.read()
            parsed = urlsplit(url)
            # cmd always runs on non-standard ports, so parsed.port is never None
            port = parsed.port
            host = parsed.hostname
            settings = Settings(host=host,
                                port=int(port),
                                cert_file=PEM,
                                key_file=KEY,
                                ca_file=CA)
            return settings
    except FileNotFoundError as e:
        LOGGER.error(f"{e.filename} not found. Is cmd running?")
        return None

def get_opts() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Slurm power script')
    parser.add_argument('-n', '--node', required=True, help='Node name for the power operation')
    parser.add_argument('-p', '--power', required=True, choices={'on', 'off'}, help='Power operation')
    return parser.parse_args()


def set_logger() -> None:
    hdlr = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('(%(asctime)s) %(message)s')
    hdlr.setFormatter(formatter)
    LOGGER.addHandler(hdlr)
    LOGGER.setLevel(logging.INFO)


def get_cm_cluster() -> Cluster:
    settings = get_settings()
    if settings is None:
        exit_error('Could not get cmd settings')
    if not settings.check_certificate_files():
        exit_error('Certificate files not found')
    auto_connect = False  # power profile does not need autoconnection - it needs to load less data
    return Cluster(settings=settings, auto_connect=auto_connect)


def power_operation(node: Node, rpc: RPC, op: Power) -> bool:
    power_operation = PowerOperation()
    power_operation.devices = [node.uuid]
    power_operation.operation = op
    (code, out) = rpc.call(service='cmdevice',
                           call='powerOperation',
                           args=[power_operation.to_dict()])
    if code:
        raise IOError(out)
    return out.get('count', 0) != 0


def power_on(node: Node, rpc: RPC) -> bool:
    try:
        if not power_operation(node, rpc, Power.Operation.ON):
            LOGGER.error("Node operation (power on) failed for %s" % node.hostname)
            return False
    except IOError as e:
        LOGGER.error(f"Power ON failed on node {node.hostname}: {e!r}")
        return False
    LOGGER.info('Power ON command succeeded: %s' % node.hostname)
    set_msg(node, 'slurm power saving', 'on')
    return True


def power_off(node: Node, rpc: RPC) -> bool:
    try:
        if not power_operation(node, rpc, Power.Operation.OFF):
            LOGGER.error("Node operation (power off) failed for %s" % node.hostname)
            return False
    except IOError as e:
        LOGGER.error(f"Power OFF failed on node {node.hostname}: {e!r}")
        return False
    LOGGER.info('Power OFF command succeeded: %s' % node.hostname)
    set_msg(node, 'slurm power saving', 'off')
    return True


def set_msg(node: Node, new_msg: str, state: str) -> None:
    found = False
    msg_strip = node.status().toolMessage.strip()
    if msg_strip == '':
        user_msg = []
    else:
        user_msg = node.status().toolMessage.split(',')

    for i in range(len(user_msg)):
        if new_msg in user_msg[i]:
            found = True
            user_msg[i] = new_msg + ': ' + state
        else:
            user_msg[i] = user_msg[i].strip()
    if not found:
        user_msg.append(new_msg + ': ' + state)

    LOGGER.info('Setting user message for %s: %s' % (node.hostname, ', '.join(user_msg)))
    node.set_user_message(', '.join(user_msg))


def exit_error(msg: str) -> None:
    LOGGER.error(msg)
    sys.exit(1)


def is_allowed(rpc: RPC, hostname: str) -> bool:
    (code, allowed) = rpc.call(service='cmjob',
                               call='isPowerSavingAllowed',
                               args=['slurm', hostname])
    if code:
        exit_error("Could not run RPC cmjob::isPowerSavingAllowed(), code: %s - %s" % (code, allowed)) 
    return allowed


def get_node(rpc: RPC, hostname: str, cluster: Cluster) -> Node:
    (code, out) = rpc.call(service='cmdevice',
                           call='getNode',
                           args=[hostname])
    if code:
        exit_error(str(out))
    converter = EntityConverter(cluster, service=None)
    return converter.convert(out)


def main() -> bool:
    opts = get_opts()
    set_logger()
    
    cluster = get_cm_cluster()
    rpc = cluster.get_rpc()

    hostnames = bracket_expand(opts.node) 
    
    success = True
    for hostname in hostnames:
        if not is_allowed(rpc, hostname):
            LOGGER.error('Power operations are not allowed for %s' % hostname)
            continue

        node = get_node(rpc, hostname, cluster)
        if opts.power == 'on':
            success &= power_on(node, rpc)
        elif opts.power == 'off':
            success &= power_off(node, rpc)

    return success

if __name__ == '__main__':
    if not main():
        sys.exit(1)
