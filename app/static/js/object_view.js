// View Object detail JS Logic for RoundReview
// ===========================================

let pdfCurrentScale = 1.20;
let pdfInstance = null;
let pdfCurrentPage = 1;
let lastClick = { x: 0, y: 0 };
let objectCurrentStatusIndex;
let commentsModePerPage = true;

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

// Get document and render PDF
pdfjsLib.getDocument(pdfUrl).promise.then(pdf => {
    pdfInstance = pdf;
    totalPageNumDisplay.textContent = pdf.numPages;
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);


    // Get the outline
    pdfInstance.getOutline().then(function(outline) {
        const outlineContainer = document.getElementById('pdf-outline-list');
        if (!Array.isArray(outline)) {
            outlineContainer.innerHTML = '<li>No outline available</li>';
            return;
        }
        buildOutlineList(outline, outlineContainer);
    });

});


// Outline list
function buildOutlineList(items, container) {

  Array.from(items).forEach(item => {
    const li = document.createElement('li');
    li.classList.add('pdf-outline-item');

    const toggle = document.createElement('span');
    toggle.textContent = item.items && item.items.length > 0 ? '+' : '';
    toggle.classList.add('toggle-icon');

    const title = document.createElement('span');
    title.textContent = item.title;
    title.style.cursor = 'pointer';

    // Click to navigate to page
    title.addEventListener('click', () => {
      pdfInstance.getDestination(item.dest).then(dest => {
        const ref = dest[0];
        pdfInstance.getPageIndex(ref).then(pageIndex => {
          const pageNumber = pageIndex + 1;
          renderPage(pageNumber); 
        });
      });
    });

    li.appendChild(toggle);
    li.appendChild(title);

    // Handle nested items
    if (item.items && item.items.length > 0) {
      const subList = document.createElement('ul');
      subList.classList.add('pdf-outline-list', 'hidden');

      buildOutlineList(item.items, subList);
      li.appendChild(subList);

      toggle.addEventListener('click', () => {
        subList.classList.toggle('hidden');
        toggle.textContent = subList.classList.contains('hidden') ? '+' : '−';
      });
    }

    container.appendChild(li);
  });
}


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


// Event listener to handle click on the PDF 
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
        if (e.key === "Enter" && commentTextarea.value !== "") {
            saveComments(commentTextarea.value, lastClick.x, lastClick.y, pdfCurrentPage);
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


// Save new comments
function saveComments(text, x, y, page) {
    getObjectComments("/api/objects/" + pdfObjectId, function (err, res) {
        if (res || res == null) {
            let data = JSON.parse(res || '{"inlineComments": []}')
            const id = `comment-${Date.now()}`;
            const authorName = document.getElementById("author-info").getAttribute("data-author-name");
            const authorId = document.getElementById("author-info").getAttribute("data-author-id");
            const resolved = false;
            x = x / pdfCurrentScale;
            y = y / pdfCurrentScale;
            data.inlineComments.push({ id, text, x, y, page, authorName, authorId, resolved });
            putObject("/api/objects/" + pdfObjectId, {"comments": data}, () => {});
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
                callback(new Error(xhttp.status), null);
            }
        }
    };
    xhttp.send();
}

// Apply comments update via xhttp
function putObject(url, data, callback) {
    const xhttp = new XMLHttpRequest();
    xhttp.open("PUT", url, true);
    xhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhttp.onreadystatechange = function () {
        if (xhttp.readyState === 4) {
            if (xhttp.status === 200) {
                callback(null, xhttp.responseText);
            } else {
                callback(new Error(xhttp.status), null);
            }
        }
    };
    const jsonData = JSON.stringify(data);
    xhttp.send(jsonData);
}

// Load comments as markers and comments list
function loadComments(per_page = true) {
    
    pdfMarkers.innerHTML = "";
    commentsList.innerHTML = "";
    commentPageId = 1;
    totalComments = 0;

    getObjectComments("/api/objects/" + pdfObjectId, function (err, res) {
        
        if (res) {    
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
                    pdfMarkers.appendChild(marker);
                }

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
                goToBtn.addEventListener("click", () => focusCommentFromSidebarToPdf(id, page));

                const deleteBtn = document.createElement("span");
                deleteBtn.title = "Delete comment";
                deleteBtn.innerHTML = "<i class='fas danger fa-trash-alt'></i>";

                // Event listener for comment delete
                deleteBtn.addEventListener("click", () => {
                    if (confirm("Are you sure you want to delete this comment?")) {
                        data = data.filter(a => a.id !== id);
                        putObject("/api/objects/" + pdfObjectId, {"comments": data}, () => {});
                        setTimeout(() => {
                            loadComments(per_page);
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
function focusCommentFromSidebarToPdf(id, page) {
    if (page != pdfCurrentPage){
        pdfCurrentPage = page;
        renderPage(pdfCurrentPage);
    }
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

// Handle comments mode
selectCommentsMode.addEventListener("change", event => {
    commentsModePerPage = true ? event.target.value == "per_page" : false;
    loadComments(commentsModePerPage);
});


buttonNightMode.addEventListener("click", event => {
    if (event.target.classList.contains("fa-sun")) {
        document.getElementById('pdf-canvas').style.filter = 'invert(64%) contrast(228%) brightness(80%) hue-rotate(180deg)';
        event.target.classList.remove("fa-sun")
        event.target.classList.add("fa-moon")
    } else {
        document.getElementById('pdf-canvas').style.filter = null;
        event.target.classList.remove("fa-moon")
        event.target.classList.add("fa-sun")
    }
});

// Handle toggle outline event
buttonToggleOutline.addEventListener("click", event => {
    outlineList.classList.toggle("open");
});

// Event listener to handle the rendering of the next page
document.getElementById("next-page").addEventListener("click", () => {
    pdfNextPage();
});

function pdfNextPage() {
    if (pdfCurrentPage < pdfInstance.numPages) {
        pdfCurrentPage++;
        renderPage(pdfCurrentPage);
    }
}

// Event listener to handle the rendering of the previous page
document.getElementById("prev-page").addEventListener("click", () => {
    pdfPrevPage();
});

function pdfPrevPage() {
    if (pdfCurrentPage > 1) {
        pdfCurrentPage--;
        renderPage(pdfCurrentPage);
    }
}

// Event listener to handle open/close information
buttonToggleInformation.addEventListener("click", () => {
    toggleInformation();
});

buttonCloseInformation.addEventListener("click", () => {
    toggleInformation();
});

function toggleInformation() {
  informationMenu.classList.toggle('open');
}


// Handle with left / right keys
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
    pdfCurrentScale = pdfDefaultScale;
    pageScaleDisplay.textContent = (pdfCurrentScale * 100).toFixed(0) + "%";
    renderPage(pdfCurrentPage);
    updateResetButtonVisibility();
});

// Event listener to show or not the reset button on zoom in/out
document.getElementById("page-zoom-in").addEventListener("click", updateResetButtonVisibility);
document.getElementById("page-zoom-out").addEventListener("click", updateResetButtonVisibility);

function updateResetButtonVisibility() {
    document.getElementById("reset-scale").style.display = (pdfCurrentScale !== pdfDefaultScale) ? "inline-block" : "none";
}

// Event listener status label
document.getElementById("status-label").addEventListener("change", () => {
    
    // Check user permission
    if (!editingEnabled){
        return false;
    }

    putObject("/api/objects/" + pdfObjectId, {"status": document.getElementById("status-label").value}, (error, res) => {
        if (res){
            updateStatusColor();
        } else {
            console.warn(objectCurrentStatusIndex)
            selectStatusElement.selectedIndex = objectCurrentStatusIndex;
            alert(error);
        }
            
    });
});

document.addEventListener('DOMContentLoaded', function () {
    updateStatusColor();
    if (!editingEnabled){
        selectStatusElement.disabled = true;
        buttonEditElement.hidden = true;
    }
});

function updateStatusColor() {
    objectCurrentStatusIndex = selectStatusElement.selectedIndex; // Save initial status
    const selectedOption = selectStatusElement.options[selectStatusElement.selectedIndex];
    const color = selectedOption.getAttribute('data-color');
    selectStatusElement.style.backgroundColor = color || 'black';
}