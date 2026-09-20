
export function renderText(rawText) {
  const safeText = rawText
    .replace(/&/g, "&amp;")       // Escape HTML
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .replace(/\n/g, "<br>")       // Convert newlines to <br>
    .replace(/ {2}/g, " &nbsp;"); // Preserve double spaces

  return safeText;
}

export function escapeText(rawText) {
  const safeText = rawText
    // Escape HTML
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")

  return safeText;
}