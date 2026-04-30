import { useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/v1/api/users'

/**
 * ResumeUploadComponent
 * Handles resume uploads using S3 presigned URLs
 * Flow:
 * 1. User selects file and fills metadata
 * 2. Call POST /resumes/upload/initiate/ → Get presigned URL
 * 3. PUT file directly to S3 using presigned URL
 * 4. Call POST /resumes/{id}/upload/complete/ → Mark upload complete
 */
export function ResumeUploadComponent({ token, onUploadComplete, onError }) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    notes: '',
    is_primary: false,
    parsed_text: '',
  })
  const [statusMessage, setStatusMessage] = useState('')

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setStatusMessage(`Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`)
    }
  }

  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const uploadToS3 = async (presignedUrl, file, contentType) => {
    /**
     * Upload file directly to S3 using presigned URL
     * Note: S3 requires exact Content-Type match and headers order
     */
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100
          setUploadProgress(percentComplete)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          setStatusMessage('✓ File uploaded to S3')
          resolve()
        } else {
          reject(new Error(`S3 upload failed: ${xhr.status} ${xhr.statusText}`))
        }
      })

      xhr.addEventListener('error', () => {
        reject(new Error('S3 upload failed: Network error'))
      })

      xhr.addEventListener('abort', () => {
        reject(new Error('S3 upload cancelled'))
      })

      // Open connection to S3
      xhr.open('PUT', presignedUrl, true)
      xhr.setRequestHeader('Content-Type', contentType)

      // Send file to S3
      xhr.send(file)
    })
  }

  const handleUpload = async (e) => {
    e.preventDefault()

    if (!selectedFile) {
      onError?.('Please select a file')
      return
    }

    if (!formData.title.trim()) {
      onError?.('Please enter a resume title')
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setStatusMessage('Starting upload...')

    try {
      // Step 1: Initiate upload - get presigned URL from backend
      setStatusMessage('Requesting presigned URL...')
      const initiateResponse = await fetch(`${API_BASE_URL}/resumes/upload/initiate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
        body: JSON.stringify({
          title: formData.title,
          filename: selectedFile.name,
          content_type: selectedFile.type,
          file_size: selectedFile.size,
          parsed_text: formData.parsed_text,
          notes: formData.notes,
          is_primary: formData.is_primary,
        }),
      })

      if (!initiateResponse.ok) {
        const errorData = await initiateResponse.json()
        throw new Error(errorData.detail || 'Failed to initiate upload')
      }

      const initiateData = await initiateResponse.json()
      const resumeId = initiateData.resume?.id ?? initiateData.id
      const { presigned_url, s3_key } = initiateData

      if (!presigned_url || !s3_key) {
        throw new Error('Invalid presigned URL response from server')
      }

      if (!resumeId) {
        throw new Error('Missing resume id in initiate response')
      }

      // Step 2: Upload file directly to S3
      setStatusMessage('Uploading to S3...'  )
      await uploadToS3(presigned_url, selectedFile, selectedFile.type)

      // Step 3: Mark upload as complete on backend
      setStatusMessage('Finalizing...')
      const completeResponse = await fetch(`${API_BASE_URL}/resumes/${resumeId}/upload/complete/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          Accept: 'application/json',
        },
        body: JSON.stringify({
          s3_key,
          s3_url: `https://${new URL(presigned_url).hostname}/${s3_key}`,
        }),
      })

      if (!completeResponse.ok) {
        const errorData = await completeResponse.json()
        throw new Error(errorData.detail || 'Failed to complete upload')
      }

      setStatusMessage('✓ Resume uploaded successfully!')
      setSelectedFile(null)
      setUploadProgress(0)
      setFormData({
        title: '',
        notes: '',
        is_primary: false,
        parsed_text: '',
      })

      onUploadComplete?.(await completeResponse.json())
    } catch (error) {
      const errorMsg = error.message || 'Upload failed'
      setStatusMessage(`✗ ${errorMsg}`)
      onError?.(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  return (
    <form onSubmit={handleUpload} className="form-container">
      <div className="form-grid">
        {/* Title */}
        <div className="field">
          <label>Resume Title *</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleFormChange}
            placeholder="e.g., Senior Engineer 2025"
            disabled={uploading}
          />
        </div>

        {/* File Input */}
        <div className="field">
          <label>Select File (PDF/DOCX) *</label>
          <input
            type="file"
            name="file"
            accept=".pdf,.docx,.doc"
            onChange={handleFileSelect}
            disabled={uploading}
          />
          {selectedFile && (
            <span className="file-info">
              {selectedFile.name} • {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </span>
          )}
        </div>

        {/* Parsed Text */}
        <div className="field" style={{ gridColumn: '1 / -1' }}>
          <label>Extracted Text (Optional)</label>
          <textarea
            name="parsed_text"
            value={formData.parsed_text}
            onChange={handleFormChange}
            placeholder="Leave empty to auto-extract from PDF/DOCX (coming soon)"
            disabled={uploading}
            rows={3}
          />
        </div>

        {/* Notes */}
        <div className="field" style={{ gridColumn: '1 / -1' }}>
          <label>Notes (Optional)</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleFormChange}
            placeholder="Any notes about this resume..."
            disabled={uploading}
            rows={2}
          />
        </div>

        {/* Set as Primary */}
        <div className="field toggle-field">
          <label>
            <input
              type="checkbox"
              name="is_primary"
              checked={formData.is_primary}
              onChange={handleFormChange}
              disabled={uploading}
            />
            Set as primary resume
          </label>
        </div>
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <div className="progress-text">
            {uploadProgress.toFixed(0)}% - {statusMessage}
          </div>
        </div>
      )}

      {/* Status Message */}
      {statusMessage && !uploading && (
        <div className={`status-message ${statusMessage.startsWith('✓') ? 'success' : statusMessage.startsWith('✗') ? 'error' : ''}`}>
          {statusMessage}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={uploading || !selectedFile || !formData.title.trim()}
        className="btn-primary"
      >
        {uploading ? `Uploading... ${uploadProgress.toFixed(0)}%` : 'Upload Resume'}
      </button>
    </form>
  )
}
