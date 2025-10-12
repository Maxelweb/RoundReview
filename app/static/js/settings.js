
import { changeTheme, getLocalSettingsTheme } from "./settings/theme.js";

const selectThemeMode = document.getElementById('theme-mode');

document.getElementById('theme-mode').addEventListener("change", event => {
    changeTheme(selectThemeMode.value, true);
});

document.addEventListener('DOMContentLoaded', function () {
    if (!selectThemeMode) return;
    for (let option of selectThemeMode.options) {
        option.selected = option.value === getLocalSettingsTheme();
    }
});
