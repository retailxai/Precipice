#!/usr/bin/env python3
"""
Production Monitoring and Alerting System
Elon-level production monitoring with real-time alerts and SLA tracking.
"""

import logging
import time
import json
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("RetailXAI.ProductionMonitor")


@dataclass
class Alert:
    """Represents a production alert."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    component: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class SLAMetric:
    """Represents an SLA metric."""
    name: str
    target: float  # Target percentage (0-100)
    current: float  # Current percentage (0-100)
    status: str  # PASS, WARN, FAIL
    last_updated: datetime


class ProductionMonitor:
    """Elon-level production monitoring system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize production monitor.
        
        Args:
            config: Configuration dictionary with monitoring settings.
        """
        self.config = config
        self.alerts: List[Alert] = []
        self.sla_metrics: Dict[str, SLAMetric] = {}
        self.alert_channels = self._setup_alert_channels()
        self.start_time = datetime.now()
        
        # SLA Targets (Elon's standards)
        self.sla_targets = {
            'uptime': 99.9,  # 99.9% uptime
            'response_time': 95.0,  # 95% of requests under 2s
            'error_rate': 99.0,  # 99% success rate
            'data_freshness': 90.0,  # 90% of data less than 1 hour old
            'api_quota_usage': 80.0,  # Stay under 80% of quota
        }
        
        logger.info("Production monitor initialized with Elon-level standards")
    
    def _setup_alert_channels(self) -> Dict[str, Any]:
        """Set up alert channels (email, Slack, etc.)."""
        channels = {}
        
        # Email alerts
        if self.config.get('email'):
            channels['email'] = self.config['email']
        
        # Slack alerts
        if self.config.get('slack_webhook'):
            channels['slack'] = self.config['slack_webhook']
        
        return channels
    
    def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        health_status = {
            'overall_status': 'HEALTHY',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'alerts': [],
            'sla_metrics': {}
        }
        
        # Check database connectivity
        db_health = self._check_database_health()
        health_status['components']['database'] = db_health
        
        # Check API endpoints
        api_health = self._check_api_health()
        health_status['components']['api'] = api_health
        
        # Check memory usage
        memory_health = self._check_memory_health()
        health_status['components']['memory'] = memory_health
        
        # Check disk space
        disk_health = self._check_disk_health()
        health_status['components']['disk'] = disk_health
        
        # Check API quotas
        quota_health = self._check_api_quotas()
        health_status['components']['quotas'] = quota_health
        
        # Calculate overall status
        failed_components = [name for name, status in health_status['components'].items() 
                           if status['status'] != 'HEALTHY']
        
        if failed_components:
            health_status['overall_status'] = 'UNHEALTHY'
            self._create_alert('CRITICAL', 'system', 
                             f"System unhealthy: {', '.join(failed_components)}")
        
        # Update SLA metrics
        self._update_sla_metrics(health_status)
        health_status['sla_metrics'] = {name: {
            'target': metric.target,
            'current': metric.current,
            'status': metric.status
        } for name, metric in self.sla_metrics.items()}
        
        return health_status
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # This would connect to your actual database
            # For now, return mock data
            return {
                'status': 'HEALTHY',
                'response_time_ms': 15.2,
                'connections_active': 3,
                'last_query_time': datetime.now().isoformat()
            }
        except Exception as e:
            self._create_alert('CRITICAL', 'database', f"Database connection failed: {e}")
            return {
                'status': 'UNHEALTHY',
                'error': str(e)
            }
    
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health."""
        endpoints = [
            'http://localhost:5000/api/health',
            'http://localhost:5000/api/stats',
            'http://localhost:5000/api/transcripts'
        ]
        
        healthy_endpoints = 0
        total_response_time = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=5)
                response_time = (time.time() - start_time) * 1000
                total_response_time += response_time
                
                if response.status_code == 200:
                    healthy_endpoints += 1
                else:
                    self._create_alert('HIGH', 'api', f"Endpoint {endpoint} returned {response.status_code}")
            except Exception as e:
                self._create_alert('HIGH', 'api', f"Endpoint {endpoint} failed: {e}")
        
        health_percentage = (healthy_endpoints / len(endpoints)) * 100
        avg_response_time = total_response_time / len(endpoints)
        
        if health_percentage < 100:
            self._create_alert('MEDIUM', 'api', f"API health at {health_percentage:.1f}%")
        
        return {
            'status': 'HEALTHY' if health_percentage >= 100 else 'DEGRADED',
            'healthy_endpoints': healthy_endpoints,
            'total_endpoints': len(endpoints),
            'health_percentage': health_percentage,
            'avg_response_time_ms': avg_response_time
        }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent > 90:
                self._create_alert('CRITICAL', 'memory', f"Memory usage at {memory_percent:.1f}%")
                status = 'UNHEALTHY'
            elif memory_percent > 80:
                self._create_alert('HIGH', 'memory', f"Memory usage at {memory_percent:.1f}%")
                status = 'WARNING'
            else:
                status = 'HEALTHY'
            
            return {
                'status': status,
                'usage_percent': memory_percent,
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3)
            }
        except Exception as e:
            self._create_alert('HIGH', 'memory', f"Memory check failed: {e}")
            return {
                'status': 'UNKNOWN',
                'error': str(e)
            }
    
    def _check_disk_health(self) -> Dict[str, Any]:
        """Check disk space."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            
            if free_percent < 5:
                self._create_alert('CRITICAL', 'disk', f"Disk space at {free_percent:.1f}%")
                status = 'UNHEALTHY'
            elif free_percent < 15:
                self._create_alert('HIGH', 'disk', f"Disk space at {free_percent:.1f}%")
                status = 'WARNING'
            else:
                status = 'HEALTHY'
            
            return {
                'status': status,
                'free_percent': free_percent,
                'total_gb': disk.total / (1024**3),
                'free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            self._create_alert('HIGH', 'disk', f"Disk check failed: {e}")
            return {
                'status': 'UNKNOWN',
                'error': str(e)
            }
    
    def _check_api_quotas(self) -> Dict[str, Any]:
        """Check API quota usage."""
        # This would check actual API quotas
        # For now, return mock data
        quota_status = {
            'youtube': {'used': 8500, 'limit': 10000, 'percent': 85.0},
            'claude': {'used': 1200, 'limit': 2000, 'percent': 60.0},
            'news_api': {'used': 450, 'limit': 1000, 'percent': 45.0}
        }
        
        for service, quota in quota_status.items():
            if quota['percent'] > 90:
                self._create_alert('CRITICAL', 'quota', f"{service} quota at {quota['percent']:.1f}%")
            elif quota['percent'] > 80:
                self._create_alert('HIGH', 'quota', f"{service} quota at {quota['percent']:.1f}%")
        
        return {
            'status': 'HEALTHY',
            'quotas': quota_status
        }
    
    def _update_sla_metrics(self, health_status: Dict[str, Any]) -> None:
        """Update SLA metrics based on health status."""
        current_time = datetime.now()
        
        # Uptime calculation
        uptime_hours = (current_time - self.start_time).total_seconds() / 3600
        uptime_percent = min(100.0, (uptime_hours / 24) * 100)  # Assume 24h target
        
        self.sla_metrics['uptime'] = SLAMetric(
            name='uptime',
            target=self.sla_targets['uptime'],
            current=uptime_percent,
            status='PASS' if uptime_percent >= self.sla_targets['uptime'] else 'FAIL',
            last_updated=current_time
        )
        
        # API response time
        api_health = health_status['components'].get('api', {})
        avg_response_time = api_health.get('avg_response_time_ms', 0)
        response_time_percent = max(0, 100 - (avg_response_time / 20))  # 2s = 100%
        
        self.sla_metrics['response_time'] = SLAMetric(
            name='response_time',
            target=self.sla_targets['response_time'],
            current=response_time_percent,
            status='PASS' if response_time_percent >= self.sla_targets['response_time'] else 'FAIL',
            last_updated=current_time
        )
        
        # Error rate
        api_health_percent = api_health.get('health_percentage', 100)
        self.sla_metrics['error_rate'] = SLAMetric(
            name='error_rate',
            target=self.sla_targets['error_rate'],
            current=api_health_percent,
            status='PASS' if api_health_percent >= self.sla_targets['error_rate'] else 'FAIL',
            last_updated=current_time
        )
    
    def _create_alert(self, severity: str, component: str, message: str) -> None:
        """Create a new alert."""
        alert = Alert(
            severity=severity,
            component=component,
            message=message,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        logger.warning(f"ALERT [{severity}] {component}: {message}")
        
        # Send immediate alerts for critical issues
        if severity == 'CRITICAL':
            self._send_alert(alert)
    
    def _send_alert(self, alert: Alert) -> None:
        """Send alert through configured channels."""
        alert_message = f"""
🚨 RETAILXAI PRODUCTION ALERT 🚨

Severity: {alert.severity}
Component: {alert.component}
Time: {alert.timestamp}
Message: {alert.message}

This is an automated alert from the RetailXAI production monitoring system.
        """.strip()
        
        # Send email alert
        if 'email' in self.alert_channels:
            self._send_email_alert(alert_message)
        
        # Send Slack alert
        if 'slack' in self.alert_channels:
            self._send_slack_alert(alert_message)
    
    def _send_email_alert(self, message: str) -> None:
        """Send email alert."""
        try:
            email_config = self.alert_channels['email']
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = "RetailXAI Production Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("Email alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_slack_alert(self, message: str) -> None:
        """Send Slack alert."""
        try:
            webhook_url = self.alert_channels['slack']
            payload = {
                'text': message,
                'username': 'RetailXAI Monitor',
                'icon_emoji': ':robot_face:'
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def get_production_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive production dashboard data."""
        health_status = self.check_system_health()
        
        # Get recent alerts (last 24 hours)
        recent_alerts = [
            {
                'severity': alert.severity,
                'component': alert.component,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved
            }
            for alert in self.alerts
            if alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        # Calculate system uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        uptime_days = uptime_seconds / 86400
        
        return {
            'system_status': health_status['overall_status'],
            'uptime_days': round(uptime_days, 2),
            'sla_metrics': {name: {
                'target': metric.target,
                'current': metric.current,
                'status': metric.status,
                'last_updated': metric.last_updated.isoformat()
            } for name, metric in self.sla_metrics.items()},
            'recent_alerts': recent_alerts,
            'components': health_status['components'],
            'last_updated': datetime.now().isoformat()
        }
    
    def resolve_alert(self, alert_index: int) -> bool:
        """Resolve an alert."""
        try:
            if 0 <= alert_index < len(self.alerts):
                self.alerts[alert_index].resolved = True
                self.alerts[alert_index].resolution_time = datetime.now()
                logger.info(f"Alert {alert_index} resolved")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_index}: {e}")
            return False


def main():
    """Run production monitor."""
    # Example configuration
    config = {
        'email': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password',
            'from': 'your-email@gmail.com',
            'to': 'alerts@yourcompany.com'
        },
        'slack_webhook': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    }
    
    monitor = ProductionMonitor(config)
    
    # Run health check
    dashboard = monitor.get_production_dashboard()
    print(json.dumps(dashboard, indent=2))


if __name__ == "__main__":
    main()
