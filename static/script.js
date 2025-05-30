document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('file-name');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    // Update file name display
    fileInput.addEventListener('change', function(e) {
        fileName.textContent = e.target.files[0] ? e.target.files[0].name : 'Selecione um arquivo Excel (.xlsx)';
    });

    // Form submission with progress bar
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        const xhr = new XMLHttpRequest();
        
        // Show progress bar
        progressContainer.style.display = 'block';
        submitBtn.disabled = true;
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percent + '%';
                progressText.textContent = percent + '%';
                
                // Change color when complete
                if (percent === 100) {
                    progressBar.style.background = 'linear-gradient(90deg, #27ae60, #2ecc71)';
                }
            }
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                // Handle successful response
                window.location.href = '/'; // Refresh to show success
            } else {
                alert('Ocorreu um erro ao processar o arquivo.');
            }
            
            // Reset form after delay
            setTimeout(function() {
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
                progressText.textContent = '0%';
                progressBar.style.background = 'linear-gradient(90deg, #3498db, #1a5276)';
                submitBtn.disabled = false;
            }, 2000);
        });
        
        xhr.open('POST', uploadForm.action, true);
        xhr.send(formData);
    });
});
