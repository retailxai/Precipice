#!/usr/bin/env python3
"""
Performance Monitoring and SLA Tracking
This script monitors system performance and tracks SLA metrics.
"""

import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class PerformanceMonitor:
    """Monitor system performance and SLA metrics."""
    
    def __init__(self, base_url: str = "http://143.198.14.56:5000"):
        self.base_url = base_url
        self.sla_targets = {
            'uptime': 99.9,
            'response_time': 95.0,  # 95% of requests under 2s
            'error_rate': 1.0,
            'data_freshness': 90.0  # 90% of data < 1 hour old
        }
        self.metrics_history = []
    
    def check_health_endpoint(self) -> Dict[str, Any]:
        """Check the health endpoint and measure response time."""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy',
                    'response_time_ms': response_time,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time_ms': response_time,
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 'error',
                'response_time_ms': response_time,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Check all API endpoints for availability and performance."""
        endpoints = [
            '/api/health',
            '/api/stats',
            '/api/transcripts',
            '/api/analyses',
            '/api/companies'
        ]
        
        results = {}
        total_response_time = 0
        successful_requests = 0
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                response_time = (time.time() - start_time) * 1000
                total_response_time += response_time
                
                if response.status_code == 200:
                    successful_requests += 1
                    results[endpoint] = {
                        'status': 'success',
                        'response_time_ms': response_time,
                        'status_code': response.status_code
                    }
                else:
                    results[endpoint] = {
                        'status': 'error',
                        'response_time_ms': response_time,
                        'status_code': response.status_code
                    }
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results[endpoint] = {
                    'status': 'error',
                    'response_time_ms': response_time,
                    'error': str(e)
                }
        
        avg_response_time = total_response_time / len(endpoints)
        success_rate = (successful_requests / len(endpoints)) * 100
        
        return {
            'endpoints': results,
            'avg_response_time_ms': avg_response_time,
            'success_rate_percent': success_rate,
            'total_endpoints': len(endpoints),
            'successful_endpoints': successful_requests
        }
    
    def calculate_sla_metrics(self, health_data: Dict[str, Any], api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SLA metrics based on current data."""
        current_time = datetime.now()
        
        # Uptime calculation (simplified - in real implementation, this would track over time)
        uptime_percent = 100.0 if health_data['status'] == 'healthy' else 0.0
        
        # Response time SLA
        response_time_percent = max(0, 100 - (api_data['avg_response_time_ms'] / 20))  # 2s = 100%
        
        # Error rate SLA
        error_rate_percent = 100 - api_data['success_rate_percent']
        
        # Data freshness (simplified - would check actual data timestamps)
        data_freshness_percent = 100.0  # Assume fresh for now
        
        sla_metrics = {
            'uptime': {
                'target': self.sla_targets['uptime'],
                'current': uptime_percent,
                'status': 'PASS' if uptime_percent >= self.sla_targets['uptime'] else 'FAIL'
            },
            'response_time': {
                'target': self.sla_targets['response_time'],
                'current': response_time_percent,
                'status': 'PASS' if response_time_percent >= self.sla_targets['response_time'] else 'FAIL'
            },
            'error_rate': {
                'target': self.sla_targets['error_rate'],
                'current': error_rate_percent,
                'status': 'PASS' if error_rate_percent <= self.sla_targets['error_rate'] else 'FAIL'
            },
            'data_freshness': {
                'target': self.sla_targets['data_freshness'],
                'current': data_freshness_percent,
                'status': 'PASS' if data_freshness_percent >= 90 else 'FAIL'  # 90% of data < 1 hour old
            }
        }
        
        return sla_metrics
    
    def run_performance_check(self) -> Dict[str, Any]:
        """Run a complete performance check."""
        print("🔍 Running performance check...")
        
        # Check health endpoint
        health_data = self.check_health_endpoint()
        print(f"   Health: {health_data['status']} ({health_data['response_time_ms']:.1f}ms)")
        
        # Check API endpoints
        api_data = self.check_api_endpoints()
        print(f"   API Success Rate: {api_data['success_rate_percent']:.1f}%")
        print(f"   Avg Response Time: {api_data['avg_response_time_ms']:.1f}ms")
        
        # Calculate SLA metrics
        sla_metrics = self.calculate_sla_metrics(health_data, api_data)
        
        # Store metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'health': health_data,
            'api': api_data,
            'sla_metrics': sla_metrics
        }
        
        self.metrics_history.append(metrics)
        
        # Keep only last 100 measurements
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from recent measurements."""
        if not self.metrics_history:
            return {'error': 'No metrics available'}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        # Calculate averages
        avg_response_time = sum(m['api']['avg_response_time_ms'] for m in recent_metrics) / len(recent_metrics)
        avg_success_rate = sum(m['api']['success_rate_percent'] for m in recent_metrics) / len(recent_metrics)
        
        # Count SLA violations
        sla_violations = 0
        total_checks = 0
        
        for metrics in recent_metrics:
            for metric_name, metric_data in metrics['sla_metrics'].items():
                total_checks += 1
                if metric_data['status'] == 'FAIL':
                    sla_violations += 1
        
        sla_compliance = ((total_checks - sla_violations) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'period': f"Last {len(recent_metrics)} measurements",
            'avg_response_time_ms': round(avg_response_time, 2),
            'avg_success_rate_percent': round(avg_success_rate, 2),
            'sla_compliance_percent': round(sla_compliance, 2),
            'total_measurements': len(self.metrics_history),
            'last_check': recent_metrics[-1]['timestamp'] if recent_metrics else None
        }
    
    def print_performance_report(self):
        """Print a comprehensive performance report."""
        print("\n" + "="*60)
        print("📊 RETAILXAI PERFORMANCE REPORT")
        print("="*60)
        
        # Run current check
        current_metrics = self.run_performance_check()
        
        print(f"\n🏥 Health Status: {current_metrics['health']['status']}")
        print(f"⏱️  Response Time: {current_metrics['health']['response_time_ms']:.1f}ms")
        print(f"🌐 API Success Rate: {current_metrics['api']['success_rate_percent']:.1f}%")
        
        print(f"\n📈 SLA Metrics:")
        for metric_name, metric_data in current_metrics['sla_metrics'].items():
            status_emoji = "✅" if metric_data['status'] == 'PASS' else "❌"
            print(f"   {status_emoji} {metric_name}: {metric_data['current']:.1f}% (target: {metric_data['target']}%)")
        
        # Performance summary
        summary = self.get_performance_summary()
        print(f"\n📊 Performance Summary:")
        print(f"   Period: {summary['period']}")
        print(f"   Avg Response Time: {summary['avg_response_time_ms']}ms")
        print(f"   Avg Success Rate: {summary['avg_success_rate_percent']}%")
        print(f"   SLA Compliance: {summary['sla_compliance_percent']}%")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if current_metrics['api']['avg_response_time_ms'] > 1000:
            print("   - Consider optimizing API response times")
        if current_metrics['api']['success_rate_percent'] < 95:
            print("   - Investigate API endpoint failures")
        if summary['sla_compliance_percent'] < 90:
            print("   - Address SLA violations to improve compliance")
        
        print(f"\n🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("="*60)

def main():
    """Main monitoring function."""
    monitor = PerformanceMonitor()
    
    print("🚀 RetailXAI Performance Monitor")
    print("Monitoring system performance and SLA metrics...")
    
    # Run performance check
    monitor.print_performance_report()
    
    # Optionally run continuous monitoring
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        print("\n🔄 Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(60)  # Check every minute
                monitor.run_performance_check()
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped")

if __name__ == "__main__":
    main()
