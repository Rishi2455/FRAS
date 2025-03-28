/**
 * Attendance System JavaScript
 * Handles webcam access, face recognition simulation, and attendance marking
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const startCameraBtn = document.getElementById('start-camera-btn');
    const stopCameraBtn = document.getElementById('stop-camera-btn');
    const cameraContainer = document.getElementById('camera-container');
    const video = document.getElementById('webcam');
    const recognitionStatus = document.getElementById('recognition-status');
    const faceBoxesContainer = document.getElementById('face-boxes');
    const notificationContainer = document.getElementById('attendance-notification');
    
    let stream = null;
    let recognitionInterval = null;
    
    // Check if required elements exist (only on attendance page)
    if (!startCameraBtn || !stopCameraBtn || !cameraContainer || !video) {
        return; // Not on the attendance page
    }
    
    // Start camera
    startCameraBtn.addEventListener('click', function() {
        startCameraBtn.classList.add('d-none');
        stopCameraBtn.classList.remove('d-none');
        cameraContainer.classList.remove('d-none');
        
        // Access webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(mediaStream) {
                stream = mediaStream;
                video.srcObject = mediaStream;
                video.onloadedmetadata = function(e) {
                    video.play();
                    // Start face recognition simulation
                    startFaceDetection();
                };
            })
            .catch(function(err) {
                console.error("Error accessing webcam: ", err);
                showNotification('error', 'Could not access webcam. Please ensure camera permissions are granted.');
                stopCamera();
            });
    });
    
    // Stop camera
    stopCameraBtn.addEventListener('click', stopCamera);
    
    function stopCamera() {
        startCameraBtn.classList.remove('d-none');
        stopCameraBtn.classList.add('d-none');
        cameraContainer.classList.add('d-none');
        
        // Stop recognition interval
        if (recognitionInterval) {
            clearInterval(recognitionInterval);
            recognitionInterval = null;
        }
        
        // Stop webcam stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            video.srcObject = null;
        }
        
        // Clear face boxes
        if (faceBoxesContainer) {
            faceBoxesContainer.innerHTML = '';
        }
        
        // Reset recognition status
        if (recognitionStatus) {
            recognitionStatus.textContent = 'Waiting for face detection...';
        }
    }
    
    // Simulate face detection and recognition
    function startFaceDetection() {
        if (recognitionInterval) {
            clearInterval(recognitionInterval);
        }
        
        recognitionInterval = setInterval(function() {
            if (!stream) return;
            
            // Simulate face detection (random timing)
            if (Math.random() > 0.7) { // 30% chance to detect a face each interval
                detectFace();
            }
        }, 2000); // Check every 2 seconds
    }
    
    function detectFace() {
        if (recognitionStatus) {
            recognitionStatus.textContent = 'Face detected! Identifying...';
        }
        
        // Simulate face detection box
        const videoWidth = video.videoWidth || 640;
        const videoHeight = video.videoHeight || 480;
        const displayWidth = video.offsetWidth;
        const displayHeight = video.offsetHeight;
        
        // Random position for face box (for simulation)
        const boxWidth = Math.floor(videoWidth * 0.2);
        const boxHeight = Math.floor(videoHeight * 0.3);
        const left = Math.floor(Math.random() * (videoWidth - boxWidth));
        const top = Math.floor(Math.random() * (videoHeight - boxHeight));
        
        // Scale coordinates to display size
        const scaledLeft = (left / videoWidth) * displayWidth;
        const scaledTop = (top / videoHeight) * displayHeight;
        const scaledWidth = (boxWidth / videoWidth) * displayWidth;
        const scaledHeight = (boxHeight / videoHeight) * displayHeight;
        
        // Create and add face box element
        if (faceBoxesContainer) {
            faceBoxesContainer.innerHTML = '';
            const faceBox = document.createElement('div');
            faceBox.className = 'face-box';
            faceBox.style.left = `${scaledLeft}px`;
            faceBox.style.top = `${scaledTop}px`;
            faceBox.style.width = `${scaledWidth}px`;
            faceBox.style.height = `${scaledHeight}px`;
            faceBoxesContainer.appendChild(faceBox);
        }
        
        // Simulate recognition delay
        setTimeout(function() {
            if (recognitionStatus) {
                recognitionStatus.textContent = 'Processing...';
            }
            
            // Simulate student recognition (get random student from table)
            simulateRecognition();
        }, 1000);
    }
    
    function simulateRecognition() {
        // Get all students from the attendance table that are not already marked as Present or Late
        const studentRows = document.querySelectorAll('table tbody tr');
        if (studentRows.length === 0) return;
        
        // Filter students who are currently marked as Absent
        const absentStudents = Array.from(studentRows).filter(row => {
            const statusSelect = row.querySelector('select');
            return statusSelect && statusSelect.value === 'Absent';
        });
        
        // If no absent students, return
        if (absentStudents.length === 0) {
            if (recognitionStatus) {
                recognitionStatus.textContent = 'All students already marked. No more faces to recognize.';
            }
            return;
        }
        
        // Select a random absent student
        const randomIndex = Math.floor(Math.random() * absentStudents.length);
        const studentRow = absentStudents[randomIndex];
        
        // Get student info - use the dataset-id attribute to get the correct ID
        const studentIdInput = studentRow.querySelector('input[name="student_id"]');
        if (!studentIdInput) return; // Safety check
        
        const studentId = studentIdInput.value;
        const studentName = studentRow.querySelector('td:nth-child(2)').textContent;
        
        // Update status to "Present" for this specific student
        const statusSelect = studentRow.querySelector('select');
        statusSelect.value = 'Present';
        
        // Update last updated time
        const updatedCell = document.getElementById(`updated-${studentId}`);
        if (updatedCell) {
            const now = new Date();
            // Format time in 12-hour format with AM/PM
            const hours = now.getHours() % 12 || 12; // Convert 0 to 12 for 12 AM
            const minutes = now.getMinutes().toString().padStart(2, '0');
            const seconds = now.getSeconds().toString().padStart(2, '0');
            const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
            const timeString = `${hours}:${minutes}:${seconds} ${ampm}`;
            updatedCell.innerHTML = `<div class="badge bg-success rounded-pill"><i class="fas fa-clock me-1"></i>${timeString}</div>`;
            
            // Add a hidden field with the timestamp for the form submission
            const timestampFieldName = `time_in-${studentId}`;
            
            // Remove any existing timestamp field first to avoid duplicates
            let existingTimestamp = studentRow.querySelector(`input[name="${timestampFieldName}"]`);
            if (existingTimestamp) {
                existingTimestamp.remove();
            }
            
            // Create a new timestamp field with the current time
            const timestampField = document.createElement('input');
            timestampField.type = 'hidden';
            timestampField.name = timestampFieldName;
            timestampField.value = `${now.getHours().toString().padStart(2, '0')}:${minutes}:${seconds}`; // 24-hour format for backend
            
            // Add it to the row
            studentRow.appendChild(timestampField);
        }
        }
        
        // Update attendance counters
        updateAttendanceStats();
        
        // Show notification
        showNotification('success', `Attendance marked for ${studentName}`);
        
        // Add to activity log for this specific student
        addToActivityLog(studentRow);
        
        // Reset recognition status
        if (recognitionStatus) {
            recognitionStatus.textContent = 'Student recognized! Waiting for next face...';
        }
    }
    
    function updateAttendanceStats() {
        // Count attendance statuses
        const rows = document.querySelectorAll('table tbody tr');
        let presentCount = 0;
        let lateCount = 0;
        let absentCount = 0;
        
        rows.forEach(row => {
            const status = row.querySelector('select').value;
            if (status === 'Present') presentCount++;
            else if (status === 'Late') lateCount++;
            else if (status === 'Absent') absentCount++;
        });
        
        // Update counters
        const totalCount = rows.length;
        
        if (document.getElementById('present-count')) {
            document.getElementById('present-count').textContent = presentCount;
        }
        if (document.getElementById('late-count')) {
            document.getElementById('late-count').textContent = lateCount;
        }
        if (document.getElementById('absent-count')) {
            document.getElementById('absent-count').textContent = absentCount;
        }
        
        // Update progress bars
        if (document.getElementById('present-bar')) {
            document.getElementById('present-bar').style.width = `${(presentCount / totalCount * 100)}%`;
        }
        if (document.getElementById('late-bar')) {
            document.getElementById('late-bar').style.width = `${(lateCount / totalCount * 100)}%`;
        }
        if (document.getElementById('absent-bar')) {
            document.getElementById('absent-bar').style.width = `${(absentCount / totalCount * 100)}%`;
        }
        
        // Add to activity log with the correct student row
        // Get the student row that was just marked present (should be studentRow from simulateRecognition)
        // We don't need to grab a different one here
    }
    
    function addToActivityLog(studentRow) {
        // Get student info
        if (!studentRow) return;
        
        const studentName = studentRow.querySelector('td:nth-child(2)').textContent;
        const now = new Date();
        
        // Format time in 12-hour format with AM/PM
        const hours = now.getHours() % 12 || 12; // Convert 0 to 12 for 12 AM
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
        const timeString = `${hours}:${minutes}:${seconds} ${ampm}`;
        
        // Create activity log entry
        const logContainer = document.getElementById('activity-log');
        if (!logContainer) return;
        
        // Remove "No attendance records" placeholder if it exists
        const placeholder = logContainer.querySelector('.text-muted');
        if (placeholder) {
            logContainer.innerHTML = '';
        }
        
        // Create new log entry
        const logItem = document.createElement('div');
        logItem.className = 'list-group-item list-group-item-action border-0';
        logItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1 fw-bold">${studentName}</h6>
                <small class="text-muted">${timeString}</small>
            </div>
            <p class="mb-1">Marked as 
                <span class="status-badge status-present">Present</span>
            </p>
        `;
        
        // Add to top of log
        logContainer.insertBefore(logItem, logContainer.firstChild);
    }
    
    function showNotification(type, message) {
        if (!notificationContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast show bg-${type === 'success' ? 'success' : 'danger'} text-white`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-${type === 'success' ? 'success' : 'danger'} text-white">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <small>Just now</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        notificationContainer.appendChild(toast);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                notificationContainer.removeChild(toast);
            }, 300);
        }, 3000);
    }
});

/**
 * Webcam functionality for student registration
 */
document.addEventListener('DOMContentLoaded', function() {
    const webcamCheckbox = document.getElementById('capture_webcam');
    const webcamContainer = document.getElementById('webcam-container');
    const fileInput = document.getElementById('student_image');
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    const webcamImageInput = document.getElementById('webcam_image');
    
    if (!webcamCheckbox) return; // Not on the student registration page
    
    let stream = null;
    
    webcamCheckbox.addEventListener('change', function() {
        if (this.checked) {
            webcamContainer.classList.remove('d-none');
            fileInput.disabled = true;
            
            // Start webcam
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(mediaStream) {
                    stream = mediaStream;
                    video.srcObject = mediaStream;
                })
                .catch(function(error) {
                    console.error('Error accessing webcam:', error);
                    alert('Could not access webcam. Please make sure your camera is connected and permissions are granted.');
                    webcamCheckbox.checked = false;
                    webcamContainer.classList.add('d-none');
                    fileInput.disabled = false;
                });
        } else {
            webcamContainer.classList.add('d-none');
            fileInput.disabled = false;
            
            // Stop webcam
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        }
    });
    
    if (captureBtn) {
        captureBtn.addEventListener('click', function() {
            // Capture photo from webcam
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            // Convert to base64 data URL
            const imageDataURL = canvas.toDataURL('image/jpeg');
            webcamImageInput.value = imageDataURL;
            
            // Show retake button
            captureBtn.classList.add('d-none');
            retakeBtn.classList.remove('d-none');
        });
    }
    
    if (retakeBtn) {
        retakeBtn.addEventListener('click', function() {
            webcamImageInput.value = '';
            captureBtn.classList.remove('d-none');
            retakeBtn.classList.add('d-none');
        });
    }
});