import React, { useState } from 'react';
import { ScenarioSelector } from './components/ScenarioSelector';
import { ChatInterface } from './components/ChatInterface';
import { Scenario } from './types';
import './App.css';

function App() {
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);

  const handleSelectScenario = (scenario: Scenario) => {
    setSelectedScenario(scenario);
  };

  const handleEndSession = () => {
    setSelectedScenario(null);
  };

  return (
    <div className="app">
      {!selectedScenario ? (
        <ScenarioSelector onSelectScenario={handleSelectScenario} />
      ) : (
        <ChatInterface 
          scenario={selectedScenario} 
          onEndSession={handleEndSession}
        />
      )}
    </div>
  );
}

export default App;
