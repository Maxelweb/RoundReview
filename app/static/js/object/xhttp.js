
// Get Object Comments
export function getObjectComments(url, callback) {
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

// Update Object
export function putObject(url, data, callback) {
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

// Update Object
export function deleteReview(url, callback) {
    const xhttp = new XMLHttpRequest();
    xhttp.open("DELETE", url, true);
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
    xhttp.send();
}