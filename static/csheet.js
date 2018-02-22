// TODO: button image loop
// let count = 0;
$(document).ready(
    function() {
        // unloadAll();
        $('body').dblclick(
            function() {
                $('.lightbox .small video:appeared').each(
                    function() {
                        reload(this, '.small');
                        if (this.readyState > 1) {
                            this.play();
                        }
                    }
                );
            }
        );
        let $smallVideos = $('.lightbox .small video');
        $smallVideos.appear();
        $smallVideos.mouseenter(
            function() {
                reload(this, '.small');
                if (this.readyState > 1) {
                    this.play();
                }
            }
        );
        $smallVideos.mouseout(
            function() {
                unload(this, '.small');
            }
        );
        $smallVideos.on('appear',
            function() {
                updatePoster(this);
            }
        );
        $smallVideos.each(
            function() {
                updatePoster(this);
            }
        );
        $('video').each(
            function() {
                recordAttr(this, ['poster', 'src']);
                $(this).removeClass('hidden');
            }
        );
        $('.noscript').addClass('hidden');
        $('img').each(
            function() {
                recordAttr(this, ['src']);
            }
        );
        $('.lightbox a.zoom').click(
            function() {
                reload(this, '.viewer');
            }
        );
        // Disable next/prev button when not avalieble.
        $('.lightbox .viewer a').click(
            function() {
                let $this = $(this);
                let $lightbox = $(getLightbox(this));
                let href;
                unload(this, '.viewer');
                switch ($this.attr('class')) {
                    case 'prev':
                        let prev = $lightbox.prev();
                        while (prev.is('.hidden')) {
                            prev = prev.prev();
                        }
                        href = '#' + prev.attr('id');
                        reload(prev, '.viewer');
                        break;
                    case 'next':
                        let next = $lightbox.next();
                        while (next.is('.hidden')) {
                            next = next.next();
                        }
                        href = '#' + next.attr('id');
                        reload(next, '.viewer');
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
        // Switch controls.
        $('.lightbox .full video').on('readystatechange',
            function() {
                if (this.readyState > 0) {
                    this.controls = this.duration > 1;
                }
            }
        );

        // Set drag data.
        $('.lightbox a.zoom').on('dragstart', function(ev) {
                ev.originalEvent.dataTransfer.clearData();
                ev.originalEvent.dataTransfer
                    .setData('text/plain', $(getLightbox(this)).data('drag'));
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
                    let isStarted = false;
                    /**
                     * Update progress bar value without sse.
                     * @argument {element} progressBar progressbar to update.
                     */
                    function updateProgressBar(progressBar) {
                        $.get('/pack_progress', function(progress) {
                            progressBar.val(progress);
                            if (isStarted && progress < 0) {
                                progressBar.addClass('hidden');
                                return;
                            } else if (progress > 0) {
                                isStarted = true;
                            }
                            setTimeout(function() {
                                updateProgressBar(progressBar);
                            }, 100);
                        });
                    }
                    updateProgressBar(progressBar);
                };
            }
        );
    }
);

/**
 * get a light box from element parent.
 * @param {Element} element this element.
 * @return {Element} lightbox element.
 */
function getLightbox(element) {
    let $element = $(element);
    if ($element.is('.lightbox')) {
        return element;
    }
    return $element.parents('.lightbox')[0];
}


/**
 * Reload related video.
 * @param {Element} element element in a lightbox.
 * @param {String} selector element selector.
 */
function reload(element, selector = '*') {
    let $lightbox = $(getLightbox(element));
    $lightbox.find(selector).find('video').each(
        function() {
            updatePoster(this);
            this.src = $(this).data('src');
            this.load();
        }
    );
    $lightbox.find(selector).find('img').each(
        function() {
            let img = this;
            let url = stampedURL($(this).data('src'));
            imageAvailable(
                url,
                function() {
                    img.src = url;
                }
            );
        }
    );
}

/**
 * Unload related video to display poster.
 * @param {Element} element element in a lightbox.
 * @param {String} selector element selector.
 */
function unload(element, selector = '*') {
    let $selected = $(getLightbox(element)).find(selector);
    $selected.find('video').each(
        function() {
            updatePoster(this);
            this.controls = false;
            this.load();
        }
    );
    $selected.find('img').each(
        function() {
            this.removeAttribute('src');
        }
    );
}

/**
 * Update video poster.
 * @param {Element} video video element.
 */
function updatePoster(video) {
    let $video = $(video);
    let $parent = $video.parent('figure.small');
    let url = $(video).data('poster');
    if (url) {
        url = stampedURL(url);
        imageAvailable(
            url,
            function() {
                // Release size
                if ($parent.length) {
                    $video.height('');
                    $parent.width('');
                }
                // update
                video.poster = url;
                // Keep size
                if ($parent.length) {
                    let height = $video.height();
                    let width = $video.width();
                    if (height == 200 && width) {
                        $video.height(height);
                        $parent.width(width);
                    }
                }
                video.removeAttribute('src');
            },
            function() {
                video.removeAttribute('poster');
            }
        );
    }
}

/**
 * Add timestamp to url.
 * @param {String} url url to stamp.
 * @param {Number} precision stamp precision.
 * @return {String} stamped url.
 */
function stampedURL(url, precision = 9) {
    return url + '?timestamp=' + new Date().getTime().toPrecision(precision);
}

/**
 * Unload all lightbox video.
 */
function unloadAll() {
    $html = $($('#images').innerHTML);
    window.stop();
    $('.lightbox .viewer img').each(
        function() {
            this.removeAttribute('src');
        }
    );
    $('.lightbox .viewer video').each(
        function() {
            this.removeAttribute('poster');
            this.removeAttribute('src');
            this.controls = false;
        }
    );
}

/**
 * Record attribute data on element.
 * @param {Element} element element to record.
 * @param {Array} attributes attribute names.
 */
function recordAttr(element, attributes) {
    let $element = $(element);
    for (let i = 0; i < attributes.length; i++) {
        let name = attributes[i];
        let value = $element.attr(name);
        if (value) {
            $element.data(name, value);
        }
    }
}
// /**
//  * Hide lightbox  element then set count.
//  * @param {element} lightbox lightbox to hide.
//  */
// function hide(lightbox) {
//     lightbox = getLightbox(lightbox);
//     let $lightbox = $(lightbox);
//     if ($lightbox.is('.hidden')) {
//         return;
//     }
//     $lightbox.addClass('hidden');

//     count += 1;
//     updateCount();
// }

// /**
//  * Show element related lightbox.
//  * @param {element} element The root element.
//  */
// function show(element) {
//     let lightbox = $(getLightbox(element));
//     if (!lightbox.is('.hidden')) {
//         return;
//     }
//     lightbox.removeClass('hidden');
//     count -= 1;
//     updateCount();
// }

// /**
//  * Update count display.
//  */
// function updateCount() {
//     let header = document.getElementsByTagName('header')[0];
//     let lightboxes = document.getElementsByClassName('lightbox');
//     let total = lightboxes.length;
//     header.children[0].innerText = (
//         (total - count).toString() + '/' + total.toString()
//     );
// }
// /**
//  * use minimal images for this element.
//  * @param {element} element root element.
//  */
// function useMinimal(element) {
//     // Use minaimal image to save memory.
//     useData(element, 'thumb',
//         function() {
//             useData(element, 'full',
//                 function() {
//                     useData(element, 'preview',
//                         function() {
//                             hide(element);
//                         }
//                     );
//                 }
//             );
//         }
//     );
// }

// /**
//  * Choose data to use on image.
//  * @param {element} element root element.
//  * @param {string} data data name.
//  * @param {function} onerror callback
//  * @return {string} Used data
//  */
// function useData(element, data, onerror) {
//     let lightbox = getLightbox(element);
//     let path = lightbox.getAttribute('data-' + data);
//     let $element = $(element);
//     if ($element.has('span.mark[for="' + data + '"]').length > 0) {
//         return;
//     }
//     // get container.
//     let container = $element.children('.container.mark');
//     if (container.length <= 0) {
//         container = $('<div/>', {
//             'class': 'mark container',
//         });
//         $element.prepend(container);
//     }
//     let mark = $('<span/>', {
//         'class': 'mark',
//         'for': data,
//     });
//     container.append(mark);
//     imageAvailable(
//         path,
//         function(temp) {
//             if (!$element.is('img')) {
//                 $element = $element.find('img');
//             }
//             $element.attr('src', temp.src);
//             $('span.mark[for="' + data + '"]', container).remove();
//             show(element);

//             mark.remove();
//         },
//         function() {
//             $('span.mark[for="' + data + '"]', container).remove();
//             if (onerror) {
//                 onerror();
//             }
//         }
//     );
//     return path;
// }

/**
 * Load image in background.
 * @param {String} url image url.
 * @param {Function} onload callback.
 * @param {Function} onerror callback.
 */
function imageAvailable(url, onload, onerror) {
    if (url == null | url == 'null') {
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
    temp.src = url;
}
