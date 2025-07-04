/**
 * Sends user audio to the backend server for storage
 * @param {string} username - The name of the user
 * @param {Blob|File} audioBlob - The audio data to upload
 * @returns {Promise<Object>} - Response with file path and status
 */
async function saveUserAudio(username, audioBlob) {
    try {
        // Create FormData to send the audio file
        const formData = new FormData();
        formData.append('audio', audioBlob, `${username}_audio_${getTimestamp()}.wav`);
        formData.append('username', username);

        // Send POST request to backend
        const response = await fetch('/pdn-admin/api/save-audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Audio saved successfully:', result);
        return result;

    } catch (error) {
        console.error('Error saving audio:', error);
        throw error;
    }
}

/**
 * Generates a timestamp string for file naming
 * @returns {string} - Timestamp in format YYYY-MM-DD_HHMM
 */
function getTimestamp() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}_${hours}${minutes}`;
}

/**
 * Example usage with voice recording
 * @param {string} username - The name of the user
 * @param {MediaRecorder} mediaRecorder - The MediaRecorder instance
 */
async function handleVoiceRecording(username, mediaRecorder) {
    return new Promise((resolve, reject) => {
        const audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            try {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const result = await saveUserAudio(username, audioBlob);
                resolve(result);
            } catch (error) {
                reject(error);
            }
        };
        
        mediaRecorder.onerror = (error) => {
            reject(error);
        };
    });
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { saveUserAudio, handleVoiceRecording, getTimestamp };
} 