# ChatTrain MVP1 🤖

AI-powered chat training platform for customer service excellence.

## 🎯 Overview

ChatTrain MVP1 enables 5 pilot users to complete 30-minute AI-powered training scenarios with real-time feedback. Built with React + FastAPI + OpenAI integration.

## ✨ Features

- **Real-time Chat Training**: Interactive scenarios with AI customers
- **Instant Feedback**: Keyword-based evaluation with improvement suggestions
- **Document Integration**: Reference materials displayed during training
- **Data Security**: Automatic PII masking for sensitive information
- **Scenario Management**: YAML-based content with Git workflow

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- OpenAI API key

### Setup (< 5 minutes)
```bash
# Clone and setup
git clone <your-repo-url>
cd ChatTrain

# Environment setup
make setup

# Configure API key
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY

# Start development
make dev

# Access at http://localhost:3000
```

## 📋 Training Scenarios

### 1. Insurance Claim Handling (30 min)
Customer files claim after car accident - practice empathy, information gathering, and next steps.

### 2. Customer Service Support (30 min)  
User experiencing login issues - practice troubleshooting, password reset, and technical support.

## 🏗️ Architecture

- **Frontend**: React + TypeScript (Port 3000)
- **Backend**: FastAPI + SQLite (Port 8000)
- **LLM**: OpenAI gpt-4o-mini integration
- **Security**: Regex-based PII masking
- **Content**: YAML scenario management

## 📊 MVP1 Success Criteria

- ✅ **5 pilot users** supported concurrently
- ✅ **2 scenarios × 30 minutes** training sessions
- ✅ **LLM feedback** with evaluation scores
- ✅ **Data masking** for sensitive information
- ✅ **<3 second** response times

## 🛠️ Available Commands

```bash
make setup      # Initial environment setup
make dev        # Start development servers
make test       # Run all tests
make build      # Build production images
make deploy     # Deploy to production
make health     # Check system status
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

## 📞 Support

### Pilot User Issues
1. Check [Troubleshooting Guide](docs/troubleshooting-guide.md)
2. Verify `.env` configuration
3. Run `make health` for system status

### Development Issues
- Ensure all dependencies installed: `make setup`
- Check service status: `make health`
- Review logs in `logs/` directory

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

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 🏆 MVP1 Achievement

ChatTrain MVP1 successfully delivers:
- Complete AI training platform
- 5 pilot user capacity
- Production-ready security
- Comprehensive testing
- Easy deployment and maintenance

**Ready for pilot testing!** 🚀

---
