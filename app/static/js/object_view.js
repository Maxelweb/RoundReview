// View Object detail JS Logic for RoundReview
// ===========================================

import { renderText } from "./utils/text.js";
import { buildOutlineList } from "./object/viewer.js";
import { getObjectComments, putObject } from "./object/xhttp.js";
import { saveComment, focusCommentFromSidebarToPdf, focusCommentFromPdfToSidebar } from "./object/comments.js"
import { saveLocalSettings } from "./object/storage.js";

// ======================= Variables and Constants =======================

let pdfCurrentScale = 1.20;
let pdfInstance = null;
let pdfCurrentPage = 1;
let lastClick = { x: 0, y: 0 };
let objectCurrentStatusIndex;
let commentsModePerPage = true;
let nightModeEnabled = false;


const pdfDefaultScale = 1.20;
const pdfUrl = document.getElementById("pdf-container").getAttribute("data-pdf-url");
const pdfObjectId = document.getElementById("pdf-container").getAttribute("data-pdf-object-id");

const pdfMarkers = document.getElementById("markers");
const commentTextarea = document.getElementById("comment-input");
const commentsList = document.getElementById("comments-list");

const currentPageNumDisplay = document.getElementById("page-num");
const totalPageNumDisplay = document.getElementById("total-pages-num");

const pageScaleDisplay = document.getElementById("page-scale");
const totalPageComments = document.getElementById("total-page-comments");
const selectStatusElement = document.getElementById("status-label");
const buttonEditElement = document.getElementById("edit-object-button");

const commentsEnabled = document.getElementById("author-info").getAttribute("data-author-can-comment") == "True";

const editingEnabled = document.getElementById("author-info").getAttribute("data-author-can-edit") == "True";

const buttonToggleOutline = document.getElementById("toggle-outline");
const outlineList = document.getElementById("pdf-outline");

const buttonToggleInformation = document.getElementById("toggle-information");
const buttonCloseInformation = document.getElementById("close-information");
const informationMenu = document.getElementById('information-menu');

const selectCommentsMode = document.getElementById('comments-mode');
const buttonNightMode = document.getElementById('night-mode')

// ======================= PDF Rendering =======================

// Render page with annotations
function renderPage(pageNumber, scale = pdfCurrentScale) {
    const canvas = document.getElementById("pdf-canvas");
    const context = canvas.getContext("2d");
    pdfInstance.getPage(pageNumber).then(page => {
        const viewport = page.getViewport({ scale });
        canvas.width =  viewport.width;
        canvas.height = viewport.height;
        const renderContext = { canvasContext: context, viewport };
        return page.render(renderContext).promise;
    }).then(() => {
        currentPageNumDisplay.textContent = pageNumber;
        pdfCurrentPage = pageNumber;
        loadComments(commentsModePerPage);
    });
}

// Get document and render PDF
pdfjsLib.getDocument(pdfUrl).promise.then(pdf => {
    pdfInstance = pdf;
    totalPageNumDisplay.textContent = pdfInstance.numPages;
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);

    // Get the outline
    pdfInstance.getOutline().then(function(outline) {
        const outlineContainer = document.getElementById('pdf-outline-list');
        if (!Array.isArray(outline)) {
            outlineContainer.innerHTML = '<li>No outline available</li>';
            return;
        }
        buildOutlineList(outline, outlineContainer, pdfInstance, renderPage);
    });

});

// ======================= PDF Toolbar =======================

// Handle night mode
buttonNightMode.addEventListener("click", event => {
    toggleNightMode();
});

function toggleNightMode() {
    const target = buttonNightMode;
    if (target.classList.contains("fa-sun")) {
        document.getElementById('pdf-canvas').style.filter = 'invert(64%) contrast(228%) brightness(80%) hue-rotate(180deg)';
        target.classList.remove("fa-sun");
        target.classList.add("fa-moon");
        nightModeEnabled = true;
    } else {
        document.getElementById('pdf-canvas').style.filter = null;
        target.classList.remove("fa-moon");
        target.classList.add("fa-sun");
        nightModeEnabled = false;
    }
    saveLocalSettings(nightModeEnabled);
}

// Handle toggle outline event
buttonToggleOutline.addEventListener("click", event => {
    outlineList.classList.toggle("open");
});

// Event listener to handle the rendering of the next page
document.getElementById("next-page").addEventListener("click", () => {
    pdfNextPage();
});

// Event listener to handle the rendering of the previous page
document.getElementById("prev-page").addEventListener("click", () => {
    pdfPrevPage();
});

function pdfNextPage() {
    if (pdfCurrentPage < pdfInstance.numPages) {
        pdfCurrentPage++;
        renderPage(pdfCurrentPage);
    }
}

function pdfPrevPage() {
    if (pdfCurrentPage > 1) {
        pdfCurrentPage--;
        renderPage(pdfCurrentPage);
    }
}


// Event listener to show or not the reset button
function updateResetButtonVisibility() {
    document.getElementById("reset-scale").style.display = (pdfCurrentScale !== pdfDefaultScale) ? "inline-block" : "none";
}

// Event listeners for zooming in and out
document.getElementById("page-zoom-in").addEventListener("click", () => {
    pdfCurrentScale = Math.min(pdfCurrentScale + 0.25, 3); // Ensure pdfscale does not exceed 3
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);
    updateResetButtonVisibility();
});

// Event listeners for zooming in and out
document.getElementById("page-zoom-out").addEventListener("click", () => {
    if (pdfCurrentScale > 0.5) {
        pdfCurrentScale = Math.max(pdfCurrentScale - 0.25, 0.5); // Ensure pdfscale does not go below 0.5
        pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
        renderPage(pdfCurrentPage);
    }
    updateResetButtonVisibility();
});

// Event listener for resetting scale
document.getElementById("reset-scale").addEventListener("click", () => {
    pdfCurrentScale = pdfDefaultScale;
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);
    updateResetButtonVisibility();
});

// Handle prev page and next page with left / right keys
document.addEventListener('keydown', function(event) {
    if (commentTextarea.style.display != 'none')
        return;

    switch (event.key) {
        case 'ArrowLeft':
            pdfPrevPage();
            break;
        case 'ArrowRight':
            pdfNextPage();
            break;
    }
});


// Handle PDF Select Status Color
document.getElementById("status-label").addEventListener("change", () => {
    // Check user permission
    if (!editingEnabled){
        return false;
    }
    putObject("/api/objects/" + pdfObjectId, {"status": document.getElementById("status-label").value}, (error, res) => {
        if (res){
            updateStatusColor();
        } else {
            selectStatusElement.selectedIndex = objectCurrentStatusIndex;
            alert(error);
        }
            
    });
});

function updateStatusColor() {
    objectCurrentStatusIndex = selectStatusElement.selectedIndex; // Save initial status
    const selectedOption = selectStatusElement.options[selectStatusElement.selectedIndex];
    const color = selectedOption.getAttribute('data-color');
    selectStatusElement.style.backgroundColor = color || 'black';
}

// ======================= Object Sidebar =======================

// Event listener to handle open/close information
buttonToggleInformation.addEventListener("click", () => informationMenu.classList.toggle('open'));
buttonCloseInformation.addEventListener("click", () => informationMenu.classList.toggle('open'));


// ======================= Comments insertion and loading =======================

// Event listener to handle click on the PDF to add comments
document.getElementById("pdf-canvas").addEventListener("click", event => {
    
    const rect = document.getElementById("pdf-canvas").getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Check user permission
    if (!commentsEnabled){
        return false;
    }

    // Save the last click coords
    lastClick = { x, y }; 

    commentTextarea.style.left = `${x}px`;
    commentTextarea.style.top = `${y}px`;
    commentTextarea.style.display = "block";
    commentTextarea.focus();

    const onKeyDown = (e) => {
        if (e.key === 'Enter' && e.shiftKey) {
            return;
        } else if (e.key === "Enter" && commentTextarea.value !== "") {
            saveComment(getObjectComments, putObject, pdfObjectId, pdfCurrentScale, commentTextarea.value, lastClick.x, lastClick.y, pdfCurrentPage);
            commentTextarea.value = "";
            commentTextarea.style.display = "none";
            commentTextarea.removeEventListener("keydown", onKeyDown);
            setTimeout(() => {
                loadComments(commentsModePerPage);
            }, 100);
        } else if (e.key === "Escape") {
            commentTextarea.value = "";
            commentTextarea.style.display = "none";
            commentTextarea.removeEventListener("keydown", onKeyDown);
        }
    };

    commentTextarea.removeEventListener("keydown", onKeyDown); // prevent duplicates
    commentTextarea.addEventListener("keydown", onKeyDown);
});



// Handle comments mode
selectCommentsMode.addEventListener("change", event => {
    commentsModePerPage = true ? event.target.value == "per_page" : false;
    loadComments(commentsModePerPage);
});


// Load comments as markers and comments list
function loadComments(per_page = true) {
    
    pdfMarkers.innerHTML = "";
    commentsList.innerHTML = "";
    let commentPageId = 1;
    let totalComments = 0;

    getObjectComments("/api/objects/" + pdfObjectId, function (err, res) {
        
        if (err) {
            commentsList.innerHTML = "<p class='danger'>Error loading comments, please try again</p>";
            return;
        }

        if (res || res == null) {

            let data = JSON.parse(res || '{"inlineComments": []}');
            let clearData;
            
            if (per_page)
                clearData = data.inlineComments.filter(a => a.page === pdfCurrentPage);
            else 
                clearData = data.inlineComments;

            clearData.forEach(({ id, text, x, y, page, authorName, authorId, resolved }) => {
            
                if (per_page || page == pdfCurrentPage) {
                    // Yellow sphere marker on document
                    const marker = document.createElement("div");
                    marker.className = "marker";
                    marker.style.left = `${x*pdfCurrentScale}px`;
                    marker.style.top = `${y*pdfCurrentScale}px`;
                    marker.dataset.commentId = id;
                    marker.addEventListener("click", () => focusCommentFromPdfToSidebar(id));
                    marker.innerText = commentPageId;
                    if (resolved) {
                        marker.classList.add("resolved");
                    }
                    pdfMarkers.appendChild(marker);
                }

                // Create comment on sidebar 
                const comment = document.createElement("div");
                comment.className = "comment";
                comment.id = id;
                comment.innerHTML = "<span class='comment-number'>("+commentPageId+")</span> <span class='comment-author'>" + authorName + ":</span> " + renderText(text);

                const commentControl = document.createElement("div");
                commentControl.className = "comment-control";
                
                const goToBtn = document.createElement("span");
                goToBtn.title = "Find in document";
                goToBtn.innerHTML = "<i class='fas fa-location-arrow'></i>";
                
                // Event listener for comment focus
                goToBtn.addEventListener("click", () => focusCommentFromSidebarToPdf(id, page, pdfCurrentPage));

                const deleteBtn = document.createElement("span");
                deleteBtn.title = "Delete comment";
                deleteBtn.innerHTML = "<i class='fas danger fa-trash-alt'></i>";

                // Event listener for comment delete
                deleteBtn.addEventListener("click", () => {
                    if (confirm("Are you sure to delete this comment?")) {
                        clearData = data.inlineComments.filter(a => a.id !== id);
                        data.inlineComments = clearData;
                        putObject("/api/objects/" + pdfObjectId, {"comments": data}, (err, res) => {
                            if (err) {
                                alert("Error removing comment: " + err);
                            }
                        });
                        setTimeout(() => {
                            return loadComments(per_page);
                        }, 100); 
                    }
                });

                const resolveBtn = document.createElement("span");
                if (!resolved) {
                    resolveBtn.title = "Resolve comment";
                    resolveBtn.innerHTML = "<i class='fas success fa-check'></i>";
                } else {
                    resolveBtn.title = "Undo resolve comment";
                    resolveBtn.innerHTML = "<i class='fas muted fa-rotate-right'></i>";
                    comment.classList.add("resolved");
                }

                // Event listener for comment resolve
                resolveBtn.addEventListener("click", () => {
                    if (!resolved || (resolved && confirm("Are you sure to UNDO resolving this comment?"))) {
                        clearData = data.inlineComments.map(a => {
                            if (a.id === id) {
                                a.resolved = !resolved;
                            }
                            return a;
                        });
                        data.inlineComments = clearData;
                        putObject("/api/objects/" + pdfObjectId, {"comments": data}, (err, res) => {
                            if (err) {
                                alert("Error resolving comment: " + err);
                            }
                        });
                        setTimeout(() => {
                            return loadComments(per_page);
                        }, 100); 
                    }
                });
                
                // Create object
                commentControl.appendChild(goToBtn);
                if (commentsEnabled) {
                    commentControl.appendChild(resolveBtn);
                    commentControl.appendChild(deleteBtn);
                }
                comment.appendChild(commentControl);
                commentsList.appendChild(comment);

                commentPageId++;
                totalComments++;
            });

            totalPageComments.textContent = totalComments;
            
            if (totalComments === 0) 
                commentsList.innerHTML = "<p class='muted'>No comments on this page.</p>";
        }
    });    
}


// ======================= On Load =======================

document.addEventListener('DOMContentLoaded', function () {
    updateStatusColor();
    if (!editingEnabled){
        selectStatusElement.disabled = true;
        buttonEditElement.hidden = true;
    }
    
    // Handle night mode from local storage
    const settings_night_mode = localStorage.getItem("rr-pdf-night-mode");
    if (settings_night_mode == null) {
        localStorage.setItem("rr-pdf-night-mode", nightModeEnabled);
    } else if (settings_night_mode != nightModeEnabled.toString()) {
        toggleNightMode();
    }
});
