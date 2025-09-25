#!/usr/bin/env python3
"""
RetailXAI Company and Source Configuration Editor

This script helps you easily add, edit, or remove companies and sources
from the RetailXAI configuration files.
"""

import yaml
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

class RetailXAIConfigEditor:
    def __init__(self, config_dir: str = "/home/retailxai/precipice/config"):
        self.config_dir = config_dir
        self.companies_file = os.path.join(config_dir, "companies.yaml")
        self.sources_file = os.path.join(config_dir, "sources.json")
        self.config_file = os.path.join(config_dir, "config.yaml")
        
    def load_companies(self) -> Dict[str, Any]:
        """Load companies configuration from YAML file."""
        try:
            with open(self.companies_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: {self.companies_file} not found")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing {self.companies_file}: {e}")
            return {}
    
    def save_companies(self, data: Dict[str, Any]) -> bool:
        """Save companies configuration to YAML file."""
        try:
            with open(self.companies_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {self.companies_file}: {e}")
            return False
    
    def load_sources(self) -> List[Dict[str, Any]]:
        """Load sources configuration from JSON file."""
        try:
            with open(self.sources_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.sources_file} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing {self.sources_file}: {e}")
            return []
    
    def save_sources(self, data: List[Dict[str, Any]]) -> bool:
        """Save sources configuration to JSON file."""
        try:
            with open(self.sources_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving {self.sources_file}: {e}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Load main configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: {self.config_file} not found")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing {self.config_file}: {e}")
            return {}
    
    def save_config(self, data: Dict[str, Any]) -> bool:
        """Save main configuration to YAML file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {self.config_file}: {e}")
            return False
    
    def add_company(self, name: str, youtube_channels: List[str] = None, 
                   rss_feed: str = None, keywords: List[str] = None) -> bool:
        """Add a new company to the configuration."""
        companies_data = self.load_companies()
        if not companies_data:
            companies_data = {"companies": []}
        
        # Check if company already exists
        for company in companies_data.get("companies", []):
            if company.get("name", "").lower() == name.lower():
                print(f"Company '{name}' already exists")
                return False
        
        new_company = {
            "name": name,
            "youtube_channels": youtube_channels or [],
            "rss_feed": rss_feed or "",
            "keywords": keywords or []
        }
        
        companies_data.setdefault("companies", []).append(new_company)
        
        if self.save_companies(companies_data):
            print(f"Successfully added company: {name}")
            return True
        return False
    
    def add_source(self, source_id: str, entity_id: str, source_type: str, 
                  details: Dict[str, Any]) -> bool:
        """Add a new source to the configuration."""
        sources_data = self.load_sources()
        
        # Check if source already exists
        for source in sources_data:
            if source.get("source_id") == source_id:
                print(f"Source '{source_id}' already exists")
                return False
        
        new_source = {
            "source_id": source_id,
            "entity_id": entity_id,
            "source_type": source_type,
            "details": details
        }
        
        sources_data.append(new_source)
        
        if self.save_sources(sources_data):
            print(f"Successfully added source: {source_id}")
            return True
        return False
    
    def add_stock_symbol(self, symbol: str) -> bool:
        """Add a stock symbol to the Yahoo Finance configuration."""
        config_data = self.load_config()
        
        if "sources" not in config_data:
            config_data["sources"] = {}
        if "yahoo_finance" not in config_data["sources"]:
            config_data["sources"]["yahoo_finance"] = {"enabled": True, "symbols": []}
        
        symbols = config_data["sources"]["yahoo_finance"].get("symbols", [])
        if symbol.upper() not in [s.upper() for s in symbols]:
            symbols.append(symbol.upper())
            config_data["sources"]["yahoo_finance"]["symbols"] = symbols
            
            if self.save_config(config_data):
                print(f"Successfully added stock symbol: {symbol.upper()}")
                return True
        else:
            print(f"Stock symbol '{symbol}' already exists")
            return False
        return False
    
    def list_companies(self) -> None:
        """List all configured companies."""
        companies_data = self.load_companies()
        companies = companies_data.get("companies", [])
        
        if not companies:
            print("No companies configured")
            return
        
        print("\n📊 Configured Companies:")
        print("=" * 50)
        for i, company in enumerate(companies, 1):
            print(f"{i}. {company.get('name', 'Unknown')}")
            print(f"   YouTube Channels: {len(company.get('youtube_channels', []))}")
            print(f"   RSS Feed: {'Yes' if company.get('rss_feed') else 'No'}")
            print(f"   Keywords: {', '.join(company.get('keywords', []))}")
            print()
    
    def list_sources(self) -> None:
        """List all configured sources."""
        sources_data = self.load_sources()
        
        if not sources_data:
            print("No sources configured")
            return
        
        print("\n📰 Configured Sources:")
        print("=" * 50)
        for i, source in enumerate(sources_data, 1):
            print(f"{i}. {source.get('source_id', 'Unknown')}")
            print(f"   Entity: {source.get('entity_id', 'Unknown')}")
            print(f"   Type: {source.get('source_type', 'Unknown')}")
            print(f"   Details: {source.get('details', {})}")
            print()
    
    def list_stock_symbols(self) -> None:
        """List all configured stock symbols."""
        config_data = self.load_config()
        symbols = config_data.get("sources", {}).get("yahoo_finance", {}).get("symbols", [])
        
        if not symbols:
            print("No stock symbols configured")
            return
        
        print("\n📈 Configured Stock Symbols:")
        print("=" * 50)
        for i, symbol in enumerate(symbols, 1):
            print(f"{i}. {symbol}")
        print()

def main():
    """Main function to run the configuration editor."""
    editor = RetailXAIConfigEditor()
    
    if len(sys.argv) < 2:
        print("RetailXAI Configuration Editor")
        print("=" * 40)
        print("Usage:")
        print("  python edit_companies_sources.py list-companies")
        print("  python edit_companies_sources.py list-sources")
        print("  python edit_companies_sources.py list-symbols")
        print("  python edit_companies_sources.py add-company 'Company Name'")
        print("  python edit_companies_sources.py add-source 'source_id' 'entity_id' 'youtube' 'channel_id'")
        print("  python edit_companies_sources.py add-symbol 'SYMBOL'")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list-companies":
        editor.list_companies()
    elif command == "list-sources":
        editor.list_sources()
    elif command == "list-symbols":
        editor.list_stock_symbols()
    elif command == "add-company":
        if len(sys.argv) < 3:
            print("Usage: add-company 'Company Name'")
            return
        company_name = sys.argv[2]
        editor.add_company(company_name)
    elif command == "add-source":
        if len(sys.argv) < 6:
            print("Usage: add-source 'source_id' 'entity_id' 'source_type' 'detail_key' 'detail_value'")
            return
        source_id = sys.argv[2]
        entity_id = sys.argv[3]
        source_type = sys.argv[4]
        detail_key = sys.argv[5]
        detail_value = sys.argv[6] if len(sys.argv) > 6 else ""
        details = {detail_key: detail_value}
        editor.add_source(source_id, entity_id, source_type, details)
    elif command == "add-symbol":
        if len(sys.argv) < 3:
            print("Usage: add-symbol 'SYMBOL'")
            return
        symbol = sys.argv[2]
        editor.add_stock_symbol(symbol)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()

