
// RoundReview Theme changer
// NOTE: this must run synchronously to avoid flashing theme change

if (localStorage.getItem("rr-theme") == "light") {
    document.getElementById('style-theme-dark').disabled = true;
    document.getElementById('style-theme-light').disabled = false;
} else {
    document.getElementById('style-theme-light').disabled = true;
    document.getElementById('style-theme-dark').disabled = false;
}
