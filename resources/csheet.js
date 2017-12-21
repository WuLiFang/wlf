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
    $('.lightbox figure').each(function() {
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
    $('.lightbox .viewer a').click(
        function() {
            let $this = $(this);
            let $lightbox = $(getLightbox(this));
            let href;
            switch ($this.attr('class')) {
                case 'prev':
                    let prev = $lightbox.prev();
                    while (prev.is('.hidden')) {
                        prev = prev.prev();
                    }
                    href = '#' + prev.attr('href');
                    break;
                case 'next':
                    let next = $lightbox.next();
                    while (next.is('.hidden')) {
                        next = next.next();
                    }
                    href = '#' + next.attr('id');
                    break;
                default:
                    href = $this.attr('href');
            }
            $this.attr('href', href);
            if (href == '#undefined') {
                return false;
            }
        }
    );


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
    let $lightbox = $(lightbox);
    if ($lightbox.is('.hidden')) {
        return;
    }
    $lightbox.addClass('hidden');

    count += 1;
    updateCount();
}

/**
 * Show element related lightbox.
 * @param {element} element The root element.
 */
function show(element) {
    let lightbox = $(getLightbox(element));
    if (!lightbox.is('.hidden')) {
        return;
    }
    lightbox.removeClass('hidden');
    count -= 1;
    updateCount();
}

/**
 * Update count display.
 */
function updateCount() {
    let header = document.getElementsByTagName('header')[0];
    let lightboxes = document.getElementsByClassName('lightbox');
    let total = lightboxes.length;
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
            let $element = $(element);
            if (!$element.is('img')) {
                $element = $element.find('img');
            }
            $element.attr('src', temp.src);
            show(element);
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
    temp.src = path + '?timestamp=' + new Date().getTime().toPrecision(9);
}
