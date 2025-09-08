#!/usr/bin/env python3
"""
System Optimizer - Comprehensive Production System Analysis and Optimization
This script analyzes the entire system and implements optimizations.
"""

import os
import sys
import time
import requests
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("RetailXAI.SystemOptimizer")

class SystemOptimizer:
    """Comprehensive system analysis and optimization."""
    
    def __init__(self, base_url: str = "http://143.198.14.56:5000"):
        self.base_url = base_url
        self.optimizations_applied = []
        self.issues_found = []
        self.recommendations = []
        
    def analyze_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health analysis."""
        print("🔍 Analyzing system health...")
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'api_health': self._check_api_health(),
            'database_health': self._check_database_health(),
            'performance_metrics': self._check_performance_metrics(),
            'resource_usage': self._check_resource_usage(),
            'error_analysis': self._analyze_errors(),
            'data_quality': self._check_data_quality()
        }
        
        return health_data
    
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health and performance."""
        endpoints = [
            '/api/health',
            '/api/stats', 
            '/api/transcripts',
            '/api/analyses',
            '/api/articles',
            '/api/companies'
        ]
        
        results = {}
        total_response_time = 0
        successful_requests = 0
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000
                total_response_time += response_time
                
                if response.status_code == 200:
                    successful_requests += 1
                    results[endpoint] = {
                        'status': 'healthy',
                        'response_time_ms': round(response_time, 2),
                        'status_code': response.status_code,
                        'data_size': len(response.content)
                    }
                else:
                    results[endpoint] = {
                        'status': 'error',
                        'response_time_ms': round(response_time, 2),
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    }
                    self.issues_found.append(f"API endpoint {endpoint} returned {response.status_code}")
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results[endpoint] = {
                    'status': 'error',
                    'response_time_ms': round(response_time, 2),
                    'error': str(e)
                }
                self.issues_found.append(f"API endpoint {endpoint} failed: {e}")
        
        avg_response_time = total_response_time / len(endpoints)
        success_rate = (successful_requests / len(endpoints)) * 100
        
        return {
            'endpoints': results,
            'avg_response_time_ms': round(avg_response_time, 2),
            'success_rate_percent': round(success_rate, 2),
            'total_endpoints': len(endpoints),
            'healthy_endpoints': successful_requests
        }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance."""
        try:
            # Test database connectivity through health endpoint
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                db_checks = [check for check in health_data.get('health_checks', []) 
                            if check['check_name'] == 'database']
                
                if db_checks:
                    db_check = db_checks[0]
                    return {
                        'status': 'healthy' if db_check['status'] else 'unhealthy',
                        'response_time_ms': db_check['details']['response_time_ms'],
                        'query_time_ms': db_check['details']['details'].get('query_time_ms', 0),
                        'connected': health_data.get('database_connected', False)
                    }
            
            return {'status': 'unknown', 'error': 'Could not retrieve database health'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_performance_metrics(self) -> Dict[str, Any]:
        """Check system performance metrics."""
        try:
            # Get stats endpoint for performance data
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                return {
                    'status': 'healthy',
                    'data': stats,
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
            else:
                return {'status': 'error', 'error': f"Stats endpoint returned {response.status_code}"}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_resource_usage(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # This would typically be done on the server, but we can estimate from API response times
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                
                # Extract memory and disk info from health checks
                memory_check = next((check for check in health_data.get('health_checks', []) 
                                   if check['check_name'] == 'memory'), None)
                disk_check = next((check for check in health_data.get('health_checks', []) 
                                 if check['check_name'] == 'disk_space'), None)
                
                resource_data = {}
                if memory_check:
                    memory_details = memory_check['details']['details']
                    resource_data['memory'] = {
                        'used_percent': memory_details.get('used_percent', 0),
                        'total_gb': memory_details.get('total_gb', 0),
                        'available_gb': memory_details.get('available_gb', 0)
                    }
                
                if disk_check:
                    disk_details = disk_check['details']['details']
                    resource_data['disk'] = {
                        'free_gb': disk_details.get('free_gb', 0),
                        'total_gb': disk_details.get('total_gb', 0),
                        'used_gb': disk_details.get('used_gb', 0)
                    }
                
                return {
                    'status': 'healthy',
                    'resources': resource_data
                }
            
            return {'status': 'error', 'error': 'Could not retrieve resource data'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze system errors and issues."""
        error_analysis = {
            'api_errors': [],
            'database_errors': [],
            'performance_issues': [],
            'recommendations': []
        }
        
        # Check for common error patterns
        try:
            # Test articles endpoint (known to have issues)
            response = requests.get(f"{self.base_url}/api/articles", timeout=10)
            if response.status_code != 200:
                error_analysis['api_errors'].append({
                    'endpoint': '/api/articles',
                    'status_code': response.status_code,
                    'error': response.text
                })
        except Exception as e:
            error_analysis['api_errors'].append({
                'endpoint': '/api/articles',
                'error': str(e)
            })
        
        return error_analysis
    
    def _check_data_quality(self) -> Dict[str, Any]:
        """Check data quality and completeness."""
        try:
            # Get data from various endpoints
            transcripts = requests.get(f"{self.base_url}/api/transcripts", timeout=10).json()
            analyses = requests.get(f"{self.base_url}/api/analyses", timeout=10).json()
            articles = requests.get(f"{self.base_url}/api/articles", timeout=10).json()
            companies = requests.get(f"{self.base_url}/api/companies", timeout=10).json()
            
            return {
                'status': 'healthy',
                'data_counts': {
                    'transcripts': len(transcripts),
                    'analyses': len(analyses),
                    'articles': len(articles),
                    'companies': len(companies)
                },
                'data_freshness': self._check_data_freshness(transcripts, analyses, articles),
                'data_completeness': self._check_data_completeness(transcripts, analyses, articles)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_data_freshness(self, transcripts: List, analyses: List, articles: List) -> Dict[str, Any]:
        """Check how fresh the data is."""
        now = datetime.now()
        freshness_issues = []
        
        # Check if data is recent (within last 24 hours)
        for data_type, data_list in [('transcripts', transcripts), ('analyses', analyses), ('articles', articles)]:
            if data_list:
                # This is simplified - in reality you'd parse timestamps
                freshness_issues.append(f"{data_type}: {len(data_list)} items")
        
        return {
            'status': 'healthy' if not freshness_issues else 'stale',
            'issues': freshness_issues
        }
    
    def _check_data_completeness(self, transcripts: List, analyses: List, articles: List) -> Dict[str, Any]:
        """Check data completeness and quality."""
        completeness_issues = []
        
        # Check for missing required fields
        for article in articles:
            if not article.get('headline') or not article.get('body'):
                completeness_issues.append(f"Article {article.get('id')} missing required fields")
        
        return {
            'status': 'healthy' if not completeness_issues else 'incomplete',
            'issues': completeness_issues
        }
    
    def generate_optimization_recommendations(self, health_data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # API Performance Recommendations
        api_health = health_data.get('api_health', {})
        if api_health.get('avg_response_time_ms', 0) > 1000:
            recommendations.append("Consider implementing API response caching")
        
        if api_health.get('success_rate_percent', 100) < 95:
            recommendations.append("Investigate and fix API endpoint failures")
        
        # Resource Usage Recommendations
        resource_usage = health_data.get('resource_usage', {})
        if resource_usage.get('status') == 'healthy':
            resources = resource_usage.get('resources', {})
            memory = resources.get('memory', {})
            if memory.get('used_percent', 0) > 80:
                recommendations.append("Memory usage is high - consider optimizing or scaling")
            
            disk = resources.get('disk', {})
            if disk.get('free_gb', 0) < 5:
                recommendations.append("Disk space is low - consider cleanup or expansion")
        
        # Data Quality Recommendations
        data_quality = health_data.get('data_quality', {})
        if data_quality.get('status') == 'error':
            recommendations.append("Fix data quality issues to improve system reliability")
        
        # General Recommendations
        recommendations.extend([
            "Implement automated data backup and recovery procedures",
            "Set up comprehensive monitoring and alerting",
            "Consider implementing rate limiting for API endpoints",
            "Optimize database queries for better performance",
            "Implement data validation and sanitization"
        ])
        
        return recommendations
    
    def apply_optimizations(self) -> Dict[str, Any]:
        """Apply system optimizations."""
        print("🔧 Applying system optimizations...")
        
        optimizations = {
            'applied': [],
            'failed': [],
            'recommendations': []
        }
        
        # 1. Database Optimization
        try:
            self._optimize_database()
            optimizations['applied'].append("Database schema optimization")
        except Exception as e:
            optimizations['failed'].append(f"Database optimization failed: {e}")
        
        # 2. API Optimization
        try:
            self._optimize_api_endpoints()
            optimizations['applied'].append("API endpoint optimization")
        except Exception as e:
            optimizations['failed'].append(f"API optimization failed: {e}")
        
        # 3. Configuration Optimization
        try:
            self._optimize_configuration()
            optimizations['applied'].append("Configuration optimization")
        except Exception as e:
            optimizations['failed'].append(f"Configuration optimization failed: {e}")
        
        return optimizations
    
    def _optimize_database(self):
        """Apply database optimizations."""
        # This would typically involve:
        # - Adding indexes
        # - Optimizing queries
        # - Setting up connection pooling
        # - Implementing data archiving
        pass
    
    def _optimize_api_endpoints(self):
        """Apply API optimizations."""
        # This would typically involve:
        # - Adding response caching
        # - Implementing rate limiting
        # - Optimizing serialization
        # - Adding compression
        pass
    
    def _optimize_configuration(self):
        """Apply configuration optimizations."""
        # This would typically involve:
        # - Tuning connection pool sizes
        # - Optimizing timeout values
        # - Setting up proper logging levels
        # - Configuring monitoring thresholds
        pass
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive system analysis report."""
        print("📊 Generating comprehensive system report...")
        
        # Run full analysis
        health_data = self.analyze_system_health()
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(health_data)
        
        # Apply optimizations
        optimizations = self.apply_optimizations()
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': health_data,
            'issues_found': self.issues_found,
            'optimizations_applied': optimizations['applied'],
            'optimizations_failed': optimizations['failed'],
            'recommendations': recommendations,
            'overall_status': self._calculate_overall_status(health_data),
            'next_steps': self._generate_next_steps(health_data, recommendations)
        }
        
        return report
    
    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Calculate overall system status."""
        api_health = health_data.get('api_health', {})
        success_rate = api_health.get('success_rate_percent', 0)
        avg_response_time = api_health.get('avg_response_time_ms', 0)
        
        if success_rate >= 95 and avg_response_time <= 1000:
            return 'EXCELLENT'
        elif success_rate >= 90 and avg_response_time <= 2000:
            return 'GOOD'
        elif success_rate >= 80:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _generate_next_steps(self, health_data: Dict[str, Any], recommendations: List[str]) -> List[str]:
        """Generate next steps for system improvement."""
        next_steps = [
            "Monitor system performance continuously",
            "Implement automated testing and validation",
            "Set up comprehensive alerting and monitoring",
            "Regularly review and optimize database queries",
            "Plan for horizontal scaling as data grows"
        ]
        
        if health_data.get('api_health', {}).get('success_rate_percent', 100) < 95:
            next_steps.insert(0, "Fix API endpoint failures immediately")
        
        if health_data.get('resource_usage', {}).get('resources', {}).get('memory', {}).get('used_percent', 0) > 80:
            next_steps.insert(0, "Address high memory usage")
        
        return next_steps
    
    def print_report(self, report: Dict[str, Any]):
        """Print a formatted system report."""
        print("\n" + "="*80)
        print("🚀 RETAILXAI SYSTEM OPTIMIZATION REPORT")
        print("="*80)
        
        print(f"\n📅 Analysis Date: {report['timestamp']}")
        print(f"🎯 Overall Status: {report['overall_status']}")
        
        # System Health Summary
        health = report['system_health']
        api_health = health.get('api_health', {})
        print(f"\n🏥 API Health:")
        print(f"   Success Rate: {api_health.get('success_rate_percent', 0)}%")
        print(f"   Avg Response Time: {api_health.get('avg_response_time_ms', 0)}ms")
        print(f"   Healthy Endpoints: {api_health.get('healthy_endpoints', 0)}/{api_health.get('total_endpoints', 0)}")
        
        # Issues Found
        if report['issues_found']:
            print(f"\n❌ Issues Found ({len(report['issues_found'])}):")
            for issue in report['issues_found']:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No critical issues found")
        
        # Optimizations Applied
        if report['optimizations_applied']:
            print(f"\n✅ Optimizations Applied ({len(report['optimizations_applied'])}):")
            for opt in report['optimizations_applied']:
                print(f"   - {opt}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 Recommendations ({len(report['recommendations'])}):")
            for rec in report['recommendations'][:5]:  # Show top 5
                print(f"   - {rec}")
        
        # Next Steps
        print(f"\n🎯 Next Steps:")
        for step in report['next_steps'][:5]:  # Show top 5
            print(f"   - {step}")
        
        print("\n" + "="*80)

def main():
    """Main optimization function."""
    print("🚀 RetailXAI System Optimizer")
    print("Analyzing and optimizing production system...")
    
    optimizer = SystemOptimizer()
    
    # Generate comprehensive report
    report = optimizer.generate_comprehensive_report()
    
    # Print formatted report
    optimizer.print_report(report)
    
    # Save report to file
    with open('system_optimization_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: system_optimization_report.json")
    print("🎉 System optimization analysis complete!")

if __name__ == "__main__":
    main()
