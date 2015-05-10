(function() {
  var a, editor, _i, _len, _ref;

  editor = new Editor();

  editor.render();

  window.upload_bg = function(files, box) {
    var file, formdata, p, progress, xhr;
    file = files[0];
    p = document.createElement('p');
    p.textContent = 'Uploading...';
    p.className = 'status';
    box.appendChild(p);
    box.querySelector('a').classList.add('hidden');
    progress = box.querySelector('.upload-progress');
    xhr = new XMLHttpRequest();
    xhr.open('POST', "/api/mod/" + window.mod_id + "/update-bg");
    xhr.upload.onprogress = function(e) {
      if (e.lengthComputable) {
        return progress.style.width = (e.loaded / e.total) * 100 + '%';
      }
    };
    xhr.onload = function(e) {
      var resp;
      if (xhr.status !== 200) {
        p.textContent = 'Please upload JPG or PNG only.';
        return setTimeout(function() {
          box.removeChild(p);
          return box.querySelector('a').classList.remove('hidden');
        }, 3000);
      } else {
        resp = JSON.parse(xhr.responseText);
        p.textContent = 'Done!';
        document.getElementById('background').value = resp.path;
        document.getElementById('header-well').style.backgroundImage = 'url("' + resp.path + '")';
        return setTimeout(function() {
          box.removeChild(p);
          return box.querySelector('a').classList.remove('hidden');
        }, 3000);
      }
    };
    formdata = new FormData();
    formdata.append('image', file);
    return xhr.send(formdata);
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
