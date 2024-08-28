document.addEventListener('DOMContentLoaded', function() {
    // Fetch logs when the page loads
    fetchLogs();

    // Set up form submission event listener
    document.getElementById('upload-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        document.getElementById('loading').style.display = 'block';
        document.getElementById('results').style.display = 'none';
        document.getElementById('error').style.display = 'none';

        axios.post('/process', formData)
            .then(function (response) {
                // Existing code...
            })
            .catch(function (error) {
                // Existing code...
            });
    });

    // Set up download buttons
    const downloadNewRowsButton = document.getElementById('download-new-rows');
    const downloadNonExistingRowsButton = document.getElementById('download-non-existing-rows');

    if (downloadNewRowsButton) {
        downloadNewRowsButton.addEventListener('click', function() {
            downloadRows('new_rows');
        });
    }

    if (downloadNonExistingRowsButton) {
        downloadNonExistingRowsButton.addEventListener('click', function() {
            downloadRows('non_existing_rows');
        });
    }
});

function fetchLogs() {
    axios.get('/logs')
        .then(function (response) {
            document.getElementById('log-content').textContent = response.data.join('\n');
        })
        .catch(function (error) {
            console.error('Error fetching logs:', error);
        });
}

document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    axios.post('/process', formData)
        .then(function (response) {
            document.getElementById('loading').style.display = 'none';
            if (response.data.error) {
                document.getElementById('error').textContent = response.data.error;
                document.getElementById('error').style.display = 'block';
                console.error('Server returned an error:', response.data.error);
            } else {
                document.getElementById('results').style.display = 'block';
                document.getElementById('new-rows-count').textContent = response.data.new_rows_count;
                document.getElementById('non-existing-rows-count').textContent = response.data.non_existing_rows_count;
                document.getElementById('download-new-rows').disabled = false;
                document.getElementById('download-non-existing-rows').disabled = false;
            }
            fetchLogs();
        })
        .catch(function (error) {
            document.getElementById('loading').style.display = 'none';
            console.error('Axios error:', error);
            if (error.response) {
                console.error('Error data:', error.response.data);
                console.error('Error status:', error.response.status);
                console.error('Error headers:', error.response.headers);
            } else if (error.request) {
                console.error('Error request:', error.request);
            } else {
                console.error('Error message:', error.message);
            }
            document.getElementById('error').textContent = 'An error occurred while processing the files. Please check the browser console for more details.';
            document.getElementById('error').style.display = 'block';
            fetchLogs();
        });
});

// Add event listeners for download buttons if they exist
const downloadNewRowsButton = document.getElementById('download-new-rows');
const downloadNonExistingRowsButton = document.getElementById('download-non-existing-rows');

if (downloadNewRowsButton) {
    downloadNewRowsButton.addEventListener('click', function() {
        downloadRows('new_rows');
    });
}

if (downloadNonExistingRowsButton) {
    downloadNonExistingRowsButton.addEventListener('click', function() {
        downloadRows('non_existing_rows');
    });
}

function downloadRows(downloadType) {
    const formData = new FormData(document.getElementById('upload-form'));
    formData.append('download_type', downloadType);

    axios.post('/download', formData, { responseType: 'blob' })
        .then(function (response) {
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', downloadType === 'new_rows' ? 'new_rows.xlsx' : 'non_existing_rows.xlsx');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            fetchLogs();
        })
        .catch(function (error) {
            console.error('Download error:', error);
            fetchLogs();
        });
}

// Fetch logs when the page loads
fetchLogs();