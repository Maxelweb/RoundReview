import { diffWordsWithSpace } from 'https://cdn.jsdelivr.net/npm/diff@5.2.0/+esm';

const compareScale = 2;
const visualCompareScale = 0.55;
const visualTileSize = 24;
const textMeasureContext = document.createElement('canvas').getContext('2d');

function getPageTextData(page) {
    return page.getTextContent().then(content => {
        let text = '';
        const items = [];
        content.items.forEach(item => {
            if (typeof item.str !== 'string' || !item.str) return;
            const start = text.length;
            text += item.str;
            items.push({ item, text: item.str, start, end: text.length });
            text += item.hasEOL ? '\n' : ' ';
        });
        return { text: text.trimEnd(), items, styles: content.styles };
    });
}

function collectTextRegions(pageData, start, end, changeType, viewport) {
    if (!viewport || start === end) return [];
    const regions = [];
    pageData.items.forEach(({ item, text, start: itemStart, end: itemEnd }) => {
        const changedStart = Math.max(start, itemStart);
        const changedEnd = Math.min(end, itemEnd);
        if (changedStart >= changedEnd) return;

        const transform = pdfjsLib.Util.transform(viewport.transform, item.transform);
        const fontHeight = Math.hypot(transform[2], transform[3]);
        const style = pageData.styles[item.fontName] || {};
        let angle = Math.atan2(transform[1], transform[0]);
        if (style.vertical) angle += Math.PI / 2;
        const ascent = style.ascent || (style.descent ? 1 + style.descent : 0.8);
        const fontAscent = fontHeight * ascent;
        const left = angle === 0
            ? transform[4]
            : transform[4] + fontAscent * Math.sin(angle);
        const top = angle === 0
            ? transform[5] - fontAscent
            : transform[5] - fontAscent * Math.cos(angle);
        const fontFamily = style.fontFamily || 'sans-serif';
        textMeasureContext.font = `${fontHeight}px ${fontFamily}`;
        const measuredWidth = textMeasureContext.measureText(text).width;
        const itemWidth = (style.vertical ? item.height : item.width) * viewport.scale;
        const measureScale = measuredWidth > 0 ? itemWidth / measuredWidth : 0;
        const prefix = textMeasureContext.measureText(text.slice(0, changedStart - itemStart)).width * measureScale;
        const changedTextWidth = textMeasureContext.measureText(text.slice(changedStart - itemStart, changedEnd - itemStart)).width * measureScale;
        regions.push({
            type: changeType,
            left: left + prefix * Math.cos(angle),
            top: top + prefix * Math.sin(angle),
            width: Math.max(2, changedTextWidth),
            height: Math.max(2, fontHeight),
            angle,
        });
    });
    return regions;
}

function comparePageText(previousData, currentData, previousViewport, currentViewport) {
    let previousOffset = 0;
    let currentOffset = 0;
    let differenceCount = 0;
    const differenceCounts = { added: 0, removed: 0, modified: 0 };
    let pending = [];
    const previousRegions = [];
    const currentRegions = [];

    const flush = () => {
        if (!pending.length) return;
        differenceCount++;
        const removed = pending.some(part => part.removed);
        const added = pending.some(part => part.added);
        const changeType = removed && added ? 'modified' : added ? 'added' : 'removed';
        differenceCounts[changeType]++;
        pending.forEach(part => {
            if (part.removed) {
                previousRegions.push(...collectTextRegions(
                    previousData,
                    previousOffset,
                    previousOffset + part.value.length,
                    changeType,
                    previousViewport,
                ));
                previousOffset += part.value.length;
            }
            if (part.added) {
                currentRegions.push(...collectTextRegions(
                    currentData,
                    currentOffset,
                    currentOffset + part.value.length,
                    changeType,
                    currentViewport,
                ));
                currentOffset += part.value.length;
            }
        });
        pending = [];
    };

    diffWordsWithSpace(previousData.text, currentData.text).forEach(part => {
        if (part.added || part.removed) {
            pending.push(part);
            return;
        }
        flush();
        previousOffset += part.value.length;
        currentOffset += part.value.length;
    });
    flush();
    return { differenceCount, differenceCounts, previousRegions, currentRegions };
}

function renderPageToCanvas(page) {
    const viewport = page.getViewport({ scale: compareScale });
    const canvas = document.createElement('canvas');
    canvas.width = Math.ceil(viewport.width);
    canvas.height = Math.ceil(viewport.height);
    return page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise.then(() => ({ canvas, viewport }));
}

function downsampleCanvas(source) {
    const canvas = document.createElement('canvas');
    canvas.width = Math.ceil(source.width * visualCompareScale / compareScale);
    canvas.height = Math.ceil(source.height * visualCompareScale / compareScale);
    canvas.getContext('2d').drawImage(source, 0, 0, canvas.width, canvas.height);
    return canvas;
}

function normalizeCanvas(source, width, height) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d', { willReadFrequently: true });
    context.fillStyle = '#fff';
    context.fillRect(0, 0, width, height);
    if (source) context.drawImage(source, 0, 0);
    return canvas;
}

function findChangedRegions(leftCanvas, rightCanvas) {
    const width = leftCanvas.width;
    const height = leftCanvas.height;
    const leftPixels = leftCanvas.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, width, height).data;
    const rightPixels = rightCanvas.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, width, height).data;
    const columns = Math.ceil(width / visualTileSize);
    const rows = Math.ceil(height / visualTileSize);
    const changedTiles = new Uint8Array(columns * rows);

    for (let tileY = 0; tileY < rows; tileY++) {
        for (let tileX = 0; tileX < columns; tileX++) {
            const startX = tileX * visualTileSize;
            const startY = tileY * visualTileSize;
            const endX = Math.min(startX + visualTileSize, width);
            const endY = Math.min(startY + visualTileSize, height);
            const threshold = Math.max(3, Math.floor((endX - startX) * (endY - startY) * 0.002));
            let changedPixels = 0;

            for (let y = startY; y < endY && changedPixels < threshold; y += 1) {
                for (let x = startX; x < endX; x += 1) {
                    const offset = (y * width + x) * 4;
                    if (Math.abs(leftPixels[offset] - rightPixels[offset]) > 40 ||
                        Math.abs(leftPixels[offset + 1] - rightPixels[offset + 1]) > 40 ||
                        Math.abs(leftPixels[offset + 2] - rightPixels[offset + 2]) > 40) {
                        changedPixels++;
                        if (changedPixels >= threshold) break;
                    }
                }
            }
            if (changedPixels >= threshold) changedTiles[tileY * columns + tileX] = 1;
        }
    }

    const visited = new Uint8Array(changedTiles.length);
    const regions = [];
    changedTiles.forEach((changed, index) => {
        if (!changed || visited[index]) return;
        const pending = [index];
        visited[index] = 1;
        let minX = columns;
        let minY = rows;
        let maxX = 0;
        let maxY = 0;

        while (pending.length) {
            const current = pending.pop();
            const tileX = current % columns;
            const tileY = Math.floor(current / columns);
            minX = Math.min(minX, tileX);
            minY = Math.min(minY, tileY);
            maxX = Math.max(maxX, tileX);
            maxY = Math.max(maxY, tileY);
            for (let offsetY = -1; offsetY <= 1; offsetY++) {
                for (let offsetX = -1; offsetX <= 1; offsetX++) {
                    const nextX = tileX + offsetX;
                    const nextY = tileY + offsetY;
                    const nextIndex = nextY * columns + nextX;
                    if (nextX >= 0 && nextX < columns && nextY >= 0 && nextY < rows &&
                        changedTiles[nextIndex] && !visited[nextIndex]) {
                        visited[nextIndex] = 1;
                        pending.push(nextIndex);
                    }
                }
            }
        }

        regions.push({
            left: minX * visualTileSize,
            top: minY * visualTileSize,
            right: Math.min(width, (maxX + 1) * visualTileSize),
            bottom: Math.min(height, (maxY + 1) * visualTileSize),
        });
    });
    return regions;
}

function canvasToObjectUrl(canvas) {
    return new Promise(resolve => canvas.toBlob(blob => resolve(URL.createObjectURL(blob)), 'image/png'));
}

function appendPdfPage(container, imageUrl, width, height, textRegions, graphicsRegions, graphicsWidth, graphicsHeight, pageNumber) {
    const page = document.createElement('section');
    page.className = 'compare-pdf-page';
    const heading = document.createElement('h4');
    heading.textContent = `Page ${pageNumber}`;
    const frame = document.createElement('div');
    frame.className = 'compare-page-frame';
    frame.style.aspectRatio = `${width} / ${height}`;
    if (imageUrl) {
        const image = document.createElement('img');
        image.src = imageUrl;
        image.alt = `PDF page ${pageNumber}`;
        frame.appendChild(image);
    }

    const graphicsOverlay = document.createElement('div');
    graphicsOverlay.className = 'compare-graphics-overlay';
    graphicsOverlay.hidden = !document.getElementById('show-visual-differences').checked;
    graphicsRegions.forEach(region => {
        const left = Math.max(0, region.left);
        const top = Math.max(0, region.top);
        const right = Math.min(graphicsWidth, region.right);
        const bottom = Math.min(graphicsHeight, region.bottom);
        if (right <= left || bottom <= top) return;
        const box = document.createElement('span');
        box.className = 'compare-graphics-box';
        box.style.left = `${left / graphicsWidth * 100}%`;
        box.style.top = `${top / graphicsHeight * 100}%`;
        box.style.width = `${(right - left) / graphicsWidth * 100}%`;
        box.style.height = `${(bottom - top) / graphicsHeight * 100}%`;
        graphicsOverlay.appendChild(box);
    });
    frame.appendChild(graphicsOverlay);

    const textOverlay = document.createElement('div');
    textOverlay.className = 'compare-text-overlay';
    textOverlay.hidden = !document.getElementById('show-text-differences').checked;
    textRegions.forEach(region => {
        const box = document.createElement('span');
        box.className = `compare-text-box compare-text-${region.type}`;
        box.style.left = `${region.left / width * 100}%`;
        box.style.top = `${region.top / height * 100}%`;
        box.style.width = `${region.width / width * 100}%`;
        box.style.height = `${region.height / height * 100}%`;
        if (region.angle) {
            box.style.transform = `rotate(${region.angle}rad)`;
            box.style.transformOrigin = 'top left';
        }
        textOverlay.appendChild(box);
    });
    frame.appendChild(textOverlay);
    page.append(heading, frame);
    container.appendChild(page);
}

async function buildComparison(previousUrl, currentUrl) {
    const [previousPdf, currentPdf] = await Promise.all([
        pdfjsLib.getDocument(previousUrl).promise,
        pdfjsLib.getDocument(currentUrl).promise,
    ]);
    const pageCount = Math.max(previousPdf.numPages, currentPdf.numPages);
    const previousContent = document.getElementById('compare-previous-content');
    const currentContent = document.getElementById('compare-current-content');
    previousContent.replaceChildren();
    currentContent.replaceChildren();

    let textDifferenceCount = 0;
    const textDifferenceCounts = { added: 0, removed: 0, modified: 0 };
    let visualDifferenceCount = 0;
    const imageUrls = [];

    for (let pageNumber = 1; pageNumber <= pageCount; pageNumber++) {
        const previousPage = pageNumber <= previousPdf.numPages ? await previousPdf.getPage(pageNumber) : null;
        const currentPage = pageNumber <= currentPdf.numPages ? await currentPdf.getPage(pageNumber) : null;
        const [previousPageText, currentPageText] = await Promise.all([
            previousPage ? getPageTextData(previousPage) : Promise.resolve({ text: '', items: [], styles: {} }),
            currentPage ? getPageTextData(currentPage) : Promise.resolve({ text: '', items: [], styles: {} }),
        ]);
        const [previousCanvas, currentCanvas] = await Promise.all([
            previousPage ? renderPageToCanvas(previousPage) : Promise.resolve(null),
            currentPage ? renderPageToCanvas(currentPage) : Promise.resolve(null),
        ]);
        const previousVisualCanvas = previousCanvas ? downsampleCanvas(previousCanvas.canvas) : null;
        const currentVisualCanvas = currentCanvas ? downsampleCanvas(currentCanvas.canvas) : null;
        const width = Math.max(previousVisualCanvas?.width || 0, currentVisualCanvas?.width || 0, 1);
        const height = Math.max(previousVisualCanvas?.height || 0, currentVisualCanvas?.height || 0, 1);
        const normalizedPrevious = normalizeCanvas(previousVisualCanvas, width, height);
        const normalizedCurrent = normalizeCanvas(currentVisualCanvas, width, height);
        const regions = findChangedRegions(normalizedPrevious, normalizedCurrent);
        visualDifferenceCount += regions.length;
        const textDiff = comparePageText(
            previousPageText,
            currentPageText,
            previousCanvas?.viewport,
            currentCanvas?.viewport,
        );
        textDifferenceCount += textDiff.differenceCount;
        Object.keys(textDifferenceCounts).forEach(type => {
            textDifferenceCounts[type] += textDiff.differenceCounts[type];
        });
        const [previousImageUrl, currentImageUrl] = await Promise.all([
            previousPage ? canvasToObjectUrl(previousCanvas.canvas) : Promise.resolve(null),
            currentPage ? canvasToObjectUrl(currentCanvas.canvas) : Promise.resolve(null),
        ]);
        if (previousImageUrl) imageUrls.push(previousImageUrl);
        if (currentImageUrl) imageUrls.push(currentImageUrl);
        appendPdfPage(
            previousContent,
            previousImageUrl,
            previousCanvas?.canvas.width || width,
            previousCanvas?.canvas.height || height,
            textDiff.previousRegions,
            regions,
            previousVisualCanvas?.width || width,
            previousVisualCanvas?.height || height,
            pageNumber,
        );
        appendPdfPage(
            currentContent,
            currentImageUrl,
            currentCanvas?.canvas.width || width,
            currentCanvas?.canvas.height || height,
            textDiff.currentRegions,
            regions,
            currentVisualCanvas?.width || width,
            currentVisualCanvas?.height || height,
            pageNumber,
        );
        normalizedPrevious.width = 0;
        normalizedPrevious.height = 0;
        normalizedCurrent.width = 0;
        normalizedCurrent.height = 0;
        if (previousVisualCanvas) {
            previousVisualCanvas.width = 0;
            previousVisualCanvas.height = 0;
        }
        if (currentVisualCanvas) {
            currentVisualCanvas.width = 0;
            currentVisualCanvas.height = 0;
        }
        if (previousCanvas) previousCanvas.canvas.width = 0;
        if (currentCanvas) currentCanvas.canvas.width = 0;
        previousPage?.cleanup();
        currentPage?.cleanup();
    }

    document.getElementById('text-difference-count').textContent = textDifferenceCount;
    document.getElementById('text-added-count').textContent = textDifferenceCounts.added;
    document.getElementById('text-removed-count').textContent = textDifferenceCounts.removed;
    document.getElementById('text-modified-count').textContent = textDifferenceCounts.modified;
    document.getElementById('visual-difference-count').textContent = visualDifferenceCount;
    return () => imageUrls.forEach(url => URL.revokeObjectURL(url));
}

export function comparePdfs(previousUrl, currentUrl) {
    return buildComparison(previousUrl, currentUrl);
}