// TODO: button image loop
let count = 0;
let isClient = false;
let lightboxHeight = 200;
$(document).ready(
    function() {
        let $videos = $('.lightbox video');
        let $smallVideos = $videos.filter('.small');
        let isAutoRefresh = false;
        $smallVideos.appear();
        $('html').dblclick(
            function() {
                $smallVideos.filter(':appeared').each(
                    function() {
                        if (!this.readyState) {
                            loadResource(this, '.small');
                        } else {
                            this.play();
                        }
                    }
                );
            }
        );
        // Soure manage.
        $smallVideos.mouseenter(
            function() {
                if (!this.readyState) {
                    loadResource(this, '.small');
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
                        if (!isAutoRefresh) {
                            updatePoster(this);
                        }
                    }
                );
            }
        );
        $('.lightbox a.zoom').click(
            function() {
                loadResource(this, '.full');
                $smallVideos.each(
                    function() {
                        this.pause();
                    }
                );
            }
        );
        if (isClient) {
            // Refresh button.
            $('.viewer').append(
                $('<button>', {
                    class: 'refresh',
                    click: function() {
                        loadResource(this, '.full', true);
                    },
                })
            );
            // Auto refresh button.
            let refreshInterval;
            let buttons = $('.refresh-module')
                .removeClass('hidden').find('button');
            let spans = buttons.find('span');
            let isHovering;
            let queueName = 'autoRefresh';
            $('.images').mouseenter(function() {
                isHovering = true;
            }).mouseleave(function() {
                isHovering = false;
            });
            let workerCount = 0;
            let put = function(video) {
                $(document).queue(queueName,
                    function() {
                        if ($(video).is(':appeared')) {
                            updatePoster(
                                video,
                                !isHovering,
                                function() {
                                    workerCount -= 1;
                                    while (workerCount < 3) {
                                        $(document).dequeue(queueName);
                                        workerCount += 1;
                                    }
                                }
                            );
                        } else {
                            $(document).dequeue(queueName);
                        }
                    }
                );
            };
            let onInterval = function(delay) {
                delay = typeof (delay) === 'undefined' ? 5000 : delay;
                let $appearedViedos = $smallVideos.filter(':appeared');
                if ($(document).queue(queueName).length == 0) {
                    workerCount = 0;
                    $appearedViedos.each(
                        function() {
                            if (this.paused) {
                                put(this);
                            }
                        }
                    );
                    setTimeout(function() {
                        $(document).dequeue(queueName);
                    }, delay);
                }
                spans.css({
                    width: Math.min(
                        $(document).queue(queueName).length
                        / $appearedViedos.length,
                        1) * 100 + '%',
                });
            };
            buttons.click(
                function() {
                    if (!isAutoRefresh) {
                        onInterval(0);
                        refreshInterval = setInterval(onInterval, 100);
                        isAutoRefresh = true;
                        buttons.attr('status', 'on');
                    } else {
                        clearInterval(refreshInterval);
                        $(document).clearQueue(queueName);
                        buttons.attr('status', 'off');
                        isAutoRefresh = false;
                    }
                }
            ).trigger('click');
        }
        // Disable next/prev button when not avalieble.
        $('.lightbox .viewer a').click(
            function() {
                let $this = $(this);
                let $lightbox = $(getLightbox(this));
                let href;
                unloadResource(this, '.full');
                switch ($this.attr('class')) {
                    case 'prev':
                        let prev = $lightbox.prev();
                        while (prev.is('.shrink')) {
                            prev = prev.prev();
                        }
                        href = '#' + prev.attr('id');
                        loadResource(prev, '.full');
                        break;
                    case 'next':
                        let next = $lightbox.next();
                        while (next.is('.shrink')) {
                            next = next.next();
                        }
                        href = '#' + next.attr('id');
                        loadResource(next, '.full');
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
        // Setup drag.
        $('.lightbox').each(
            function() {
                this.draggable = true;
            }
        ).on('dragstart',
            function(ev) {
                let event = ev.originalEvent;
                // let lightbox = getLightbox(this);
                let lightbox = this;
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
        // Video play controls.
        $smallVideos.on('loadeddata',
            function() {
                this.play();
            }
        );
        $smallVideos.mouseenter(
            function() {
                if (this.readyState > 1) {
                    this.play();
                }
            }
        );
        $smallVideos.mouseleave(
            function() {
                this.pause();
            }
        );
        $('.lightbox video.full').on('loadedmetadata',
            function() {
                this.controls = this.duration > 0.1;
            }
        );
        // simlpe help
        $('nav').append(
            $('<button>', {
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
                shrinkLightbox(this);
                if (!isClient) {
                    updatePoster(this);
                }
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
 * @param {Boolean} isRefresh if `isRefresh` is true, will add timestamp to url.
 */
function loadResource(element, selector, isRefresh) {
    selector = typeof (selector) === 'undefined' ? '*' : selector;
    let $lightbox = $(getLightbox(element));
    let $selected = $lightbox.find(selector);
    $selected.filter('video').each(
        function() {
            updatePoster(this);
            let url = $(this).data('src');
            if (isRefresh || isClient && this.src && !this.readyState) {
                url = stampedURL(url);
            }
            this.src = url;
            this.load();
        }
    );
    $selected.find('img').each(
        function() {
            let img = this;
            let url = $(this).data('src');
            if (!img.src) {
                img.src = url;
            }
            url = isClient ? stampedURL(url) : url;
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
    let $selected = $(getLightbox(element)).find('video').filter(selector);
    $selected.each(
        function() {
            this.controls = false;
            this.removeAttribute('src');
            if (!$(this).is('.small')) {
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
 * @param {Boolean} isReplace force poster to display.
 * @param {Function} onfinish Callback on finish.
 */
function updatePoster(video, isReplace, onfinish) {
    let $video = $(video);
    let isSmall = $video.is('.small');
    let url = $video.data('poster');
    let $lightbox = $(getLightbox(video));
    let addIndicator = function() {
        if (isSmall) {
            $lightbox.css({
                border: '1px solid white',
                padding: '0',
            });
        } else {
            $video.css({border: '1px solid white'});
        }
    };
    let removeIndicator = function() {
        if (isSmall) {
            $lightbox.css({
                border: '',
                padding: '1px',
            });
        } else {
            $video.css({border: ''});
        }
    };
    if (url) {
        if (!video.poster) {
            video.poster = url;
        }
        url = isClient ? stampedURL(url) : url;
        addIndicator();
        imageAvailable(
            url,
            function(img) {
                if (isSmall) {
                    getLightbox(video).dataset.ratio =
                        img.width / img.height;
                }
                expandLightbox(video);
                video.poster = url;
                if (isReplace) {
                    video.removeAttribute('src');
                    video.load();
                }
                removeIndicator();
                if (onfinish) {
                    onfinish(img);
                }
            },
            function() {
                if (video.attributes.poster == url) {
                    video.removeAttribute('poster');
                }
                if (isSmall && !video.poster) {
                    shrinkLightbox(video);
                }
                removeIndicator();
                if (onfinish) {
                    onfinish();
                }
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
    $lightbox.width('10px');
    count += 1;
    updateCount();
}

/**
 * Expand element related lightbox.
 * @param {Element} element The root element.
 */
function expandLightbox(element) {
    let $lightbox = $(getLightbox(element));
    $lightbox.height(lightboxHeight);
    $lightbox.width($lightbox.data('ratio') * lightboxHeight);
    if ($lightbox.is('.shrink')) {
        $lightbox.removeClass('shrink');
        count -= 1;
        updateCount();
    }
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
