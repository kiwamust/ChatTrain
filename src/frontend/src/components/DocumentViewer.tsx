// Document viewer component for displaying reference materials
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './DocumentViewer.css';

interface DocumentViewerProps {
  documents: string[];
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({ documents }) => {
  const { t } = useTranslation();
  const [activeDoc, setActiveDoc] = useState(0);

  // Mock document content based on filename
  const getDocumentContent = (filename: string) => {
    const mockContents: { [key: string]: React.ReactElement } = {
      'service_guide.pdf': (
        <div className="mock-document">
          <h2>{t('documentViewer.documents.service_guide.title')}</h2>
          <h3>{t('documentViewer.documents.service_guide.greeting.title')}</h3>
          <p>{t('documentViewer.documents.service_guide.greeting.description')}</p>
          <ul>
            {t('documentViewer.documents.service_guide.greeting.examples', { returnObjects: true }).map((example: string, index: number) => (
              <li key={index}>"{ example}"</li>
            ))}
          </ul>
          
          <h3>{t('documentViewer.documents.service_guide.listening.title')}</h3>
          <p>{t('documentViewer.documents.service_guide.listening.description')}</p>
          <ul>
            {t('documentViewer.documents.service_guide.listening.techniques', { returnObjects: true }).map((technique: string, index: number) => (
              <li key={index}>{technique}</li>
            ))}
          </ul>
          
          <h3>{t('documentViewer.documents.service_guide.resolution.title')}</h3>
          <p>{t('documentViewer.documents.service_guide.resolution.description')}</p>
          <ul>
            <li><strong>S</strong>ituation - {t('documentViewer.documents.service_guide.resolution.star.situation')}</li>
            <li><strong>T</strong>ask - {t('documentViewer.documents.service_guide.resolution.star.task')}</li>
            <li><strong>A</strong>ction - {t('documentViewer.documents.service_guide.resolution.star.action')}</li>
            <li><strong>R</strong>esult - {t('documentViewer.documents.service_guide.resolution.star.result')}</li>
          </ul>
        </div>
      ),
      'scripts.md': (
        <div className="mock-document">
          <h2>{t('documentViewer.documents.scripts.title')}</h2>
          <h3>{t('documentViewer.documents.scripts.complaints.title')}</h3>
          <p><strong>Template:</strong> "{t('documentViewer.documents.scripts.complaints.template')}"</p>
          
          <h3>{t('documentViewer.documents.scripts.technical.title')}</h3>
          <p><strong>Template:</strong> "{t('documentViewer.documents.scripts.technical.template')}"</p>
          
          <h3>{t('documentViewer.documents.scripts.billing.title')}</h3>
          <p><strong>Template:</strong> "{t('documentViewer.documents.scripts.billing.template')}"</p>
        </div>
      ),
      'tech_manual.pdf': (
        <div className="mock-document">
          <h2>{t('documentViewer.documents.tech_manual.title')}</h2>
          <h3>{t('documentViewer.documents.tech_manual.commonIssues')}</h3>
          <h4>{t('documentViewer.documents.tech_manual.login.title')}</h4>
          <ol>
            {t('documentViewer.documents.tech_manual.login.steps', { returnObjects: true }).map((step: string, index: number) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
          
          <h4>{t('documentViewer.documents.tech_manual.performance.title')}</h4>
          <ol>
            {t('documentViewer.documents.tech_manual.performance.steps', { returnObjects: true }).map((step: string, index: number) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </div>
      ),
      'troubleshooting.md': (
        <div className="mock-document">
          <h2>{t('documentViewer.documents.troubleshooting.title')}</h2>
          <h3>{t('documentViewer.documents.troubleshooting.procedures')}</h3>
          <h4>{t('documentViewer.documents.troubleshooting.errorCodes.title')}</h4>
          <ul>
            <li><strong>Error 401:</strong> {t('documentViewer.documents.troubleshooting.errorCodes.401')}</li>
            <li><strong>Error 404:</strong> {t('documentViewer.documents.troubleshooting.errorCodes.404')}</li>
            <li><strong>Error 500:</strong> {t('documentViewer.documents.troubleshooting.errorCodes.500')}</li>
          </ul>
          
          <h4>{t('documentViewer.documents.troubleshooting.diagnosticQuestions.title')}</h4>
          <ol>
            {t('documentViewer.documents.troubleshooting.diagnosticQuestions.questions', { returnObjects: true }).map((question: string, index: number) => (
              <li key={index}>{question}</li>
            ))}
          </ol>
        </div>
      ),
      'sales_guide.pdf': (
        <div className="mock-document">
          <h2>{t('documentViewer.documents.sales_guide.title')}</h2>
          <h3>{t('documentViewer.documents.sales_guide.rapport.title')}</h3>
          <ul>
            {t('documentViewer.documents.sales_guide.rapport.techniques', { returnObjects: true }).map((technique: string, index: number) => (
              <li key={index}>{technique}</li>
            ))}
          </ul>
          
          <h3>{t('documentViewer.documents.sales_guide.needs.title')}</h3>
          <p>{t('documentViewer.documents.sales_guide.needs.description')}</p>
          <ul>
            {t('documentViewer.documents.sales_guide.needs.questions', { returnObjects: true }).map((question: string, index: number) => (
              <li key={index}>"{question}"</li>
            ))}
          </ul>
        </div>
      ),
      'objection_handling.md': (
        <div className="mock-document">
          <h2>{t('documentViewer.documents.objection_handling.title')}</h2>
          <h3>{t('documentViewer.documents.objection_handling.subtitle')}</h3>
          
          <h4>"{t('documentViewer.documents.objection_handling.expensive.objection')}"</h4>
          <p><strong>Response:</strong> "{t('documentViewer.documents.objection_handling.expensive.response')}"</p>
          
          <h4>"{t('documentViewer.documents.objection_handling.think.objection')}"</h4>
          <p><strong>Response:</strong> "{t('documentViewer.documents.objection_handling.think.response')}"</p>
          
          <h4>"{t('documentViewer.documents.objection_handling.current.objection')}"</h4>
          <p><strong>Response:</strong> "{t('documentViewer.documents.objection_handling.current.response')}"</p>
        </div>
      )
    };

    return mockContents[filename] || (
      <div className="mock-document">
        <h2>{filename}</h2>
        <p>{t('documentViewer.mockContent', { filename })}</p>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
      </div>
    );
  };

  return (
    <div className="document-viewer">
      <div className="document-tabs">
        <h3>{t('documentViewer.referenceDocuments')}</h3>
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