var count = 0;
$("document").ready(function() {
    $(".lightbox .thumb").each(
        function() {
            use_minimal(this);
            // $(this).attr("src", null);
        }
    );
    $(".lightbox .thumb").mouseenter(
        function() {
            use_data(this, "preview");
        }
    );
    $(".lightbox .thumb").mouseout(
        function() {
            use_minimal(this);
        }
    );
    $(".lightbox .thumb").appear();
    // $(".lightbox .thumb").on("appear", function(e, $affected) {
    //     $affected.each(function() {
    //         use_data(this, "preview");
    //     });
    // });
    $(".lightbox .thumb").on("disappear", function(e, $affected) {
        $affected.each(function() {
            use_minimal(this);
        });
    });
})

function get_lightbox(element) {
    var $element = $(element);
    if ($element.is(".lightbox")) {
        return element
    }
    return $element.parents(".lightbox")[0]
}

function hide(lightbox) {
    var lightbox = get_lightbox(lightbox);
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

function use_minimal(element) {
    // Use minaimal image to save memory.
    use_data(element, "thumb",
        function() {
            use_data(element, "full",
                function() {
                    use_data(element, "preview",
                        function() {
                            hide(element);
                        }
                    );
                }
            );
        }
    );
}

function use_data(element, data, onerror) {
    var lightbox = get_lightbox(element);
    var path = lightbox.getAttribute("data-" + data);
    image_available(
        path,
        function() {
            element.src = path;
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