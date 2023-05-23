""" This program will read an ini file and add the key value pairs in the file to your windows environment variables """
import configparser
import winreg
import sys
import os
import argparse

from rich.logging import RichHandler
from loguru import logger


def load_ini_file(file_path: str) -> dict[str, str]:
    """ Loads an ini file and parses the key value pairs inside the file """
    env_vars = {}
    config = configparser.ConfigParser()

    absolute_path = os.path.abspath(file_path)
    config.read(absolute_path)
    for section in config.sections():
        section = config[section]
        for var_name in section:
            env_vars[var_name] = section[var_name]
    
    default_section = config['DEFAULT']
    for var_name in default_section:
        env_vars[var_name] = default_section[var_name]

    return env_vars


def set_env_vars_from_ini_file(env_vars: dict[str, str]) -> None:
    """ Sets environment variables based on the given dictionary """
    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    environment = winreg.OpenKey(registry, r'Environment',
                                 0, winreg.KEY_ALL_ACCESS)
    for key, value in env_vars.items():
        if key.startswith('-'):
            try:
                winreg.DeleteValue(environment, key[1:])
            except FileNotFoundError as exc:
                logger.error(f'Could not delete environment variable: {key[1:]} it was not found.')
        else:
            winreg.SetValueEx(environment, key, 0, winreg.REG_EXPAND_SZ, value)

    winreg.CloseKey(environment)
    winreg.CloseKey(registry)


def check_is_windows() -> bool:
    """ Returns true if the script is being run on windows """
    return sys.platform.startswith('win32')


def setup_logger() -> None:
    logger.add('logs/log_{time}.log', rotation='1 MB')
    logger.configure(handlers=[{'sink': RichHandler()}])


def main(file_path: str) -> None:
    setup_logger()
    if not check_is_windows():
        raise OSError('This script can only run on Windows. ')
    env_vars = load_ini_file(file_path)
    set_env_vars_from_ini_file(env_vars)
    logger.info(env_vars)
    logger.info('The logged environment variables have been added or removed on your system.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create environment variables from ini file.')
    parser.add_argument('--file_path', type=str, help='The path to the ini file, including the file itself.')
    args = parser.parse_args()
    main(args.file_path)
