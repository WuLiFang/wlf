let count = 0;
$(document).ready(function() {
    $('.lightbox .small').mouseenter(
        function() {
            useData(this, 'preview');
        }
    );
    $('.lightbox .small').mouseout(
        function() {
            useMinimal(this);
        }
    );
    $('.lightbox .small').click(
        function() {
            let lightbox = getLightbox(this);
            $(lightbox).find('img').each(
                function() {
                    let element = this;
                    useData(element, 'full',
                        function() {
                            useData(element, 'preview');
                        }
                    );
                }
            );
        }
    );
    $('.lightbox img').each(function() {
        let $this = $(this);
        $this.appear();
        $this.on('appear',
            function(e, $affected) {
                $affected.each(function() {
                    useMinimal(this);
                    // console.log(this);
                });
            }
        );
    });

    // $(".lightbox .small").on("disappear", function(e, $affected) {
    //     $affected.each(function() {
    //         use_minimal(this);
    //     });
    // });

    $('img').each(
        function() {
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
    let $element = $(element);
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
        let prev = lightbox.previousElementSibling;
        while (prev.style.display == 'none') {
            prev = prev.previousElementSibling;
        }
        let next = lightbox.nextElementSibling;
        while (next.style.display == 'none') {
            next = next.nextElementSibling;
        }
        prev = $(prev);
        next = $(next);

        prev.find('a.next').attr('href', ('#' + next.attr('id')));
        next.find('a.prev').attr('href', ('#' + prev.attr('id')));
    } catch (TypeError) {
        return;
    }

    // deal count
    let header = document.getElementsByTagName('header')[0];
    let lightboxes = document.getElementsByClassName('lightbox');
    let total = lightboxes.length;
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
        function() {
            useData(element, 'full',
                function() {
                    useData(element, 'preview',
                        function() {
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
    let lightbox = getLightbox(element);
    let path = lightbox.getAttribute('data-' + data);
    imageAvailable(
        path,
        function(temp) {
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
    let temp = new Image;
    temp.onload = function() {
        onload(temp);
    };
    temp.onerror = onerror;
    // temp.src = path + "?r=" + Date.now() / 1000;
    temp.src = path + '?timestamp=' + new Date().getTime().toPrecision(9);
    // console.log(path + ' complete: ' + temp.complete);
}
