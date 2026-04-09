import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default Leaflet icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function FlightMap({ currentHeading, assignedHeading }) {
  // Hardcoded starting position near London Heathrow for this test
  const startPos = [51.47, -0.45]; 
  
  // Calculate the "Target Vector" line based on ATC instruction
  const calculateVector = (startPoint, heading, distanceMultiplier = 0.1) => {
    if (!heading) return null;
    const rad = (heading - 90) * (Math.PI / 180); 
    const endLat = startPoint[0] - (distanceMultiplier * Math.sin(rad));
    const endLng = startPoint[1] + (distanceMultiplier * Math.cos(rad));
    return [startPoint, [endLat, endLng]];
  };

  const targetVectorPath = calculateVector(startPos, assignedHeading);

  return (
    <div className="map-wrapper">
      <div className="map-header">
        <span>NAVIGATION DISPLAY (ND)</span>
        {assignedHeading && <span className="vector-alert">TARGET HEADING: {assignedHeading}°</span>}
      </div>
      
      <MapContainer 
        center={startPos} 
        zoom={10} 
        style={{ height: '350px', width: '100%', borderRadius: '0 0 8px 8px' }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />
        
        <Marker position={startPos}>
          <Popup>Current Aircraft Position</Popup>
        </Marker>

        {targetVectorPath && (
          <Polyline 
            positions={targetVectorPath} 
            color="#4ade80" 
            dashArray="10, 10" 
            weight={3} 
          />
        )}
      </MapContainer>
    </div>
  );
}