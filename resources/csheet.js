var count = 0;

function hide(lightbox) {
    lightbox = lightbox.parentNode.parentNode.parentNode;
    lightbox.style.display = 'none';
    try {
        var prev = lightbox.previousElementSibling;
        while (prev.style.display == 'none') {
            prev = prev.previousElementSibling;
        }
        var next = lightbox.nextElementSibling;
        while (next.style.display == 'none') {
            next = next.nextElementSibling;
        }

        prev.children[1].children[3].href = next.children[0].children[0].href;
        next.children[1].children[2].href = prev.children[0].children[0].href;
    } catch (TypeError) {}

    // deal count
    var header = document.getElementsByTagName("header")[0];
    var lightboxes = document.getElementsByClassName('lightbox');
    var total = lightboxes.length;
    count += 1;
    header.children[0].innerText = `${total - count}/${total}`;
}

function use_minimal(lightbox) {
    // Use minaimal image to save memory.
    // console.log("use_minimal");
    var lightbox = lightbox;
    use_data(lightbox, "thumb",
        function() {
            use_data(lightbox, "full",
                function() {
                    use_data(lightbox, "preview",
                        function() {
                            hide(lightbox);
                        }
                    );
                }
            );
        }
    );
}

function use_data(lightbox, data, onerror) {
    var path = lightbox.getAttribute("data-" + data);
    console.log("Try use: " + data + " value :" + path);
    image_available(
        path,
        function() {
            console.log("Use " + data + ": " + path);
            lightbox.src = path;
        },
        onerror
    );
    return path;
}

function image_available(path, onload, onerror) {
    if (path == null | path == 'null') {
        if (typeof(onerror) != "undefined") {
            onerror();
        }
        return;
    }
    var temp = new Image;
    temp.onload = onload;
    temp.onerror = onerror;
    // temp.src = path + "?r=" + Date.now() / 1000;
    temp.src = path;
    // console.log(path + ' complete: ' + temp.complete);
}