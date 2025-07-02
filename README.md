<div align="center">

# ChatTrain MVP1 🤖

**AI-powered chat training platform for customer service excellence**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![React](https://img.shields.io/badge/React-19.1.0-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

</div>

## 📖 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [📋 Training Scenarios](#-training-scenarios)
- [🛠️ Development](#️-development)
- [🧪 Testing](#-testing)
- [🚢 Deployment](#-deployment)
- [📚 Documentation](#-documentation)
- [🛡️ Security](#️-security)
- [📈 Performance](#-performance)
- [🔧 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## 🎯 Overview

ChatTrain MVP1 enables **5 pilot users** to complete **30-minute AI-powered training scenarios** with real-time feedback. Built with modern web technologies and OpenAI integration for enterprise-grade customer service training.

### Key Benefits
- 🎯 **Interactive Learning**: Real-time chat scenarios with AI customers
- ⚡ **Instant Feedback**: Immediate evaluation and improvement suggestions  
- 📊 **Progress Tracking**: Detailed session analytics and performance metrics
- 🔒 **Enterprise Security**: Automatic PII masking and data protection
- 📱 **Modern UI**: Responsive React interface with split-pane design

## ✨ Features

- **Real-time Chat Training**: Interactive scenarios with AI customers
- **Instant Feedback**: Keyword-based evaluation with improvement suggestions
- **Document Integration**: Reference materials displayed during training
- **Data Security**: Automatic PII masking for sensitive information
- **Scenario Management**: YAML-based content with Git workflow

## 🚀 Quick Start

> **Get ChatTrain running in under 5 minutes!**

### Prerequisites
Make sure you have these installed:
- 🟢 **Node.js 20+** - [Download here](https://nodejs.org/)
- 🐍 **Python 3.11+** - [Download here](https://python.org/)
- 🐳 **Docker** - [Download here](https://docker.com/)
- 🔑 **OpenAI API Key** - [Get yours here](https://platform.openai.com/api-keys)

### One-Command Setup
```bash
# 1. Clone the repository
git clone https://github.com/kiwamust/ChatTrain.git
cd ChatTrain

# 2. Setup everything (dependencies, environment, database)
make setup

# 3. Configure your OpenAI API key
cp .env.example .env
echo "OPENAI_API_KEY=your_api_key_here" >> .env

# 4. Start the development environment
make dev
```

### 🎉 That's it! Access your application:
- **Frontend**: http://localhost:3000 (Main application)
- **Backend API**: http://localhost:8000 (API endpoints)  
- **API Docs**: http://localhost:8000/docs (Interactive documentation)

### Quick Health Check
```bash
# Verify everything is working
make health

# Check service status  
make status

# View logs if needed
make logs
```

### Alternative: Docker-Only Setup
```bash
# If you prefer using only Docker
docker compose up -d
# Then configure your .env file and restart
```

## 📋 Training Scenarios

### 1. Insurance Claim Handling (30 min)
Customer files claim after car accident - practice empathy, information gathering, and next steps.

### 2. Customer Service Support (30 min)  
User experiencing login issues - practice troubleshooting, password reset, and technical support.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ChatTrain MVP1                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │   Frontend      │    │    Backend       │    │  Storage    │ │
│  │  (React + TS)   │◄──►│   (FastAPI)      │◄──►│             │ │
│  │   Port 3000     │    │    Port 8000     │    │             │ │
│  │                 │    │                  │    │             │ │
│  │ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────┐ │ │
│  │ │  Chat UI    │ │    │ │ WebSocket    │ │    │ │ SQLite  │ │ │
│  │ │  Interface  │ │    │ │ /chat/stream │ │    │ │ Database│ │ │
│  │ └─────────────┘ │    │ └──────────────┘ │    │ └─────────┘ │ │
│  │ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────┐ │ │
│  │ │ Document    │ │    │ │  REST API    │ │    │ │ YAML    │ │ │
│  │ │ Viewer      │ │    │ │  Endpoints   │ │    │ │ Content │ │ │
│  │ └─────────────┘ │    │ └──────────────┘ │    │ └─────────┘ │ │
│  └─────────────────┘    │ ┌──────────────┐ │    └─────────────┘ │
│                         │ │   Security   │ │                    │
│  ┌─────────────────┐    │ │ PII Masking  │ │    ┌─────────────┐ │
│  │ i18n Support    │    │ └──────────────┘ │    │ OpenAI API  │ │
│  │ (EN/JA)         │    │        │         │    │ gpt-4o-mini │ │
│  └─────────────────┘    └────────┼─────────┘    └─────────────┘ │
│                                  │                              │
│                         ┌────────▼─────────┐                    │
│                         │  LLM Integration │                    │
│                         │  & Feedback      │                    │
│                         │  Generation      │                    │
│                         └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Frontend**: React 19.1.0 + TypeScript + Vite
- **Backend**: FastAPI 0.104.1 + Uvicorn + WebSockets  
- **Database**: SQLite (development) / PostgreSQL (production)
- **LLM**: OpenAI GPT-4o-mini integration
- **Security**: Regex-based PII masking + rate limiting
- **Content**: YAML-based scenario management + Git workflow
- **Deployment**: Docker + Docker Compose
- **Internationalization**: React-i18next (EN/JA)

## 📊 MVP1 Success Criteria

- ✅ **5 pilot users** supported concurrently
- ✅ **2 scenarios × 30 minutes** training sessions
- ✅ **LLM feedback** with evaluation scores
- ✅ **Data masking** for sensitive information
- ✅ **<3 second** response times

## 🛠️ Development

### Available Commands
```bash
# Setup & Installation
make setup              # Initial environment setup
make install            # Alias for setup

# Development  
make dev                # Start development servers
make dev-logs           # Start with live logs
make dev-build          # Build and start development

# Testing
make test               # Run all tests
make test-backend       # Backend tests only
make test-frontend      # Frontend tests only  
make test-integration   # Integration tests
make test-load          # Load testing

# Production
make build              # Build production images
make deploy             # Deploy to production
make deploy-backup      # Deploy with backup

# Monitoring & Control
make status             # Show service status
make health             # Health checks
make logs               # View development logs
make stop               # Stop services
make restart            # Restart services

# Maintenance
make backup             # Create data backup
make clean              # Clean up containers
make update             # Update dependencies
```

### Development Workflow
1. **Initial Setup**: `make setup` (run once)
2. **Daily Development**: `make dev` 
3. **Running Tests**: `make test` (before commits)
4. **Code Quality**: `make lint` (if available)
5. **Health Checks**: `make health` (troubleshooting)

### Environment Variables
Create a `.env` file with these required variables:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (with defaults)
FRONTEND_PORT=3000
BACKEND_PORT=8000
DATABASE_URL=sqlite:///./chattrain.db
LOG_LEVEL=INFO
```

### Code Structure
```
src/
├── frontend/          # React TypeScript application
│   ├── components/    # Reusable UI components  
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API integration
│   └── types/         # TypeScript definitions
├── backend/           # FastAPI Python application
│   ├── app/           # Main application code
│   ├── services/      # Business logic
│   └── security/      # Security modules
content/               # Training scenarios (YAML + docs)
tests/                 # Test suite
docs/                  # Documentation
scripts/               # Utility scripts
```

## 📚 Documentation

- [Technical Design](docs/technical-design.md) - System architecture
- [API Specification](docs/api-specification.md) - REST + WebSocket APIs
- [YAML Schema](docs/yaml-schema.md) - Scenario format
- [Security Requirements](docs/security-requirements.md) - Data protection
- [Testing Strategy](docs/test-strategy.md) - QA approach
- [Deployment Guide](docs/deployment-guide.md) - Setup instructions
- [Pilot User Guide](docs/pilot-user-guide.md) - End user instructions

## 🧪 Testing

### Automated Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories  
pytest tests/test_api.py -v           # API endpoints
pytest tests/test_websocket.py -v     # Real-time chat
pytest tests/test_integration.py -v   # End-to-end flows
```

### Manual Testing
```bash
# 5-user load test
python scripts/integration_test_enhanced.py --users 5

# System health check
make health
```

## 🛡️ Security

- **Data Masking**: Automatic PII protection (accounts, cards, emails, phones)
- **Input Validation**: XSS/injection prevention
- **Rate Limiting**: 20 requests/minute per user
- **Audit Logging**: Complete security event tracking

## 📈 Performance

- **Response Time**: <3 seconds validated
- **Concurrent Users**: 5 pilots supported
- **Database**: SQLite <1MB footprint
- **Cost**: ~$0.00015 per training message

## 🚢 Deployment

### Development
```bash
make dev
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Production
```bash
make build
make deploy
# Includes Docker, health monitoring, backup procedures
```

## 🔧 Troubleshooting

### Common Issues & Solutions

<details>
<summary><strong>🚫 Services won't start</strong></summary>

**Symptoms**: `make dev` fails or services don't respond

**Solutions**:
```bash
# 1. Check Docker is running
docker info

# 2. Check port availability  
lsof -i :3000  # Frontend port
lsof -i :8000  # Backend port

# 3. Clean and restart
make clean
make setup
make dev

# 4. Check logs for errors
make logs
```
</details>

<details>
<summary><strong>🔑 OpenAI API Issues</strong></summary>

**Symptoms**: Chat doesn't work, API errors in logs

**Solutions**:
```bash
# 1. Verify API key is set
cat .env | grep OPENAI_API_KEY

# 2. Test API key manually
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.openai.com/v1/models

# 3. Check API quota/billing
# Visit: https://platform.openai.com/usage
```
</details>

<details>
<summary><strong>🗄️ Database Connection Issues</strong></summary>

**Symptoms**: Database errors, session data not saving

**Solutions**:
```bash
# 1. Check database logs
make logs-db

# 2. Reset database (⚠️ destroys data)
make reset-db

# 3. Check file permissions
ls -la *.db
```
</details>

<details>
<summary><strong>🔗 WebSocket Connection Failures</strong></summary>

**Symptoms**: Chat interface not updating, connection drops

**Solutions**:
```bash
# 1. Check backend logs
make logs-backend

# 2. Verify WebSocket endpoint
curl -i -N \
     -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     http://localhost:8000/chat/stream

# 3. Check firewall/proxy settings
```
</details>

<details>
<summary><strong>📊 Performance Issues</strong></summary>

**Symptoms**: Slow responses, high CPU usage

**Solutions**:
```bash
# 1. Run performance check
make health

# 2. Check resource usage
docker stats

# 3. Run load test to identify bottlenecks
make test-load

# 4. Check OpenAI response times in logs
```
</details>

### Getting Help

1. **Check the logs**: `make logs` for all services
2. **Run health check**: `make health` for system status  
3. **Review documentation**: See [docs/](docs/) folder
4. **Check GitHub Issues**: Search existing issues
5. **Create new issue**: Include logs and system info

### Debug Mode
```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
make restart

# View detailed logs
make logs
```

## 🎯 Pilot Testing

### User Journey
1. Select training scenario
2. Complete 30-minute chat session
3. Receive feedback and scoring
4. Review reference documents
5. Export session summary

### Success Metrics
- 80%+ completion rate
- Meaningful feedback received
- <3 second response times
- Positive user experience

## 🔄 Content Updates

### Adding Scenarios
1. Create YAML file in `content/new_scenario/`
2. Add supporting documents (PDF/Markdown)
3. Validate: `python scripts/validate_scenarios.py`
4. Commit and deploy

### YAML Format
```yaml
id: "scenario_name_v1"
title: "Scenario Title"
duration_minutes: 30
bot_messages:
  - content: "Customer message"
    expected_keywords: ["help", "assist"]
llm_config:
  model: "gpt-4o-mini"
  temperature: 0.7
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup
```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/ChatTrain.git
cd ChatTrain

# 3. Add upstream remote
git remote add upstream https://github.com/kiwamust/ChatTrain.git

# 4. Create a feature branch  
git checkout -b feature/your-feature-name

# 5. Setup development environment
make setup
```

### Contribution Guidelines

#### Code Standards
- **Frontend**: Follow React/TypeScript best practices
- **Backend**: Follow FastAPI and Python PEP 8 standards
- **Documentation**: Update relevant docs for new features
- **Tests**: Add tests for new functionality
- **Commits**: Use conventional commit messages

#### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```bash
feat(chat): add typing indicator for AI responses
fix(security): improve PII masking regex patterns  
docs(readme): update installation instructions
test(api): add websocket connection tests
```

#### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add/update tests as needed
   - Update documentation

3. **Test Your Changes**
   ```bash
   make test           # Run all tests
   make health         # Health check
   make lint           # Code quality (if available)
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat(scope): your feature description"
   git push origin feature/your-feature
   ```

5. **Open Pull Request**
   - Use the provided PR template
   - Link related issues
   - Add screenshots for UI changes
   - Request review from maintainers

#### What to Contribute

**🎯 High Priority**
- Bug fixes and security improvements
- Performance optimizations  
- Test coverage improvements
- Documentation enhancements

**🌟 Feature Ideas**
- New training scenarios
- UI/UX improvements
- Additional language support
- Analytics and reporting features

**📝 Content Contributions**
- Training scenario YAML files
- Reference documents
- Translation improvements
- User guides and tutorials

### Code Review Process

1. **Automated Checks**: All PRs run automated tests
2. **Maintainer Review**: Core team reviews code quality
3. **Testing**: Features tested in development environment  
4. **Documentation**: Ensure docs are updated
5. **Merge**: Squash and merge with conventional commit message

### Questions or Issues?

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Bug Reports**: Create detailed GitHub Issues  
- 💡 **Feature Requests**: Submit GitHub Issues with enhancement label
- 📧 **Security Issues**: Email maintainers directly

### Recognition

Contributors are recognized in:
- README acknowledgments
- Release notes
- Contributor graphs
- Special recognition for major contributions

## 🏆 MVP1 Achievement

ChatTrain MVP1 successfully delivers:
- Complete AI training platform
- 5 pilot user capacity
- Production-ready security
- Comprehensive testing
- Easy deployment and maintenance

**Ready for pilot testing!** 🚀

---

<div align="center">

## 🌟 Star this repository if you find it helpful!

**ChatTrain MVP1** - Built with ❤️ for customer service excellence

[🐛 Report Bug](https://github.com/kiwamust/ChatTrain/issues) • [✨ Request Feature](https://github.com/kiwamust/ChatTrain/issues) • [📖 Documentation](docs/) • [💬 Discussions](https://github.com/kiwamust/ChatTrain/discussions)

**Made with:** React • FastAPI • OpenAI • Docker • TypeScript • Python

---

© 2024 ChatTrain. Released under the [MIT License](LICENSE).

</div>
