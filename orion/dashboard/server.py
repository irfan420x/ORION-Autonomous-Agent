"""
ORION Dashboard Server
======================

Serves the web dashboard and provides API endpoints.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import aiohttp, fall back to basic HTTP server
try:
    from aiohttp import web
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    import http.server
    import socketserver


class DashboardServer:
    """Web server for the ORION Dashboard."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, api=None):
        self.host = host
        self.port = port
        self.api = api
        self._template_dir = Path(__file__).parent / "templates"
    
    def start(self):
        """Start the dashboard server."""
        if HAS_AIOHTTP:
            self._start_aiohttp()
        else:
            self._start_basic()
    
    def _start_basic(self):
        """Start a basic HTTP server (fallback)."""
        os.chdir(self._template_dir)
        
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer((self.host, self.port), handler) as httpd:
            logger.info(f"Dashboard running at http://{self.host}:{self.port}")
            httpd.serve_forever()
    
    def _start_aiohttp(self):
        """Start aiohttp server with API support."""
        app = web.Application()
        
        # Serve static files
        app.router.add_static('/static/', path=self._template_dir, name='static')
        
        # API routes
        app.router.add_get('/', self._handle_index)
        app.router.add_get('/api/system', self._handle_system)
        app.router.add_get('/api/processes', self._handle_processes)
        app.router.add_get('/api/memory', self._handle_memory)
        app.router.add_get('/api/tasks', self._handle_tasks)
        app.router.add_get('/api/runtime', self._handle_runtime)
        app.router.add_post('/api/action', self._handle_action)
        
        web.run_app(app, host=self.host, port=self.port, print=lambda x: logger.info(x))
    
    async def _handle_index(self, request):
        """Serve the main dashboard page."""
        index_path = self._template_dir / "index.html"
        return web.FileResponse(index_path)
    
    async def _handle_system(self, request):
        """API: System overview."""
        if self.api:
            return web.json_response(self.api.get_system_overview())
        return web.json_response({"error": "API not initialized"})
    
    async def _handle_processes(self, request):
        """API: Process list."""
        if self.api:
            return web.json_response(self.api.get_processes())
        return web.json_response([])
    
    async def _handle_memory(self, request):
        """API: Memory stats."""
        if self.api:
            return web.json_response(self.api.get_memory_stats())
        return web.json_response({})
    
    async def _handle_tasks(self, request):
        """API: Task list."""
        if self.api:
            return web.json_response(self.api.get_tasks())
        return web.json_response([])
    
    async def _handle_runtime(self, request):
        """API: Runtime status."""
        if self.api:
            return web.json_response(self.api.get_runtime_status())
        return web.json_response({})
    
    async def _handle_action(self, request):
        """API: Execute action."""
        data = await request.json()
        action_id = data.get('action_id')
        params = data.get('params', {})
        
        if self.api:
            result = self.api.execute_action(action_id, params)
            return web.json_response(result)
        return web.json_response({"error": "API not initialized"})


def main():
    """Run the dashboard server standalone."""
    logging.basicConfig(level=logging.INFO)
    
    server = DashboardServer()
    server.start()


if __name__ == "__main__":
    main()
