from .parser import ConfigParser


def initialize_conf() -> ConfigParser:
    config_parser = ConfigParser()
    config_parser.build_config()
    return config_parser
