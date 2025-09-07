"""
Yahoo Finance Collector
Collects financial data from Yahoo Finance API.
"""

import logging
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import json

logger = logging.getLogger("RetailXAI.YahooFinanceCollector")


class YahooFinanceCollector:
    """Collects financial data from Yahoo Finance API."""

    def __init__(self, symbols: List[str], shutdown_event: Optional[threading.Event] = None):
        """Initialize Yahoo Finance collector.
        
        Args:
            symbols: List of stock symbols to collect data for
            shutdown_event: Event for graceful shutdown
        """
        self.symbols = symbols
        self.shutdown_event = shutdown_event
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json,text/plain,*/*'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests

    def _check_shutdown(self) -> bool:
        """Check if shutdown is requested."""
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("Shutdown requested, stopping Yahoo Finance operations")
            return True
        return False

    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def _extract_financial_metrics(self, quote_data: Dict) -> Dict:
        """Extract financial metrics from quote data."""
        metrics = {}
        
        try:
            # Extract price data
            if 'regularMarketPrice' in quote_data:
                metrics['price'] = quote_data['regularMarketPrice']
            
            if 'marketCap' in quote_data:
                metrics['market_cap'] = quote_data['marketCap']
            
            if 'trailingPE' in quote_data:
                metrics['trailing_pe'] = quote_data['trailingPE']
            
            if 'forwardPE' in quote_data:
                metrics['forward_pe'] = quote_data['forwardPE']
            
            if 'epsTrailingTwelveMonths' in quote_data:
                metrics['eps_ttm'] = quote_data['epsTrailingTwelveMonths']
            
            if 'beta' in quote_data:
                metrics['beta'] = quote_data['beta']
            
            if 'regularMarketChange' in quote_data:
                metrics['change'] = quote_data['regularMarketChange']
            
            if 'regularMarketChangePercent' in quote_data:
                metrics['change_percent'] = quote_data['regularMarketChangePercent']
            
            if 'regularMarketVolume' in quote_data:
                metrics['volume'] = quote_data['regularMarketVolume']
            
            if 'averageVolume' in quote_data:
                metrics['avg_volume'] = quote_data['averageVolume']
            
            if 'fiftyTwoWeekHigh' in quote_data:
                metrics['52_week_high'] = quote_data['fiftyTwoWeekHigh']
            
            if 'fiftyTwoWeekLow' in quote_data:
                metrics['52_week_low'] = quote_data['fiftyTwoWeekLow']
            
            if 'dividendYield' in quote_data:
                metrics['dividend_yield'] = quote_data['dividendYield']
            
            if 'priceToBook' in quote_data:
                metrics['price_to_book'] = quote_data['priceToBook']
            
            if 'priceToSalesTrailing12Months' in quote_data:
                metrics['price_to_sales'] = quote_data['priceToSalesTrailing12Months']
                
        except Exception as e:
            logger.warning(f"Error extracting financial metrics: {e}")
            
        return metrics

    def collect_symbol(self, symbol: str) -> Optional[Dict]:
        """Collect financial data for a single symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with financial data or None if failed
        """
        if self._check_shutdown():
            return None
            
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'quoteResponse' not in data or 'result' not in data['quoteResponse']:
                logger.warning(f"No data found for symbol: {symbol}")
                return None
            
            result = data['quoteResponse']['result']
            if not result:
                logger.warning(f"No result found for symbol: {symbol}")
                return None
            
            quote_data = result[0]
            
            # Extract key information
            company_info = {
                'source': 'yahoo_quote',
                'url': url,
                'title': f"Yahoo Finance Quote - {symbol}",
                'published_at': datetime.now().isoformat(),
                'summary': f"Financial data for {symbol} from Yahoo Finance",
                'metadata': {
                    'symbol': symbol,
                    'company_name': quote_data.get('longName', ''),
                    'exchange': quote_data.get('fullExchangeName', ''),
                    'currency': quote_data.get('currency', ''),
                    'financial_metrics': self._extract_financial_metrics(quote_data),
                    'raw_data': quote_data  # Store full data as metadata
                }
            }
            
            logger.info(f"Successfully collected Yahoo Finance data for {symbol}")
            return company_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error collecting Yahoo Finance data for {symbol}: {e}")
            return None

    def collect_all_symbols(self) -> List[Dict]:
        """Collect financial data for all symbols.
        
        Returns:
            List of financial data
        """
        if self._check_shutdown():
            return []
            
        results = []
        
        for symbol in self.symbols:
            if self._check_shutdown():
                break
                
            financial_data = self.collect_symbol(symbol)
            if financial_data:
                results.append(financial_data)
                
            # Small delay between symbols
            time.sleep(0.5)
            
        logger.info(f"Collected Yahoo Finance data for {len(results)} symbols")
        return results

