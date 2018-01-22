# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Copyright 2017-2018 Juanjo Alvarez

from typing import Dict, Any
from sys import platform
import os
import json

from raimixer.version import __version__

CONFIG_FILENAME = 'raimixer_conf.json'


class ConfigException(Exception):
    pass


def user_config_dir() -> str:
    from getpass import getuser

    user = getuser()
    if platform == 'darwin':
        return f'/Users/{user}/Library'
    elif os.name == 'posix':
        return f'/home/{user}'
    elif platform.startswith('win'):
        return os.path.join(os.getenv('APPDATA'), 'Local')
    else:
        raise ConfigException('Unsupported OS')


def user_raiblocks_config() -> str:
    # Windows: C:\Users\<user\AppData\Local\RaiBlocks\
    # OSX: /Users/<user>/Library/RaiBlocks/
    # Linux: /home/<user>/RaiBlocks/

    raiblocks_config_dir = os.path.join(user_config_dir(), 'RaiBlocks')

    real_path = os.path.join(raiblocks_config_dir, 'config.json')
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        raise ConfigException(f'Could not find RaiBlocks config (tried: {real_path})')

    return real_path


def maybe_create_confdir() -> str:
    conf_base = 'raimixer' if platform.startswith('win') else '.raimixer'
    raimixer_config_dir = os.path.join(user_config_dir(), conf_base)

    if not os.path.exists(raimixer_config_dir):
        os.mkdir(raimixer_config_dir)

    return raimixer_config_dir


def write_raimixer_config(confdict: Dict[str, object]) -> None:
    raimixer_conf = os.path.join(maybe_create_confdir(), CONFIG_FILENAME)
    with open(raimixer_conf, 'w') as raimix_file:
        confdict['version'] = __version__
        raimix_file.write(json.dumps(confdict, indent=4))


def _get_default_config() -> Dict[str, object]:
    rai_config = get_raiblocks_config()
    config = {
        'rpc_address': rai_config['rpc_address'],
        'rpc_port': rai_config['rpc_port'],
        'num_mixer_accounts': '4',
        'dest_from_multiple': False,
        'leave_remainder': False,
        'num_mixing_rounds': '2',
        'unit': 'mrai',
        'version': str(__version__)
    }
    return config


def _upgrade_config(conf: Dict[str, object]):
    default_conf = _get_default_config()
    changed = False

    for def_key in default_conf:
        if def_key not in conf:
            print(f'Upgrading config file with new setting "{def_key}"...')
            conf[def_key] = default_conf[def_key]
            changed = True

    if changed:
        write_raimixer_config(conf)


def read_raimixer_config() -> Dict[str, object]:
    config: Dict[str, object] = {}
    raimixer_conf = os.path.join(maybe_create_confdir(), CONFIG_FILENAME)

    def write_default_config() -> Dict[str, object]:
        default_conf = _get_default_config()
        write_raimixer_config(default_conf)
        return default_conf

    if not os.path.exists(raimixer_conf):
        config = write_default_config()
    else:
        with open(raimixer_conf) as raimix_file:
            fcontent = raimix_file.read()
            if len(fcontent.strip()) == 0:
                config = write_default_config()
            else:
                config = json.loads(fcontent)
                _upgrade_config(config)

    return config


def get_raiblocks_config() -> Dict[str, object]:
    rai_config: Dict[str, Any] = {}
    config: Dict[str, Any] = {}

    with open(user_raiblocks_config()) as raiconf_file:
        rai_config = json.loads(raiconf_file.read())

    config['wallet'] = rai_config['wallet']
    config['default_account'] = rai_config['account']
    config['rpc_enabled'] = rai_config['rpc_enable']
    config['control_enabled'] = rai_config['rpc']['enable_control']
    config['rpc_address'] = rai_config['rpc']['address']
    config['rpc_port'] = rai_config['rpc']['port']
    config['representatives'] = rai_config['node']['preconfigured_representatives']

    return config


if __name__ == '__main__':
    from pprint import pprint
    pprint(get_raiblocks_config())
