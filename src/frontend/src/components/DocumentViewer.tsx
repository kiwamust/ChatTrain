// Document viewer component for displaying reference materials
import React, { useState } from 'react';
import './DocumentViewer.css';

interface DocumentViewerProps {
  documents: string[];
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({ documents }) => {
  const [activeDoc, setActiveDoc] = useState(0);

  // Mock document content based on filename
  const getDocumentContent = (filename: string) => {
    const mockContents: { [key: string]: JSX.Element } = {
      'service_guide.pdf': (
        <div className="mock-document">
          <h2>Customer Service Guide</h2>
          <h3>1. Greeting Customers</h3>
          <p>Always begin with a warm, professional greeting:</p>
          <ul>
            <li>"Good morning/afternoon, thank you for contacting us."</li>
            <li>"How may I assist you today?"</li>
          </ul>
          
          <h3>2. Active Listening</h3>
          <p>Key techniques:</p>
          <ul>
            <li>Let the customer finish speaking</li>
            <li>Ask clarifying questions</li>
            <li>Summarize their concerns</li>
          </ul>
          
          <h3>3. Problem Resolution</h3>
          <p>Follow the STAR method:</p>
          <ul>
            <li><strong>S</strong>ituation - Understand the issue</li>
            <li><strong>T</strong>ask - Identify what needs to be done</li>
            <li><strong>A</strong>ction - Take appropriate steps</li>
            <li><strong>R</strong>esult - Ensure customer satisfaction</li>
          </ul>
        </div>
      ),
      'scripts.md': (
        <div className="mock-document">
          <h2>Common Response Scripts</h2>
          <h3>Handling Complaints</h3>
          <p><strong>Template:</strong> "I understand your frustration, and I sincerely apologize for the inconvenience. Let me look into this right away and find a solution for you."</p>
          
          <h3>Technical Issues</h3>
          <p><strong>Template:</strong> "I'd be happy to help you resolve this technical issue. Can you please provide me with [specific information needed]?"</p>
          
          <h3>Billing Inquiries</h3>
          <p><strong>Template:</strong> "I'll review your account details to clarify this billing matter. May I have your account number or email address associated with the account?"</p>
        </div>
      ),
      'tech_manual.pdf': (
        <div className="mock-document">
          <h2>Technical Support Manual</h2>
          <h3>Common Issues and Solutions</h3>
          <h4>Login Problems</h4>
          <ol>
            <li>Verify username/email is correct</li>
            <li>Check CAPS LOCK key</li>
            <li>Reset password if needed</li>
            <li>Clear browser cache and cookies</li>
          </ol>
          
          <h4>Performance Issues</h4>
          <ol>
            <li>Check internet connection speed</li>
            <li>Update to latest software version</li>
            <li>Restart device</li>
            <li>Check system requirements</li>
          </ol>
        </div>
      ),
      'troubleshooting.md': (
        <div className="mock-document">
          <h2>Troubleshooting Guide</h2>
          <h3>Step-by-Step Procedures</h3>
          <h4>Error Code Reference</h4>
          <ul>
            <li><strong>Error 401:</strong> Authentication failed - Reset credentials</li>
            <li><strong>Error 404:</strong> Resource not found - Verify URL/path</li>
            <li><strong>Error 500:</strong> Server issue - Wait and retry</li>
          </ul>
          
          <h4>Diagnostic Questions</h4>
          <ol>
            <li>When did the issue first occur?</li>
            <li>What were you trying to do?</li>
            <li>Have you made any recent changes?</li>
            <li>Can you reproduce the issue?</li>
          </ol>
        </div>
      ),
      'sales_guide.pdf': (
        <div className="mock-document">
          <h2>Sales Training Guide</h2>
          <h3>Building Rapport</h3>
          <ul>
            <li>Use the customer's name</li>
            <li>Mirror their communication style</li>
            <li>Show genuine interest in their needs</li>
          </ul>
          
          <h3>Identifying Needs</h3>
          <p>Ask open-ended questions:</p>
          <ul>
            <li>"What challenges are you facing?"</li>
            <li>"What would an ideal solution look like?"</li>
            <li>"How would this help your business?"</li>
          </ul>
        </div>
      ),
      'objection_handling.md': (
        <div className="mock-document">
          <h2>Handling Sales Objections</h2>
          <h3>Common Objections & Responses</h3>
          
          <h4>"It's too expensive"</h4>
          <p><strong>Response:</strong> "I understand price is important. Let's look at the value and ROI this brings to your business..."</p>
          
          <h4>"I need to think about it"</h4>
          <p><strong>Response:</strong> "Of course! What specific aspects would you like to consider? I can provide additional information to help with your decision."</p>
          
          <h4>"We're happy with our current solution"</h4>
          <p><strong>Response:</strong> "That's great to hear! Many of our customers felt the same way before seeing how we could enhance their current setup..."</p>
        </div>
      )
    };

    return mockContents[filename] || (
      <div className="mock-document">
        <h2>{filename}</h2>
        <p>Mock content for {filename}. This would show the actual document content in the real implementation.</p>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
      </div>
    );
  };

  return (
    <div className="document-viewer">
      <div className="document-tabs">
        <h3>Reference Documents</h3>
        <div className="tabs">
          {documents.map((doc, index) => (
            <button
              key={doc}
              className={`tab ${activeDoc === index ? 'active' : ''}`}
              onClick={() => setActiveDoc(index)}
              aria-selected={activeDoc === index}
              role="tab"
            >
              {doc}
            </button>
          ))}
        </div>
      </div>
      
      <div className="document-content" role="tabpanel">
        {getDocumentContent(documents[activeDoc])}
      </div>
    </div>
  );
};