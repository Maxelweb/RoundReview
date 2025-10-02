// Create/Edit Object detail JS Logic for RoundReview
// ===========================================

const locationInput = document.getElementById('locationInput');
const locationText = document.getElementById('locationText');
const locationSegments = document.getElementById('locationSegments');
const locationHidden = document.getElementById('locationHidden');
let segments = [];

// Initialize segments if locationHidden has a value
if (locationHidden.value && locationHidden.value.trim() !== '') {
    segments = locationHidden.value.split('/').filter(Boolean);
}

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
        if (idx < segments.length - 1) {
            const slash = document.createElement('span');
            slash.textContent = '/';
            slash.style.margin = '0 2px';
            locationSegments.appendChild(slash);
        }
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

// If there's a value in the hidden input (e.g. from server), render segments
renderSegments();



// Object PDF
// FIXME: do not include in edit
const objectPdf = document.getElementById('objectPdf');
const objectName = document.getElementById('objectName');

objectPdf.addEventListener('change', function() {
    if (objectName.value.trim() === '' && objectPdf.files.length > 0) {
        const fileName = objectPdf.files[0].name;
        const nameWithoutExtension = fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
        objectName.value = nameWithoutExtension;
    }
});