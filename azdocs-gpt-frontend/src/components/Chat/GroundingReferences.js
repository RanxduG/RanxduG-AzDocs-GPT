import React from 'react';
import './GroundingReferences.css';

const GroundingReferences = ({ references }) => {
  console.log('GroundingReferences component rendered with references:', references);

  return (
    <div className="grounding-references">
      <h4 className="references-title">References</h4>
      
      <div className="references-list">
        {references.map((reference, index) => (
          <div key={index} className="reference-item">
            <div className="reference-header">
              <span className="reference-doc-name">[{reference.title}]</span>
            </div>
            <div className="reference-content">
              {reference.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GroundingReferences;