import { useState, useEffect } from 'react';
import FlightMap from './FlightMap';
import './App.css';

function App() {
  const [instruction, setInstruction] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to the FastAPI WebSocket we built in Phase 4
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

    ws.onopen = () => {
      console.log('Connected to Context Engine');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received new instruction:', data);
      setInstruction(data);
    };

    ws.onclose = () => {
      console.log('Disconnected from Context Engine');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>PILOT ASSIST <span>SYSTEM</span></h1>
        <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'LIVE LINK' : 'OFFLINE'}
        </div>
      </header>

      <main className="main-content">
        {!instruction ? (
          <div className="waiting-screen">
            <div className="radar-spinner"></div>
            <p>Awaiting ATC Instructions...</p>
          </div>
        ) : (
          <div className={`instruction-card ${instruction.anomaly_detected ? 'alert' : ''}`}>
            
            {instruction.anomaly_detected && (
              <div className="alert-banner">⚠️ CAUTION / ANOMALY DETECTED</div>
            )}

            <div className="grid-layout">
              <DataBlock label="CALLSIGN" value={instruction.callsign} highlight={true} />
              <DataBlock label="HEADING" value={instruction.assigned_heading ? `${instruction.assigned_heading}°` : null} />
              <DataBlock label="ALTITUDE" value={instruction.assigned_altitude} />
              <DataBlock label="FREQUENCY" value={instruction.frequency ? `${instruction.frequency} MHz` : null} />
              <DataBlock label="SQUAWK" value={instruction.squawk_code} />
              <DataBlock label="DESTINATION" value={instruction.clearance_limit} />
            </div>

            {/* --- MAP VISUALIZER --- */}
            <FlightMap assignedHeading={instruction.assigned_heading} />

            {instruction.departure_procedure && (
              <div className="procedure-block">
                <span>PROCEDURE / ROUTE</span>
                <p>{instruction.departure_procedure}</p>
              </div>
            )}

          </div>
        )}
      </main>
    </div>
  );
}

// A simple reusable component for the data squares
function DataBlock({ label, value, highlight }) {
  if (!value) return <div className="data-block empty"><span className="label">{label}</span><span className="value">--</span></div>;
  
  return (
    <div className={`data-block ${highlight ? 'highlight' : ''}`}>
      <span className="label">{label}</span>
      <span className="value">{value}</span>
    </div>
  );
}

export default App;