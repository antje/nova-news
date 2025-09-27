### Service Monitoring and Log Management

NovaNews includes a comprehensive monitoring system via the `monitor.sh` script that provides real-time service status, log streaming, and health checks for all system components.

#### Quick Start

```bash
# Show service status and health
./monitor.sh status

# Monitor all service logs with color coding
./monitor.sh

# Monitor specific service logs
./monitor.sh backend   # Backend API logs
./monitor.sh frontend  # Next.js frontend logs
./monitor.sh mcp       # MCP server logs
```

#### Service Status Monitoring

**Real-time Health Check:**
```bash
./monitor.sh status
```

This command displays:
- ✅ **Service Status**: Running/stopped status for each service
- 🔌 **Port Status**: Whether services are listening on expected ports
- 📁 **Log File Info**: Log file locations and sizes
- 🗄️ **Database Status**: PostgreSQL connectivity check

**Example Output:**
```
🔍 NovaNews Service Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Backend API - Running (PID: 12345, Port: 8000)
✅ Frontend - Running (PID: 12346, Port: 8001)  
✅ MCP Server - Running (PID: 12347)
🗄️  Database (PostgreSQL): Running (Port: 5432)

📝 Log files:
  📄 logs/backend.log (2.3MB)
  📄 logs/frontend.log (456KB)
  📄 logs/mcp.log (89KB)

💡 Use './monitor.sh [backend|frontend|mcp]' to view specific logs
💡 Use 'Ctrl+C' to stop monitoring
```

#### Live Log Monitoring

**Monitor All Services:**
```bash
./monitor.sh
# or
./monitor.sh all
```

Features:
- **Color-coded output** for easy service identification
- **Timestamped entries** for each log line
- **Multi-service streaming** in a single terminal
- **Automatic fallback** if advanced tools aren't available

**Monitor Individual Services:**
```bash
# Backend API logs (FastAPI, uvicorn, database operations)
./monitor.sh backend

# Frontend logs (Next.js development server, build output)
./monitor.sh frontend

# MCP server logs (AI assistant integration, tool calls)
./monitor.sh mcp
```

#### Enhanced Monitoring with Multitail

For improved log viewing, install `multitail`:

```bash
# macOS
brew install multitail

# Ubuntu/Debian
sudo apt-get install multitail

# CentOS/RHEL
sudo yum install multitail
```

With `multitail` installed, `./monitor.sh` automatically provides:
- **Side-by-side log windows** for each service
- **Individual scroll buffers** for each log stream
- **Better visual separation** between services
- **Advanced filtering and search** capabilities

#### Service Health Indicators

**Status Icons:**
- ✅ **Service Running**: Process active and port listening
- ⚠️ **Partial Issues**: Process running but port issues, or port active but no PID file
- ❌ **Service Down**: Process not running
- 🔴 **Not Running**: Service completely stopped

**Port Monitoring:**
- **Backend API**: Port 8000 (HTTP API endpoints)
- **Frontend**: Port 8001 (Next.js development server)
- **Database**: Port 5432 (PostgreSQL)
- **MCP Server**: No specific port (STDIO communication)

#### Log File Locations

**Log Directory Structure:**
```
logs/
├── backend.log     # FastAPI API server logs
├── frontend.log    # Next.js development server logs
└── mcp.log         # MCP server logs
```

**Log Content Examples:**

**Backend logs** (`logs/backend.log`):
```
2024-01-15 10:30:15 - INFO - Starting search job: 550e8400-e29b-41d4-a716-446655440000
2024-01-15 10:30:16 - INFO - Launching search for topic='nova act' sources=['latent_space']
2024-01-15 10:30:18 - INFO - Scraping latent_space for topic: nova act
2024-01-15 10:30:25 - INFO - Found 3 articles from latent_space
2024-01-15 10:30:25 - INFO - Job completed with 3 result(s)
```

**Frontend logs** (`logs/frontend.log`):
```
ready - started server on 0.0.0.0:8001, url: http://localhost:8001
info  - Loaded env from /path/to/project/.env.local
info  - Using webpack 5. Reason: Enabled by default
event - compiled client and server successfully in 2.1s (165 modules)
```

**MCP logs** (`logs/mcp.log`):
```
2024-01-15 10:25:30 - INFO - Starting NovaNews MCP server
2024-01-15 10:25:30 - INFO - API base URL: http://localhost:8000
2024-01-15 10:25:30 - INFO - HTTP timeout: 300 seconds
2024-01-15 10:30:45 - INFO - Received search_news request: topic=machine learning
```

#### Troubleshooting with Monitoring

**Common Issues and Diagnosis:**

**1. Service Won't Start**
```bash
./monitor.sh status
# Look for:
# - Port conflicts (another process using 8000/8001)
# - Missing dependencies
# - Environment variable issues
```

**2. Service Crashes**
```bash
./monitor.sh backend    # Check for error messages
tail -50 logs/backend.log  # View recent errors
```

**3. Database Connection Issues**
```bash
./monitor.sh status
# Check PostgreSQL status
# Verify DATABASE_URL in .env
```

**4. Performance Issues**
```bash
./monitor.sh           # Watch for error patterns
# Monitor resource usage patterns
# Check for long-running requests
```

#### Log Management

**Automatic Log Rotation:**
NovaNews doesn't implement automatic log rotation. For production deployments, consider:

```bash
# Manual log cleanup
find logs/ -name "*.log" -size +100M -delete

# Or rotate logs
mv logs/backend.log logs/backend.log.$(date +%Y%m%d)
./stop.sh && ./start.sh  # Restart to create new logs
```

**Log Analysis:**
```bash
# Search for errors across all logs
grep -i error logs/*.log

# Find database connection issues  
grep -i "database\|postgres\|connection" logs/backend.log

# Monitor job completion rates
grep "Job completed\|Job failed" logs/backend.log | tail -20
```

#### Advanced Monitoring

**Process Monitoring:**
```bash
# Check memory usage
ps aux | grep -E "(uvicorn|node|python.*mcp)"

# Monitor open connections
lsof -i :8000  # Backend connections
lsof -i :8001  # Frontend connections
```

**Database Monitoring:**
```bash
# Check active database connections
psql $DATABASE_URL -c "SELECT count(*) as active_connections FROM pg_stat_activity;"

# Monitor job queue
psql $DATABASE_URL -c "SELECT status, count(*) FROM search_jobs GROUP BY status;"
```

**Integration with External Tools:**
```bash
# Send logs to external monitoring (example)
./monitor.sh backend | logger -t novanews-backend

# Prometheus metrics (if implemented)
curl http://localhost:8000/metrics

# Health check endpoint
curl http://localhost:8000/api/health
```

#### Monitoring Best Practices

1. **Regular Status Checks**: Run `./monitor.sh status` periodically
2. **Log Review**: Monitor logs during active development
3. **Error Alerting**: Set up alerts for error patterns in production
4. **Resource Monitoring**: Watch for memory/disk usage growth
5. **Database Health**: Monitor job completion rates and database size
6. **Performance Baseline**: Establish normal response time patterns

#### Monitoring in Production

For production deployments, consider:

**Log Aggregation:**
- Ship logs to centralized logging (ELK, Splunk, etc.)
- Implement structured logging with JSON format
- Add correlation IDs for request tracing

**Metrics Collection:**
- Add Prometheus metrics endpoints
- Monitor response times and error rates
- Track job completion statistics

**Alerting:**
- Set up alerts for service downtime
- Monitor error rate thresholds
- Alert on database connection failures

**Health Checks:**
- Implement comprehensive health endpoints
- Add dependency health checks (database, external APIs)
- Set up uptime monitoring
