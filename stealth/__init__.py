"""
Stealth Global
"""
import os
from configobj import ConfigObj
from validate import Validator
import importlib

context = None


class Config(object):

    '''Builds deuce conf on passing in a dict.'''

    def __init__(self, config):
        for k, v in config.items():
            if isinstance(v, dict):
                setattr(self, k, Config(v))
            else:
                setattr(self, k, v)


# NOTE(TheSriram): The user can add in their rule of where they
# want the .inis' placed, and their priorities.

config_files_root = {
    'config': '/etc/stealth/config.ini',
    'configspec': '/etc/stealth/configspec.ini',
    'status': False,
    'priority': 2
}
config_files_user = {
    'config': '{0:}/.stealth/config.ini'.format(os.environ.get('HOME')),
    'configspec': '{0:}/.stealth/configspec.ini'.format(
        os.environ.get('HOME')),
    'status': False,
    'priority': 1
}

config_files_deuce = {
    'config': os.path.abspath('ini/config.ini'),
    'configspec': os.path.abspath('ini/configspec.ini'),
    'status': True,
    'priority': 3
}

conf_list = [config_files_root, config_files_user, config_files_deuce]


def get_correct_conf(conf_list):
    for config_params in conf_list:
        conf_params = Config(config_params)
        for k, v in config_params.items():
            if k not in ["status", "priority"]:  # pragma: no cover
                if not os.path.exists(os.path.abspath(
                    getattr(conf_params, k))) or \
                        (k + '.ini' not in getattr(conf_params, k)):
                    pass
                else:
                    config_params['status'] = True
    final_conf_list = [conf for conf in conf_list if conf['status'] is True]
    sorted_conf_list = sorted(final_conf_list, key=lambda k: k['priority'])

    del sorted_conf_list[0]['status']
    del sorted_conf_list[0]['priority']
    return sorted_conf_list[0]

config_files = get_correct_conf(conf_list)

conf_ini = Config(config_files)

for k, v in config_files.items():
    if not os.path.exists(os.path.abspath(getattr(conf_ini, k))) or \
            (k + '.ini' not in getattr(conf_ini, k)):  # pragma: no cover
        raise OSError("Please set absolute path to "
                      "correct {0} ini file".format(k))

configspec = ConfigObj(
    os.path.abspath(conf_ini.configspec),
    interpolation=False,
    list_values=False,
    _inspec=True)

config = ConfigObj(
    os.path.abspath(conf_ini.config),
    configspec=configspec,
    interpolation=False)
if not config.validate(Validator()):  # pragma: no cover
    raise ValueError('Validation of config failed wrt to configspec')

conf_dict = config.dict()
conf = Config(conf_dict)
