# ChatTrain Scenario YAML Schema

## Overview

This document defines the YAML schema for ChatTrain training scenarios. Scenarios are defined using a structured YAML format that specifies learning objectives, LLM behavior, conversation flow, evaluation criteria, and supporting materials.

## Schema Definition

### Root Schema

```yaml
# Required: Unique identifier for the scenario
id: string

# Required: Semantic version (SemVer format)
version: string

# Required: Human-readable title
title: string

# Optional: Detailed description
description?: string

# Required: Domain classification
domain: string

# Optional: Difficulty level
difficulty?: "beginner" | "intermediate" | "advanced"

# Optional: Expected duration in minutes
duration_minutes?: number

# Optional: Tags for categorization
tags?: string[]

# Required: SMART learning goals (at least 1)
smart_goals:
  - S: string  # Specific
    M: string  # Measurable  
    A: string  # Achievable
    R: string  # Relevant
    T: string  # Time-bound

# Required: LLM configuration
llm_profile:
  model: string
  temperature: number  # 0.0 - 1.0
  max_tokens?: number
  system_prompt: string
  persona?: PersonaConfig

# Required: Conversation steps
steps: Step[]

# Optional: Session completion conditions
completion_conditions?: CompletionConfig

# Optional: A/B testing variants
variant?: "A" | "B"

# Optional: Supporting documents
attachments?: AttachmentConfig[]

# Optional: Metadata
metadata?: object
```

### PersonaConfig

```yaml
# LLM persona configuration
persona:
  # Required: Character name
  name: string
  
  # Optional: Background information
  background?: string
  
  # Optional: Emotional state
  emotional_state?: string
  
  # Optional: Knowledge level about the topic
  knowledge_level?: "novice" | "intermediate" | "expert"
  
  # Optional: Communication style
  communication_style?: string
  
  # Optional: Specific traits or characteristics
  traits?: string[]
  
  # Optional: Goals or motivations
  goals?: string[]
```

### Step

```yaml
# Required: Unique step identifier
id: string

# Required: Message sender role
role: "bot" | "user" | "system" | "feedback"

# Required for bot/system roles: Message content
message?: string

# Optional: Expected user actions (for user role steps)
expected_user_actions?: string[]

# Optional: Evaluation criteria
rubric?: RubricConfig

# Optional: Conditional logic
conditions?: ConditionConfig[]

# Optional: Attachments specific to this step
attachments?: AttachmentConfig[]

# Optional: Step metadata
metadata?: object
```

### RubricConfig

```yaml
# Evaluation rubric for user responses
rubric:
  # Required criteria that must be present
  must_include?: string[]
  
  # Preferred criteria (nice to have)
  nice_to_have?: string[]
  
  # Criteria that should be avoided
  should_avoid?: string[]
  
  # Minimum required score (0-100)
  minimum_score?: number
  
  # Custom evaluation prompts for GPT Judge
  custom_evaluation?: string
  
  # Weight for this step in overall scoring
  weight?: number
```

### ConditionConfig

```yaml
# Conditional logic for dynamic scenarios
conditions:
  # Condition type
  - type: "user_response_contains" | "step_score_above" | "session_time_elapsed"
    
    # Condition parameters
    params:
      # For user_response_contains
      keywords?: string[]
      
      # For step_score_above  
      threshold?: number
      
      # For session_time_elapsed
      minutes?: number
    
    # Action to take if condition is met
    action:
      type: "jump_to_step" | "end_session" | "show_hint"
      target?: string  # Step ID or message
```

### CompletionConfig

```yaml
# Session completion conditions
completion_conditions:
  # Completion type
  type: "all_steps_completed" | "minimum_score_reached" | "time_limit" | "user_chooses_exit"
  
  # Minimum overall score required (0-100)
  minimum_score?: number
  
  # Maximum session duration in minutes
  time_limit_minutes?: number
  
  # Allow early completion if conditions are met
  allow_early_completion?: boolean
```

### AttachmentConfig

```yaml
# Supporting documents and materials
attachments:
  - # Required: Filename
    filename: string
    
    # Required: File type
    type: "pdf" | "markdown" | "image" | "url"
    
    # Optional: Display title
    title?: string
    
    # Optional: Description
    description?: string
    
    # Required for URL type: External URL
    url?: string
    
    # Optional: When to show this attachment
    show_condition?: "always" | "on_step" | "on_demand"
    
    # Optional: Specific step ID when to show
    show_on_step?: string
```

## Complete Example

```yaml
id: "onboarding.claim_handling.v1"
version: "1.0.0"
title: "Insurance Claim Handling Basics"
description: "Learn to handle customer insurance claims with empathy and efficiency"
domain: "onboarding"
difficulty: "beginner"
duration_minutes: 30
tags: ["insurance", "customer-service", "claims"]

smart_goals:
  - S: "Handle an insurance claim inquiry from start to information gathering"
    M: "Successfully collect policy number, incident details, and contact information"
    A: "Using company guidelines and communication best practices"
    R: "To ensure customer satisfaction and accurate claim processing"
    T: "Within a 30-minute training session"

llm_profile:
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 200
  system_prompt: |
    You are Sarah Johnson, a customer who was recently in a car accident and needs to file an insurance claim.
    You are somewhat anxious about the process but cooperative. You have your policy information available.
    Respond naturally as if you're really in this situation.
  persona:
    name: "Sarah Johnson"
    background: "Office worker who was in a minor car accident yesterday"
    emotional_state: "anxious but hopeful"
    knowledge_level: "novice"
    communication_style: "direct but polite"
    traits: ["detail-oriented", "slightly worried", "wants clear guidance"]
    goals: ["get claim processed quickly", "understand next steps", "avoid complications"]

steps:
  - id: "step_1_greeting"
    role: "bot"
    message: "Hi, I was in a car accident yesterday and I need to file a claim. Can you help me with that?"
    rubric:
      must_include: ["empathy", "willingness_to_help", "next_steps"]
      nice_to_have: ["personal_greeting", "reassurance"]
      minimum_score: 70
      weight: 15

  - id: "step_2_policy_info"
    role: "user"
    expected_user_actions: ["ask_for_policy_number", "gather_basic_info"]
    rubric:
      must_include: ["policy_number_request", "incident_date_question"]
      nice_to_have: ["verification_method", "data_security_mention"]
      minimum_score: 80
      weight: 25

  - id: "step_3_policy_response"
    role: "bot"
    message: "Yes, my policy number is AC-789456. The accident happened yesterday around 3 PM."
    rubric:
      must_include: ["confirmation_of_info", "additional_questions"]
      nice_to_have: ["documentation_explanation", "timeline_setting"]
      minimum_score: 75
      weight: 20

  - id: "step_4_incident_details"
    role: "user"
    expected_user_actions: ["gather_incident_details", "ask_about_injuries", "location_details"]
    rubric:
      must_include: ["location_question", "other_parties_involved", "police_report"]
      nice_to_have: ["injury_concern", "property_damage_assessment"]
      should_avoid: ["rushed_questioning", "insensitive_language"]
      minimum_score: 85
      weight: 30

  - id: "step_5_details_response"
    role: "bot"
    message: "It happened on Highway 101 near the Main Street exit. There was another car involved - they rear-ended me at a red light. The police came and filed a report. I have some neck pain but nothing severe."
    conditions:
      - type: "user_response_contains"
        params:
          keywords: ["doctor", "medical", "injury"]
        action:
          type: "show_hint"
          target: "Great job showing concern for medical issues!"

  - id: "step_6_next_steps"
    role: "user"
    expected_user_actions: ["provide_next_steps", "set_expectations", "contact_information"]
    rubric:
      must_include: ["clear_next_steps", "timeline", "contact_method"]
      nice_to_have: ["documentation_needed", "claim_number_mention", "follow_up_schedule"]
      minimum_score: 80
      weight: 10

completion_conditions:
  type: "all_steps_completed"
  minimum_score: 75
  allow_early_completion: false

attachments:
  - filename: "claim_handling_guide.pdf"
    type: "pdf"
    title: "Claim Handling Procedures"
    description: "Official company guidelines for processing insurance claims"
    show_condition: "always"
    
  - filename: "empathy_phrases.md"
    type: "markdown"
    title: "Empathetic Communication Examples"
    description: "Sample phrases for showing empathy to customers"
    show_condition: "on_demand"
    
  - filename: "claim_form_example.pdf"
    type: "pdf"
    title: "Sample Claim Form"
    description: "Example of completed claim documentation"
    show_condition: "on_step"
    show_on_step: "step_6_next_steps"

variant: "A"

metadata:
  created_by: "T.Trainer"
  created_date: "2025-06-15"
  last_modified: "2025-06-20"
  review_status: "approved"
  target_audience: "new_customer_service_reps"
```

## Validation Rules

### Required Fields
- `id`: Must be unique across all scenarios
- `version`: Must follow SemVer format (e.g., "1.0.0")
- `title`: Must be 5-100 characters
- `domain`: Must be alphanumeric with underscores
- `smart_goals`: Must have at least one complete SMART goal
- `llm_profile`: Must include model, temperature, and system_prompt
- `steps`: Must have at least one step

### Data Type Validation
- `temperature`: Must be between 0.0 and 1.0
- `duration_minutes`: Must be positive integer
- `minimum_score`: Must be between 0 and 100
- `weight`: Must be positive number
- `version`: Must match semantic versioning pattern

### Business Logic Validation
- Step IDs must be unique within a scenario
- Referenced step IDs in conditions must exist
- Rubric weights should sum to 100 across all steps
- Bot steps must have message content
- User steps must have expected_user_actions or rubric

### File References
- All attachment filenames must exist in the scenario directory
- PDF files must be under 10MB
- Markdown files must be valid CommonMark
- Image files must be PNG, JPG, or SVG format

## Schema Evolution

### Version Compatibility
- Minor version changes (1.0.x): Backward compatible
- Major version changes (2.x.x): May require migration
- Schema versioning separate from scenario versioning

### Deprecated Fields
Fields marked as deprecated will be supported for 2 major versions before removal.

### Extension Points
- `metadata` field allows custom properties
- `conditions` system supports custom condition types
- `rubric.custom_evaluation` allows scenario-specific evaluation logic

---

This YAML schema provides the complete specification for defining ChatTrain training scenarios with full validation and TDD support.