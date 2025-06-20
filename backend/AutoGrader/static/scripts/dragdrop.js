document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('.dropzone').forEach(zone => {
        const fileInput = zone.querySelector('input[type="file"]');

        zone.addEventListener('click', () => fileInput.click());

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            fileInput.files = files;

            const fileNames = Array.from(files).map(file => file.name).join(', ');
            zone.querySelector('p').textContent = `Archivo seleccionado: ${fileNames}`;
        });
    });
});
