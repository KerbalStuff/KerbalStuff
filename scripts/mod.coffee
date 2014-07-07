InstantClick.on('change', () ->
    if window.location.pathname.indexOf('/mod/') == 0
        if window.editable
            window.activateStats()

            window.upload_zipball = (files, box) ->
                p = document.createElement('p')
                p.textContent = 'Ready to continue.'
                box.appendChild(p)
                box.querySelector('a').classList.add('hidden')

            edit.addEventListener('click', (e) ->
                e.preventDefault()
                p = e.target.parentElement.parentElement
                v = e.target.parentElement.dataset.version
                c = p.querySelector('.raw-changelog').innerHTML
                m = document.getElementById('version-edit-modal')
                m.querySelector('.version-id').value = v
                m.querySelector('.changelog-text').innerHTML = c
                $(m).modal()
            , false) for edit in document.querySelectorAll('.edit-version')

            $("#submit-button").click((e) ->
                e.preventDefault()
                $('.upload-link').removeClass('text-danger')
                $("#version").parent().removeClass('has-error')

                if not document.getElementById('zipball').files.length
                    $('.upload-link').addClass('text-danger')
                    return
                if not $("#version").val()
                    $("#version").parent().addClass('has-error')
                    return

                document.getElementById('update-form').submit()
            )

            get_image_path = (media) ->
                path = null
                for file in media.files
                    if file.type == 'image/png' or file.type == 'image/jpeg'
                        path = file
                for file in media.extras
                    if file.type == 'image/png' or file.type == 'image/jpeg'
                        path = file
                return path

            screenshots = []
            window.upload_screenshot = (files, box) ->
                upload_mediacrush(files, box, (media, p) ->
                    path = get_image_path(media)
                    if path == null
                        p.textContent = 'Please upload images only.'
                    else
                        panel = document.getElementById('uploaded-screenshots')
                        if panel.dataset.empty == 'true'
                            panel.innerHTML = ''
                        panel.dataset.empty = 'false'
                        img = document.createElement('img')
                        img.src = path.url
                        img.dataset.id = media.hash
                        img.style.cursor = 'pointer'
                        img.addEventListener('click', () ->
                            delete_screenshot(media.hash)
                        , false)
                        panel.appendChild(img)
                        input = document.querySelector('input[name="screenshots"]')
                        screenshots.push(media.hash)
                        input.value = screenshots.join(',')
                        if screenshots.length == 5
                            box.parentElement.removeChild(box)
                        setTimeout(() ->
                            box.removeChild(p)
                            box.querySelector('a').classList.remove('hidden')
                        , 2000)
                )

            videos = []
            window.upload_video = (files, box) ->
                upload_mediacrush(files, box, (media, p) ->
                    if media.blob_type != 'video'
                        p.textContent = 'Please upload videos only.'
                    else
                        path = get_image_path(media)
                        if path == null
                            p.textContent = 'Please upload videos only.'
                        else
                            panel = document.getElementById('uploaded-videos')
                            if panel.dataset.empty == 'true'
                                panel.innerHTML = ''
                            panel.dataset.empty = 'false'
                            img = document.createElement('img')
                            img.src = path.url
                            panel.appendChild(img)
                            input = document.querySelector('input[name="videos"]')
                            videos.push(media.hash)
                            input.value = videos.join(',')
                            if videos.length == 2
                                box.parentElement.removeChild(box)
                    setTimeout(() ->
                        box.removeChild(p)
                        box.querySelector('a').classList.remove('hidden')
                    , 2000)
                )

            window.upload_background = (files, box) ->
                upload_mediacrush(files, box, (media, p) ->
                    path = get_image_path(media)
                    if path == null
                        p.textContent = 'Please upload images only.'
                    else
                        document.getElementById('backgroundMedia').value = path.file
                        setTimeout(() ->
                            box.removeChild(p)
                            box.querySelector('a').classList.remove('hidden')
                        , 3000)
                )

            window.upload_zipball = (files, box) ->
                p = document.createElement('p')
                p.textContent = 'Ready to continue.'
                box.appendChild(p)
                box.querySelector('a').classList.add('hidden')

            upload_mediacrush = (files, box, callback) ->
                file = files[0]
                p = document.createElement('p')
                p.textContent = 'Uploading...'
                box.appendChild(p)
                box.querySelector('a').classList.add('hidden')
                progress = box.querySelector('.upload-progress')

                MediaCrush.upload(file, (media) ->
                    progress.classList.add('fade-out')
                    progress.style.width = '100%'
                    p.textContent = 'Processing...'
                    media.wait(() ->
                        MediaCrush.get(media.hash, (media) ->
                            p.textContent = 'Done'
                            callback(media, p)
                        )
                    )
                , (e) ->
                    if e.lengthComputable
                        progress.style.width = (e.loaded / e.total) * 100 + '%'
                )

            delete_screenshot = (m) ->
                screenshots = screenshots.filter((i) -> i != m)
                document.getElementById('screenshots').value = screenshots.join(',')
                img = document.querySelector('#uploaded-screenshots img[data-id="' + m + '"]')
                img.parentElement.removeChild(img)

            delete_video = (m) ->
                videos = videos.filter((i) -> i != m)
                document.getElementById('videos').value = videos.join(',')
                img = document.querySelector('#uploaded-videos img[data-id="' + m + '"]')
                img.parentElement.removeChild(img)

            for v in window.screen_list.split(',')
                ((v) ->
                    if v
                        screenshots.push(v.substr(1, v.length - 5))
                        panel = document.getElementById('uploaded-screenshots')
                        if panel.dataset.empty == 'true'
                            panel.innerHTML = ''
                        panel.dataset.empty = 'false'
                        img = document.createElement('img')
                        img.src = 'https://cdn.mediacru.sh' + v
                        img.dataset.id = v.substr(1, v.length - 5)
                        img.style.cursor = 'pointer'
                        img.addEventListener('click', () ->
                            delete_screenshot(v.substr(1, v.length - 5))
                        , false)
                        panel.appendChild(img)
                        document.getElementById('screenshots').value = screenshots.join(',')
                )(v)
            for v in window.video_list.split(',')
                ((v) ->
                    if v
                        videos.push(v)
                        panel = document.getElementById('uploaded-videos')
                        if panel.dataset.empty == 'true'
                            panel.innerHTML = ''
                        panel.dataset.empty = 'false'
                        img = document.createElement('img')
                        img.src = 'https://cdn.mediacru.sh/' + v + '.jpg'
                        img.dataset.id = v
                        img.style.cursor = 'pointer'
                        img.addEventListener('click', () ->
                            delete_video(v)
                        , false)
                        panel.appendChild(img)
                        document.getElementById('videos').value = videos.join(',')
                )(v)
, false)
