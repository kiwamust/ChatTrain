# ChatTrain Troubleshooting Guide 🔧

This comprehensive troubleshooting guide helps you resolve common issues with ChatTrain MVP1. Follow the steps below to diagnose and fix problems quickly.

## 🚨 Emergency Quick Fixes

### System Down - Emergency Recovery
```bash
# Stop everything and restart
make stop
make clean
make setup
make dev

# If that fails, nuclear option:
docker system prune -af
make setup
make dev
```

### Critical Issues Hotline
1. **Backend won't start**: Check Docker, database, environment variables
2. **Frontend won't load**: Check Node.js version, rebuild frontend
3. **Database connection failed**: Reset database, check credentials
4. **OpenAI API errors**: Verify API key, check rate limits

## 📋 Diagnostic Checklist

Before diving into specific issues, run this quick diagnostic:

```bash
# 1. Check system health
make health

# 2. Check service status
make status

# 3. Check recent logs
make logs | tail -50

# 4. Check resources
docker stats --no-stream

# 5. Verify environment
cat .env | grep -v "API_KEY\|PASSWORD"
```

## 🔍 Issue Categories

### 1. Installation & Setup Issues

#### Problem: Setup Script Fails
**Symptoms**: `./scripts/setup.sh` exits with errors

**Diagnosis**:
```bash
# Check system requirements
node --version    # Should be 20+
python3 --version # Should be 3.11+
docker --version  # Should be latest
docker info       # Should show running state
```

**Solutions**:

1. **Update system tools**:
   ```bash
   # macOS with Homebrew
   brew update
   brew upgrade node python@3.11 docker
   ```

2. **Fix Docker issues**:
   ```bash
   # Restart Docker Desktop
   # Check Docker Desktop settings
   # Ensure enough resources allocated (4GB RAM minimum)
   ```

3. **Permission issues**:
   ```bash
   chmod +x scripts/*.sh
   sudo chown -R $USER:$USER .
   ```

#### Problem: Environment Configuration Issues
**Symptoms**: Missing or invalid environment variables

**Diagnosis**:
```bash
# Check .env file exists
ls -la .env

# Validate required variables
grep -E "OPENAI_API_KEY|POSTGRES_PASSWORD" .env
```

**Solutions**:

1. **Create .env from template**:
   ```bash
   cp .env.example .env
   # Edit .env and set required values
   ```

2. **Validate OpenAI API key**:
   ```bash
   # Test API key (replace with your key)
   curl -H "Authorization: Bearer sk-..." https://api.openai.com/v1/models
   ```

3. **Fix database credentials**:
   ```bash
   # Ensure POSTGRES_PASSWORD is set and strong
   # Update both .env and docker-compose.yml if needed
   ```

### 2. Service Startup Issues

#### Problem: Docker Containers Won't Start
**Symptoms**: `make dev` fails, containers exit immediately

**Diagnosis**:
```bash
# Check container status
docker compose ps

# Check container logs
docker compose logs

# Check for port conflicts
lsof -i :3000
lsof -i :8000
lsof -i :5432
```

**Solutions**:

1. **Port conflicts**:
   ```bash
   # Kill processes using required ports
   sudo lsof -ti:3000 | xargs kill -9
   sudo lsof -ti:8000 | xargs kill -9
   sudo lsof -ti:5432 | xargs kill -9
   ```

2. **Resource issues**:
   ```bash
   # Check Docker resources
   docker system df
   docker system prune -f
   
   # Increase Docker Desktop memory/CPU limits
   ```

3. **Image build failures**:
   ```bash
   # Rebuild images from scratch
   docker compose build --no-cache
   make dev
   ```

#### Problem: Backend Service Fails to Start
**Symptoms**: Backend container exits, FastAPI won't start

**Diagnosis**:
```bash
# Check backend logs
make logs-backend

# Check Python dependencies
docker compose exec backend pip list

# Check file permissions
ls -la src/backend/
```

**Solutions**:

1. **Python dependency issues**:
   ```bash
   # Rebuild backend container
   docker compose build backend
   
   # Or fix dependencies manually
   docker compose exec backend pip install -r requirements.txt
   ```

2. **Application errors**:
   ```bash
   # Check application startup
   docker compose exec backend python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   
   # Debug mode
   docker compose exec backend python -c "from app.main import app; print('App loaded successfully')"
   ```

3. **File permission issues**:
   ```bash
   # Fix ownership
   sudo chown -R $USER:$USER src/backend/
   chmod -R 755 src/backend/
   ```

#### Problem: Frontend Service Fails to Start
**Symptoms**: Frontend container exits, React app won't load

**Diagnosis**:
```bash
# Check frontend logs
make logs-frontend

# Check Node.js version in container
docker compose exec frontend node --version

# Check build status
docker compose exec frontend npm run build
```

**Solutions**:

1. **Node.js version issues**:
   ```bash
   # Check host Node.js version
   node --version  # Should be 20+
   
   # Rebuild frontend container
   docker compose build frontend
   ```

2. **Build failures**:
   ```bash
   # Clean and rebuild
   cd src/frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   cd ../..
   docker compose build frontend
   ```

3. **Vite configuration issues**:
   ```bash
   # Check Vite config
   cat src/frontend/vite.config.ts
   
   # Test local build
   cd src/frontend
   npm run dev
   ```

### 3. Database Issues

#### Problem: Database Connection Failures
**Symptoms**: Backend can't connect to PostgreSQL

**Diagnosis**:
```bash
# Check database status
make logs-db

# Test database connection
docker compose exec database pg_isready -U chattrain

# Check database logs for errors
docker compose logs database | grep ERROR
```

**Solutions**:

1. **Database not ready**:
   ```bash
   # Wait for database startup (can take 30-60 seconds)
   sleep 60
   docker compose exec database pg_isready -U chattrain
   ```

2. **Credential issues**:
   ```bash
   # Check environment variables
   grep POSTGRES .env
   
   # Test connection with correct credentials
   docker compose exec database psql -U chattrain -d chattrain -c "SELECT 1;"
   ```

3. **Database corruption or reset needed**:
   ```bash
   # Reset database (WARNING: destroys data)
   make reset-db
   
   # Or restore from backup
   make restore BACKUP_DIR=backups/latest
   ```

#### Problem: Database Initialization Fails
**Symptoms**: Schema not created, tables missing

**Diagnosis**:
```bash
# Check if tables exist
docker compose exec database psql -U chattrain -d chattrain -c "\dt"

# Check initialization logs
make logs-db | grep -i "init\|create\|table"
```

**Solutions**:

1. **Re-run initialization**:
   ```bash
   # Manual initialization
   docker compose exec database psql -U chattrain -d chattrain -f /docker-entrypoint-initdb.d/init_db.sql
   ```

2. **Fix initialization script**:
   ```bash
   # Check script syntax
   cat scripts/init_db.sql
   
   # Test script locally
   psql -h localhost -U chattrain -d chattrain -f scripts/init_db.sql
   ```

### 4. Application Issues

#### Problem: Chat Interface Not Working
**Symptoms**: Messages not sending, WebSocket errors

**Diagnosis**:
```bash
# Check WebSocket connection in browser console
# Look for WebSocket errors

# Check backend WebSocket logs
make logs-backend | grep -i websocket

# Test WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws
```

**Solutions**:

1. **WebSocket connection issues**:
   ```bash
   # Check nginx configuration (if using reverse proxy)
   # Ensure WebSocket upgrade headers are set
   
   # Test direct backend connection
   curl http://localhost:8000/health
   ```

2. **Frontend WebSocket client issues**:
   ```bash
   # Check browser console for errors
   # Clear browser cache and cookies
   # Try different browser
   ```

3. **Backend WebSocket handler issues**:
   ```bash
   # Check backend logs for WebSocket errors
   make logs-backend | grep -i "websocket\|connection\|upgrade"
   
   # Restart backend service
   docker compose restart backend
   ```

#### Problem: LLM/OpenAI API Issues
**Symptoms**: AI not responding, API errors

**Diagnosis**:
```bash
# Check API key
grep OPENAI_API_KEY .env

# Check backend logs for API errors
make logs-backend | grep -i "openai\|api\|rate\|limit"

# Test API directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Solutions**:

1. **API key issues**:
   ```bash
   # Verify API key is correct
   # Check OpenAI account billing and usage
   # Regenerate API key if needed
   ```

2. **Rate limiting**:
   ```bash
   # Check rate limit settings
   grep RATE_LIMIT .env
   
   # Wait for rate limits to reset
   # Upgrade OpenAI plan if needed
   ```

3. **API model issues**:
   ```bash
   # Check if model exists and is accessible
   # Update OPENAI_MODEL in .env to supported model
   # Check OpenAI service status
   ```

### 5. Performance Issues

#### Problem: Slow Response Times
**Symptoms**: Chat responses take too long, timeouts

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Check system load
top
df -h

# Check network latency
ping google.com
```

**Solutions**:

1. **Resource constraints**:
   ```bash
   # Increase Docker resources
   # Close other applications
   # Monitor memory usage
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

2. **Database performance**:
   ```bash
   # Check database queries
   docker compose exec database psql -U chattrain -d chattrain -c "SELECT * FROM pg_stat_activity;"
   
   # Rebuild indexes if needed
   docker compose exec database psql -U chattrain -d chattrain -c "REINDEX DATABASE chattrain;"
   ```

3. **Network issues**:
   ```bash
   # Check DNS resolution
   nslookup api.openai.com
   
   # Test direct IP connection
   # Consider VPN issues
   ```

### 6. Data & Backup Issues

#### Problem: Data Loss or Corruption
**Symptoms**: Sessions lost, database errors

**Diagnosis**:
```bash
# Check database integrity
docker compose exec database psql -U chattrain -d chattrain -c "SELECT count(*) FROM sessions;"

# Check backup status
ls -la backups/

# Check volume mounts
docker volume ls
```

**Solutions**:

1. **Restore from backup**:
   ```bash
   # List available backups
   ls -la backups/
   
   # Restore from latest backup
   make restore BACKUP_DIR=backups/$(ls backups/ | tail -1)
   ```

2. **Database repair**:
   ```bash
   # Check and repair database
   docker compose exec database psql -U chattrain -d chattrain -c "VACUUM ANALYZE;"
   ```

3. **Prevent future data loss**:
   ```bash
   # Set up automated backups
   crontab -e
   # Add: 0 2 * * * cd /path/to/chattrain && make backup
   ```

## 🔧 Advanced Troubleshooting

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
docker compose up -d

# Enable verbose logging
export LOG_LEVEL=DEBUG
docker compose restart backend
```

### Container Shell Access
```bash
# Access backend container
docker compose exec backend bash

# Access frontend container
docker compose exec frontend sh

# Access database container
docker compose exec database bash
```

### Network Debugging
```bash
# Check internal network
docker network ls
docker network inspect chattrain_chattrain-network

# Test internal connectivity
docker compose exec backend curl http://database:5432
docker compose exec frontend curl http://backend:8000/health
```

### Log Analysis
```bash
# Analyze error patterns
make logs | grep -i error | sort | uniq -c

# Check timing issues
make logs | grep -i timeout

# Monitor real-time logs
make logs | grep -E "(ERROR|WARN|FAIL)" --color=always
```

## 📊 Monitoring & Alerts

### Health Monitoring
```bash
# Continuous health monitoring
watch -n 30 'make health'

# Resource monitoring
watch -n 10 'docker stats --no-stream'

# Log monitoring
tail -f logs/*.log | grep -E "(ERROR|WARN)" --color=always
```

### Automated Alerts
```bash
# Simple alert script (save as monitor.sh)
#!/bin/bash
while true; do
    if ! make health > /dev/null 2>&1; then
        echo "ALERT: ChatTrain health check failed at $(date)" | mail -s "ChatTrain Alert" admin@company.com
    fi
    sleep 300  # Check every 5 minutes
done
```

## 🆘 When All Else Fails

### Complete System Reset
```bash
# Nuclear option - rebuilds everything
make stop
make clean-all
rm -rf backups/emergency_$(date +%Y%m%d_%H%M%S)
make backup  # If system is partially working
make setup
make dev
```

### Recovery Checklist
- [ ] Backup current state (if possible)
- [ ] Document the issue and steps that led to it
- [ ] Check system resources and requirements
- [ ] Reset to known good state
- [ ] Restore data from backup
- [ ] Test functionality thoroughly
- [ ] Update documentation with lessons learned

### Getting Help

1. **Gather Information**:
   ```bash
   # Create diagnostic report
   make health > diagnostic_report.txt
   make status >> diagnostic_report.txt
   docker system info >> diagnostic_report.txt
   ```

2. **Contact Support**:
   - Include diagnostic report
   - Describe steps that led to the issue
   - Specify environment (dev/prod)
   - Include error messages and logs

3. **GitHub Issues**:
   - Create detailed issue with reproduction steps
   - Include system information
   - Tag with appropriate labels

## 📚 Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://reactjs.org/docs/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **OpenAI API Documentation**: https://platform.openai.com/docs/

---

**Remember**: Most issues can be resolved by following the diagnostic steps and solutions above. When in doubt, start with the basic health checks and work your way through the specific issue categories.

*Last updated: December 2023*