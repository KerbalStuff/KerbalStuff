(function() {
  var error, get, loading, valid;

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
    var a, form, name, progress, xhr, _i, _len, _ref;
    _ref = document.querySelectorAll('.has-error');
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      a = _ref[_i];
      a.classList.remove('has-error');
    }
    document.getElementById('error-alert').classList.add('hidden');
    valid = true;
    name = get('pack-name');
    if (name === '') {
      error('pack-name');
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
    xhr.open('POST', '/api/pack/create');
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
    form.append('name', name);
    document.getElementById('submit').setAttribute('disabled', 'disabled');
    progress.querySelector('.progress-bar').style.width = '0%';
    progress.classList.add('active');
    return xhr.send(form);
  }, false);

  document.getElementById('submit').removeAttribute('disabled');

}).call(this);
