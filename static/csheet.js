// TODO: button image loop
let count = 0;
$(document).ready(
    function() {
        $('html').dblclick(
            function() {
                $('.lightbox .small video:appeared').each(
                    function() {
                        loadResource(this, '.small');
                        this.play();
                    }
                );
            }
        );
        let $smallVideos = $('.lightbox .small video');
        $smallVideos.appear();
        $smallVideos.mouseenter(
            function() {
                loadResource(this, '.small');
                if (this.readyState > 1) {
                    this.play();
                }
            }
        );
        $smallVideos.mouseout(
            function() {
                this.pause();
            }
        );
        $smallVideos.on('durationchange',
            function() {
                if (this.readyState > 1) {
                    this.play();
                }
            }
        );
        $smallVideos.on('disappear',
            function() {
                unloadResource(this, '.small');
            }
        );
        $smallVideos.on('appear',
            function() {
                $(getLightbox(this)).find('video').each(
                    function() {
                        updatePoster(this);
                    }
                );
            }
        );
        $('.lightbox a.zoom').click(
            function() {
                loadResource(this, '.viewer');
            }
        );
        $('.viewer button.refresh').click(
            function() {
                unloadResource(this);
                loadResource(this);
            }
        );
        // Disable next/prev button when not avalieble.
        $('.lightbox .viewer a').click(
            function() {
                let $this = $(this);
                let $lightbox = $(getLightbox(this));
                let href;
                unloadResource(this, '.viewer');
                switch ($this.attr('class')) {
                    case 'prev':
                        let prev = $lightbox.prev();
                        while (prev.is('.shrink')) {
                            prev = prev.prev();
                        }
                        href = '#' + prev.attr('id');
                        loadResource(prev, '.viewer');
                        break;
                    case 'next':
                        let next = $lightbox.next();
                        while (next.is('.shrink')) {
                            next = next.next();
                        }
                        href = '#' + next.attr('id');
                        loadResource(next, '.viewer');
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
        $('.lightbox .full video').on('durationchange',
            function() {
                this.controls = this.duration > 1;
            }
        );

        // Setup drag.
        let $figures = $('.lightbox figure');
        $figures.each(
            function() {
                this.draggable = true;
            }
        );
        $figures.on('dragstart',
            function(ev) {
                let event = ev.originalEvent;
                let lightbox = getLightbox(this);
                let dragData = $(lightbox).data('drag');
                let plainData = dragData;
                if (window.location.protocol == 'file:') {
                    plainData =
                        window.location.origin +
                        decodeURI(
                            window.location.pathname.slice(
                                0, window.location.pathname.lastIndexOf('/'))) +
                        '/' +
                        plainData;
                }
                event.dataTransfer.setData('text/plain', plainData);
                event.dataTransfer
                    .setData('text/uri-list',
                        window.location.origin +
                        window.location.pathname +
                        window.location.search +
                        '#' +
                        lightbox.id);
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
        // Setup.
        $('.noscript').remove();
        $('video').removeClass('hidden');
        $smallVideos.each(
            function() {
                updatePoster(this);
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
function loadResource(element, selector) {
    selector = typeof (selector) === 'undefined' ? '*' : selector;
    let $lightbox = $(getLightbox(element));
    let $selected = $lightbox.find(selector);
    $selected.find('video').each(
        function() {
            updatePoster(this);
            if (!this.src) {
                this.src = $(this).data('src');
                this.load();
            }
        }
    );
    $selected.find('img').each(
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
function unloadResource(element, selector) {
    selector = typeof (selector) === 'undefined' ? '*' : selector;
    let $selected = $(getLightbox(element)).find(selector);
    $selected.find('video').each(
        function() {
            this.controls = false;
            this.removeAttribute('src');
            if (!$(this).parent('figure.small').length) {
                this.removeAttribute('poster');
            }
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
                expandLightbox(video);
            },
            function() {
                if (video.poster == url) {
                    video.removeAttribute('poster');
                }
                shrinkLightbox(video);
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
function stampedURL(url, precision) {
    precision = typeof (precision) === 'undefined' ? 9 : precision;
    return url + '?timestamp=' + new Date().getTime().toPrecision(precision);
}

/**
 * Shrink lightbox  element then set count.
 * @param {Element} element lightbox to hide.
 */
function shrinkLightbox(element) {
    let $lightbox = $(getLightbox(element));
    if ($lightbox.is('.shrink')) {
        return;
    }
    $lightbox.addClass('shrink');

    count += 1;
    updateCount();
}

/**
 * Expand element related lightbox.
 * @param {Element} element The root element.
 */
function expandLightbox(element) {
    let $lightbox = $(getLightbox(element));
    if (!$lightbox.is('.shrink')) {
        return;
    }
    $lightbox.removeClass('shrink');
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
 * Load image in background.
 * @param {String} url image url.
 * @param {Function} onload callback.
 * @param {Function} onerror callback.
 */
function imageAvailable(url, onload, onerror) {
    let temp = new Image;
    temp.onload = function() {
        onload(temp);
    };
    temp.onerror = onerror;
    temp.src = url;
}
