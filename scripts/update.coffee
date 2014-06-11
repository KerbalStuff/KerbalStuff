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

window.upload_zipball = (files, box) ->
    p = document.createElement('p')
    p.textContent = 'Ready to continue.'
    box.appendChild(p)
    box.querySelector('a').classList.add('hidden')
