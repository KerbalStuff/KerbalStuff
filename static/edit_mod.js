(function() {
  var a, _i, _len, _ref;

  window.upload_bg = function(files, box) {
    var file, p, progress;
    file = files[0];
    p = document.createElement('p');
    p.textContent = 'Uploading...';
    p.className = 'status';
    box.appendChild(p);
    box.querySelector('a').classList.add('hidden');
    progress = box.querySelector('.upload-progress');
    return MediaCrush.upload(file, function(media) {
      progress.classList.add('fade-out');
      progress.style.width = '100%';
      p.textContent = 'Processing...';
      return media.wait(function() {
        return MediaCrush.get(media.hash, function(media) {
          var path, _i, _len, _ref;
          p.textContent = 'Done';
          path = null;
          _ref = media.files;
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            file = _ref[_i];
            if (file.type === 'image/png' || file.type === 'image/jpeg') {
              path = file;
            }
          }
          if (path === null) {
            return p.textContent = 'Please upload images only.';
          } else {
            document.getElementById('background').value = path.file;
            document.getElementById('header-well').style.backgroundImage = 'url("https://mediacru.sh/' + path.file + '")';
            return setTimeout(function() {
              box.removeChild(p);
              return box.querySelector('a').classList.remove('hidden');
            }, 3000);
          }
        });
      });
    }, function(e) {
      if (e.lengthComputable) {
        return progress.style.width = (e.loaded / e.total) * 100 + '%';
      }
    });
  };

  document.getElementById('add-shared-author').addEventListener('click', function(e) {
    var data, m, u, xhr;
    e.preventDefault();
    m = document.getElementById('shared-author-error');
    u = document.getElementById("new-shared-author");
    m.classList.add('hidden');
    xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/mod/' + window.mod_id + '/grant');
    xhr.onload = function() {
      var b, div, response;
      response = JSON.parse(this.responseText);
      if (response.error) {
        m.textContent = response.message;
        return m.classList.remove('hidden');
      } else {
        div = document.createElement('div');
        div.className = 'col-md-6';
        div.textContent = u.value;
        b = document.getElementById('beforeme');
        b.parentElement.insertBefore(div, b);
        return u.value = '';
      }
    };
    data = new FormData();
    data.append('user', u.value);
    return xhr.send(data);
  }, false);

  document.getElementById('new-shared-author').addEventListener('keypress', function(e) {
    if (e.keyCode === 13) {
      e.preventDefault();
      return document.getElementById('add-shared-author').click();
    }
  }, false);

  _ref = document.querySelectorAll('.remove-author');
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    a = _ref[_i];
    a.addEventListener('click', function(e) {
      var form, target, xhr;
      e.preventDefault();
      target = e.target;
      if (target.tagName !== 'A') {
        target = target.parentElement;
      }
      xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/mod/' + window.mod_id + '/revoke');
      xhr.onload = function() {
        return window.location = window.location;
      };
      form = new FormData();
      form.append('user', target.dataset.user);
      return xhr.send(form);
    }, false);
  }

}).call(this);
