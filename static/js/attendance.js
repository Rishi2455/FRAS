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
    let lastRecognizedTime = 0;
    const RECOGNITION_COOLDOWN = 5000; // 5 seconds cooldown between recognitions

    // Check if required elements exist (only on attendance page)
    if (!startCameraBtn || !stopCameraBtn || !cameraContainer || !video) {
        return; // Not on the attendance page
    }

    // Start camera
    startCameraBtn.addEventListener('click', function() {
        startCameraBtn.classList.add('d-none');
        stopCameraBtn.classList.remove('d-none');
        cameraContainer.classList.remove('d-none');

        // Access webcam with higher resolution
        navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "user"
            }
        })
        .then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = mediaStream;
            video.onloadedmetadata = function(e) {
                video.play();
                startFaceDetection();
            };
        })
        .catch(function(err) {
            console.error("Error accessing webcam:", err);
            stopCamera();
            recognitionStatus.textContent = "Error: Could not access webcam";
        });
    });

    stopCameraBtn.addEventListener('click', stopCamera);

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        if (recognitionInterval) {
            clearInterval(recognitionInterval);
            recognitionInterval = null;
        }

        cameraContainer.classList.add('d-none');
        startCameraBtn.classList.remove('d-none');
        stopCameraBtn.classList.add('d-none');
        recognitionStatus.textContent = "Camera stopped";
    }

    function startFaceDetection() {
        if (recognitionInterval) {
            clearInterval(recognitionInterval);
        }

        recognitionInterval = setInterval(() => {
            if (!stream) return;

            const currentTime = Date.now();
            if (currentTime - lastRecognizedTime < RECOGNITION_COOLDOWN) {
                return; // Skip detection during cooldown
            }

            recognitionStatus.textContent = 'Scanning for faces...';

            // Simulate face detection delay
            setTimeout(() => {
                if (!stream) return; // Check again if camera is still active

                recognitionStatus.textContent = 'Processing...';
                detectAndMarkAttendance();
            }, 1000);

        }, 2000); // Check every 2 seconds
    }

    function detectAndMarkAttendance(detectedFaceName) {
        if (!stream) return;

        if (!detectedFaceName) {
            recognitionStatus.textContent = "No face detected";
            return;
        }

        // Find student whose name matches the detected face
        const studentRow = Array.from(document.querySelectorAll('table tbody tr')).find(row => {
            const studentName = row.querySelector('td:nth-child(2)').textContent.trim();
            const statusSelect = row.querySelector('select[name="status"]');
            return statusSelect && statusSelect.value === 'Absent' && studentName === detectedFaceName;
        });

        if (!studentRow) {
            recognitionStatus.textContent = `Face detected but no matching absent student found: ${detectedFaceName}`;
            return;
        }

        const studentId = studentRow.querySelector('input[name="student_id"]').value;
        const statusSelect = document.getElementById(`status-${studentId}`);

        if (statusSelect) {
            statusSelect.value = 'Present';
            lastRecognizedTime = Date.now(); // Update last recognition time

            recognitionStatus.textContent = `Face recognized: ${detectedFaceName}`;
            updateAttendanceUI(studentId, detectedFaceName);
        }
    }


    function updateAttendanceUI(studentId, studentName, detectionTime = null) {
        const now = new Date();
        let timeStr;
        if (detectionTime) {
          timeStr = detectionTime;
        } else {
          timeStr = now.toLocaleTimeString('en-US', {
            hour12: true,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          });
        }

        // Update timestamp display
        const timeElement = document.getElementById(`updated-${studentId}`);
        if (timeElement) {
            const badge = document.createElement('div');
            badge.className = 'badge bg-success rounded-pill';
            badge.innerHTML = `<i class="fas fa-clock me-1"></i> ${timeStr}`;
            timeElement.innerHTML = '';
            timeElement.appendChild(badge);
        }

        // Update hidden timestamp field
        const timeValue = now.toTimeString().split(' ')[0];
        const studentRow = document.querySelector(`input[name="student_id"][value="${studentId}"]`).closest('tr');
        if (studentRow) {
            let timeField = studentRow.querySelector(`input[name="time_in-${studentId}"]`);
            if (!timeField) {
                timeField = document.createElement('input');
                timeField.type = 'hidden';
                timeField.name = `time_in-${studentId}`;
                timeField.value = timeValue;
                const form = document.getElementById('attendance-form');
                form.appendChild(timeField);
            }
        }

        // Show notification
        showNotification(studentName);
        updateSummaryCounts();
        addActivityLog(studentName, 'Present', timeStr);
    }

    function showNotification(studentName) {
        const toastElement = document.createElement('div');
        toastElement.className = 'toast';
        toastElement.setAttribute('role', 'alert');
        toastElement.setAttribute('aria-live', 'assertive');
        toastElement.setAttribute('aria-atomic', 'true');

        toastElement.innerHTML = `
            <div class="toast-header bg-success text-white">
                <i class="fas fa-check-circle me-2"></i>
                <strong class="me-auto">Attendance Marked</strong>
                <small>just now</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                <strong>${studentName}</strong> has been marked present.
            </div>
        `;

        notificationContainer.appendChild(toastElement);
        const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 3000 });
        toast.show();

        toastElement.addEventListener('hidden.bs.toast', () => {
            notificationContainer.removeChild(toastElement);
        });
    }

    function updateSummaryCounts() {
        const statuses = Array.from(document.querySelectorAll('select[name="status"]')).map(el => el.value);
        const presentCount = statuses.filter(s => s === 'Present').length;
        const lateCount = statuses.filter(s => s === 'Late').length;
        const absentCount = statuses.filter(s => s === 'Absent').length;

        document.getElementById('present-count').textContent = presentCount;
        document.getElementById('late-count').textContent = lateCount;
        document.getElementById('absent-count').textContent = absentCount;
    }

    function addActivityLog(studentName, status, time) {
        const activityLog = document.getElementById('activity-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'list-group-item list-group-item-action border-0';

        logEntry.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1 fw-bold">${studentName}</h6>
                <small class="text-muted">${time}</small>
            </div>
            <p class="mb-1">Marked as <span class="status-badge status-${status.toLowerCase()}">${status}</span></p>
        `;

        if (activityLog.firstChild) {
            activityLog.insertBefore(logEntry, activityLog.firstChild);
        } else {
            activityLog.appendChild(logEntry);
        }

        const emptyMessage = activityLog.querySelector('.text-center');
        if (emptyMessage) {
            activityLog.removeChild(emptyMessage);
        }
    }

    // Simulate face detection and recognition (rest of the original functions remain)
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
