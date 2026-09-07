// Create/Edit Object detail JS Logic for RoundReview
// ===========================================

const locationInput = document.getElementById('locationInput');
const locationText = document.getElementById('locationText');
const locationSegments = document.getElementById('locationSegments');
const locationHidden = document.getElementById('locationHidden');
let segments = [];

function renderSegments() {
    // Limit depth to 3
    if (segments.length > 3) {
        segments = segments.slice(0, 3);
    }
    locationSegments.innerHTML = '';
    segments.forEach((seg, idx) => {
        const span = document.createElement('span');
        span.textContent = seg;
        span.style.border = '1px solid #007bff';
        span.style.borderRadius = '4px';
        span.style.padding = '2px 8px';
        span.style.marginRight = '2px';
        span.style.background = 'transparent';
        span.style.marginBottom = '2px';
        span.style.display = 'flex';
        span.style.alignItems = 'center';
        locationSegments.appendChild(span);
        const slash = document.createElement('span');
        slash.textContent = '/';
        slash.style.margin = '0 2px';
        locationSegments.appendChild(slash);
    });
    locationHidden.value = '/' + segments.join('/');
}

locationText.addEventListener('keydown', function(e) {
    if (e.key === '/' && locationText.value.trim() !== '') {
        if (segments.length < 3) {
            segments.push(locationText.value.trim());
            locationText.value = '';
            renderSegments();
        }
        e.preventDefault();
    } else if ((e.key === 'Backspace' || e.key === 'Delete') && locationText.value === '') {
        if (segments.length > 0) {
            segments.pop();
            renderSegments();
            e.preventDefault();
        }
    }
});

locationText.addEventListener('blur', function() {
    if (locationText.value.trim() !== '') {
        if (segments.length < 3) {
            segments.push(locationText.value.trim());
            locationText.value = '';
            renderSegments();
        }
    }
});

locationInput.addEventListener('click', function() {
    locationText.focus();
});


// Handle name of object based on filename during loading
function fileNameLoadingAsName() {
    const objectPdf = document.getElementById('objectPdf');
    const objectName = document.getElementById('objectName');
    const pdfDropZone = document.getElementById('pdfDropZone');
    const pdfDropIcon = pdfDropZone ? pdfDropZone.querySelector('.pdf-drop-icon') : null;
    const pdfDropText = pdfDropZone ? pdfDropZone.querySelector('.pdf-drop-text') : null;

    const updateNameFromFile = () => {
        if (objectPdf.files.length > 0) {
            const fileName = objectPdf.files[0].name;
            const nameWithoutExtension = fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
            if (objectName.value.trim() === '') {
                objectName.value = nameWithoutExtension;
            }
            // Update drop zone display
            if (pdfDropIcon && pdfDropText) {
                pdfDropIcon.innerHTML = '<i class="fas fa-file-pdf"></i>';
                pdfDropText.textContent = fileName;
            }
        }
    };

    objectPdf.addEventListener('change', updateNameFromFile);

    // Handle drag and drop on PDF drop zone
    if (pdfDropZone) {
        pdfDropZone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            pdfDropZone.classList.add('drag-over');
        });

        pdfDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        pdfDropZone.addEventListener('dragleave', (e) => {
            if (!pdfDropZone.contains(e.relatedTarget)) {
                pdfDropZone.classList.remove('drag-over');
            }
        });

        pdfDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            pdfDropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type !== 'application/pdf') {
                    window.alert('Only PDF files can be uploaded.');
                    return;
                }
                const transfer = new DataTransfer();
                transfer.items.add(file);
                objectPdf.files = transfer.files;
                updateNameFromFile();
            }
        });

        pdfDropZone.addEventListener('click', () => {
            objectPdf.click();
        });
    }
}


document.addEventListener('DOMContentLoaded', () => {
    // Apply if objectPdf is present
    if (document.getElementById('objectPdf') != null)
        fileNameLoadingAsName();

    // Initialize segments if locationHidden has a value
    if (locationHidden.value && locationHidden.value.trim() !== '') {
        segments = locationHidden.value.split('/').filter(Boolean);
    }
    renderSegments();
});
