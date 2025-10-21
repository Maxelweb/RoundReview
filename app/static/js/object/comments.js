

// Save new comment
export function saveComment(getFunction, putFunction, pdfObjectId, pdfCurrentScale, text, x, y, page) {
    getFunction("/api/objects/" + pdfObjectId, function (err, res) {
        if (res || res == null) {
            let data = JSON.parse(res || '{"inlineComments": []}')
            const id = `comment-${Date.now()}`;
            const authorName = document.getElementById("author-info").getAttribute("data-author-name");
            const authorId = document.getElementById("author-info").getAttribute("data-author-id");
            const resolved = false;
            x = x / pdfCurrentScale;
            y = y / pdfCurrentScale;
            data.inlineComments.push({ id, text, x, y, page, authorName, authorId, resolved });
            putFunction("/api/objects/" + pdfObjectId, {"comments": data}, () => {});
        }
    });
}


// Highlight comment handler
export function focusCommentFromSidebarToPdf(id, page, pdfCurrentPage, renderPageFunction) {
    if (page != pdfCurrentPage){
        pdfCurrentPage = page;
        renderPageFunction(pdfCurrentPage);
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
export function focusCommentFromPdfToSidebar(id) {
    document.querySelectorAll(".comment").forEach(el => el.classList.remove("focused"));
    const target = document.getElementById(id);
    if (target) {
        target.classList.add("focused");
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => target.classList.remove("focused"), 1500); // Remove highlight
    }
}