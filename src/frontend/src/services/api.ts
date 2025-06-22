// API client with mock services for development
import type { Scenario, Session } from '../types';

// Mock API for development
export const mockAPI = {
  getScenarios: (): Promise<{ scenarios: Scenario[] }> => 
    Promise.resolve({
      scenarios: [
        { 
          id: "customer_service_v1", 
          title: "Customer Service Training",
          description: "Handle customer inquiries professionally",
          documents: ["service_guide.pdf", "scripts.md"] 
        },
        { 
          id: "technical_support_v1", 
          title: "Technical Support Training", 
          description: "Resolve technical issues effectively",
          documents: ["tech_manual.pdf", "troubleshooting.md"]
        },
        { 
          id: "sales_training_v1", 
          title: "Sales Training", 
          description: "Master sales techniques and customer engagement",
          documents: ["sales_guide.pdf", "objection_handling.md"]
        }
      ]
    }),
    
  createSession: (_scenarioId: string, _userId: string): Promise<Session> => 
    Promise.resolve({ 
      session_id: `mock-session-${Date.now()}`,
      websocket_url: `ws://localhost:8000/chat/mock-session-${Date.now()}`
    })
};

// Mock WebSocket for development
export class MockWebSocket {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  
  constructor(url: string) {
    console.log("Mock WebSocket created for:", url);
    setTimeout(() => this.onopen?.(), 100);
  }
  
  send(data: string) {
    console.log("Mock WS send:", data);
    const message = JSON.parse(data);
    
    // Simulate server responses based on message type
    setTimeout(() => {
      if (message.type === "user_message") {
        const responses = [
          "I'm experiencing issues with my account and need help resetting my password.",
          "The product I received is damaged. What should I do?",
          "I've been waiting for my order for 2 weeks. Can you check the status?",
          "Your service has been terrible! I want to speak to a manager!",
          "Thank you for your help. The solution worked perfectly!"
        ];
        
        const feedbackComments = [
          "Good response! Try to include more empathy.",
          "Excellent! You showed understanding and provided a clear solution.",
          "Consider asking clarifying questions before proposing a solution.",
          "Great job staying calm and professional.",
          "Perfect! You handled the situation with expertise."
        ];
        
        this.onmessage?.({
          data: JSON.stringify({
            type: "assistant_message",
            content: responses[Math.floor(Math.random() * responses.length)],
            feedback: {
              score: Math.floor(Math.random() * 30) + 70, // 70-100
              comment: feedbackComments[Math.floor(Math.random() * feedbackComments.length)],
              found_keywords: ["help", "assist", "resolve", "understand"]
            }
          })
        } as MessageEvent);
      }
    }, 1000 + Math.random() * 1000); // 1-2 second delay
  }
  
  close() {
    console.log("Mock WebSocket closed");
    this.onclose?.();
  }
}

// Export the API based on environment
export const api = mockAPI; // In production, this would switch to real API