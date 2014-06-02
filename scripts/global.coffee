((box) ->
    link = box.querySelector('a')
    input = box.querySelector('input')
    progress = box.querySelector('.upload-progress')

    link.addEventListener('click', (e) ->
        e.preventDefault()
        input.click()
    , false)

    input.addEventListener('change', (e) ->
        eval(box.dataset.event + '(input.files, box)')
    , false)

    progress.addEventListener('animationend', (e) ->
        progress.style.width = 0
        progress.classList.remove('fade-out')
    , false)
)(box) for box in document.querySelectorAll('.upload-well')
