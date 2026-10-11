import os
import pickle

import yaml
from yaml.loader import SafeLoader


def load_yaml(yaml_path):
    """
    Loads a YAML file from the given path.

    Args:
        yaml_path (str): The path to the YAML file.

    Returns:
        dict: The loaded YAML data.

    Raises:
        InvalidYAMLPathException: If the YAML file does not exist.
    """
    if os.path.exists(yaml_path):
        with open(yaml_path) as f:
            yaml_data = yaml.load(f, Loader=SafeLoader)
    else:
        raise InvalidYAMLPathException(f"YAML file does not exist: {yaml_path}")
    return yaml_data


class InvalidYAMLPathException(Exception):
    pass


def load_pickle(path):
    with open(path, "rb") as handle:
        variable = pickle.load(handle)
    return variable
