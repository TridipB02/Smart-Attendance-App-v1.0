// -------------------- Camera Feed Refresh --------------------
function refreshCameraFeed() {
    const img = document.getElementById('cameraFeed');
    if (img) {
        img.src = "/video_feed?t=" + new Date().getTime();
    }
}

// Refresh ~10 FPS
setInterval(refreshCameraFeed, 100);

// -------------------- Exit Camera --------------------
function exitCamera() {
    fetch('/stop_camera')
        .then(() => {
            window.location.href = '/attendance';
        });
}

// -------------------- Dataset Image Preview --------------------
const imageInput = document.getElementById('image');
if (imageInput) {
    const previewContainer = document.createElement('div');
    previewContainer.style.marginTop = "10px";
    imageInput.parentNode.appendChild(previewContainer);

    imageInput.addEventListener('change', function() {
        previewContainer.innerHTML = "";
        const file = this.files[0];
        if (file) {
            const imgPreview = document.createElement('img');
            imgPreview.src = URL.createObjectURL(file);
            imgPreview.style.maxWidth = "150px";
            imgPreview.style.maxHeight = "150px";
            imgPreview.style.border = "1px solid #ccc";
            imgPreview.style.borderRadius = "5px";
            previewContainer.appendChild(imgPreview);
        }
    });
}

// -------------------- Delete Confirmation --------------------
const deleteForms = document.querySelectorAll('.delete-btn');
deleteForms.forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!confirm("Are you sure you want to delete this user?")) {
            e.preventDefault();
        }
    });
});
