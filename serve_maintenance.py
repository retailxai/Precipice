#!/usr/bin/env python3
"""
Simple HTTP server to serve maintenance page
"""

import http.server
import socketserver
import os
from datetime import datetime

class MaintenanceHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/maintenance':
            self.send_response(503)  # Service Unavailable
            self.send_header('Content-type', 'text/html')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('X-XSS-Protection', '1; mode=block')
            self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
            self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            # Serve maintenance.html
            try:
                with open('maintenance.html', 'r') as f:
                    content = f.read()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.wfile.write(b'<h1>Maintenance Mode</h1><p>Dashboard is offline for security updates</p>')
        elif self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "maintenance",
                "message": "Dashboard is in maintenance mode for security updates",
                "timestamp": datetime.now().isoformat(),
                "expected_completion": "Within 24 hours"
            }
            self.wfile.write(str(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 - Not Found</h1><p>Dashboard is in maintenance mode</p>')

if __name__ == "__main__":
    PORT = 8001
    
    print("🔧 Starting RetailXAI Maintenance Server")
    print("======================================")
    print("Maintenance mode is active")
    print("Dashboard is offline for security updates")
    print("")
    print("Access URLs:")
    print(f"  Maintenance Page: http://localhost:{PORT}")
    print(f"  Health Check: http://localhost:{PORT}/api/health")
    print("")
    print("To stop maintenance mode:")
    print("  ./disable_maintenance.sh")
    print("")
    
    with socketserver.TCPServer(("", PORT), MaintenanceHandler) as httpd:
        print(f"Server running on port {PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down maintenance server...")
            httpd.shutdown()

