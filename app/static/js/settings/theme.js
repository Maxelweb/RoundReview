
export function changeTheme(value, saveSettings = false) {
    
    if (value == "light") {
        document.getElementById('style-theme-dark').disabled = true;
        document.getElementById('style-theme-light').disabled = false;
    } else {
        document.getElementById('style-theme-light').disabled = true;
        document.getElementById('style-theme-dark').disabled = false;
        value = "dark";
    }
    
    if (saveSettings)
        saveLocalSettingsTheme(value);  
}

export function saveLocalSettingsTheme(themeType) {
    return localStorage.setItem("rr-theme", themeType);
}

export function getLocalSettingsTheme() {
    return localStorage.getItem("rr-theme");
}