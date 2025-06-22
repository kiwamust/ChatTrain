"""
ChatTrain MVP1 Feedback Service
Simple keyword-based evaluation and feedback generation
"""
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime


class FeedbackService:
    """Provides simple evaluation and feedback for training sessions"""
    
    def __init__(self):
        # Define quality indicators for different scenarios
        self.quality_indicators = {
            "politeness": ["please", "thank you", "sorry", "apologize", "appreciate"],
            "empathy": ["understand", "hear you", "frustrating", "concern", "help"],
            "clarity": ["explain", "clarify", "specifically", "detail", "step"],
            "solution": ["resolve", "fix", "solution", "assist", "support", "troubleshoot"]
        }
        
    def evaluate_message(
        self,
        user_message: str,
        expected_keywords: List[str],
        scenario_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate user message based on keywords and quality indicators
        
        Args:
            user_message: The user's message to evaluate
            expected_keywords: Keywords expected for this scenario step
            scenario_context: Current scenario context
            
        Returns:
            Dict containing score, feedback, and suggestions
        """
        # Normalize message for comparison
        normalized_message = user_message.lower()
        
        # Calculate keyword matches
        keyword_matches = self._calculate_keyword_matches(normalized_message, expected_keywords)
        
        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(normalized_message)
        
        # Generate overall score (70-100 range)
        base_score = 70
        keyword_score = min(keyword_matches["match_percentage"] * 20, 20)  # Max 20 points
        quality_score = sum(quality_scores.values()) * 2.5  # Max 10 points (4 categories * 2.5)
        
        total_score = int(base_score + keyword_score + quality_score)
        total_score = min(total_score, 100)  # Cap at 100
        
        # Generate feedback
        feedback = self._generate_feedback(
            total_score,
            keyword_matches,
            quality_scores,
            expected_keywords
        )
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            keyword_matches,
            quality_scores,
            expected_keywords
        )
        
        return {
            "score": total_score,
            "feedback": feedback,
            "suggestions": suggestions,
            "details": {
                "keyword_matches": keyword_matches,
                "quality_scores": quality_scores,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _calculate_keyword_matches(self, message: str, expected_keywords: List[str]) -> Dict[str, Any]:
        """Calculate how many expected keywords were used"""
        if not expected_keywords:
            return {"matched": [], "missed": [], "match_percentage": 0}
        
        matched = []
        missed = []
        
        for keyword in expected_keywords:
            # Check for word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, message):
                matched.append(keyword)
            else:
                missed.append(keyword)
        
        match_percentage = (len(matched) / len(expected_keywords)) * 100 if expected_keywords else 0
        
        return {
            "matched": matched,
            "missed": missed,
            "match_percentage": match_percentage
        }
    
    def _calculate_quality_scores(self, message: str) -> Dict[str, float]:
        """Calculate quality scores for different communication aspects"""
        scores = {}
        
        for category, indicators in self.quality_indicators.items():
            found = 0
            for indicator in indicators:
                pattern = r'\b' + re.escape(indicator) + r'\b'
                if re.search(pattern, message):
                    found += 1
            
            # Score is percentage of indicators found (0-1)
            scores[category] = min(found / len(indicators), 1.0) if indicators else 0
        
        return scores
    
    def _generate_feedback(
        self,
        score: int,
        keyword_matches: Dict[str, Any],
        quality_scores: Dict[str, float],
        expected_keywords: List[str]
    ) -> str:
        """Generate constructive feedback based on evaluation"""
        feedback_parts = []
        
        # Overall performance
        if score >= 90:
            feedback_parts.append("Excellent response! You demonstrated strong communication skills.")
        elif score >= 80:
            feedback_parts.append("Good job! Your response was effective with room for minor improvements.")
        elif score >= 75:
            feedback_parts.append("Decent response. You covered the basics but could enhance your communication.")
        else:
            feedback_parts.append("Your response needs improvement to meet professional standards.")
        
        # Keyword usage feedback
        if keyword_matches["match_percentage"] >= 80:
            feedback_parts.append("You used relevant terminology effectively.")
        elif keyword_matches["match_percentage"] >= 50:
            feedback_parts.append(f"You included some key concepts ({', '.join(keyword_matches['matched'][:3])}).")
        else:
            feedback_parts.append("Consider using more specific terminology related to the issue.")
        
        # Quality feedback
        high_quality_areas = [k for k, v in quality_scores.items() if v >= 0.6]
        low_quality_areas = [k for k, v in quality_scores.items() if v < 0.3]
        
        if high_quality_areas:
            feedback_parts.append(f"Strengths: {', '.join(high_quality_areas)}.")
        
        if low_quality_areas:
            feedback_parts.append(f"Areas to improve: {', '.join(low_quality_areas)}.")
        
        return " ".join(feedback_parts)
    
    def _generate_suggestions(
        self,
        keyword_matches: Dict[str, Any],
        quality_scores: Dict[str, float],
        expected_keywords: List[str]
    ) -> List[str]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # Keyword suggestions
        if keyword_matches["missed"] and keyword_matches["match_percentage"] < 50:
            missed_sample = keyword_matches["missed"][:3]
            suggestions.append(
                f"Try incorporating terms like '{', '.join(missed_sample)}' to be more specific."
            )
        
        # Quality suggestions
        if quality_scores.get("politeness", 0) < 0.3:
            suggestions.append(
                "Add polite phrases like 'please' or 'thank you' to improve rapport."
            )
        
        if quality_scores.get("empathy", 0) < 0.3:
            suggestions.append(
                "Show more empathy by acknowledging the customer's feelings or frustration."
            )
        
        if quality_scores.get("clarity", 0) < 0.3:
            suggestions.append(
                "Be more specific and clear in your explanations. Use step-by-step instructions if needed."
            )
        
        if quality_scores.get("solution", 0) < 0.3:
            suggestions.append(
                "Focus more on providing concrete solutions or next steps to resolve the issue."
            )
        
        # If doing well, provide advanced tips
        if not suggestions:
            suggestions.append(
                "Great work! Try adding more personalization or asking follow-up questions to ensure understanding."
            )
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def generate_session_summary(self, messages: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary feedback for entire training session"""
        if not evaluations:
            return {
                "average_score": 0,
                "summary": "No evaluations available for this session.",
                "strengths": [],
                "improvements": []
            }
        
        # Calculate average score
        scores = [eval.get("score", 0) for eval in evaluations]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Identify trends
        all_quality_scores = [eval.get("details", {}).get("quality_scores", {}) for eval in evaluations]
        
        # Calculate average quality scores
        quality_averages = {}
        for category in self.quality_indicators.keys():
            category_scores = [qs.get(category, 0) for qs in all_quality_scores if qs]
            quality_averages[category] = sum(category_scores) / len(category_scores) if category_scores else 0
        
        # Identify strengths and weaknesses
        strengths = [k for k, v in quality_averages.items() if v >= 0.6]
        improvements = [k for k, v in quality_averages.items() if v < 0.4]
        
        # Generate summary
        if average_score >= 85:
            summary = "Excellent training session! You consistently demonstrated professional communication skills."
        elif average_score >= 75:
            summary = "Good training session. You showed solid communication skills with some areas for growth."
        else:
            summary = "This session highlighted several areas for improvement. Focus on the suggestions below."
        
        return {
            "average_score": round(average_score, 1),
            "summary": summary,
            "strengths": strengths,
            "improvements": improvements,
            "total_messages": len(messages),
            "total_evaluations": len(evaluations)
        }