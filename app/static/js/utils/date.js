
export function formatRelativeDate(isoTimestamp) {
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
