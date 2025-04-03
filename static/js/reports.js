/**
 * Reports JavaScript
 * Handles attendance report data visualization using Chart.js
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the reports page
    const attendanceChart = document.getElementById('attendance-chart');
    const studentChart = document.getElementById('student-chart');

    if (!attendanceChart && !studentChart) return; // Not on the reports page

    // Fetch date-based report data
    function fetchDateReport(date) {
        console.log("Generating date report for:", date);
        const url = `/api/date_attendance?date=${date}`;
        console.log("Fetching data from:", url);

        fetch(url)
            .then(response => {
                console.log("API Response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("API Data received:", data);
                if (data && data.stats) {
                    updateDateChart(data);
                    updateAttendanceTable(data.attendance_records);
                    updateAttendanceStats(data.stats);
                }
            })
            .catch(error => {
                console.error("Error fetching date attendance:", error);
                showError("Failed to load attendance data. Please try again.");
            });
    }

    // Fetch student-based report data
    function fetchStudentReport(studentId, startDate, endDate) {
        const url = `/api/student_attendance?student_id=${studentId}&start_date=${startDate}&end_date=${endDate}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data && data.stats) {
                    updateStudentChart(data);
                    updateStudentAttendanceTable(data.attendance_records);
                    updateStudentStats(data.stats);
                }
            })
            .catch(error => {
                console.error("Error fetching student attendance:", error);
                showError("Failed to load student attendance data. Please try again.");
            });
    }

    // Update the date-based attendance chart
    function updateDateChart(data) {
        if (!attendanceChart) return;

        // Create or update chart
        if (window.attendanceChartInstance) {
            window.attendanceChartInstance.destroy();
        }

        const ctx = attendanceChart.getContext('2d');
        window.attendanceChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Late', 'Absent'],
                datasets: [{
                    data: [data.stats.present, data.stats.late, data.stats.absent],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',  // green for present
                        'rgba(255, 193, 7, 0.8)',  // yellow for late
                        'rgba(220, 53, 69, 0.8)'   // red for absent
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Update the student-specific attendance chart
    function updateStudentChart(data) {
        if (!studentChart) return;

        // Prepare data for chart - count status occurrences by date
        const dateLabels = [];
        const presentData = [];
        const lateData = [];
        const absentData = [];

        // Process attendance records
        data.attendance_records.forEach(record => {
            if (!dateLabels.includes(record.date)) {
                dateLabels.push(record.date);
            }

            const index = dateLabels.indexOf(record.date);

            // Initialize data arrays
            if (presentData.length <= index) presentData.push(0);
            if (lateData.length <= index) lateData.push(0);
            if (absentData.length <= index) absentData.push(0);

            // Increment appropriate counter
            if (record.status === 'Present') {
                presentData[index]++;
            } else if (record.status === 'Late') {
                lateData[index]++;
            } else if (record.status === 'Absent') {
                absentData[index]++;
            }
        });

        // Create or update chart
        if (window.studentChartInstance) {
            window.studentChartInstance.destroy();
        }

        const ctx = studentChart.getContext('2d');
        window.studentChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dateLabels,
                datasets: [
                    {
                        label: 'Present',
                        data: presentData,
                        backgroundColor: 'rgba(40, 167, 69, 0.8)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Late',
                        data: lateData,
                        backgroundColor: 'rgba(255, 193, 7, 0.8)',
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Absent',
                        data: absentData,
                        backgroundColor: 'rgba(220, 53, 69, 0.8)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Update attendance table with records
    function updateAttendanceTable(records) {
        const tableBody = document.getElementById('attendance-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (records.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-3">No attendance records found</td>
                </tr>
            `;
            return;
        }

        records.forEach(record => {
            const statusClass = record.status === 'Present' ? 'status-present' :
                              (record.status === 'Late' ? 'status-late' : 'status-absent');

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.display_id}</td>
                <td>${record.name}</td>
                <td><span class="status-badge ${statusClass}">${record.status}</span></td>
                <td>${record.time_in || 'N/A'}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Update student attendance table with records
    function updateStudentAttendanceTable(records) {
        const tableBody = document.getElementById('student-attendance-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (records.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center py-3">No attendance records found</td>
                </tr>
            `;
            return;
        }

        records.forEach(record => {
            const statusClass = record.status === 'Present' ? 'status-present' :
                              (record.status === 'Late' ? 'status-late' : 'status-absent');

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.date}</td>
                <td><span class="status-badge ${statusClass}">${record.status}</span></td>
                <td>${record.time_in || 'N/A'}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Update attendance stats display
    function updateAttendanceStats(stats) {
        if (document.getElementById('total-count')) {
            document.getElementById('total-count').textContent = stats.total;
        }
        if (document.getElementById('present-count')) {
            document.getElementById('present-count').textContent = stats.present;
        }
        if (document.getElementById('late-count')) {
            document.getElementById('late-count').textContent = stats.late;
        }
        if (document.getElementById('absent-count')) {
            document.getElementById('absent-count').textContent = stats.absent;
        }
        if (document.getElementById('attendance-rate')) {
            document.getElementById('attendance-rate').textContent = `${Math.round(stats.attendance_rate)}%`;
        }
    }

    // Update student stats display
    function updateStudentStats(stats) {
        if (document.getElementById('student-total')) {
            document.getElementById('student-total').textContent = stats.total;
        }
        if (document.getElementById('student-present')) {
            document.getElementById('student-present').textContent = stats.present;
        }
        if (document.getElementById('student-late')) {
            document.getElementById('student-late').textContent = stats.late;
        }
        if (document.getElementById('student-absent')) {
            document.getElementById('student-absent').textContent = stats.absent;
        }
        if (document.getElementById('student-rate')) {
            const rate = stats.total > 0 ? Math.round(((stats.present + stats.late) / stats.total) * 100) : 0;
            document.getElementById('student-rate').textContent = `${rate}%`;
        }
    }

    // Show error message
    function showError(message) {
        const errorContainer = document.getElementById('error-container');
        if (!errorContainer) return;

        errorContainer.textContent = message;
        errorContainer.classList.remove('d-none');

        setTimeout(() => {
            errorContainer.classList.add('d-none');
        }, 5000);
    }

    // Set up event listeners for date selector
    const dateSelector = document.getElementById('date-selector');
    if (dateSelector) {
        // Set default date to today
        const today = new Date().toISOString().split('T')[0];
        dateSelector.value = today;

        // Initial data load
        fetchDateReport(today);

        // Add change event listener
        dateSelector.addEventListener('change', function() {
            fetchDateReport(this.value);
        });
    }

    // Set up event listeners for student and date range selectors
    const studentSelector = document.getElementById('student-selector');
    const startDateSelector = document.getElementById('start-date');
    const endDateSelector = document.getElementById('end-date');
    const generateReportBtn = document.getElementById('generate-report');

    if (studentSelector && startDateSelector && endDateSelector && generateReportBtn) {
        // Set default dates
        const today = new Date();
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(today.getMonth() - 1);

        startDateSelector.value = oneMonthAgo.toISOString().split('T')[0];
        endDateSelector.value = today.toISOString().split('T')[0];

        // Add click event listener for the generate report button
        generateReportBtn.addEventListener('click', function() {
            const studentId = studentSelector.value;
            const startDate = startDateSelector.value;
            const endDate = endDateSelector.value;

            if (!studentId) {
                showError("Please select a student");
                return;
            }

            fetchStudentReport(studentId, startDate, endDate);
        });
    }
});
