// Henter referanser til skjult <input>, dropzone label og elementet som viser valgt filnavn
const input = document.getElementById('fileInput');
const label = document.getElementById('dropzone');
const display = document.getElementById('selectedFile');
// Oppdaterer visningen når brukeren velger fil via fildialogen
input.addEventListener('change', () => {
    display.textContent = input.files[0] ? input.files[0].name : '';
});
// Markerer dropzone visuelt når en fil dras over den
label.addEventListener('dragover', e => { e.preventDefault(); label.classList.add('drag-over'); });
label.addEventListener('dragleave', () => label.classList.remove('drag-over'));
// Håndterer drop: legger droppet fil inn i input-elementet og viser navnet
label.addEventListener('drop', e => {
    e.preventDefault();
    label.classList.remove('drag-over');
    input.files = e.dataTransfer.files;
    display.textContent = input.files[0] ? input.files[0].name : '';
});

// Åpner PDF-modal med en <iframe> som peker på PDF-fila
function openPdf(src, name) {
    document.getElementById('pdfFrame').src = src;
    document.getElementById('pdfName').textContent = name;
    document.getElementById('pdfBackdrop').classList.add('active');
    document.body.style.overflow = 'hidden';
}
// Lukker PDF modalen og fjerner src slik at fila ikke ligger lastet i bakgrunnen
function closePdf() {
    document.getElementById('pdfFrame').src = '';
    document.getElementById('pdfBackdrop').classList.remove('active');
    document.body.style.overflow = '';
}
// Escape-tasten lukker PDF-modalen
document.addEventListener('keydown', e => { if (e.key === 'Escape') closePdf(); });
