(function() {
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
    xhr.open('POST', "/api/user/" + window.username + "/update-bg");
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
        document.getElementById('backgroundMedia').value = resp.path;
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

}).call(this);
