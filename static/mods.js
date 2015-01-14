(function() {
  window.activateStats = function() {
    var worker;
    worker = new Worker("/static/statworker.js");
    worker.addEventListener('message', function(e) {
      var k, keyColor, keyText, keyUI, li, _i, _len, _ref, _results;
      switch (e.data.action) {
        case "downloads_ready":
          new Chart(document.getElementById('downloads-over-time').getContext("2d")).Line({
            labels: e.data.data.labels,
            datasets: e.data.data.entries
          }, {
            animation: false
          });
          keyUI = document.getElementById('downloads-over-time-key');
          _ref = e.data.data.key;
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            k = _ref[_i];
            li = document.createElement('li');
            keyColor = document.createElement('span');
            keyText = document.createElement('span');
            keyColor.className = 'key-color';
            keyText.className = 'key-text';
            keyColor.style.backgroundColor = k.color;
            keyText.textContent = k.name;
            li.appendChild(keyColor);
            li.appendChild(keyText);
            _results.push(keyUI.appendChild(li));
          }
          return _results;
          break;
        case "followers_ready":
          return new Chart(document.getElementById('followers-over-time').getContext("2d")).Line({
            labels: e.data.data.labels,
            datasets: e.data.data.entries
          }, {
            animation: false
          });
      }
    }, false);
    worker.postMessage({
      action: "set_versions",
      data: window.versions
    });
    worker.postMessage({
      action: "set_timespan",
      data: window.thirty_days_ago
    });
    worker.postMessage({
      action: "process_downloads",
      data: window.download_stats
    });
    return worker.postMessage({
      action: "process_followers",
      data: window.follower_stats
    });
  };

}).call(this);
(function() {
  var accept, b, edit, reject, _i, _j, _k, _len, _len1, _len2, _ref, _ref1, _ref2;

  window.activateStats();

  _ref = document.querySelectorAll('.edit-version');
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    edit = _ref[_i];
    edit.addEventListener('click', function(e) {
      var c, m, p, v;
      e.preventDefault();
      p = e.target.parentElement.parentElement;
      v = e.target.parentElement.dataset.version;
      c = p.querySelector('.raw-changelog').innerHTML;
      m = document.getElementById('version-edit-modal');
      m.querySelector('.version-id').value = v;
      m.querySelector('.changelog-text').innerHTML = c;
      return $(m).modal();
    }, false);
  }

  _ref1 = document.querySelectorAll('.delete-version');
  for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
    edit = _ref1[_j];
    edit.addEventListener('click', function(e) {
      var m;
      e.preventDefault();
      m = document.getElementById('confirm-delete-version');
      m.querySelector('form').action = "/mod/" + mod_id + "/version/" + e.target.dataset.version + "/delete";
      return $(m).modal();
    }, false);
  }

  _ref2 = document.querySelectorAll('.set-default-version');
  for (_k = 0, _len2 = _ref2.length; _k < _len2; _k++) {
    b = _ref2[_k];
    b.addEventListener('click', function(e) {
      var mod, target, version, xhr;
      e.preventDefault();
      target = e.target;
      while (target.tagName !== 'P') {
        target = target.parentElement;
      }
      version = target.dataset.version;
      mod = window.mod_id;
      xhr = new XMLHttpRequest();
      xhr.open('POST', "/api/mod/" + mod + "/set-default/" + version);
      xhr.onload = function() {
        return window.location = window.location;
      };
      return xhr.send();
    }, false);
  }

  document.getElementById('download-link-primary').addEventListener('click', function(e) {
    if (!readCookie('do-not-offer-registration') && !window.logged_in) {
      return setTimeout(function() {
        return $("#register-for-updates").modal();
      }, 2000);
    }
  }, false);

  document.getElementById('do-not-offer-registration').addEventListener('click', function(e) {
    return createCookie('do-not-offer-registration', 1, 365 * 10);
  }, false);

  accept = document.getElementById('accept-authorship-invite');

  if (accept) {
    accept.addEventListener('click', function(e) {
      var xhr;
      e.preventDefault();
      xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/mod/' + mod_id + '/accept_grant');
      xhr.onload = function() {
        return window.location = window.location;
      };
      return xhr.send();
    }, false);
  }

  reject = document.getElementById('reject-authorship-invite');

  if (reject) {
    reject.addEventListener('click', function(e) {
      var xhr;
      e.preventDefault();
      xhr = new XMLHttpRequest();
      xhr.open('POST', '/api/mod/' + mod_id + '/reject_grant');
      xhr.onload = function() {
        return window.location = window.location;
      };
      return xhr.send();
    }, false);
  }

}).call(this);
