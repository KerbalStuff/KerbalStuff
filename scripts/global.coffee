((box) ->
    link = box.querySelector('a')
    input = box.querySelector('input')
    progress = box.querySelector('.upload-progress')

    if box.dataset.file?
        input = document.getElementById(box.dataset.file)

    link.addEventListener('click', (e) ->
        e.preventDefault()
        input.click()
    , false)

    input.addEventListener('change', (e) ->
        progress.style.width = 0
        progress.classList.remove('fade-out')
        eval(box.dataset.event + '(input.files, box)')
    , false)

    progress.addEventListener('animationend', (e) ->
        progress.style.width = 0
        progress.classList.remove('fade-out')
    , false)
)(box) for box in document.querySelectorAll('.upload-well')

link.addEventListener('click', (e) ->
    e.preventDefault()
    xhr = new XMLHttpRequest()
    if e.target.classList.contains('follow-button')
        xhr.open('POST', "/mod/#{e.target.dataset.mod}/follow")
        e.target.classList.remove('follow-button')
        e.target.classList.add('unfollow-button')
        e.target.textContent = 'Unfollow'
        try
            document.getElementById('alert-follow').classList.remove('hidden')
            document.getElementById('alert-follow-confirmed').textContent = e.target.dataset.name
    else
        xhr.open('POST', "/mod/#{e.target.dataset.mod}/unfollow")
        e.target.classList.remove('unfollow-button')
        e.target.classList.add('follow-button')
        e.target.textContent = 'Follow'
    xhr.send()
, false) for link in document.querySelectorAll('.follow-button, .unfollow-button')

link.addEventListener('click', (e) ->
    e.preventDefault()
    xhr = new XMLHttpRequest()
    if e.target.classList.contains('feature-button')
        xhr.open('POST', "/mod/#{e.target.dataset.mod}/feature")
        e.target.classList.remove('feature-button')
        e.target.classList.add('unfeature-button')
        e.target.textContent = 'Unfeature'
    else
        xhr.open('POST', "/mod/#{e.target.dataset.mod}/unfeature")
        e.target.classList.remove('unfeature-button')
        e.target.classList.add('feature-button')
        e.target.textContent = 'Feature'
    xhr.send()
, false) for link in document.querySelectorAll('.feature-button, .unfeature-button')
