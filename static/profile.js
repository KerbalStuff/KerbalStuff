(function() {
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
            document.getElementById('backgroundMedia').value = path.file;
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

}).call(this);
