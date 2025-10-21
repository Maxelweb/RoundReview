// View Objects in Project JS Logic for RoundReview
// ================================================

import { formatRelativeDate } from "./utils/date.js"

document.addEventListener('DOMContentLoaded', function () {
    
    const allObjectLastUpdates = document.querySelectorAll('.object-last-update');
    allObjectLastUpdates.forEach(el => {
        const isoTimestamp = el.getAttribute('data-timestamp');
        if (isoTimestamp) {
            el.textContent = formatRelativeDate(isoTimestamp);
        }
    });

    const folderLinks = document.querySelectorAll('.folder-link');
    folderLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const folderPath = this.closest('.folder-row').dataset.folderPath;
            const folderContent = document.querySelector(`.folder-file[data-folder-path="${folderPath}"]`);
            if (folderContent) {
                const isOpen = folderContent.style.display !== 'none';
                folderContent.style.display = isOpen ? 'none' : '';
                this.closest('.folder-row').dataset.open = !isOpen;
            }
        });
    });
});

