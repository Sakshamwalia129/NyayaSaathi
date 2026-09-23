import { useState, useRef } from "react";
import "./FileUpload.css";

// Format bytes to human-readable string
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({ file, onFileChange, onFileRemove }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) onFileChange(dropped);
  }

  function handleDragOver(e) {
    e.preventDefault();
  }

  function handleDragEnter(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleInputChange(e) {
    const selected = e.target.files[0];
    if (selected) onFileChange(selected);
  }

  return (
    <div className="file-upload">
      {!file ? (
        // Drop zone
        <div
          className={`file-upload__dropzone${isDragging ? " file-upload__dropzone--active" : ""}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          role="button"
          tabIndex={0}
          aria-label="Upload a judgment file. Click or drag and drop a PDF or text file."
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
          }}
        >
          {/* Upload icon */}
          <span className="file-upload__icon" aria-hidden="true">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </span>
          <p className="file-upload__primary-text">Drop your judgment here</p>
          <p className="file-upload__secondary-text">
            or <span className="file-upload__link">choose a PDF / text file</span>
          </p>
          <p className="file-upload__formats">Accepts: PDF, TXT</p>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt"
            className="file-upload__input"
            onChange={handleInputChange}
            aria-label="Select a court judgment file"
            tabIndex={-1}
          />
        </div>
      ) : (
        // File selected state
        <div className="file-upload__selected animate-fade-in">
          {/* Document icon */}
          <span className="file-upload__file-icon" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </span>
          <div className="file-upload__file-info">
            <p className="file-upload__file-name">{file.name}</p>
            <p className="file-upload__file-meta">
              {file.type || "Unknown type"} · {formatBytes(file.size)}
            </p>
          </div>
          <button
            className="file-upload__remove"
            onClick={onFileRemove}
            aria-label={`Remove file: ${file.name}`}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
