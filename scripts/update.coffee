zipFile = null
loading = false
valid = true
get = (name) -> document.getElementById(name).value
error = (name) ->
    document.getElementById(name).parentElement.classList.add('has-error')
    document.getElementById('error-alert').classList.remove('hidden')
    valid = false

document.getElementById('submit').addEventListener('click', () ->
    a.classList.remove('has-error') for a in document.querySelectorAll('.has-error')
    document.getElementById('error-alert').classList.add('hidden')
    valid = true

    kspVersion = get('ksp-version')
    version = get('version')
    changelog = get('changelog')
    notifyFollowers = get('notify-followers')

    error('version') if version == ''
    if zipFile == null
        valid = false

    return unless valid
    return if loading
    loading = true

    progress = document.getElementById('progress')
    xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/mod/' + window.mod_id + '/update')
    xhr.upload.onprogress = (e) ->
        if e.lengthComputable
            value = (e.loaded / e.total) * 100
            progress.querySelector('.progress-bar').style.width = value + '%'
    xhr.onload = () ->
        result = JSON.parse(this.responseText)
        progress.classList.remove('active')
        if not result.error?
            window.location = JSON.parse(this.responseText).url
        else
            alert = document.getElementById('error-alert')
            alert.classList.remove('hidden')
            alert.textContent = result.message
            document.getElementById('submit').removeAttribute('disabled')
            document.querySelector('.upload-mod a').classList.remove('hidden')
            document.querySelector('.upload-mod p').classList.add('hidden')
            loading = false
    form = new FormData()
    form.append('ksp-version', kspVersion)
    form.append('version', version)
    form.append('changelog', changelog)
    form.append('notify-followers', notifyFollowers)
    form.append('zipball', zipFile)
    document.getElementById('submit').setAttribute('disabled', 'disabled')
    progress.classList.add('active')
    progress.querySelector('.progress-bar').style.width = '0%'
    xhr.send(form)
, false)

document.querySelector('.upload-mod a').addEventListener('click', (e) ->
    e.preventDefault()
    document.querySelector('.upload-mod input').click()
, false)

document.querySelector('.upload-mod input').addEventListener('change', (e) ->
    zipFile = e.target.files[0]
    parent = document.querySelector('.upload-mod')
    parent.querySelector('a').classList.add('hidden')
    p = document.createElement('p')
    p.textContent = 'Ready.'
    parent.appendChild(p)
, false)

document.getElementById('submit').removeAttribute('disabled')
