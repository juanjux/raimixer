from typing import Dict, Any

class ConfigException(Exception):
    pass


def search_config_path() -> str:
    # Windows: C:\Users\<user\AppData\Local\RaiBlocks\
    # OSX: /Users/<user>/Library/RaiBlocks/
    # Linux: /home/<user>/RaiBlocks/
    import os
    from sys import platform
    from getpass import getuser

    user = getuser()

    possible_path: str = ''

    if platform == 'darwin':
        possible_path = f'/Users/{user}/Library/RaiBlocks'
    elif os.name == 'posix':
        possible_path = f'/home/{user}/RaiBlocks'
    elif platform.startswith('win'):
        possible_path = os.path.join(os.getenv('APPDATA'), 'Local', 'RaiBlocks')
    else:
        raise ConfigException('Unsupported OS')

    real_path = os.path.join(possible_path, 'config.json')
    if not os.path.exists(real_path) or not os.path.isfile(real_path):
        raise ConfigException(f'Could not find RaiBlocks config (tried: {real_path})')

    return real_path


def get_raiblocks_config() -> Dict[str, str]:
    import json

    rai_config: Dict[str, Any] = {}
    config: Dict[str, Any] = {}

    with open(search_config_path()) as raiconf_file:
        rai_config = json.loads(raiconf_file.read())

    config['wallet'] = rai_config['wallet']
    config['default_account'] = rai_config['account']
    config['rpc_enabled'] = rai_config['rpc_enable']
    config['control_enabled'] = rai_config['rpc']['enable_control']
    config['rpc_address'] = rai_config['rpc']['address']
    config['rpc_port'] = rai_config['rpc']['port']
    config['reps'] = rai_config['node']['preconfigured_representatives']

    return config


if __name__ == '__main__':
    from pprint import pprint
    pprint(get_raiblocks_config())
