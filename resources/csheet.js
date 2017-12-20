var count = 0;
$(document).ready(function () {
    $('.lightbox .small').mouseenter(
        function () {
            useData(this, 'preview');
        }
    );
    $('.lightbox .small').mouseout(
        function () {
            useMinimal(this);
        }
    );
    $('.lightbox .small').click(
        function () {
            var lightbox = getLightbox(this);
            $(lightbox).find('img').each(
                function () {
                    var element = this;
                    useData(element, 'full',
                        function () {
                            useData(element, 'preview');
                        }
                    );
                }
            );
        }
    );
    $('.lightbox .small img').appear();
    $('.lightbox .small img').on('appear',
        function (e, $affected) {
            $affected.each(function () {
                useMinimal(this);
            });
        }
    );

    // $(".lightbox .small").on("disappear", function(e, $affected) {
    //     $affected.each(function() {
    //         use_minimal(this);
    //     });
    // });

    $('img').each(
        function () {
            $(this).attr('src', null);
            useMinimal(this);
        }
    );
});

/**
 * get a light box from element parent.
 * @param {element} element this element.
 * @return {element} lightbox element.
 */
function getLightbox(element) {
    var $element = $(element);
    if ($element.is('.lightbox')) {
        return element;
    }
    return $element.parents('.lightbox')[0];
}

/**
 * Hide lightbox  element then set count.
 * @param {element} lightbox lightbox to hide.
 */
function hide(lightbox) {
    lightbox = getLightbox(lightbox);
    if (lightbox.style.display == 'none') {
        return;
    }
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
        prev = $(prev);
        next = $(next);

        prev.find('a.next').attr('href', ('#' + next.attr('id')));
        next.find('a.prev').attr('href', ('#' + prev.attr('id')));
    } catch (TypeError) { }

    // deal count
    var header = document.getElementsByTagName('header')[0];
    var lightboxes = document.getElementsByClassName('lightbox');
    var total = lightboxes.length;
    count += 1;
    header.children[0].innerText = (
        (total - count).toString() + '/' + total.toString()
    );
}

/**
 * use minimal images for this element.
 * @param {element} element root element.
 */
function useMinimal(element) {
    // Use minaimal image to save memory.
    useData(element, 'thumb',
        function () {
            useData(element, 'full',
                function () {
                    useData(element, 'preview',
                        function () {
                            hide(element);
                        }
                    );
                }
            );
        }
    );
}

/**
 * Choose data to use on image.
 * @param {element} element root element.
 * @param {string} data data name.
 * @param {function} onerror callback
 * @return {string} Used data
 */
function useData(element, data, onerror) {
    var lightbox = getLightbox(element);
    var path = lightbox.getAttribute('data-' + data);
    imageAvailable(
        path,
        function (temp) {
            element.src = temp.src;
        },
        onerror
    );
    return path;
}

/**
 * Load image in background.
 * @param {string} path image path.
 * @param {function} onload callback.
 * @param {function} onerror callback.
 */
function imageAvailable(path, onload, onerror) {
    if (path == null | path == 'null') {
        if (typeof (onerror) != 'undefined') {
            onerror();
        }
        return;
    }
    var temp = new Image;
    temp.onload = function () {
        onload(temp);
    };
    temp.onerror = onerror;
    // temp.src = path + "?r=" + Date.now() / 1000;
    temp.src = path + '?timestamp=' + new Date().getTime().toPrecision(9);
    // console.log(path + ' complete: ' + temp.complete);
}
