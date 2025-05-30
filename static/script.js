document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('file-name');
    const quoteForm = document.getElementById('quoteForm');
    const submitBtn = document.getElementById('submitBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultsTable = document.getElementById('resultsTable').getElementsByTagName('tbody')[0];

    // Update file name display
    fileInput.addEventListener('change', function(e) {
        fileName.textContent = e.target.files[0] ? e.target.files[0].name : 'Selecione o arquivo';
    });

    // Form submission with progress bar
    quoteForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(quoteForm);
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
                    progressBar.style.backgroundColor = var(--success-color);
                }
            }
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                updateResultsTable(response.data);
            } else {
                alert('Ocorreu um erro ao processar a planilha.');
            }
            
            // Reset form after delay
            setTimeout(function() {
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
                progressText.textContent = '0%';
                progressBar.style.backgroundColor = var(--secondary-color);
                submitBtn.disabled = false;
            }, 2000);
        });
        
        xhr.open('POST', quoteForm.action, true);
        xhr.send(formData);
    });
    
    // Function to update results table
    function updateResultsTable(data) {
        // Clear existing rows
        resultsTable.innerHTML = '';
        
        // Add new rows
        data.forEach(function(row) {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>${row.Nota || 'N/A'}</td>
                <td>${row.Descricao || 'N/A'}</td>
                <td>${row.Transportadora || 'Nenhuma cotação'}</td>
                <td>${row.ValorFrete || 'R$ 0,00'}</td>
                <td>${row.Prazo || 'N/A'}</td>
                <td>${row.ICMS || 'R$ 0,00'}</td>
                <td>${row.AliquotaICMS || '0%'}</td>
            `;
            
            resultsTable.appendChild(tr);
        });
    }
    
    // Initial empty state for table
    updateResultsTable([
        { Nota: 'SUL', Descricao: 'SUDESTE LOGISTICA E TRANSPORTES LTDA' },
        { Nota: 'SUL', Descricao: 'SUDESTE LOGISTICA E TRANSPORTES LTDA' },
        { Nota: 'SUL', Descricao: 'SUDESTE LOGISTICA E TRANSPORTES LTDA' },
        { Nota: 'MIRELLA', Descricao: 'TRANSPORTES LOG LTDA' },
        { Nota: 'REUNIDAS', Descricao: 'TRANSPORTES S/A' },
        { Nota: 'FAST', Descricao: 'TRANSPORTES LTDA' }
    ]);
});
