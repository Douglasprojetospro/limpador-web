document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('file-name');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    // Exibir nome do arquivo selecionado
    fileInput.addEventListener('change', function (e) {
        fileName.textContent = e.target.files[0]
            ? e.target.files[0].name
            : 'Selecione um arquivo Excel (.xlsx)';
    });

    // Envio do formulário com barra de progresso
    uploadForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(uploadForm);
        const xhr = new XMLHttpRequest();

        progressContainer.style.display = 'block';
        submitBtn.disabled = true;

        xhr.upload.addEventListener('progress', function (e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percent + '%';
                progressText.textContent = percent + '%';

                if (percent === 100) {
                    progressBar.style.background = 'linear-gradient(90deg, #27ae60, #2ecc71)';
                }
            }
        });

        xhr.addEventListener('load', function () {
            if (xhr.status === 200) {
                // Forçar download se a resposta for arquivo
                const disposition = xhr.getResponseHeader('Content-Disposition');
                const filename = disposition
                    ? (disposition.match(/filename="(.+)"/) || [])[1] || 'dados_processados.xlsx'
                    : 'dados_processados.xlsx';

                const blob = xhr.response;
                const link = document.createElement('a');
                const url = window.URL.createObjectURL(blob);
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                alert('Ocorreu um erro ao processar o arquivo.');
            }

            setTimeout(function () {
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
                progressText.textContent = '0%';
                progressBar.style.background = 'linear-gradient(90deg, #3498db, #1a5276)';
                submitBtn.disabled = false;
                uploadForm.reset();
                fileName.textContent = 'Selecione um arquivo Excel (.xlsx)';
            }, 2000);
        });

        xhr.open('POST', uploadForm.action, true);
        xhr.responseType = 'blob';
        xhr.send(formData);
    });
});
