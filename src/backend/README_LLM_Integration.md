# ChatTrain MVP1 - LLM Integration Guide

## Overview
This document explains the LLM (Large Language Model) integration for ChatTrain MVP1, which provides realistic AI-powered training conversations and automated evaluation feedback.

## Architecture

### Core Services

1. **LLMService** (`app/services/llm_service.py`)
   - Manages OpenAI API integration
   - Handles conversation generation
   - Provides mock mode for development
   - Implements rate limiting and error handling

2. **FeedbackService** (`app/services/feedback_service.py`)
   - Keyword-based evaluation system
   - Scores user responses (70-100 range)
   - Generates constructive feedback
   - Provides improvement suggestions

3. **PromptBuilder** (`app/services/prompt_builder.py`)
   - Constructs scenario-specific system prompts
   - Formats conversation history
   - Manages context for different training scenarios

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Required for real LLM responses
OPENAI_API_KEY=your_openai_api_key_here

# Optional configurations
OPENAI_MODEL=gpt-4o-mini  # Cost-effective model
MAX_TOKENS=200            # Response length limit
TEMPERATURE=0.7           # Response creativity (0-1)
```

### 3. Running in Mock Mode
If no API key is provided, the system automatically runs in mock mode:
- Provides contextual mock responses
- Still performs evaluation and feedback
- Useful for development and testing

## Usage Flow

### 1. User sends message via WebSocket
```json
{
  "type": "user_message",
  "content": "I understand your frustration. Let me help you reset your password."
}
```

### 2. System generates AI response
The LLM service:
- Builds scenario-specific prompt
- Includes conversation history
- Calls OpenAI API (or mock)
- Returns realistic response

### 3. Evaluation feedback
The system evaluates the user's message and sends:
```json
{
  "type": "evaluation_feedback",
  "score": 85,
  "content": "Good job! Your response was effective...",
  "suggestions": [
    "Try incorporating terms like 'verify' to be more specific."
  ]
}
```

## Testing

### Unit Tests
Test individual services:
```bash
python test_llm_integration.py
```

### Integration Tests
Test WebSocket + LLM flow:
```bash
# Start the server first
python run_dev.py

# In another terminal
python test_websocket_llm.py
```

## Scenario Configuration

Scenarios define the training context and expected behaviors:

```python
{
    "title": "Customer Service Training",
    "config_json": {
        "description": "Practice handling customer complaints",
        "objectives": [
            "Handle complaints professionally",
            "Show empathy",
            "Provide solutions"
        ]
    }
}
```

## Evaluation System

### Scoring Components
1. **Base Score**: 70 points (everyone starts here)
2. **Keyword Match**: Up to 20 points
3. **Quality Indicators**: Up to 10 points
   - Politeness
   - Empathy
   - Clarity
   - Solution-oriented

### Expected Keywords
Keywords are dynamically determined based on:
- Scenario type
- Conversation context
- Current topic (e.g., password reset, refund, technical issue)

## API Response Format

### LLM Response Structure
```python
{
    "content": "Thank you for verifying that...",  # AI response
    "evaluation": {
        "score": 85,
        "feedback": "Good job! Your response...",
        "suggestions": ["Try incorporating..."],
        "details": {
            "keyword_matches": {...},
            "quality_scores": {...}
        }
    },
    "metadata": {
        "model": "gpt-4o-mini",
        "tokens": 156,
        "timestamp": "2025-06-22T10:00:00Z"
    }
}
```

## Cost Management

### Token Limits
- Responses limited to 200 tokens (configurable)
- Approximately $0.00015 per request with gpt-4o-mini
- 1000 training messages ≈ $0.15

### Rate Limiting
- Minimum 1 second between API calls
- Automatic retry with exponential backoff
- Graceful fallback to mock mode on errors

## Best Practices

1. **Scenario Design**
   - Provide clear objectives
   - Include realistic context
   - Define expected behaviors

2. **Keyword Selection**
   - Use domain-specific terms
   - Include action words
   - Balance specificity with flexibility

3. **Feedback Quality**
   - Keep feedback constructive
   - Provide specific examples
   - Limit to 3 suggestions maximum

## Troubleshooting

### Common Issues

1. **"Using mock mode" message**
   - Ensure OPENAI_API_KEY is set in .env
   - Check API key validity

2. **Rate limit errors**
   - System handles automatically
   - Consider upgrading OpenAI tier if persistent

3. **Low evaluation scores**
   - Review expected keywords
   - Check scenario configuration
   - Ensure proper context is provided

## Future Enhancements

1. **Advanced Evaluation**
   - Sentiment analysis
   - Grammar checking
   - Contextual understanding

2. **Model Options**
   - Support for GPT-4
   - Custom fine-tuned models
   - Alternative LLM providers

3. **Analytics**
   - Token usage tracking
   - Performance metrics
   - Learning progress tracking

## Security Notes

- API keys are never logged or exposed
- All LLM requests are server-side only
- User data is not sent to OpenAI for training
- Conversation history is stored locally only

## Support

For issues or questions:
1. Check the test scripts for examples
2. Review error logs in the console
3. Verify environment configuration
4. Test in mock mode first