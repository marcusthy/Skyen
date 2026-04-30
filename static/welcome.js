// Henter referanser til skjult <input>, dropzone label og elementet som viser valgt filnavn
const input = document.getElementById('fileInput');
const label = document.getElementById('dropzone');
const display = document.getElementById('selectedFile');

// Oppsummerer hvilke filer som er valgt (1 fil → navn, flere → antall + første navn)
function oppdaterValgteFiler() {
    const filer = input.files;
    if (!filer || filer.length === 0) {
        display.textContent = '';
    } else if (filer.length === 1) {
        display.textContent = filer[0].name;
    } else {
        display.textContent = `${filer.length} filer valgt (${filer[0].name}, …)`;
    }
}

// Oppdaterer visningen når brukeren velger filer via fildialogen
input.addEventListener('change', oppdaterValgteFiler);
// Markerer dropzone visuelt når en fil dras over den
label.addEventListener('dragover', e => { e.preventDefault(); label.classList.add('drag-over'); });
label.addEventListener('dragleave', () => label.classList.remove('drag-over'));
// Håndterer drop: legger droppede filer inn i input-elementet og viser oppsummering
label.addEventListener('drop', e => {
    e.preventDefault();
    label.classList.remove('drag-over');
    input.files = e.dataTransfer.files;
    oppdaterValgteFiler();
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
