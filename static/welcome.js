const input = document.getElementById('fileInput');
const label = document.getElementById('dropzone');
const display = document.getElementById('selectedFile');
input.addEventListener('change', () => {
    display.textContent = input.files[0] ? input.files[0].name : '';
});
label.addEventListener('dragover', e => { e.preventDefault(); label.classList.add('drag-over'); });
label.addEventListener('dragleave', () => label.classList.remove('drag-over'));
label.addEventListener('drop', e => {
    e.preventDefault();
    label.classList.remove('drag-over');
    input.files = e.dataTransfer.files;
    display.textContent = input.files[0] ? input.files[0].name : '';
});

function openPdf(src, name) {
    document.getElementById('pdfFrame').src = src;
    document.getElementById('pdfName').textContent = name;
    document.getElementById('pdfBackdrop').classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closePdf() {
    document.getElementById('pdfFrame').src = '';
    document.getElementById('pdfBackdrop').classList.remove('active');
    document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closePdf(); });
