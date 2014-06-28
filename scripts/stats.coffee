applyScale = (min, max) ->
    jump = 1
    if max > 20
        jump = 5
    else if max > 100
        jump = 10
    else if max > 200
        jump = 20
    else if max > 500
        jump = 50
    else if max > 1000
        jump = 100
    else if max > 4000
        jump = Math.ceil(10 / max - min)
    return jump

months = ['Janurary', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
colors = [
    ['rgba(222,93,93,0.7)', 'rgba(179,74,74,1)'],
    ['rgba(93,222,93,0.7)', 'rgba(74,177,74,1)'],
    ['rgba(93,93,222,0.7)', 'rgba(74,74,177)'],
    ['rgba(222,158,93,0.7)', 'rgba(177,126,74)']
]
if window.download_stats
    # Let's do some stats baby
    # Each chart is set up in its own scope to make my life easier
    (() ->
        # Downloads
        chart = document.getElementById('downloads-over-time')
        labels = []
        entries = []
        max = 0
        color = 0
        key = []
        for i in [0..30]
            a = new Date(thirty_days_ago.getTime())
            a.setDate(a.getDate() + i)
            labels.push("#{months[a.getMonth()]} #{a.getDate()}")
        for v in window.versions
            data = []
            for i in [0..30]
                a = new Date(thirty_days_ago.getTime())
                a.setDate(a.getDate() + i)
                events = _.filter(download_stats, (d) ->
                    b = new Date(d.created)
                    return a.getDate() == b.getDate() and d.version_id == v.id
                )
                downloads = 0
                if events?
                    downloads = _.reduce(events, (m, e) ->
                        return m + e.downloads
                    , 0)
                data.push(downloads)
                if downloads > max
                    max = downloads
            if _.some(data, (d) -> d != 0)
                entries.push({
                    fillColor: colors[color][0],
                    strokeColor: colors[color][1],
                    pointColor: colors[color][1],
                    pointStrokeColor: '#fff',
                    data: data
                })
                key.push({ name: v.name, color: colors[color][0] })
                color++
                if color >= colors.length
                    color = 0
        jump = applyScale(0, max)
        entries.reverse()
        key.reverse()
        new Chart(chart.getContext("2d")).Line({
            labels : labels,
            datasets : entries
        }, {
            scaleOverride: true,
            scaleSteps: max / jump,
            scaleStepWidth: jump,
            scaleStartValue: 0
        })
        # Create key
        keyUI = document.getElementById('downloads-over-time-key')
        for k in key
            li = document.createElement('li')
            keyColor = document.createElement('span')
            keyText = document.createElement('span')
            keyColor.className = 'key-color'
            keyText.className = 'key-text'
            keyColor.style.backgroundColor = k.color
            keyText.textContent = k.name
            li.appendChild(keyColor)
            li.appendChild(keyText)
            keyUI.appendChild(li)
    )()
    (() ->
        # Followers
        chart = document.getElementById('followers-over-time')
        labels = []
        entries = []
        min = 0
        max = 0
        color = 0
        for i in [0..30]
            a = new Date(thirty_days_ago.getTime())
            a.setDate(a.getDate() + i)
            labels.push("#{months[a.getMonth()]} #{a.getDate()}")
        data = []
        for i in [0..30]
            a = new Date(thirty_days_ago.getTime())
            a.setDate(a.getDate() + i)
            events = _.filter(follower_stats, (d) ->
                b = new Date(d.created)
                return a.getDate() == b.getDate()
            )
            delta = 0
            if events?
                delta = _.reduce(events, (m, e) ->
                    return m + e.delta
                , 0)
            data.push(delta)
            if delta > max
                max = delta
            if delta < min
                min = delta
        if _.some(data, (d) -> d != 0)
            entries.push({
                fillColor: colors[color][0],
                strokeColor: colors[color][1],
                pointColor: colors[color][1],
                pointStrokeColor: '#fff',
                data: data
            })
            color++
            if color >= colors.length
                color = 0
        jump = 1 # TODO: Consider making this a more sensible value
        entries.reverse()
        new Chart(chart.getContext("2d")).Line({
            labels : labels,
            datasets : entries
        }, {
            scaleOverride: true,
            scaleSteps: max / jump,
            scaleStepWidth: jump,
            scaleStartValue: min
        })
    )()
