"""
SEC EDGAR Company Facts Collector
Collects financial data from SEC EDGAR API for retail companies.
"""

import logging
import time
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading

logger = logging.getLogger("RetailXAI.SECEDGARCollector")


class SECEDGARCollector:
    """Collects company financial data from SEC EDGAR API."""

    def __init__(self, cik_map: Dict[str, str], shutdown_event: Optional[threading.Event] = None):
        """Initialize SEC EDGAR collector.
        
        Args:
            cik_map: Dictionary mapping ticker symbols to CIK numbers
            shutdown_event: Event for graceful shutdown
        """
        self.cik_map = cik_map
        self.shutdown_event = shutdown_event
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RetailXAI Data Collector (contact@retailxai.com)',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping SEC EDGAR operations")
            return True
        return False

    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing tracking parameters."""
        if '?' in url:
            url = url.split('?')[0]
        return url

    def _extract_financial_metrics(self, facts_data: Dict) -> Dict:
        """Extract key financial metrics from SEC facts data."""
        metrics = {}
        
        try:
            # Extract revenue data
            if 'Revenues' in facts_data.get('facts', {}).get('us-gaap', {}):
                revenue_data = facts_data['facts']['us-gaap']['Revenues']['units']
                if 'USD' in revenue_data:
                    latest_revenue = max(revenue_data['USD'], key=lambda x: x['end'])
                    metrics['revenue'] = latest_revenue['val']
                    metrics['revenue_period'] = latest_revenue['end']
            
            # Extract COGS
            if 'CostOfGoodsAndServicesSold' in facts_data.get('facts', {}).get('us-gaap', {}):
                cogs_data = facts_data['facts']['us-gaap']['CostOfGoodsAndServicesSold']['units']
                if 'USD' in cogs_data:
                    latest_cogs = max(cogs_data['USD'], key=lambda x: x['end'])
                    metrics['cogs'] = latest_cogs['val']
                    metrics['cogs_period'] = latest_cogs['end']
            
            # Extract SG&A
            if 'SellingGeneralAndAdministrativeExpense' in facts_data.get('facts', {}).get('us-gaap', {}):
                sga_data = facts_data['facts']['us-gaap']['SellingGeneralAndAdministrativeExpense']['units']
                if 'USD' in sga_data:
                    latest_sga = max(sga_data['USD'], key=lambda x: x['end'])
                    metrics['sga'] = latest_sga['val']
                    metrics['sga_period'] = latest_sga['end']
            
            # Extract Operating Income
            if 'OperatingIncomeLoss' in facts_data.get('facts', {}).get('us-gaap', {}):
                op_income_data = facts_data['facts']['us-gaap']['OperatingIncomeLoss']['units']
                if 'USD' in op_income_data:
                    latest_op_income = max(op_income_data['USD'], key=lambda x: x['end'])
                    metrics['operating_income'] = latest_op_income['val']
                    metrics['operating_income_period'] = latest_op_income['end']
            
            # Extract Net Income
            if 'NetIncomeLoss' in facts_data.get('facts', {}).get('us-gaap', {}):
                net_income_data = facts_data['facts']['us-gaap']['NetIncomeLoss']['units']
                if 'USD' in net_income_data:
                    latest_net_income = max(net_income_data['USD'], key=lambda x: x['end'])
                    metrics['net_income'] = latest_net_income['val']
                    metrics['net_income_period'] = latest_net_income['end']
                    
        except Exception as e:
            logger.warning(f"Error extracting financial metrics: {e}")
            
        return metrics

    def collect_company_facts(self, ticker: str) -> Optional[Dict]:
        """Collect company facts for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with company facts data or None if failed
        """
        if self._check_shutdown():
            return None
            
        if ticker not in self.cik_map:
            logger.warning(f"CIK not found for ticker: {ticker}")
            return None
            
        cik = self.cik_map[ticker]
        url = self.base_url.format(cik)
        
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            facts_data = response.json()
            
            # Extract key information
            company_info = {
                'source': 'sec_edgar',
                'url': url,
                'title': f"SEC Company Facts - {ticker}",
                'published_at': datetime.now().isoformat(),
                'summary': f"Financial data for {ticker} from SEC EDGAR",
                'metadata': {
                    'ticker': ticker,
                    'cik': cik,
                    'entity_name': facts_data.get('entityName', ''),
                    'entity_type': facts_data.get('entityType', ''),
                    'sic': facts_data.get('sic', ''),
                    'sic_description': facts_data.get('sicDescription', ''),
                    'state_of_incorporation': facts_data.get('stateOfIncorporation', ''),
                    'financial_metrics': self._extract_financial_metrics(facts_data),
                    'raw_data': facts_data  # Store full JSON as metadata
                }
            }
            
            logger.info(f"Successfully collected SEC data for {ticker}")
            return company_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching SEC data for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error collecting SEC data for {ticker}: {e}")
            return None

    def collect_all_companies(self) -> List[Dict]:
        """Collect company facts for all companies in CIK map.
        
        Returns:
            List of company facts data
        """
        if self._check_shutdown():
            return []
            
        results = []
        
        for ticker in self.cik_map.keys():
            if self._check_shutdown():
                break
                
            company_data = self.collect_company_facts(ticker)
            if company_data:
                results.append(company_data)
                
            # Small delay between companies
            time.sleep(0.5)
            
        logger.info(f"Collected SEC data for {len(results)} companies")
        return results

