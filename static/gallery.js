function handleTile(el) {
    const src = el.dataset.src;
    const name = el.dataset.name;
    const download = el.dataset.download;
    const filId = el.dataset.filId;
    if (el.dataset.video === 'true') {
        openVideo(src, name, download, filId);
    } else {
        openModal(src, name, download, filId);
    }
}
function openModal(src, name, downloadUrl, filId) {
    document.getElementById('modalImg').src = src;
    document.getElementById('modalName').textContent = name;
    document.getElementById('modalDownload').href = downloadUrl;
    document.getElementById('modalDeleteForm').action = '/slett/' + filId;
    document.getElementById('modalBackdrop').classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closeModal() {
    document.getElementById('modalBackdrop').classList.remove('active');
    document.body.style.overflow = '';
    document.getElementById('modalImg').src = '';
}
function openVideo(src, name, downloadUrl, filId) {
    document.getElementById('modalVideo').src = src;
    document.getElementById('videoName').textContent = name;
    document.getElementById('videoDownload').href = downloadUrl;
    document.getElementById('videoDeleteForm').action = '/slett/' + filId;
    document.getElementById('videoBackdrop').classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closeVideo() {
    const v = document.getElementById('modalVideo');
    v.pause();
    v.src = '';
    document.getElementById('videoBackdrop').classList.remove('active');
    document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeModal(); closeVideo(); } });
