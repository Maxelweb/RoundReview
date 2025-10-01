// View Objects in Project JS Logic for RoundReview
// ================================================

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


function formatRelativeDate(isoTimestamp) {
    const inputDate = new Date(isoTimestamp);
    const now = new Date();

    const inputMidnight = new Date(inputDate.getFullYear(), inputDate.getMonth(), inputDate.getDate());
    const nowMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const diffTime = nowMidnight - inputMidnight;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    const hours = inputDate.getHours().toString().padStart(2, '0');
    const minutes = inputDate.getMinutes().toString().padStart(2, '0');

    if (diffDays === 0) {
        return `today, ${hours}:${minutes}`;
    } else if (diffDays === 1) {
        return `yesterday, ${hours}:${minutes}`;
    } else if (isNaN(diffDays)) {
        return ``;
    } else {
        return `${diffDays} days ago`;
    }
}
