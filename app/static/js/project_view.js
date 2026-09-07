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
    
    const moveFileDialog = document.getElementById('move-file-dialog');
    const moveFileForm = document.getElementById('move-file-form');
    const moveFileName = document.getElementById('moveFileName');
    const moveFromPath = document.getElementById('moveFromPath');
    const moveToPath = document.getElementById('moveToPath');

    let draggedFile = null;
    let folderAutoOpenTimer = null;

    if (dropDialog && dropFile) {
        let activeFolder = null;

        const isFileDrag = event => event.dataTransfer && event.dataTransfer.types.includes('Files');
        const isFileRowDrag = event => event.dataTransfer && event.dataTransfer.types.includes('text/plain') && draggedFile;

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

        const toggleFolder = (folderRow) => {
            const folderPath = folderRow.dataset.folderPath;
            const folderContent = document.querySelector(`.folder-file[data-folder-path="${folderPath}"]`);
            if (folderContent && folderContent.style.display === 'none') {
                folderContent.style.display = '';
                folderRow.dataset.open = true;
            }
        };

        const openFolderAndParents = (folderRow) => {
            // Open this folder
            toggleFolder(folderRow);
            // Find and open all parent folders recursively
            let current = folderRow;
            while (current) {
                const parentFolderFile = current.closest('.folder-file');
                if (parentFolderFile) {
                    const parentPath = parentFolderFile.dataset.folderPath;
                    const parentFolderRow = document.querySelector(`.folder-row[data-folder-path="${parentPath}"]`);
                    if (parentFolderRow) {
                        toggleFolder(parentFolderRow);
                        current = parentFolderRow;
                    } else {
                        break;
                    }
                } else {
                    break;
                }
            }
        };

        document.querySelectorAll('.dialog-close').forEach(button => {
            button.addEventListener('click', () => {
                dropDialog.close();
                moveFileDialog.close();
            });
        });

        // Handle file row click to navigate
        document.querySelectorAll('.file-row').forEach(fileRow => {
            fileRow.addEventListener('click', event => {
                // Don't navigate if clicking on drag handle
                if (event.target.closest('.file-drag-handle')) return;
                const objectUrl = fileRow.dataset.objectUrl;
                if (objectUrl) {
                    window.location.href = objectUrl;
                }
            });
        });

        // Handle file row drag
        document.querySelectorAll('.file-drag-handle').forEach(dragHandle => {
            dragHandle.addEventListener('dragstart', event => {
                const fileRow = dragHandle.closest('.file-row');
                draggedFile = {
                    id: fileRow.dataset.fileId,
                    name: fileRow.dataset.fileName,
                    path: fileRow.dataset.filePath
                };
                fileRow.classList.add('drag-source');
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', draggedFile.id);
            });

            dragHandle.addEventListener('dragend', event => {
                const fileRow = dragHandle.closest('.file-row');
                fileRow.classList.remove('drag-source');
            });
        });

        document.querySelectorAll('.folder-row').forEach(folderRow => {
            folderRow.addEventListener('dragenter', event => {
                if (!isFileDrag(event) && !isFileRowDrag(event)) return;
                event.preventDefault();
                folderRow.classList.add('drag-over');
                
                // Auto-open folder after 1 second if file is being dragged
                if (isFileRowDrag(event)) {
                    folderAutoOpenTimer = setTimeout(() => {
                        openFolderAndParents(folderRow);
                    }, 1000);
                }
            });

            folderRow.addEventListener('dragover', event => {
                if (!isFileDrag(event) && !isFileRowDrag(event)) return;
                event.preventDefault();
                event.dataTransfer.dropEffect = isFileDrag(event) ? 'copy' : 'move';
            });

            folderRow.addEventListener('dragleave', event => {
                if (!folderRow.contains(event.relatedTarget)) {
                    folderRow.classList.remove('drag-over');
                    if (folderAutoOpenTimer) {
                        clearTimeout(folderAutoOpenTimer);
                        folderAutoOpenTimer = null;
                    }
                }
            });

            folderRow.addEventListener('drop', event => {
                if (isFileRowDrag(event)) {
                    event.preventDefault();
                    folderRow.classList.remove('drag-over');
                    if (folderAutoOpenTimer) {
                        clearTimeout(folderAutoOpenTimer);
                        folderAutoOpenTimer = null;
                    }
                    
                    const targetPath = folderRow.dataset.folderPath;
                    if (draggedFile && draggedFile.path !== targetPath) {
                        // Show move confirmation dialog
                        moveFileName.textContent = draggedFile.name;
                        moveFromPath.textContent = draggedFile.path;
                        moveToPath.textContent = targetPath;
                        moveFileDialog.showModal();
                        
                        // Store target path for form submission
                        moveFileForm.dataset.fileId = draggedFile.id;
                        moveFileForm.dataset.targetPath = targetPath;
                    }
                    draggedFile = null;
                } else if (isFileDrag(event)) {
                    folderRow.classList.remove('drag-over');
                    activeFolder = folderRow;
                    openDropDialog(folderRow);
                    handleFileDrop(event);
                }
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

        // Handle move file form submission
        if (moveFileForm) {
            moveFileForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const fileId = moveFileForm.dataset.fileId;
                const targetPath = moveFileForm.dataset.targetPath;
                
                if (!fileId || !targetPath) return;

                try {
                    const projectId = window.location.pathname.split('/')[2];
                    const response = await fetch(`/projects/${projectId}/objects/${fileId}/edit`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            'object_id': fileId,
                            'path': targetPath
                        })
                    });

                    if (response.ok) {
                        moveFileDialog.close();
                        window.location.reload();
                    } else {
                        window.alert('Failed to move document. Please try again.');
                    }
                } catch (error) {
                    console.error('Error moving file:', error);
                    window.alert('Error moving document: ' + error.message);
                }
            });
        }
    }
});

