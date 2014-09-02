window.activateStats()
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

edit.addEventListener('click', (e) ->
    e.preventDefault()
    m = document.getElementById('confirm-delete-version')
    m.querySelector('form').action = "/mod/#{mod_id}/version/#{e.target.dataset.version}/delete"
    $(m).modal()
, false) for edit in document.querySelectorAll('.delete-version')
