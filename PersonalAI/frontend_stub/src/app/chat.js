async function send(){
  const q = document.getElementById('query').value;
  const res = await fetch('/api/chat/stream', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({query: q})});
  const j = await res.json();
  document.getElementById('reply').innerText = JSON.stringify(j, null, 2);
}

async function upload(){
  const files = document.getElementById('file').files;
  const fd = new FormData();
  for(let i=0;i<files.length;i++) fd.append('files', files[i]);
  const res = await fetch('/api/upload', {method:'POST', body: fd});
  const j = await res.json();
  document.getElementById('uploadResult').innerText = JSON.stringify(j, null, 2);
}
