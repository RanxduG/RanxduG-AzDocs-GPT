import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/UI/Header';
import './CSS/UploadPage.css';

const UploadPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [user, setUser] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadResults, setUploadResults] = useState([]);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('userInfo');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  // Access levels configuration
  const accessLevels = [
    { value: 1, label: 'Level 1 - Public', description: 'Accessible to all users' },
    { value: 2, label: 'Level 2 - Internal', description: 'Internal company documents' },
    { value: 3, label: 'Level 3 - Confidential', description: 'Confidential information' },
    { value: 4, label: 'Level 4 - Restricted', description: 'Highly restricted access' },
    { value: 5, label: 'Level 5 - Top Secret', description: 'Maximum security clearance required' }
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== files.length) {
      alert('Only PDF files are allowed. Non-PDF files have been filtered out.');
    }
    
    addFiles(pdfFiles);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    addFiles(files);
  };

  const addFiles = (files) => {
    const newFiles = files.map((file, index) => ({
      id: Date.now() + index,
      file: file,
      name: file.name,
      size: file.size,
      accessLevel: 1, // Default access level
      status: 'pending'
    }));
    
    setSelectedFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (fileId) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const updateFileAccessLevel = (fileId, accessLevel) => {
    setSelectedFiles(prev => 
      prev.map(f => f.id === fileId ? { ...f, accessLevel: parseInt(accessLevel) } : f)
    );
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) {
      alert('Please select files to upload');
      return;
    }

    setUploading(true);
    setUploadResults([]);
    
    const results = [];

    for (const fileItem of selectedFiles) {
      try {
        setUploadProgress(prev => ({ ...prev, [fileItem.id]: 0 }));
        
        const formData = new FormData();
        formData.append('file', fileItem.file);
        formData.append('accessLevel', fileItem.accessLevel);
        formData.append('fileName', fileItem.name);

        const response = await fetch('/api/upload/pdf', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        });

        if (response.ok) {
          const result = await response.json();
          results.push({
            fileName: fileItem.name,
            status: 'success',
            message: 'Upload successful',
            blobUrl: result.blobUrl
          });
          setUploadProgress(prev => ({ ...prev, [fileItem.id]: 100 }));
        } else {
          const error = await response.json();
          results.push({
            fileName: fileItem.name,
            status: 'error',
            message: error.error || 'Upload failed'
          });
        }
      } catch (error) {
        results.push({
          fileName: fileItem.name,
          status: 'error',
          message: 'Network error during upload'
        });
      }
    }

    setUploadResults(results);
    setUploading(false);
    
    // Clear selected files if all uploads were successful
    if (results.every(r => r.status === 'success')) {
      setSelectedFiles([]);
      setUploadProgress({});
    }
  };

  const clearAll = () => {
    setSelectedFiles([]);
    setUploadProgress({});
    setUploadResults([]);
  };

  return (
    <div className="upload-page-fullwidth">
      <Header />
      <div className="upload-container">
        <div className="upload-header">
          <h2>Document Upload</h2>
          <p>Upload PDF documents to the Azure knowledge base with appropriate access levels</p>
        </div>

        {/* Upload Area */}
        <div 
          className={`upload-dropzone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
            </svg>
          </div>
          <h3>Drop PDF files here or click to browse</h3>
          <p>Only PDF files are supported</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            <div className="files-header">
              <h3>Selected Files ({selectedFiles.length})</h3>
              <button 
                className="btn-secondary"
                onClick={clearAll}
                disabled={uploading}
              >
                Clear All
              </button>
            </div>
            
            <div className="files-list">
              {selectedFiles.map(fileItem => (
                <div key={fileItem.id} className="file-item">
                  <div className="file-info">
                    <div className="file-details">
                      <span className="file-name">{fileItem.name}</span>
                      <span className="file-size">{formatFileSize(fileItem.size)}</span>
                    </div>
                    
                    <div className="access-level-selector">
                      <label htmlFor={`access-${fileItem.id}`}>Access Level:</label>
                      <select
                        id={`access-${fileItem.id}`}
                        value={fileItem.accessLevel}
                        onChange={(e) => updateFileAccessLevel(fileItem.id, e.target.value)}
                        disabled={uploading}
                      >
                        {accessLevels.map(level => (
                          <option key={level.value} value={level.value}>
                            {level.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  {uploadProgress[fileItem.id] !== undefined && (
                    <div className="upload-progress">
                      <div 
                        className="progress-bar"
                        style={{ width: `${uploadProgress[fileItem.id]}%` }}
                      ></div>
                    </div>
                  )}
                  
                  <button
                    className="btn-remove"
                    onClick={() => removeFile(fileItem.id)}
                    disabled={uploading}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            
            <div className="upload-actions">
              <button
                className="btn-primary"
                onClick={uploadFiles}
                disabled={uploading || selectedFiles.length === 0}
              >
                {uploading ? 'Uploading...' : `Upload ${selectedFiles.length} File${selectedFiles.length > 1 ? 's' : ''}`}
              </button>
            </div>
          </div>
        )}

        {/* Upload Results */}
        {uploadResults.length > 0 && (
          <div className="upload-results">
            <h3>Upload Results</h3>
            <div className="results-list">
              {uploadResults.map((result, index) => (
                <div key={index} className={`result-item ${result.status}`}>
                  <div className="result-icon">
                    {result.status === 'success' ? '✓' : '✗'}
                  </div>
                  <div className="result-details">
                    <span className="result-filename">{result.fileName}</span>
                    <span className="result-message">{result.message}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Access Level Information */}
        <div className="access-info">
          <h3>Access Level Guide</h3>
          <div className="access-levels">
            {accessLevels.map(level => (
              <div key={level.value} className="access-level-item">
                <span className="level-badge">Level {level.value}</span>
                <div className="level-info">
                  <span className="level-name">{level.label.split(' - ')[1]}</span>
                  <span className="level-description">{level.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;