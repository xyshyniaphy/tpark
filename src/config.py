"""
Configuration management for the Tokyo Parking Crawler.

This module handles loading, validating, and merging configuration from a YAML-based .env file.
It provides functions to create a sample .env file and to load the Gemini system prompt.

Example:
    >>> from src.config import load_yaml_env, validate_config
    >>> config = load_yaml_env(".env.sample")
    >>> errors = validate_config(config)
    >>> if not errors:
    ...     print("Configuration is valid.")
    Configuration is valid.
"""

import os
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

from src.utils import DEFAULT_CONFIG

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def load_yaml_env(env_file: str = ".env") -> Dict[str, Any]:
    """
    Load configuration from a YAML-formatted .env file.
    This function manually parses the file to find the APP_CONFIG YAML block.
    """
    if not os.path.exists(env_file):
        print(f"Warning: {env_file} not found. Using default configuration.")
        return DEFAULT_CONFIG

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the line where the APP_CONFIG YAML block starts
        start_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("APP_CONFIG:"):
                start_index = i + 1
                break

        if start_index == -1:
            print(f"Warning: APP_CONFIG not found in {env_file}. Using default configuration.")
            return DEFAULT_CONFIG

        # Extract the indented YAML lines
        yaml_lines = []
        for i in range(start_index, len(lines)):
            line = lines[i]
            if line.strip() == "" or line.startswith("    "):
                yaml_lines.append(line[4:])  # Remove 4-space indentation
            else:
                # Reached the end of the YAML block
                break
        
        yaml_content = "".join(yaml_lines)

        if not yaml_content.strip():
            print(f"Warning: APP_CONFIG is empty in {env_file}. Using default configuration.")
            return DEFAULT_CONFIG

        user_config = yaml.safe_load(yaml_content)
        
        # Also load regular environment variables from the .env file
        # This allows overriding gemini_api_key with a separate GEMINI_API_KEY env var
        load_dotenv(env_file)
        if os.getenv("GEMINI_API_KEY"):
            user_config["gemini_api_key"] = os.getenv("GEMINI_API_KEY")

        return merge_with_defaults(user_config)

    except (yaml.YAMLError, IndexError) as e:
        print(f"Error parsing YAML from {env_file}: {e}")
        return DEFAULT_CONFIG

def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate the configuration dictionary against required keys and types.

    Args:
        config: The configuration dictionary to validate.

    Returns:
        A list of error messages. An empty list indicates a valid configuration.
    """
    errors = []
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            errors.append(f"Missing required configuration key: {key}")
        elif not isinstance(config[key], type(value)):
            errors.append(
                f"Invalid type for key '{key}'. Expected {type(value).__name__}, got {type(config[key]).__name__}."
            )
    return errors

def merge_with_defaults(user_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge user-provided configuration with the default configuration.

    Args:
        user_config: The user's configuration dictionary.

    Returns:
        The merged configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config

def load_system_prompt(file: str) -> str:
    """
    Load the Gemini system prompt from a file.

    Args:
        file: The path to the system prompt file.

    Returns:
        The content of the system prompt file.
    """
    try:
        with open(file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: System prompt file not found at {file}. Using empty prompt.")
        return ""

def create_sample_env(file: str = ".env.sample") -> None:
    """
    Create a sample .env file with the default configuration in YAML format.

    Args:
        file: The path to the sample .env file to create.
    """
    content = "# YAML configuration for the Tokyo Parking Crawler\n"
    content += "APP_CONFIG: |\n"
    
    # Correctly indent the YAML block
    yaml_string = yaml.dump(DEFAULT_CONFIG, indent=4, default_flow_style=False)
    for line in yaml_string.splitlines():
        content += f"    {line}\n"

    try:
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Sample configuration file created at {file}")
    except IOError as e:
        print(f"Error creating sample configuration file: {e}")
