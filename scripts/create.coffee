validation = [
    () ->
        return document.getElementById('description').value != '' and document.getElementById('name').value != ''
    , () ->
        if document.getElementById('installation').value == ''
            return false
        else if document.getElementById('installation').value == 'Just copy the files to the folders bro'
            document.getElementById('error').textContent = "That's not actually acceptable, try again"
            return false
        return true
    , () ->
        for i in ['version', 'ksp-version', 'license']
            if document.getElementById(i).value == ''
                return false
        return true
    , () ->
        return screenshots.length >= 2
    , () ->
        return true
    , () ->
        return true
    , () ->
        return document.getElementById('zipball').files.length != 0
]
step=0

if document.getElementById('continue-link')
    $("#process-tabs a, #process-tabs-2 a").click((e) -> e.preventDefault())
    $("#continue-link")
        .tooltip()
        .click((e) ->
            e.preventDefault()
            if e.target.getAttribute('disabled') == 'disabled'
                return
            error = document.getElementById('error')
            error.classList.add('hidden')
            error.textContent = 'Whoops! You missed some things. Double check them, please.'
            if validation[step]()? and validation[step]()
                step++
                if step != 0
                    $("#back-link").removeClass('hidden')
                if $("#process-tabs .active").next().size() == 1
                    $("#process-tabs .active").next().children('a').tab('show')
                else
                    if $("#process-tabs-2 .active").next().size() == 1
                        $("#process-tabs-2 .active").next().children('a').tab('show')
                    else
                        e.target.setAttribute('disabled', 'disabled')
                        $("form").submit()
            else
                error.classList.remove('hidden')
        )
    $("#back-link")
        .click((e) ->
            e.preventDefault()
            if e.target.getAttribute('disabled') == 'disabled'
                return
            error = document.getElementById('error')
            error.classList.add('hidden')
            error.textContent = 'Whoops! You missed some things. Double check them, please.'
            step--
            if step == 0
                e.target.classList.add('hidden')
            if $("#process-tabs-2 .active").prev().size() == 1
                $("#process-tabs-2 .active").prev().children('a').tab('show')
            else
                if $("#process-tabs .active").prev().size() == 1
                    $("#process-tabs .active").prev().children('a').tab('show')
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
            document.querySelector('html').style.backgroundImage = "url('#{path.url}')"
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

ksp_versions = []
xhr = new XMLHttpRequest()
xhr.open('GET', '/static/ksp-versions.json')
xhr.onload = () ->
    ksp_versions = JSON.parse(this.responseText)
    version_box = $('#ksp-version')
    version_box.val(ksp_versions[ksp_versions.length - 1])
    engine = new Bloodhound({
        name: 'versions',
        local: ksp_versions,
        datumTokenizer: (d) -> Bloodhound.tokenizers.whitespace(d),
        queryTokenizer: Bloodhound.tokenizers.whitespace
    })
    engine.initialize()
    version_box
        .focus(() -> version_box.typeahead('val', ''))
        .typeahead(null, {
        source: engine.ttAdapter(),
        displayKey: (a) -> a
    })
xhr.send()
