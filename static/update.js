(function() {
  var dragNop, error, get, loading, selectFile, valid, zipFile;

  zipFile = null;

  loading = false;

  valid = true;

  get = function(name) {
    return document.getElementById(name).value;
  };

  error = function(name) {
    document.getElementById(name).parentElement.classList.add('has-error');
    document.getElementById('error-alert').classList.remove('hidden');
    return valid = false;
  };

  document.getElementById('submit').addEventListener('click', function() {
    var a, changelog, form, kspVersion, notifyFollowers, progress, version, xhr, _i, _len, _ref;
    _ref = document.querySelectorAll('.has-error');
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      a = _ref[_i];
      a.classList.remove('has-error');
    }
    document.getElementById('error-alert').classList.add('hidden');
    valid = true;
    kspVersion = get('ksp-version');
    version = get('version');
    changelog = get('changelog');
    notifyFollowers = document.getElementById('notify-followers').checked;
    if (version === '') {
      error('version');
    }
    if (zipFile === null) {
      valid = false;
    }
    if (!valid) {
      return;
    }
    if (loading) {
      return;
    }
    loading = true;
    progress = document.getElementById('progress');
    xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/mod/' + window.mod_id + '/update');
    xhr.upload.onprogress = function(e) {
      var value;
      if (e.lengthComputable) {
        value = (e.loaded / e.total) * 100;
        return progress.querySelector('.progress-bar').style.width = value + '%';
      }
    };
    xhr.onload = function() {
      var alert, result;
      result = JSON.parse(this.responseText);
      progress.classList.remove('active');
      if (result.error == null) {
        return window.location = JSON.parse(this.responseText).url;
      } else {
        alert = document.getElementById('error-alert');
        alert.classList.remove('hidden');
        alert.textContent = result.message;
        document.getElementById('submit').removeAttribute('disabled');
        document.querySelector('.upload-mod a').classList.remove('hidden');
        document.querySelector('.upload-mod p').classList.add('hidden');
        return loading = false;
      }
    };
    form = new FormData();
    form.append('ksp-version', kspVersion);
    form.append('version', version);
    form.append('changelog', changelog);
    form.append('notify-followers', notifyFollowers);
    form.append('zipball', zipFile);
    document.getElementById('submit').setAttribute('disabled', 'disabled');
    progress.classList.add('active');
    progress.querySelector('.progress-bar').style.width = '0%';
    return xhr.send(form);
  }, false);

  selectFile = function(file) {
    var p, parent;
    zipFile = file;
    parent = document.querySelector('.upload-mod');
    parent.querySelector('a').classList.add('hidden');
    p = document.createElement('p');
    p.textContent = 'Ready.';
    return parent.appendChild(p);
  };

  document.querySelector('.upload-mod a').addEventListener('click', function(e) {
    e.preventDefault();
    return document.querySelector('.upload-mod input').click();
  }, false);

  document.querySelector('.upload-mod input').addEventListener('change', function(e) {
    return selectFile(e.target.files[0]);
  }, false);

  dragNop = function(e) {
    e.stopPropagation();
    return e.preventDefault();
  };

  window.addEventListener('dragenter', dragNop, false);

  window.addEventListener('dragleave', dragNop, false);

  window.addEventListener('dragover', dragNop, false);

  window.addEventListener('drop', function(e) {
    dragNop(e);
    return selectFile(e.dataTransfer.files[0]);
  }, false);

  document.getElementById('submit').removeAttribute('disabled');

}).call(this);
