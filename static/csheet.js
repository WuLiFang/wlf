// TODO: button image loop
// let count = 0;
$(document).ready(
    function() {
        $('body').dblclick(
            function() {
                $('.lightbox .small video:appeared').each(
                    function() {
                        this.play();
                        // useData(this, 'preview');
                    }
                );
            }
        );
        $('.lightbox .small video').mouseenter(
            function() {
                this.load();
                this.play();
            }
        );
        $('.lightbox .small video').mouseout(
            function() {
                this.pause();
            }
        );
        // $('.lightbox .small').click(
        //     function() {
        //         let lightbox = getLightbox(this);
        //         $(lightbox).find('img').each(
        //             function() {
        //                 let element = this;
        //                 useData(element, 'full',
        //                     function() {
        //                         useData(element, 'preview');
        //                     }
        //                 );
        //             }
        //         );
        //     }
        // );
        // $('.lightbox figure video').each(function() {
        //     let $this = $(this);
        //     $this.appear();
        //     $this.on('disappear',
        //         function(e, $affected) {
        //             $affected.each(function() {
        //                 $(this).find('video').each(
        //                     function() {
        //                         this.pause();
        //                     }
        //                 );
        //                 // useMinimal(this);
        //                 // console.log(this);
        //             });
        //         }
        //     );
        // });
        // Disable next/prev button when not avalieble.
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
                        reload(prev);
                        break;
                    case 'next':
                        let next = $lightbox.next();
                        while (next.is('.hidden')) {
                            next = next.next();
                        }
                        href = '#' + next.attr('id');
                        reload(next);
                        break;
                    default:
                        href = $this.attr('href');
                }
                $('.lightbox video').each(
                    function() {
                        this.pause();
                    }
                );
                $this.attr('href', href);
                if (href == '#undefined') {
                    return false;
                }
            }
        );
        $('.lightbox a.zoom').click(
            function() {
                reload(this);
            }
        );
        // Switch controls.
        $('.lightbox .full video').on('canplaythrough',
            function() {
                // let video = this;
                /** Hide controls for single frame.  */
                this.controls = this.duration > 1;
                // function setControls() {
                //     video.controls = video.duration > 1;
                // };
                // this.oncanplaythrough = setControls;
                // setControls();
            }
        );

        // Set drag data.
        $('.lightbox a.zoom').on('dragstart', function(ev) {
                ev.originalEvent.dataTransfer.clearData();
                ev.originalEvent.dataTransfer
                    .setData('text/plain', $(getLightbox(this)).data('drag'));
            }

        );

        // $('.lightbox img').each(
        //     function() {
        //         $(this).attr('src', null);
        //         hide(this);
        //         useMinimal(this);
        //     }
        // );
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
 * Reload related video.
 * @param {element} element lightbox related element.
 */
function reload(element) {
    let lightbox = getLightbox(element);
    $(lightbox).find('video').each(
        function() {
            // this.src = $(lightbox).data('preview') +
            //     '?timestamp=' + new Date().getTime().toPrecision(9);
            this.load();
        }
    );
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

// /**
//  * Load image in background.
//  * @param {string} path image path.
//  * @param {function} onload callback.
//  * @param {function} onerror callback.
//  */
// function imageAvailable(path, onload, onerror) {
//     if (path == null | path == 'null') {
//         if (typeof (onerror) != 'undefined') {
//             onerror();
//         }
//         return;
//     }
//     let temp = new Image;
//     temp.onload = function() {
//         onload(temp);
//     };
//     temp.onerror = onerror;
//     temp.src = path + '?timestamp=' + new Date().getTime().toPrecision(9);
// }
