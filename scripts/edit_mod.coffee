window.upload_bg = (files, box) ->
    file = files[0]
    p = document.createElement('p')
    p.textContent = 'Uploading...'
    p.className = 'status'
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
                path = null
                for file in media.files
                    if file.type == 'image/png' or file.type == 'image/jpeg'
                        path = file
                if path == null
                    p.textContent = 'Please upload images only.'
                else
                    document.getElementById('background').value = path.file
                    document.getElementById('header-well').style.backgroundImage = 'url("https://mediacru.sh/' + path.file + '")'
                    setTimeout(() ->
                        box.removeChild(p)
                        box.querySelector('a').classList.remove('hidden')
                    , 3000)
            )
        )
    , (e) ->
        if e.lengthComputable
            progress.style.width = (e.loaded / e.total) * 100 + '%'
    )

document.getElementById('add-shared-author').addEventListener('click', (e) ->
    e.preventDefault()
    m = document.getElementById('shared-author-error')
    u = document.getElementById("new-shared-author")
    m.classList.add('hidden')
    xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/mod/' + window.mod_id + '/grant')
    xhr.onload = () ->
        response = JSON.parse(this.responseText)
        if response.error
            m.textContent = response.message
            m.classList.remove('hidden')
        else
            div = document.createElement('div')
            div.className = 'col-md-6'
            div.textContent = u.value
            b = document.getElementById('beforeme')
            b.parentElement.insertBefore(div, b)
            u.value = ''
    data = new FormData()
    data.append('user', u.value)
    xhr.send(data)
, false)

a.addEventListener('click', (e) ->
    e.preventDefault()
    target = e.target
    if target.tagName != 'A'
        target = target.parentElement
    xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/mod/' + window.mod_id + '/revoke')
    xhr.onload = () ->
        #window.location = window.location
    form = new FormData()
    form.append('user', target.dataset.user)
    xhr.send(form)
, false) for a in document.querySelectorAll('.remove-author')
