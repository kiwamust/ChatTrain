"""
ChatTrain MVP1 Prompt Builder Service
Constructs prompts for OpenAI API based on scenario context
"""
import json
from typing import List, Dict, Any, Optional


class PromptBuilder:
    """Builds prompts for LLM interactions based on scenario context"""
    
    def __init__(self):
        self.default_system_prompt = """You are a professional training partner helping users practice real-world conversation scenarios. 
Your role is to simulate realistic interactions based on the given scenario while maintaining appropriate professionalism and context."""
    
    def build_system_prompt(self, scenario: Optional[Dict[str, Any]] = None) -> str:
        """
        Build system prompt based on scenario configuration
        
        Args:
            scenario: Scenario configuration dict containing title, config_json, etc.
            
        Returns:
            System prompt string for the LLM
        """
        if not scenario:
            return self.default_system_prompt
        
        # Parse scenario config if it's JSON string
        config = scenario.get("config_json", {})
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}
        
        scenario_title = scenario.get("title", "Training Scenario")
        description = config.get("description", "")
        objectives = config.get("objectives", [])
        
        # Build scenario-specific system prompt
        prompt_parts = [
            f"You are a professional training partner for a {scenario_title} scenario.",
            ""
        ]
        
        if description:
            prompt_parts.append(f"Scenario Description: {description}")
            prompt_parts.append("")
        
        if objectives:
            prompt_parts.append("Training Objectives:")
            for obj in objectives:
                prompt_parts.append(f"- {obj}")
            prompt_parts.append("")
        
        # Add role-specific instructions based on scenario type
        if "customer service" in scenario_title.lower():
            prompt_parts.extend([
                "You are playing the role of a customer who needs assistance.",
                "Express realistic concerns, frustrations, or questions that a customer might have.",
                "Respond naturally to the trainee's attempts to help you.",
                "If the trainee provides good service, acknowledge it. If they don't address your concerns, express appropriate dissatisfaction.",
                "Stay in character throughout the conversation."
            ])
        elif "technical support" in scenario_title.lower():
            prompt_parts.extend([
                "You are playing the role of a user experiencing technical issues.",
                "Describe your technical problems in a way that a typical user would (not necessarily using technical terms correctly).",
                "Provide additional details when asked, but don't volunteer all information at once.",
                "Show appropriate frustration if the issue has been ongoing, but remain cooperative.",
                "Follow the trainee's troubleshooting steps and provide realistic feedback on whether they work."
            ])
        else:
            prompt_parts.extend([
                "Engage in realistic conversation based on the scenario context.",
                "Provide appropriate responses that challenge the trainee to demonstrate their skills.",
                "Stay in character and maintain consistency throughout the interaction.",
                "React naturally to the trainee's communication style and solutions."
            ])
        
        prompt_parts.extend([
            "",
            "Remember to:",
            "- Maintain a realistic persona throughout the conversation",
            "- Provide appropriate emotional responses",
            "- Give the trainee opportunities to demonstrate their skills",
            "- Stay focused on the training scenario"
        ])
        
        return "\n".join(prompt_parts)
    
    def build_conversation_messages(
        self, 
        system_prompt: str,
        recent_messages: List[Dict[str, Any]], 
        current_message: str
    ) -> List[Dict[str, str]]:
        """
        Build conversation message list for OpenAI API
        
        Args:
            system_prompt: System prompt for the conversation
            recent_messages: List of recent messages from database
            current_message: Current user message to respond to
            
        Returns:
            List of message dicts formatted for OpenAI API
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in recent_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Map database roles to OpenAI roles
            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": content})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def build_evaluation_prompt(
        self,
        user_message: str,
        expected_keywords: List[str],
        conversation_context: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for evaluating user's message
        
        Args:
            user_message: The user's message to evaluate
            expected_keywords: Keywords expected in a good response
            conversation_context: Recent conversation history
            
        Returns:
            Evaluation prompt string
        """
        context_summary = self._summarize_conversation(conversation_context)
        
        prompt = f"""Evaluate this customer service response based on the conversation context.

Conversation Context:
{context_summary}

User's Response:
"{user_message}"

Expected Keywords/Concepts: {', '.join(expected_keywords)}

Provide a brief evaluation covering:
1. Did they address the customer's concern?
2. Was their tone appropriate and professional?
3. Did they use relevant keywords or concepts?
4. What could be improved?

Keep the evaluation constructive and under 100 words."""
        
        return prompt
    
    def _summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Summarize recent conversation for context"""
        if not messages:
            return "Start of conversation"
        
        summary_parts = []
        for msg in messages[-3:]:  # Last 3 messages for context
            role = "Customer" if msg.get("role") == "assistant" else "Trainee"
            content = msg.get("content", "")[:100]  # Truncate long messages
            summary_parts.append(f"{role}: {content}...")
        
        return "\n".join(summary_parts)