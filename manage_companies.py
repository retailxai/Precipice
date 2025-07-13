import argparse
import logging
import sys
from typing import Dict, List

import yaml

from entities import Company
from database_manager import DatabaseManager

logger = logging.getLogger("RetailXAI.ManageCompanies")


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to YAML file.

    Returns:
        Configuration dictionary.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)


def load_companies(companies_file: str) -> List[Company]:
    """Load companies from YAML file.

    Args:
        companies_file: Path to companies YAML file.

    Returns:
        List of Company entities.
    """
    try:
        with open(companies_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return [
                Company(
                    name=c["name"],
                    youtube_channels=c["youtube_channels"],
                    rss_feed=c["rss_feed"],
                    keywords=c["keywords"],
                )
                for c in data["companies"]
            ]
    except Exception as e:
        logger.error(f"Failed to load companies: {e}")
        return []


def save_companies(companies: List[Company], companies_file: str) -> None:
    """Save companies to YAML file.

    Args:
        companies: List of Company entities.
        companies_file: Path to companies YAML file.
    """
    data = {"companies": [vars(c) for c in companies]}
    try:
        with open(companies_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True)
        logger.info(f"Saved companies to {companies_file}")
    except Exception as e:
        logger.error(f"Failed to save companies: {e}")


def list_companies(companies_file: str, verbose: bool = False) -> None:
    """List all companies.

    Args:
        companies_file: Path to companies YAML file.
        verbose: If True, print detailed information.
    """
    companies = load_companies(companies_file)
    if not companies:
        print("No companies found.")
        return
    for company in companies:
        if verbose:
            print(f"Name: {company.name}")
            print(f"YouTube Channels: {', '.join(company.youtube_channels)}")
            print(f"RSS Feed: {company.rss_feed or 'None'}")
            print(f"Keywords: {', '.join(company.keywords)}")
            print("-" * 40)
        else:
            print(company.name)


def add_company(companies_file: str, db_manager: DatabaseManager, name: str, youtube_channels: List[str], rss_feed: str, keywords: List[str]) -> None:
    """Add a new company.

    Args:
        companies_file: Path to companies YAML file.
        db_manager: DatabaseManager instance.
        name: Company name.
        youtube_channels: List of YouTube channel IDs.
        rss_feed: RSS feed URL.
        keywords: List of keywords.
    """
    companies = load_companies(companies_file)
    if any(c.name.lower() == name.lower() for c in companies):
        logger.error(f"Company {name} already exists")
        return
    company = Company(name=name, youtube_channels=youtube_channels, rss_feed=rss_feed, keywords=keywords)
    companies.append(company)
    save_companies(companies, companies_file)
    db_manager.insert_company(company)
    logger.info(f"Added company: {name}")


def update_company(companies_file: str, db_manager: DatabaseManager, name: str, youtube_channels: List[str], rss_feed: str, keywords: List[str]) -> None:
    """Update an existing company.

    Args:
        companies_file: Path to companies YAML file.
        db_manager: DatabaseManager instance.
        name: Company name.
        youtube_channels: List of YouTube channel IDs.
        rss_feed: RSS feed URL.
        keywords: List of keywords.
    """
    companies = load_companies(companies_file)
    for company in companies:
        if company.name.lower() == name.lower():
            company.youtube_channels = youtube_channels or company.youtube_channels
            company.rss_feed = rss_feed or company.rss_feed
            company.keywords = keywords or company.keywords
            save_companies(companies, companies_file)
            db_manager.insert_company(company)  # Updates via ON CONFLICT
            logger.info(f"Updated company: {name}")
            return
    logger.error(f"Company {name} not found")


def remove_company(companies_file: str, name: str) -> None:
    """Remove a company.

    Args:
        companies_file: Path to companies YAML file.
        name: Company name.
    """
    companies = load_companies(companies_file)
    companies = [c for c in companies if c.name.lower() != name.lower()]
    save_companies(companies, companies_file)
    logger.info(f"Removed company: {name}")


def main():
    """Command-line interface for managing companies."""
    parser = argparse.ArgumentParser(description="Manage RetailXAI companies")
    parser.add_argument("action", choices=["list", "add", "update", "remove"], help="Action to perform")
    parser.add_argument("--name", help="Company name")
    parser.add_argument("--youtube_channels", nargs="*", default=[], help="YouTube channel IDs")
    parser.add_argument("--rss_feed", help="RSS feed URL")
    parser.add_argument("--keywords", nargs="*", default=[], help="Keywords")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output for list")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    db_manager = DatabaseManager(config["global"]["database"])
    companies_file = config["sources"]["youtube"]["channels"]

    if args.action == "list":
        list_companies(companies_file, args.verbose)
    elif args.action == "add":
        if not args.name:
            parser.error("The --name argument is required for add")
        add_company(companies_file, db_manager, args.name, args.youtube_channels, args.rss_feed, args.keywords)
    elif args.action == "update":
        if not args.name:
            parser.error("The --name argument is required for update")
        update_company(companies_file, db_manager, args.name, args.youtube_channels, args.rss_feed, args.keywords)
    elif args.action == "remove":
        if not args.name:
            parser.error("The --name argument is required for remove")
        remove_company(companies_file, args.name)

    db_manager.close()


if __name__ == "__main__":
    main()
