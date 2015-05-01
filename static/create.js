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
    var a, ckan, form, kspVersion, license, name, progress, shortDescription, version, xhr, _i, _len, _ref;
    _ref = document.querySelectorAll('.has-error');
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      a = _ref[_i];
      a.classList.remove('has-error');
    }
    document.getElementById('error-alert').classList.add('hidden');
    valid = true;
    name = get('mod-name');
    shortDescription = get('mod-short-description');
    license = get('mod-license');
    if (license === 'Other') {
      license = get('mod-other-license');
    }
    version = get('mod-version');
    kspVersion = get('mod-ksp-version');
    ckan = document.getElementById("ckan").checked;
    if (name === '') {
      error('mod-name');
    }
    if (shortDescription === '') {
      error('mod-short-description');
    }
    if (license === '') {
      error('mod-license');
    }
    if (version === '') {
      error('mod-version');
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
    xhr.open('POST', '/api/mod/create');
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
        return window.location = JSON.parse(this.responseText).url + "?new=True";
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
    form.append('name', name);
    form.append('short-description', shortDescription);
    form.append('license', license);
    form.append('version', version);
    form.append('ksp-version', kspVersion);
    form.append('ckan', ckan);
    form.append('zipball', zipFile);
    document.getElementById('submit').setAttribute('disabled', 'disabled');
    progress.querySelector('.progress-bar').style.width = '0%';
    progress.classList.add('active');
    return xhr.send(form);
  }, false);

  document.getElementById('mod-license').addEventListener('change', function() {
    var license;
    license = get('mod-license');
    if (license === 'Other') {
      return document.getElementById('mod-other-license').classList.remove('hidden');
    } else {
      return document.getElementById('mod-other-license').classList.add('hidden');
    }
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

  $('[data-toggle="tooltip"]').tooltip();

}).call(this);
