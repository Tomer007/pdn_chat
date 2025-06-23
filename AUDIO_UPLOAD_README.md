# Audio Upload Functionality

This document describes the audio upload functionality that allows users to record and save audio files to the backend server.

## Overview

The audio upload system consists of:

1. **Frontend JavaScript** - Handles audio recording and upload
2. **Backend API Routes** - Manages file storage and retrieval
3. **File Organization** - Organizes audio files by user in the `/saved_results/` directory

## Features

- ✅ Record audio using browser's MediaRecorder API
- ✅ Automatic file naming with timestamps
- ✅ User-specific folder organization
- ✅ File validation and error handling
- ✅ Audio playback after recording
- ✅ Skip recording option
- ✅ Upload status feedback

## File Structure

```
saved_results/
├── user1/
│   ├── user1_audio_2025-01-15_1430.wav
│   └── user1_audio_2025-01-15_1500.wav
├── user2/
│   └── user2_audio_2025-01-15_1600.wav
└── ...
```

## API Endpoints

### POST `/api/save-audio`
Upload an audio file for a specific user.

**Request:**
- `audio` (file): The audio file to upload
- `username` (string): The name of the user

**Response:**
```json
{
  "success": true,
  "message": "Audio saved successfully",
  "file_path": "saved_results/user1/user1_audio_2025-01-15_1430.wav",
  "filename": "user1_audio_2025-01-15_1430.wav",
  "username": "user1",
  "timestamp": "2025-01-15_1430"
}
```

### GET `/api/audio/{username}`
Get list of audio files for a specific user.

**Response:**
```json
{
  "success": true,
  "message": "Found 2 audio files",
  "files": [
    {
      "filename": "user1_audio_2025-01-15_1500.wav",
      "file_path": "saved_results/user1/user1_audio_2025-01-15_1500.wav",
      "size": 1024,
      "created": "2025-01-15T15:00:00"
    }
  ]
}
```

### DELETE `/api/audio/{username}/{filename}`
Delete a specific audio file.

**Response:**
```json
{
  "success": true,
  "message": "Audio file deleted successfully",
  "filename": "user1_audio_2025-01-15_1430.wav"
}
```

## Frontend Usage

### Basic Audio Recording

```javascript
// Start recording
const startBtn = document.getElementById('startRecordBtn');
startBtn.onclick = async function() {
    // Recording logic...
};

// Stop recording and upload
mediaRecorder.onstop = async (e) => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    
    try {
        const result = await saveUserAudio(username, audioBlob);
        console.log('Audio uploaded successfully:', result);
    } catch (error) {
        console.error('Failed to upload audio:', error);
    }
};
```

### Skip Recording

```javascript
// Skip button functionality
const skipBtn = document.getElementById('skipBtn');
skipBtn.onclick = function() {
    // Skip to questionnaire without recording
    document.getElementById('voiceRecordArea').classList.add('hidden');
    document.getElementById('questionArea').classList.remove('hidden');
    loadQuestion(currentQuestion);
};
```

## Security Features

- **Username Sanitization**: Removes special characters for file system safety
- **File Extension Validation**: Ensures proper audio file types
- **Path Traversal Protection**: Prevents directory traversal attacks
- **File Size Limits**: Configurable file size restrictions

## Error Handling

The system handles various error scenarios:

- **Microphone Access Denied**: Shows user-friendly error message
- **Network Issues**: Displays upload failure notification
- **Invalid Files**: Validates file type and size
- **Server Errors**: Graceful error handling with logging

## Testing

Run the test suite to verify functionality:

```bash
python -m unittest tests/test_audio_upload.py
```

## Configuration

### File Storage Location
The base directory for saved audio files can be configured in `app/api/audio_routes.py`:

```python
SAVED_RESULTS_DIR = Path("saved_results")
```

### File Naming Convention
Files are named using the pattern: `{username}_audio_{timestamp}.{extension}`

Example: `john_doe_audio_2025-01-15_1430.wav`

## Dependencies

- **Frontend**: Modern browser with MediaRecorder API support
- **Backend**: FastAPI, Python 3.7+
- **File System**: Standard file system access

## Browser Compatibility

The audio recording functionality requires:
- Chrome 47+
- Firefox 25+
- Safari 14+
- Edge 79+

## Troubleshooting

### Common Issues

1. **Microphone not working**
   - Check browser permissions
   - Ensure HTTPS connection (required for MediaRecorder)

2. **Upload fails**
   - Check network connection
   - Verify server is running
   - Check file size limits

3. **Files not saving**
   - Verify directory permissions
   - Check disk space
   - Review server logs

### Debug Mode

Enable debug logging by setting the log level in `audio_routes.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] Audio compression for smaller file sizes
- [ ] Cloud storage integration (AWS S3, Google Cloud Storage)
- [ ] Audio transcription using speech-to-text
- [ ] Audio quality analysis
- [ ] Batch upload functionality
- [ ] Audio file encryption 