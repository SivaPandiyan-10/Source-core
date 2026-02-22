const express = require('express');
const path = require('path');
const proxy = require('http-proxy-middleware');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname)));

// Proxy API to backend running on localhost:8000 (adjust as needed)
app.use('/api', (req, res) => {
  const target = process.env.BACKEND_URL || 'http://localhost:8000';
  const fetch = require('node-fetch');
  const url = target + req.originalUrl;
  const opts = {method: req.method, headers: req.headers};
  if(req.method !== 'GET' && req.method !== 'HEAD') opts.body = req;
  req.pipe(require('request')({url: url, method: req.method, headers: req.headers})).pipe(res);
});

app.listen(port, () => console.log(`Frontend stub listening on http://localhost:${port}`));
