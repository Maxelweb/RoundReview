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

    const dropDialog = document.getElementById('drop-upload-dialog');
    const dropFile = document.getElementById('dropObjectPdf');
    const dropName = document.getElementById('dropObjectName');
    const dropLocation = document.getElementById('dropLocation');
    const dropLocationHidden = document.getElementById('dropLocationHidden');
    const dropForm = dropDialog ? dropDialog.querySelector('form') : null;

    if (dropDialog && dropFile) {
        let activeFolder = null;

        const isFileDrag = event => event.dataTransfer && event.dataTransfer.types.includes('Files');

        const openDropDialog = folderRow => {
            const folderPath = folderRow.dataset.folderPath;
            activeFolder = folderRow;
            dropLocation.textContent = folderPath;
            dropLocationHidden.value = folderPath;
            dropDialog.showModal();
        };

        const handleFileDrop = event => {
            if (!isFileDrag(event)) return;
            event.preventDefault();
            if (activeFolder) activeFolder.classList.remove('drag-over');
            const file = event.dataTransfer.files[0];
            if (!file || file.type !== 'application/pdf') {
                dropDialog.close();
                window.alert('Only PDF files can be uploaded.');
                return;
            }

            const transfer = new DataTransfer();
            transfer.items.add(file);
            dropFile.files = transfer.files;
            if (!dropName.value) {
                dropName.value = file.name.replace(/\.pdf$/i, '');
            }
            dropName.focus();
        };

        document.querySelectorAll('.dialog-close').forEach(button => {
            button.addEventListener('click', () => dropDialog.close());
        });

        document.querySelectorAll('.folder-row').forEach(folderRow => {
            folderRow.addEventListener('dragenter', event => {
                if (!isFileDrag(event)) return;
                event.preventDefault();
                folderRow.classList.add('drag-over');
            });

            folderRow.addEventListener('dragover', event => {
                if (!isFileDrag(event)) return;
                event.preventDefault();
                event.dataTransfer.dropEffect = 'copy';
            });

            folderRow.addEventListener('dragleave', event => {
                if (!folderRow.contains(event.relatedTarget)) {
                    folderRow.classList.remove('drag-over');
                }
            });

            folderRow.addEventListener('drop', event => {
                folderRow.classList.remove('drag-over');
                activeFolder = folderRow;
                openDropDialog(folderRow);
                handleFileDrop(event);
            });
        });

        dropDialog.addEventListener('dragover', event => {
            if (!isFileDrag(event)) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
        });
        dropDialog.addEventListener('drop', handleFileDrop);

        dropDialog.addEventListener('close', () => {
            if (activeFolder) activeFolder.classList.remove('drag-over');
            activeFolder = null;
            if (dropForm) dropForm.reset();
        });
    }
});

