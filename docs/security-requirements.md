# ChatTrain MVP1 Security Requirements and Data Masking Specification

## Overview

This document defines comprehensive security requirements and data masking specifications for ChatTrain MVP1. The system implements a "Retrieval-Only" approach with robust data redaction to ensure sensitive information never reaches external LLM services while maintaining training effectiveness.

## Security Architecture

### Defense in Depth Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  • Input validation • XSS prevention • CSRF protection     │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  • Authentication • Authorization • Rate limiting           │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Data Processing Layer                     │
│  • Input sanitization • Data masking • Content filtering   │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    RAG Engine Layer                         │
│  • Vector search • Context summarization • Token limiting  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   External LLM Layer                        │
│  • API key security • Rate limiting • Response validation  │
└─────────────────────────────────────────────────────────────┘
```

## Data Classification

### Sensitivity Levels

| Level | Description | Examples | Protection Requirements |
|-------|-------------|----------|------------------------|
| **Critical** | Regulated personal data | SSN, Credit cards, Medical records | Never transmitted to LLM |
| **Confidential** | Business sensitive | Customer names, Account numbers | Masked before transmission |
| **Internal** | Company information | Employee IDs, Internal codes | Context-dependent masking |
| **Public** | Non-sensitive data | Product names, General procedures | No masking required |

### Data Types in Scope

```python
SENSITIVE_DATA_TYPES = {
    # Personal Identifiable Information (PII)
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    'phone_number': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    
    # Financial Information
    'account_number': r'\b[A-Z]{2}\d{6,12}\b',
    'routing_number': r'\b\d{9}\b',
    'policy_number': r'\b[A-Z]{1,3}-?\d{6,10}\b',
    
    # Personal Names (context-aware)
    'person_name': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
    'customer_id': r'\bCUST\d{6,10}\b',
    
    # Addresses
    'street_address': r'\b\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b',
    'zip_code': r'\b\d{5}(-\d{4})?\b',
    
    # Medical Information
    'medical_record': r'\bMRN[-\s]?\d{6,10}\b',
    'prescription': r'\bRx[-\s]?\d{6,10}\b',
    
    # Government IDs
    'license_number': r'\b[A-Z]\d{7,12}\b',
    'passport': r'\b[A-Z]{1,2}\d{6,9}\b'
}
```

## Retrieval-Only RAG Architecture

### Process Flow

```python
def secure_rag_pipeline(user_query: str, scenario_id: str) -> str:
    """
    Secure RAG pipeline that never sends full documents to LLM
    """
    # 1. Query Processing
    sanitized_query = sanitize_input(user_query)
    
    # 2. Vector Search (Local)
    relevant_docs = vector_search(sanitized_query, scenario_id, k=3)
    
    # 3. Content Summarization (Local)
    summaries = []
    for doc in relevant_docs:
        # Extract key information locally
        summary = extract_key_points(doc.content, max_length=100)
        summaries.append(summary)
    
    # 4. Data Masking
    combined_context = " ".join(summaries)
    masked_context = apply_data_masking(combined_context)
    
    # 5. Final Validation
    validated_context = validate_no_sensitive_data(masked_context)
    
    return validated_context
```

### Vector Search Security

```python
class SecureVectorStore:
    """Secure vector store with access controls"""
    
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"
        self.max_results = 3
        self.max_context_tokens = 100
    
    async def search_documents(
        self,
        query_embedding: List[float],
        scenario_id: str,
        user_permissions: List[str]
    ) -> List[DocumentChunk]:
        """Search with permission-based filtering"""
        
        # 1. Validate user permissions
        if not self.has_scenario_access(scenario_id, user_permissions):
            raise PermissionError("Insufficient permissions for scenario")
        
        # 2. Execute vector search
        results = await self.vector_db.similarity_search(
            embedding=query_embedding,
            filter={"scenario_id": scenario_id},
            limit=self.max_results
        )
        
        # 3. Apply content filtering
        filtered_results = []
        for result in results:
            if self.is_content_allowed(result.content, user_permissions):
                filtered_results.append(result)
        
        return filtered_results
    
    def is_content_allowed(self, content: str, permissions: List[str]) -> bool:
        """Check if content is allowed for user"""
        sensitivity_level = self.classify_content_sensitivity(content)
        return sensitivity_level in permissions
```

## Data Masking Implementation

### Multi-Layer Masking Strategy

```python
class DataMaskingEngine:
    """Comprehensive data masking with multiple strategies"""
    
    def __init__(self):
        self.patterns = SENSITIVE_DATA_TYPES
        self.context_analyzer = ContextAnalyzer()
        self.whitelist = self.load_whitelist()
    
    def mask_content(self, text: str, context: str = None) -> MaskingResult:
        """Apply comprehensive data masking"""
        
        result = MaskingResult(original=text, masked=text, redactions=[])
        
        # 1. Regex-based pattern matching
        result = self.apply_regex_masking(result)
        
        # 2. Named Entity Recognition (NER)
        result = self.apply_ner_masking(result, context)
        
        # 3. Context-aware masking
        result = self.apply_contextual_masking(result, context)
        
        # 4. Whitelist validation
        result = self.apply_whitelist_filtering(result)
        
        # 5. Final validation
        self.validate_masking_effectiveness(result)
        
        return result
    
    def apply_regex_masking(self, result: MaskingResult) -> MaskingResult:
        """Apply regex-based masking patterns"""
        
        for data_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, result.masked, re.IGNORECASE)
            
            for match in matches:
                original_value = match.group(0)
                masked_value = self.generate_mask_token(data_type, original_value)
                
                result.masked = result.masked.replace(original_value, masked_value)
                result.redactions.append(Redaction(
                    type=data_type,
                    original=original_value,
                    masked=masked_value,
                    position=(match.start(), match.end()),
                    confidence=0.9
                ))
        
        return result
    
    def apply_ner_masking(self, result: MaskingResult, context: str) -> MaskingResult:
        """Apply Named Entity Recognition masking"""
        
        entities = self.ner_model.extract_entities(result.masked)
        
        for entity in entities:
            if entity.label in ['PERSON', 'ORG', 'GPE']:
                # Skip if in whitelist
                if entity.text.lower() in self.whitelist.get(entity.label, []):
                    continue
                
                masked_value = self.generate_mask_token(entity.label, entity.text)
                result.masked = result.masked.replace(entity.text, masked_value)
                
                result.redactions.append(Redaction(
                    type=entity.label,
                    original=entity.text,
                    masked=masked_value,
                    position=(entity.start, entity.end),
                    confidence=entity.confidence
                ))
        
        return result
    
    def generate_mask_token(self, data_type: str, original: str) -> str:
        """Generate appropriate mask token"""
        
        masks = {
            'ssn': '{{SSN}}',
            'credit_card': '{{CARD_NUMBER}}',
            'account_number': '{{ACCOUNT_ID}}',
            'person_name': '{{CUSTOMER_NAME}}',
            'email': '{{EMAIL_ADDRESS}}',
            'phone_number': '{{PHONE_NUMBER}}',
            'street_address': '{{ADDRESS}}',
            'policy_number': '{{POLICY_ID}}',
            'PERSON': '{{PERSON}}',
            'ORG': '{{ORGANIZATION}}',
            'GPE': '{{LOCATION}}'
        }
        
        return masks.get(data_type, f'{{{{{data_type.upper()}}}}}')
```

### Context-Aware Masking

```python
class ContextAnalyzer:
    """Analyze context to improve masking accuracy"""
    
    def __init__(self):
        self.business_contexts = {
            'insurance': ['policy', 'claim', 'premium', 'deductible'],
            'banking': ['account', 'routing', 'deposit', 'withdrawal'],
            'healthcare': ['patient', 'diagnosis', 'treatment', 'prescription']
        }
    
    def analyze_context(self, text: str) -> Dict[str, float]:
        """Determine business context of text"""
        
        context_scores = {}
        words = text.lower().split()
        
        for context, keywords in self.business_contexts.items():
            score = sum(1 for word in words if word in keywords)
            context_scores[context] = score / len(words)
        
        return context_scores
    
    def should_mask_entity(self, entity: str, context: Dict[str, float]) -> bool:
        """Determine if entity should be masked based on context"""
        
        # Example: Don't mask common company names in business context
        if context.get('insurance', 0) > 0.1 and entity in ['Allstate', 'Geico', 'Progressive']:
            return False
        
        # Default to masking for safety
        return True
```

## Security Controls

### Input Validation and Sanitization

```python
class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self):
        self.max_message_length = 2000
        self.allowed_file_types = ['.pdf', '.md', '.txt']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_user_message(self, message: str) -> ValidationResult:
        """Validate user chat message"""
        
        result = ValidationResult(valid=True, errors=[])
        
        # Length validation
        if len(message) > self.max_message_length:
            result.valid = False
            result.errors.append(f"Message too long: {len(message)} > {self.max_message_length}")
        
        # Content validation
        if self.contains_malicious_content(message):
            result.valid = False
            result.errors.append("Message contains potentially malicious content")
        
        # HTML/Script injection check
        if self.contains_html_injection(message):
            result.valid = False
            result.errors.append("Message contains HTML/script injection attempt")
        
        return result
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input text"""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove script tags
        text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        return text
```

### Rate Limiting and Abuse Prevention

```python
class RateLimiter:
    """Multi-tier rate limiting system"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.limits = {
            'messages_per_minute': 20,
            'sessions_per_hour': 5,
            'llm_calls_per_hour': 50,
            'failed_attempts_per_hour': 10
        }
    
    async def check_rate_limit(self, user_id: str, action: str) -> RateLimitResult:
        """Check if action is within rate limits"""
        
        key = f"rate_limit:{user_id}:{action}"
        window = self.get_window_duration(action)
        limit = self.limits.get(f"{action}_per_{window}", 100)
        
        # Use sliding window counter
        current_count = await self.get_sliding_window_count(key, window)
        
        if current_count >= limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                current=current_count,
                reset_time=self.get_reset_time(window)
            )
        
        # Increment counter
        await self.increment_counter(key, window)
        
        return RateLimitResult(
            allowed=True,
            limit=limit,
            current=current_count + 1,
            reset_time=self.get_reset_time(window)
        )
```

### Authentication and Authorization

```python
class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hour
        self.max_concurrent_sessions = 3
    
    async def authenticate_request(self, request: Request) -> AuthResult:
        """Authenticate incoming request"""
        
        # Extract session token
        session_token = self.extract_session_token(request)
        if not session_token:
            return AuthResult(authenticated=False, reason="No session token")
        
        # Validate session
        session = await self.validate_session(session_token)
        if not session:
            return AuthResult(authenticated=False, reason="Invalid session")
        
        # Check session timeout
        if self.is_session_expired(session):
            await self.invalidate_session(session_token)
            return AuthResult(authenticated=False, reason="Session expired")
        
        # Update last activity
        await self.update_session_activity(session_token)
        
        return AuthResult(authenticated=True, user_id=session.user_id)
    
    async def authorize_scenario_access(self, user_id: str, scenario_id: str) -> bool:
        """Check if user has access to specific scenario"""
        
        user_permissions = await self.get_user_permissions(user_id)
        scenario_requirements = await self.get_scenario_requirements(scenario_id)
        
        return self.has_required_permissions(user_permissions, scenario_requirements)
```

## LLM Security

### API Key Management

```python
class LLMSecurityManager:
    """Secure LLM API integration"""
    
    def __init__(self):
        self.api_keys = self.load_encrypted_keys()
        self.rate_limits = {
            'requests_per_minute': 60,
            'tokens_per_day': 50000
        }
    
    async def make_secure_llm_request(
        self,
        messages: List[Dict],
        context: str,
        user_id: str
    ) -> LLMResponse:
        """Make secure request to LLM service"""
        
        # 1. Pre-request validation
        await self.validate_request_limits(user_id)
        
        # 2. Content filtering
        filtered_messages = self.filter_sensitive_content(messages)
        filtered_context = self.apply_final_masking(context)
        
        # 3. Token counting and limiting
        total_tokens = self.count_tokens(filtered_messages, filtered_context)
        if total_tokens > 4000:  # Conservative limit
            raise SecurityError("Request exceeds token limit")
        
        # 4. Make request with monitoring
        start_time = time.time()
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=filtered_messages + [{"role": "system", "content": filtered_context}],
                max_tokens=500,
                temperature=0.7
            )
            
            # 5. Response validation
            validated_response = self.validate_llm_response(response)
            
            # 6. Audit logging
            await self.log_llm_interaction(
                user_id=user_id,
                request_tokens=total_tokens,
                response_tokens=response.usage.completion_tokens,
                duration=time.time() - start_time,
                status="success"
            )
            
            return validated_response
            
        except Exception as e:
            await self.log_llm_interaction(
                user_id=user_id,
                error=str(e),
                duration=time.time() - start_time,
                status="error"
            )
            raise
    
    def validate_llm_response(self, response) -> str:
        """Validate LLM response for safety"""
        
        content = response.choices[0].message.content
        
        # Check for potential data leakage
        if self.contains_sensitive_patterns(content):
            raise SecurityError("LLM response contains sensitive patterns")
        
        # Check for injection attempts
        if self.contains_injection_patterns(content):
            raise SecurityError("LLM response contains injection patterns")
        
        return content
```

### Prompt Injection Prevention

```python
class PromptInjectionDefense:
    """Defend against prompt injection attacks"""
    
    def __init__(self):
        self.injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything\s+above',
            r'new\s+instructions?:',
            r'system\s*:\s*you\s+are',
            r'["\']?\s*\+\s*["\']',  # String concatenation
            r'exec\(|eval\(|import\s+os',  # Code execution
        ]
    
    def detect_prompt_injection(self, user_input: str) -> InjectionDetectionResult:
        """Detect potential prompt injection attempts"""
        
        result = InjectionDetectionResult(detected=False, patterns=[])
        
        for pattern in self.injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                result.detected = True
                result.patterns.append(pattern)
        
        # Advanced detection using ML model
        ml_score = self.ml_injection_detector.predict(user_input)
        if ml_score > 0.8:
            result.detected = True
            result.ml_confidence = ml_score
        
        return result
    
    def sanitize_prompt(self, user_input: str) -> str:
        """Sanitize user input to prevent injection"""
        
        # Remove potential injection patterns
        sanitized = user_input
        for pattern in self.injection_patterns:
            sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)
        
        # Escape special characters
        sanitized = self.escape_special_characters(sanitized)
        
        # Truncate if too long
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."
        
        return sanitized
```

## Audit and Monitoring

### Security Event Logging

```python
class SecurityAuditLogger:
    """Comprehensive security event logging"""
    
    def __init__(self):
        self.logger = logging.getLogger('security_audit')
        self.alert_thresholds = {
            'failed_auth_attempts': 5,
            'rate_limit_violations': 10,
            'injection_attempts': 3
        }
    
    async def log_security_event(
        self,
        event_type: str,
        user_id: str = None,
        session_id: str = None,
        details: Dict = None,
        risk_level: str = 'LOW'
    ):
        """Log security event with structured data"""
        
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'session_id': session_id,
            'risk_level': risk_level,
            'details': details or {},
            'source_ip': self.get_client_ip(),
            'user_agent': self.get_user_agent()
        }
        
        self.logger.warning(json.dumps(event))
        
        # Check for alert conditions
        await self.check_alert_conditions(event_type, user_id)
    
    async def check_alert_conditions(self, event_type: str, user_id: str):
        """Check if security event should trigger alert"""
        
        threshold = self.alert_thresholds.get(event_type)
        if not threshold:
            return
        
        # Count recent events
        recent_count = await self.count_recent_events(event_type, user_id, minutes=60)
        
        if recent_count >= threshold:
            await self.send_security_alert(
                alert_type=f"THRESHOLD_EXCEEDED_{event_type}",
                user_id=user_id,
                count=recent_count,
                threshold=threshold
            )
```

### Data Masking Validation

```python
class MaskingValidator:
    """Validate effectiveness of data masking"""
    
    def __init__(self):
        self.test_patterns = self.load_test_patterns()
    
    def validate_masking_effectiveness(self, original: str, masked: str) -> ValidationReport:
        """Comprehensive validation of masking effectiveness"""
        
        report = ValidationReport()
        
        # 1. Pattern-based validation
        for pattern_name, pattern in SENSITIVE_DATA_TYPES.items():
            original_matches = re.findall(pattern, original)
            masked_matches = re.findall(pattern, masked)
            
            if masked_matches:
                report.add_failure(
                    f"Sensitive pattern '{pattern_name}' still present after masking",
                    original_matches=original_matches,
                    remaining_matches=masked_matches
                )
        
        # 2. Entropy analysis
        original_entropy = self.calculate_entropy(original)
        masked_entropy = self.calculate_entropy(masked)
        
        if masked_entropy > original_entropy * 0.8:
            report.add_warning("Masked text retains high entropy, may contain sensitive data")
        
        # 3. Known test data validation
        for test_data in self.test_patterns:
            if test_data in masked:
                report.add_failure(f"Test sensitive data '{test_data}' found in masked output")
        
        return report
    
    async def run_masking_test_suite(self) -> TestSuiteResult:
        """Run comprehensive test suite for masking"""
        
        test_cases = self.load_test_cases()
        results = []
        
        for test_case in test_cases:
            masking_result = self.masking_engine.mask_content(test_case.input)
            validation_report = self.validate_masking_effectiveness(
                test_case.input,
                masking_result.masked
            )
            
            results.append(TestResult(
                case_id=test_case.id,
                passed=validation_report.passed,
                failures=validation_report.failures,
                warnings=validation_report.warnings
            ))
        
        return TestSuiteResult(results)
```

## Compliance and Regulations

### GDPR Compliance

```python
class GDPRCompliance:
    """GDPR compliance utilities"""
    
    def __init__(self):
        self.personal_data_categories = [
            'names', 'email_addresses', 'phone_numbers', 
            'addresses', 'identification_numbers'
        ]
    
    def classify_personal_data(self, text: str) -> List[str]:
        """Classify types of personal data in text"""
        
        found_categories = []
        
        for category in self.personal_data_categories:
            if self.contains_personal_data_type(text, category):
                found_categories.append(category)
        
        return found_categories
    
    def generate_data_processing_record(
        self,
        user_id: str,
        data_types: List[str],
        purpose: str,
        legal_basis: str
    ) -> Dict:
        """Generate GDPR-compliant data processing record"""
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'data_categories': data_types,
            'processing_purpose': purpose,
            'legal_basis': legal_basis,
            'retention_period': '2_years',
            'data_subject_rights': [
                'access', 'rectification', 'erasure', 
                'portability', 'restriction'
            ]
        }
```

### Security Testing

```python
class SecurityTestSuite:
    """Automated security testing"""
    
    async def run_penetration_tests(self) -> List[TestResult]:
        """Run automated penetration tests"""
        
        tests = [
            self.test_sql_injection,
            self.test_xss_prevention,
            self.test_data_masking_effectiveness,
            self.test_rate_limiting,
            self.test_session_security,
            self.test_prompt_injection_defense
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                results.append(TestResult(
                    test_name=test.__name__,
                    passed=False,
                    error=str(e)
                ))
        
        return results
    
    async def test_data_masking_effectiveness(self) -> TestResult:
        """Test data masking with known sensitive data"""
        
        test_inputs = [
            "My SSN is 123-45-6789 and credit card is 4532-1234-5678-9012",
            "Contact John Doe at john.doe@email.com or 555-123-4567",
            "Account number AC-789456 for policy P-123456789"
        ]
        
        for test_input in test_inputs:
            masked = self.masking_engine.mask_content(test_input)
            
            # Verify no sensitive patterns remain
            validation = self.masking_validator.validate_masking_effectiveness(
                test_input, masked.masked
            )
            
            if not validation.passed:
                return TestResult(
                    test_name="data_masking_effectiveness",
                    passed=False,
                    details=validation.failures
                )
        
        return TestResult(
            test_name="data_masking_effectiveness",
            passed=True
        )
```

## Implementation Checklist

### Development Phase
- [ ] Implement data masking engine with regex patterns
- [ ] Add Named Entity Recognition (NER) for context-aware masking
- [ ] Implement retrieval-only RAG pipeline
- [ ] Add input validation and sanitization
- [ ] Implement rate limiting system
- [ ] Add security event logging
- [ ] Create masking test suite

### Testing Phase  
- [ ] Test all sensitive data patterns
- [ ] Validate masking effectiveness
- [ ] Test prompt injection defenses
- [ ] Verify rate limiting functionality
- [ ] Test session security
- [ ] Run penetration test suite

### Deployment Phase
- [ ] Configure secure API key storage
- [ ] Set up monitoring and alerting
- [ ] Enable audit logging
- [ ] Configure rate limits for production
- [ ] Set up backup and recovery
- [ ] Document security procedures

### Maintenance Phase
- [ ] Regular security audits
- [ ] Update masking patterns
- [ ] Monitor for new threats
- [ ] Review access logs
- [ ] Update dependencies
- [ ] Security training for team

---

This comprehensive security specification ensures ChatTrain MVP1 maintains the highest security standards while protecting sensitive data and preventing unauthorized access or data leakage.