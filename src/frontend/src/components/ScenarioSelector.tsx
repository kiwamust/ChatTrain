// Scenario selection screen component
import React, { useEffect, useState } from 'react';
import { Scenario } from '../types';
import { api } from '../services/api';
import './ScenarioSelector.css';

interface ScenarioSelectorProps {
  onSelectScenario: (scenario: Scenario) => void;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({ onSelectScenario }) => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const response = await api.getScenarios();
        setScenarios(response.scenarios);
      } catch (err) {
        setError('Failed to load scenarios');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadScenarios();
  }, []);

  if (loading) {
    return (
      <div className="scenario-selector">
        <div className="loading">Loading scenarios...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="scenario-selector">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="scenario-selector">
      <div className="header">
        <h1>ChatTrain - Select Training Scenario</h1>
        <p>Choose a training scenario to begin your session</p>
      </div>
      
      <div className="scenarios-grid">
        {scenarios.map((scenario) => (
          <div
            key={scenario.id}
            className="scenario-card"
            onClick={() => onSelectScenario(scenario)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSelectScenario(scenario);
              }
            }}
          >
            <h3>{scenario.title}</h3>
            <p>{scenario.description}</p>
            <div className="documents-info">
              <span className="document-count">
                {scenario.documents.length} reference document{scenario.documents.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};