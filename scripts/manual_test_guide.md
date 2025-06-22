# ChatTrain MVP1 Manual Test Guide

## Overview

This manual test guide provides step-by-step validation procedures for ChatTrain MVP1 pilot deployment. Use this guide to validate the system with real pilot users and ensure all MVP1 requirements are met.

---

## Pre-Test Setup

### System Requirements Check

**Before starting any tests, verify:**

1. **Environment Setup**
   ```bash
   # Check system is running
   curl http://localhost:8000/api/health
   # Expected: {"status":"healthy","timestamp":"...","version":"1.0.0"}
   ```

2. **Content Verification**
   ```bash
   # Check scenarios are loaded
   curl http://localhost:8000/api/scenarios
   # Expected: JSON array with at least 2 scenarios
   ```

3. **Database Connectivity**
   ```bash
   # Check content stats
   curl http://localhost:8000/api/content/stats
   # Expected: JSON with loader and file_server stats
   ```

### Test Data Preparation

**Required Scenarios:**
- ✅ `customer_service_v1` - Customer service training scenario
- ✅ `claim_handling_v1` - Claims processing training scenario  

**Required Documents per Scenario:**
- ✅ PDF guide (service manual, claim guide)
- ✅ Markdown examples (empathy examples, troubleshooting steps)

---

## Test Suite 1: Individual User Journey

### Test 1.1: Scenario Discovery and Selection

**Objective:** Validate user can discover and select training scenarios

**Steps:**
1. Open browser to `http://localhost:3000` (Frontend)
2. Navigate to scenario selection page
3. Verify scenarios are displayed with:
   - ✅ Scenario title
   - ✅ Description
   - ✅ Estimated duration
   - ✅ Difficulty level

**Expected Results:**
- [ ] Page loads within 3 seconds
- [ ] At least 2 scenarios visible
- [ ] All scenario metadata displayed correctly
- [ ] No JavaScript errors in console

**Success Criteria:** All checkboxes above ✅

---

### Test 1.2: Training Session Initialization

**Objective:** Validate user can start a training session

**Steps:**
1. Select "Customer Service" scenario
2. Click "Start Training Session"
3. Verify session setup:
   - ✅ Session ID generated
   - ✅ Chat interface loads
   - ✅ Document viewer loads
   - ✅ Reference materials accessible

**Expected Results:**
- [ ] Session starts within 5 seconds
- [ ] Chat interface is responsive
- [ ] Documents load correctly (PDF/MD)
- [ ] Split-pane interface works (resizable)

**Success Criteria:** All checkboxes above ✅

---

### Test 1.3: Complete Training Conversation

**Objective:** Validate 30-minute training session completion

**Scenario:** Customer Service Training Session

**Setup:**
- User: Pilot User 1
- Scenario: customer_service_v1
- Target: Complete 10+ message exchanges
- Duration: ~15-30 minutes

**Conversation Flow:**

| Step | User Action | Expected Bot Response | Validation |
|------|-------------|----------------------|------------|
| 1 | Type: "Hello! How can I help you today?" | Customer greeting + initial issue | ✅ Response within 3s |
| 2 | Show empathy + ask clarifying question | Customer provides more details | ✅ Feedback score ≥70 |
| 3 | Offer specific solution | Customer acceptance/question | ✅ Keywords detected |
| 4 | Confirm resolution + offer additional help | Customer satisfaction | ✅ Professional closure |
| 5+ | Continue conversation naturally | Varied customer responses | ✅ Consistent quality |

**Performance Tracking:**
- [ ] Each message receives feedback within 3 seconds
- [ ] Feedback includes score (0-100), comment, and keywords found
- [ ] Average feedback score ≥ 75
- [ ] At least 1 "improvement suggestion" provided
- [ ] No system errors or crashes

**Session Completion:**
- [ ] Session marked as "completed"
- [ ] Final summary generated with:
  - Total exchanges: ___
  - Average score: ___/100
  - Strengths identified: ___
  - Areas for improvement: ___
  - Overall assessment: ___

**Success Criteria:** All performance tracking items ✅ AND completion summary generated

---

### Test 1.4: Document Reference Integration

**Objective:** Validate document viewer integration during training

**Steps:**
1. During active training session
2. Open reference documents in right pane:
   - ✅ service_manual.pdf
   - ✅ empathy_examples.md
   - ✅ troubleshooting_steps.md

**Document Interaction Tests:**
- [ ] PDF loads and displays correctly
- [ ] Markdown renders with proper formatting
- [ ] Can navigate between documents
- [ ] Documents remain accessible during chat
- [ ] No performance degradation with documents open

**Referencing Workflow:**
1. Customer mentions "billing issue"
2. User opens troubleshooting_steps.md
3. User references specific steps in response
4. Verify: Response quality improves with document reference

**Success Criteria:** Documents load correctly AND can be referenced during conversation

---

## Test Suite 2: Multi-User Validation

### Test 2.1: Five Concurrent Pilot Users

**Objective:** Validate system handles 5 simultaneous users (MVP1 requirement)

**Setup:**
- 5 pilot users with different devices/browsers
- Staggered start times (30 seconds apart)
- Same scenario: customer_service_v1

**Execution:**

| User | Start Time | Browser | Expected Completion |
|------|------------|---------|-------------------|
| Pilot 1 | 10:00:00 | Chrome | 10:15:00 |
| Pilot 2 | 10:00:30 | Firefox | 10:15:30 |
| Pilot 3 | 10:01:00 | Safari | 10:16:00 |
| Pilot 4 | 10:01:30 | Edge | 10:16:30 |
| Pilot 5 | 10:02:00 | Chrome | 10:17:00 |

**Real-Time Monitoring:**
```bash
# Monitor system during test
watch -n 5 'curl -s http://localhost:8000/api/health && echo'
```

**Performance Validation:**
- [ ] All 5 users connect successfully
- [ ] No user experiences >3s response delays
- [ ] No system crashes or errors
- [ ] Database handles concurrent writes
- [ ] Memory usage remains stable

**Individual User Verification:**
- [ ] User 1: Completes ≥8 exchanges
- [ ] User 2: Completes ≥8 exchanges  
- [ ] User 3: Completes ≥8 exchanges
- [ ] User 4: Completes ≥8 exchanges
- [ ] User 5: Completes ≥8 exchanges

**Success Criteria:** All users complete successfully with acceptable performance

---

### Test 2.2: Sequential Session Testing

**Objective:** Validate multiple sessions per user across scenarios

**User Journey:**
1. **Pilot User 1 - Session 1:**
   - Scenario: customer_service_v1
   - Duration: ~15 minutes
   - Target: Complete successfully

2. **Pilot User 1 - Session 2:**
   - Scenario: claim_handling_v1  
   - Duration: ~15 minutes
   - Target: Apply learnings from Session 1

**Validation Points:**
- [ ] User can start Session 2 immediately after Session 1
- [ ] Performance data from Session 1 is saved
- [ ] Session 2 shows improvement indicators
- [ ] Different scenario content loads correctly
- [ ] User maintains context between sessions

**Cross-Session Analysis:**
- Session 1 avg score: ___/100
- Session 2 avg score: ___/100
- Improvement: ___% 
- Skills transfer evident: [ ] Yes [ ] No

**Success Criteria:** User completes both sessions AND shows measurable improvement

---

## Test Suite 3: System Validation

### Test 3.1: Performance Under Load

**Objective:** Validate system performance meets MVP1 requirements

**Load Test Setup:**
```bash
# Run automated load test
cd scripts/
python load_test.py --users 5 --duration 300
```

**Manual Performance Validation:**

**Response Time Checks:**
- [ ] Health endpoint: <1s response
- [ ] Scenario loading: <2s response
- [ ] Session creation: <2s response
- [ ] WebSocket connection: <1s establish
- [ ] Chat message response: <3s average

**Resource Monitoring:**
```bash
# Monitor during load test
htop  # CPU/Memory usage
netstat -an | grep :8000  # Connection count
```

**Acceptance Thresholds:**
- [ ] CPU usage <80% under load
- [ ] Memory usage <2GB under load
- [ ] Response time 95th percentile <5s
- [ ] Error rate <5% under load
- [ ] System remains stable for 30+ minutes

**Success Criteria:** All thresholds met under 5-user concurrent load

---

### Test 3.2: Data Integrity and Security

**Objective:** Validate data handling and security measures

**Data Flow Validation:**
1. **Message Storage:**
   - Send test message with sensitive data: "My account AC-123456"
   - Verify: Database stores masked version: "My account {{ACCOUNT}}"
   - Check: Original sensitive data not in logs

2. **Session Persistence:**
   - Create session, add 5 messages
   - Disconnect and reconnect
   - Verify: All messages restored correctly
   - Check: Session state maintained

3. **Feedback Generation:**
   - Send message with expected keywords
   - Verify: Feedback identifies keywords correctly
   - Check: Scoring algorithm consistency

**Security Validation:**
- [ ] Sensitive data masked in database
- [ ] Sensitive data masked in logs  
- [ ] API endpoints return appropriate errors for invalid data
- [ ] WebSocket connections validated properly
- [ ] No sensitive data in client-side console

**Success Criteria:** All data properly masked AND session integrity maintained

---

### Test 3.3: Error Handling and Recovery

**Objective:** Validate graceful error handling

**Simulated Failure Scenarios:**

1. **Network Interruption:**
   - Disconnect internet during active chat
   - Reconnect after 30 seconds
   - Verify: Session resumes gracefully
   - Check: No data loss

2. **High Latency Simulation:**
   ```bash
   # Simulate network delay (Linux/Mac)
   sudo tc qdisc add dev lo root netem delay 2000ms
   ```
   - Continue conversation with 2s delay
   - Verify: System remains usable
   - Check: Appropriate loading indicators

3. **Invalid Input Handling:**
   - Send malformed JSON to WebSocket
   - Send extremely long messages (>10KB)
   - Send special characters/emoji
   - Verify: System handles gracefully

**Recovery Validation:**
- [ ] User can continue after network interruption
- [ ] System provides meaningful error messages
- [ ] No crashes or data corruption
- [ ] Performance degrades gracefully under stress
- [ ] System auto-recovers when conditions improve

**Success Criteria:** System handles all error scenarios gracefully

---

## Test Suite 4: User Acceptance Testing

### Test 4.1: Pilot User Feedback Collection

**Objective:** Gather qualitative feedback from real pilot users

**User Experience Survey:**

**Scenario Completion Assessment:**
- [ ] Scenario instructions were clear
- [ ] Training content felt realistic
- [ ] Difficulty level was appropriate
- [ ] Duration felt reasonable (15-30 min)

**Interface Usability:**
- [ ] Chat interface was intuitive
- [ ] Document viewer was helpful
- [ ] Split-pane layout worked well
- [ ] Navigation was straightforward

**Feedback Quality:**
- [ ] Feedback felt relevant and helpful
- [ ] Scoring made sense
- [ ] Suggestions were actionable
- [ ] Real-time feedback enhanced learning

**Overall Satisfaction:**
Rate 1-5 (5 = Excellent):
- Ease of use: ___/5
- Content quality: ___/5  
- Technical performance: ___/5
- Learning value: ___/5
- Likelihood to recommend: ___/5

**Open Feedback:**
- What worked best? ___
- What needs improvement? ___
- Technical issues encountered? ___
- Feature requests? ___

**Success Criteria:** Average rating ≥4.0 across all categories

---

### Test 4.2: Training Effectiveness Validation

**Objective:** Validate training achieves learning objectives

**Pre/Post Assessment:**

**Before Training:**
- Customer service confidence (1-10): ___
- Familiarity with empathy techniques (1-10): ___
- Problem-solving approach confidence (1-10): ___

**After Training:**
- Customer service confidence (1-10): ___
- Familiarity with empathy techniques (1-10): ___
- Problem-solving approach confidence (1-10): ___

**Skill Demonstration:**
Present pilot user with new customer scenario (not from training):
- [ ] Demonstrates empathy appropriately
- [ ] Asks clarifying questions
- [ ] Provides structured solution
- [ ] Maintains professional tone
- [ ] Achieves customer satisfaction

**Performance Metrics:**
- Pre-training simulation score: ___/100
- Post-training simulation score: ___/100
- Improvement: ___%
- Target: ≥15% improvement

**Success Criteria:** Average improvement ≥15% AND demonstrated skill transfer

---

## Test Suite 5: Production Readiness

### Test 5.1: Deployment Validation

**Objective:** Validate system ready for pilot deployment

**Environment Checks:**
- [ ] Production database configured
- [ ] SSL certificates installed
- [ ] Environment variables secured
- [ ] Logging configured properly
- [ ] Monitoring tools active

**Backup and Recovery:**
- [ ] Database backup tested
- [ ] Recovery procedure documented
- [ ] Rollback plan prepared
- [ ] Data retention policy implemented

**Security Hardening:**
- [ ] API rate limiting active
- [ ] Input validation comprehensive
- [ ] Error messages don't expose internals
- [ ] Access controls implemented

**Success Criteria:** All production checklist items completed

---

### Test 5.2: Go/No-Go Decision Matrix

**MVP1 Pilot Launch Readiness:**

| Category | Requirement | Status | Notes |
|----------|-------------|---------|-------|
| **Core Functionality** | 4 API endpoints working | ✅/❌ | |
| | WebSocket chat functional | ✅/❌ | |
| | Document viewing works | ✅/❌ | |
| | Session management works | ✅/❌ | |
| **Performance** | <3s response times | ✅/❌ | |
| | 5 concurrent users supported | ✅/❌ | |
| | System stable under load | ✅/❌ | |
| **User Experience** | Pilot users complete training | ✅/❌ | |
| | Feedback quality acceptable | ✅/❌ | |
| | User satisfaction ≥4.0/5 | ✅/❌ | |
| **Data & Security** | Sensitive data masked | ✅/❌ | |
| | Error handling graceful | ✅/❌ | |
| | Data integrity maintained | ✅/❌ | |
| **Content Management** | 2+ scenarios available | ✅/❌ | |
| | Documents load correctly | ✅/❌ | |
| | Content updates working | ✅/❌ | |

**Go/No-Go Decision:**
- **GO:** ≥95% of requirements ✅ (allow 1-2 minor issues)
- **NO-GO:** <95% of requirements ✅ (address critical issues first)

**Decision:** [ ] GO [ ] NO-GO

**Signature:** _________________ Date: _________

---

## Appendix A: Test Data Requirements

### Sample User Messages
```
- "Hello! How can I help you today?"
- "I understand your frustration. Let me look into that for you."
- "Can you provide me with your account number so I can assist you better?"
- "I've found the issue and here's how we can resolve it..."
- "Is there anything else I can help you with today?"
```

### Expected Bot Responses
```
- "Hi, I'm having trouble accessing my account."
- "I keep getting an error message when I try to log in."
- "My account number is AC-123456."
- "Yes, that sounds like it should work. Let me try that."
- "Thank you so much! You've been very helpful."
```

### Test Scenarios
1. **Account Access Issues** - Password reset, account lockout
2. **Billing Inquiries** - Incorrect charges, payment methods
3. **Technical Support** - Website issues, app problems
4. **Service Requests** - Feature requests, account changes

---

## Appendix B: Troubleshooting Guide

### Common Issues and Solutions

**Issue:** WebSocket connection fails
**Solution:** Check firewall settings, verify port 8000 accessible

**Issue:** Documents don't load
**Solution:** Verify content directory exists, check file permissions

**Issue:** Slow response times
**Solution:** Check database performance, restart services if needed

**Issue:** Feedback not generating
**Solution:** Verify LLM service configuration, check API keys

**Issue:** Session data not persisting
**Solution:** Check database connectivity, verify table schemas

---

## Appendix C: Success Metrics Summary

**Technical Metrics:**
- ✅ API response time <3s (95th percentile)
- ✅ WebSocket connection time <1s
- ✅ 5 concurrent users supported
- ✅ Error rate <5% under load
- ✅ 99% uptime during testing

**User Experience Metrics:**
- ✅ User satisfaction ≥4.0/5
- ✅ Task completion rate ≥90%
- ✅ Training effectiveness ≥15% improvement
- ✅ Support ticket volume <5% of sessions

**Content Quality Metrics:**
- ✅ Feedback relevance score ≥4.0/5
- ✅ Keyword detection accuracy ≥80%
- ✅ Response variety (no repetitive feedback)
- ✅ Learning objective coverage 100%

**Success Criteria:** All metrics above thresholds = MVP1 READY ✅