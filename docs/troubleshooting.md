### Troubleshooting

#### Service Monitoring
First, check overall system health:
```bash
./monitor.sh status    # Check service status and health
./monitor.sh           # Monitor live logs for errors
```

#### Admin Dashboard Issues

**Cannot access admin dashboard**
- Verify frontend is running on `http://localhost:8001`
- Check that `/admin` route is accessible
- Ensure backend admin APIs are responding at `/api/admin/*`

**Job deletion fails**
- Cannot delete running jobs (by design for safety)
- Check job status before attempting deletion
- Verify admin API connectivity

**Site management errors**
- At least one site must be marked as default
- Site codes must be unique
- Active sites cannot be deleted if they're defaults

#### Common Issues

**API returns empty list**
- Ensure `NOVA_ACT_API_KEY` is set. The legacy synchronous API handler returns `[]` if missing:
```python
api_key = os.getenv("NOVA_ACT_API_KEY")
if not api_key:
    return []
```
- Check backend logs: `./monitor.sh backend`

**CORS errors in the browser**
- Backend must be running at `http://localhost:8000` and CORS allows `http://localhost:8001` (see CORS configuration in `api/main.py`)
- Check service status: `./monitor.sh status`

**No frontend results or WebSocket connection issues**
- Check browser network tab for failed WebSocket connections
- Verify backend WebSocket endpoint is running at `/ws/logs/{job_id}`
- Monitor frontend logs: `./monitor.sh frontend`
- Check backend API logs: `./monitor.sh backend`
- Ensure job_id exists before connecting to WebSocket

**Nova Act session timeouts**
- Reduce `max_items_per_site` or try `headless=False` for visibility
- Step and timeout limits are enforced inside `_scrape_site_for_topic` and `_scrape_sites_by_topic_parallel` in `novanews.py`
- Monitor real-time scraping logs: `./monitor.sh backend`

**AgentCore browser issues**
- Confirm `NOVANEWS_BROWSER_MODE=agentcore` is set before launching `./start.sh`
- Provide valid AWS credentials and `AWS_BEARER_TOKEN_BEDROCK`
- Override the region with `AGENTCORE_BROWSER_REGION` if your Bedrock resources live outside `us-east-1`
- Disable preview actuation (`AGENTCORE_BROWSER_PREVIEW_ACTUATION=false`) if the AgentCore sandbox blocks Playwright commands
- Check backend logs for the AgentCore deep-link to inspect the remote session

**WebSocket connection errors**
- Check browser console for WebSocket connection failures
- Verify WebSocket URL format: `ws://localhost:8000/ws/logs/{job_id}`
- Ensure CORS is properly configured in FastAPI
- Check that job exists before connecting

**Slack notification missing**
- Ensure `.env` contains `SLACK_WEBHOOK_URL` and the workspace allows incoming webhooks
- Confirm `NOVANEWS_ENABLE_SLACK_NOTIFICATIONS=true` or launch with `./start.sh --slack true`
- Increase/decrease preview size via `SLACK_WEBHOOK_PREVIEW_LIMIT` (1–10)
- Review backend logs for "Slack notification has been sent" or silent failures

**MCP server cannot reach API**
- Verify `NOVA_NEWS_API_BASE_URL` and that backend is reachable
- Check MCP server logs: `./monitor.sh mcp`
- Ensure all admin endpoints are accessible

**Services won't start**
- Check port conflicts: `./monitor.sh status`
- Verify environment variables in `.env`
- Check individual service logs: `./monitor.sh [backend|frontend|mcp]`

**Database connection errors**
- Ensure PostgreSQL is running: `./monitor.sh status`
- Verify `DATABASE_URL` in `.env`
- Check backend logs for connection errors: `./monitor.sh backend`

#### Advanced Troubleshooting

For detailed monitoring and debugging, see: `docs/monitoring.md`
