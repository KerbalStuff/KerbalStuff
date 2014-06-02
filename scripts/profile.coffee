window.upload_bg = (files, box) ->
    file = files[0]
    p = document.createElement('p')
    p.textContent = 'Uploading...'
    box.appendChild(p)
    box.removeChild(box.querySelector('a'))
    progress = box.querySelector('.upload-progress')

    MediaCrush.upload(file, (media) ->
        progress.classList.add('fade-out')
        progress.style.width = '100%'
        p.textContent = 'Processing...'
        media.wait(() ->
            MediaCrush.get(media.hash, (media) ->
                p.textContent = 'Done'
                path = null
                for file in media.files
                    if file.type == 'image/png' or file.type == 'image/jpeg'
                        path = file
                if path == null
                    p.textContent = 'Please upload images only.'
                else
                    document.querySelector('html').style.backgroundImage = "url('#{path.url}')"
                    document.getElementById('backgroundMedia').value = path.file
            )
        )
    , (e) ->
        if e.lengthComputable
            progress.style.width = (e.loaded / e.total) * 100 + '%'
    )
