"""
Main entry point for the Tokyo Parking Crawler CLI.

This script initializes the application, parses command-line arguments,
loads configuration, and executes the main workflow to find and rank
monthly parking lots in Tokyo.

Usage:
    python tokyo_parking_crawler.py "<location>"
    python tokyo_parking_crawler.py "<latitude>,<longitude>"

Example:
    python tokyo_parking_crawler.py "Shibuya Station"
"""

import argparse
import sys

from src.config import load_yaml_env, create_sample_env
from src.utils import setup_logging, show_banner, show_usage_instructions, VERSION
from src.workflow import execute_workflow

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main function to run the CLI application."""
    parser = argparse.ArgumentParser(
        description="Find monthly parking lots in Tokyo suitable for camping cars.",
        add_help=False, # Custom help handling
    )
    parser.add_argument(
        "location",
        nargs="?",
        help="The location to search for (e.g., \"Shibuya Station\") or coordinates (e.g., \"35.6,139.7\")."
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit."
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Show program's version number and exit."
    )
    parser.add_argument(
        "--init", action="store_true", help="Create a sample .env.sample file and exit."
    )

    args = parser.parse_args()

    if args.version:
        print(f"Tokyo Parking Crawler Version: {VERSION}")
        sys.exit(0)

    if args.init:
        create_sample_env()
        sys.exit(0)
        
    if args.help or not args.location:
        show_banner()
        parser.print_help()
        show_usage_instructions()
        sys.exit(0)

    # Load configuration
    config = load_yaml_env()

    # Setup logging
    logger = setup_logging(config["log_level"], config["log_file"])

    # Show banner
    show_banner()

    try:
        logger.info(f"Starting workflow for location: {args.location}")
        result = execute_workflow(args.location, config)

        if result.get("error"):
            logger.error(f"Workflow failed with error: {result['error']}")
            print(f"\nError: {result['error']}")
        else:
            logger.info("Workflow completed successfully.")
            print("\nWorkflow finished. Results are in the output file.")
            # The final markdown is printed by the output node

    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred. See {config['log_file']} for details.")

if __name__ == "__main__":
    main()
