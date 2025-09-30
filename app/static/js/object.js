
// Object JS Logic for RoundReview
// ===============================

let pdfCurrentScale = 1.35;
let pdfInstance = null;
let pdfCurrentPage = 1;
let lastClick = { x: 0, y: 0 };

const pdfscaleDefault = 1.35;
const pdfUrl = document.getElementById("pdf-container").getAttribute("data-pdf-url");
const pdfObjectId = document.getElementById("pdf-container").getAttribute("data-pdf-object-id");

const pdfMarkers = document.getElementById("markers");
const commentTextarea = document.getElementById("comment-input");
const commentsList = document.getElementById("comments-list");

const currentPageNumDisplay = document.getElementById("page-num");
const totalPageNumDisplay = document.getElementById("total-pages-num");

const pageScaleDisplay = document.getElementById("page-scale");
const totalPageComments = document.getElementById("total-page-comments");

// Get document and render PDF
pdfjsLib.getDocument(pdfUrl).promise.then(pdf => {
    pdfInstance = pdf;
    totalPageNumDisplay.textContent = pdf.numPages;
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);
});

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
        loadAnnotations();
    });
}


// Event listener to handle click on the PDF 
document.getElementById("pdf-canvas").addEventListener("click", event => {
    
    const rect = document.getElementById("pdf-canvas").getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Check user permission
    const commentsEnabled = document.getElementById("author-info").getAttribute("data-author-can-comment") == "True";
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
        if (e.key === "Enter" && commentTextarea.value !== "") {
            saveComments(commentTextarea.value, lastClick.x, lastClick.y, pdfCurrentPage);
            commentTextarea.value = "";
            commentTextarea.style.display = "none";
            commentTextarea.removeEventListener("keydown", onKeyDown);
            setTimeout(() => {
                loadAnnotations();
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


// Save new comments
function saveComments(text, x, y, page) {
    getObjectComments("/api/objects/" + pdfObjectId, function (err, res) {
        if (res || res == null) {
            let data = JSON.parse(res || "[]")
            const id = `comment-${Date.now()}`;
            const authorName = document.getElementById("author-info").getAttribute("data-author-name");
            const authorId = document.getElementById("author-info").getAttribute("data-author-id");
            const resolved = false;
            x = x / pdfCurrentScale;
            y = y / pdfCurrentScale;
            data.push({ id, text, x, y, page, authorName, authorId, resolved });
            putObject("/api/objects/" + pdfObjectId, {"comments": data})
        }
    });
}


// Get latest comments
function getObjectComments(url, callback) {
    const xhttp = new XMLHttpRequest();
    xhttp.open("GET", url, true);
    xhttp.setRequestHeader("Accept", "application/json");
    xhttp.onreadystatechange = function () {
        if (xhttp.readyState === 4) {
            if (xhttp.status === 200) {
                try {
                    const responseJson = JSON.parse(xhttp.responseText);
                    callback(null, responseJson["object"]["comments"]);
                } catch (e) {
                    console.error("Error in JSON: ", e);
                    callback(e, null);
                }
            } else {
                callback(new Error("Error HTTP: " + xhttp.status), null);
            }
        }
    };
    xhttp.send();
}

// Apply comments update via xhttp
function putObject(url, data) {
    const xhttp = new XMLHttpRequest();
    xhttp.open("PUT", url, true);
    xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhttp.onreadystatechange = function () {
        if (xhttp.readyState === 4) {
            if (xhttp.status === 200) {
                // TODO: 
                console.log("OK: ", xhttp.responseText);
            } else {
                console.error("Error: ", xhttp.status, xhttp.statusText);
            }
        }
    };
    const jsonData = JSON.stringify(data);
    xhttp.send(jsonData);
}

// Load comments as markers and comments list
function loadAnnotations() {
    
    pdfMarkers.innerHTML = "";
    commentsList.innerHTML = "";
    commentPageId = 1;
    totalComments = 0;

    getObjectComments("/api/objects/" + pdfObjectId, function (err, res) {
        
        if (res) {    
            let data = JSON.parse(res || "[]");
            data.filter(a => a.page === pdfCurrentPage).forEach(({ id, text, x, y, page, authorName, authorId, resolved }) => {

                // Yellow sphere marker on document
                const marker = document.createElement("div");
                marker.className = "marker";
                marker.style.left = `${x*pdfCurrentScale}px`;
                marker.style.top = `${y*pdfCurrentScale}px`;
                marker.dataset.commentId = id;
                marker.addEventListener("click", () => focusCommentFromPdfToSidebar(id));
                marker.innerText = commentPageId;
                pdfMarkers.appendChild(marker);

                // Create comment on sidebar 
                const comment = document.createElement("div");
                comment.className = "comment";
                comment.id = id;
                comment.innerHTML = "<span class='comment-number'>("+commentPageId+")</span> <span class='comment-author'>" + authorName + ":</span> " + text;

                const commentControl = document.createElement("div");
                commentControl.className = "comment-control";
                
                const goToBtn = document.createElement("span");
                goToBtn.title = "Find in document";
                goToBtn.innerHTML = "<i class='fas fa-location-arrow'></i>";
                
                // Event listener for comment focus
                goToBtn.addEventListener("click", () => focusCommentFromSidebarToPdf(id));

                const deleteBtn = document.createElement("span");
                deleteBtn.title = "Delete comment";
                deleteBtn.innerHTML = "<i class='fas danger fa-trash-alt'></i>";

                // Event listener for comment delete
                deleteBtn.addEventListener("click", () => {
                    if (confirm("Are you sure you want to delete this comment?")) {
                        data = data.filter(a => a.id !== id);
                        putObject("/api/objects/" + pdfObjectId, {"comments": data})
                        setTimeout(() => {
                            loadAnnotations();
                        }, 100);
                    }
                });
                
                // Create object
                commentControl.appendChild(goToBtn);
                commentControl.appendChild(deleteBtn);
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


// Highlight comment handler
function focusCommentFromSidebarToPdf(id) {
    document.querySelectorAll(".comment").forEach(el => el.classList.remove("focused"));
    const target = document.getElementById(id);
    if (target) {
        target.classList.add("focused");
        setTimeout(() => target.classList.remove("focused"), 1500); // Remove highlight
        const marker = document.querySelector(`.marker[data-comment-id='${id}']`);
        if (marker) {
            marker.scrollIntoView({ behavior: "smooth", block: "center" });
            marker.classList.add("focused");
            setTimeout(() => marker.classList.remove("focused"), 1500); // Remove highlight
        }
    }
}

// Highlight pdf marker handler
function focusCommentFromPdfToSidebar(id) {
    document.querySelectorAll(".comment").forEach(el => el.classList.remove("focused"));
    const target = document.getElementById(id);
    if (target) {
        target.classList.add("focused");
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => target.classList.remove("focused"), 1500); // Remove highlight
    }
}


// Event listener to handle the rendering of the next page
document.getElementById("next-page").addEventListener("click", () => {
    if (pdfCurrentPage < pdfInstance.numPages) {
        pdfCurrentPage++;
        renderPage(pdfCurrentPage);
    }
});

// Event listener to handle the rendering of the previous page
document.getElementById("prev-page").addEventListener("click", () => {
    if (pdfCurrentPage > 1) {
        pdfCurrentPage--;
        renderPage(pdfCurrentPage);
    }
});

// Event listeners for zooming in and out
document.getElementById("page-zoom-in").addEventListener("click", () => {
    pdfCurrentScale = Math.min(pdfCurrentScale + 0.25, 3); // Ensure pdfscale does not exceed 3
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);
});

// Event listeners for zooming in and out
document.getElementById("page-zoom-out").addEventListener("click", () => {
    if (pdfCurrentScale > 0.5) {
        pdfCurrentScale = Math.max(pdfCurrentScale - 0.25, 0.5); // Ensure pdfscale does not go below 0.5
        pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
        renderPage(pdfCurrentPage);
    }
});

// Event listener for resetting scale
document.getElementById("reset-scale").addEventListener("click", () => {
    pdfCurrentScale = pdfscaleDefault;
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);
    updateResetButtonVisibility();
});

// Event listener to show or not the reset button on zoom in/out
document.getElementById("page-zoom-in").addEventListener("click", updateResetButtonVisibility);
document.getElementById("page-zoom-out").addEventListener("click", updateResetButtonVisibility);

function updateResetButtonVisibility() {
    document.getElementById("reset-scale").style.display = (pdfCurrentScale !== pdfscaleDefault) ? "inline-block" : "none";
}