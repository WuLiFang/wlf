// TODO: button image loop
let count = 0;
$(document).ready(
    function() {
        $('.lightbox .small').mouseenter(
            function() {
                useData(this, 'preview');
            }
        );
        $('body').dblclick(
            function() {
                $('.lightbox .small:appeared').each(
                    function() {
                        useData(this, 'preview');
                    }
                );
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
                        href = '#' + prev.attr('id');
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
        $('.lightbox img').on('dragstart', function(ev) {
            ev.originalEvent.dataTransfer
                .setData('text', $(getLightbox(this)).data('drag'));
        }

        );

        $('.lightbox img').each(
            function() {
                $(this).attr('src', null);
                hide(this);
                useMinimal(this);
            }
        );
        // simlpe help
        $('nav').append(
            $('<button/>', {
                text: '帮助',
                click: function() {
                    $('.help').toggleClass('hidden');
                },
            })
        );
        // show pack progress
        $('button.pack').click(
            function() {
                let progressBar = $('progress.pack');
                let isStarted = false;
                progressBar.removeClass('hidden');
                $(this).addClass('hidden');
                if (typeof (EventSource) != 'undefined') {
                    let source = new EventSource('/pack_progress');
                    source.onmessage = function(event) {
                        if (event.data > 0) {
                            isStarted = true;
                        }
                        progressBar.val(event.data);
                        if (isStarted && event.data < 0) {
                            source.close();
                            progressBar.addClass('hidden');
                        }
                    };
                } else {
                    alert('由于当前浏览器不支持SSE, 不能显示进度');
                    // $.get('/pack_progress'
                    //     + '?timestamp=' + new Date().getTime(),
                    //     function(progress) {
                    //         let update = function() {
                    //             progressBar.val(progress);
                    //             if (progress > 0) {
                    //                 isStarted = true;
                    //             } else if (isStarted && progress < 0) {
                    //                 progressBar.addClass('hidden');
                    //                 return;
                    //             }
                    //             setInterval(update, isStarted ? 1000 : 10000);
                    //         };
                    //         update();
                    //     });
                }
            }
        );
    }
);

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
    let $element = $(element);
    if ($element.has('span.mark[for="' + data + '"]').length > 0) {
        return;
    }
    // get container.
    let container = $element.children('.container.mark');
    if (container.length <= 0) {
        container = $('<div/>', {
            'class': 'mark container',
        });
        $element.prepend(container);
    }
    let mark = $('<span/>', {
        'class': 'mark',
        'for': data,
    });
    container.append(mark);
    imageAvailable(
        path,
        function(temp) {
            if (!$element.is('img')) {
                $element = $element.find('img');
            }
            $element.attr('src', temp.src);
            $('span.mark[for="' + data + '"]', container).remove();
            show(element);

            mark.remove();
        },
        function() {
            $('span.mark[for="' + data + '"]', container).remove();
            onerror();
        }
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
