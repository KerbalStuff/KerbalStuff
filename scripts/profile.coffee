window.upload_bg = (files, box) ->
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
                path = null
                for file in media.files
                    if file.type == 'image/png' or file.type == 'image/jpeg'
                        path = file
                if path == null
                    p.textContent = 'Please upload images only.'
                else
                    document.getElementById('backgroundMedia').value = path.file
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

(() ->
    engine = new Bloodhound({
        name: 'versions',
        remote: '/ksp-profile-proxy/%QUERY',
        datumTokenizer: (d) -> Bloodhound.tokenizers.whitespace(d.name),
        queryTokenizer: Bloodhound.tokenizers.whitespace
    })
    engine.initialize()
    $("#ksp-forum-user")
        .typeahead(null,
        {
            source: engine.ttAdapter(),
            displayKey: (a) -> a.name
        })
        .on('typeahead:autocompleted', (e, s) ->
            $("#ksp-forum-id").val(s.id)
        )
)()
