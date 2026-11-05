const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'dist');
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
http.createServer((req,res)=>{
 if(req.url==='/api/techniques/health'||req.url==='/api/techniques/analyze'){
  const upstream=http.request({hostname:'127.0.0.1',port:8224,path:req.url.endsWith('health')?'/health':'/analyze',method:req.method,headers:req.headers['content-type']?{'content-type':req.headers['content-type']} : {}},r=>{res.writeHead(r.statusCode,{'Content-Type':r.headers['content-type']||'application/json'});r.pipe(res)});
  let size=0;req.on('data',c=>{size+=c.length;if(size>100*1024*1024){upstream.destroy();req.destroy()}});
  upstream.on('error',()=>{if(!res.headersSent)res.writeHead(503,{'Content-Type':'application/json'});res.end(JSON.stringify({detail:'Technique research server is not running. No technique was inferred.'}));});
  res.on('close',()=>upstream.destroy());req.pipe(upstream);return;
 }
 if(req.url==='/api/muscriptor/transcribe'&&req.method==='POST'){
  if(!/^multipart\/form-data; boundary=/.test(req.headers['content-type']||'')){res.writeHead(400);return res.end('Audio upload required.');}
  if(Number(req.headers['content-length'])>110*1024*1024){res.writeHead(413);return res.end('Upload too large.');}
  const upstream=http.request({hostname:'127.0.0.1',port:8222,path:'/transcribe',method:'POST',headers:{'content-type':req.headers['content-type']}},r=>{res.writeHead(r.statusCode,{'Content-Type':r.headers['content-type']||'text/plain','Cache-Control':'no-store'});r.pipe(res)});
  let size=0;req.on('data',chunk=>{size+=chunk.length;if(size>110*1024*1024){upstream.destroy();req.destroy()}});
  upstream.on('error',()=>{if(!res.headersSent)res.writeHead(503);res.end('Muscriptor is unavailable. Start the local model server on port 8222. No alternative model will be used.');});
  res.on('close',()=>upstream.destroy());req.pipe(upstream);return;
 }
 const filename=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname.replace(/\/$/,'/index.html'));
 if(!filename.startsWith(root+path.sep)||/transcription-worker|\/model\/|\/wasm\//.test(filename)){res.writeHead(404);return res.end('Not found');}
 fs.readFile(filename,(err,bytes)=>{res.writeHead(err?404:200,{'Content-Type':types[path.extname(filename)]||'application/octet-stream','Cache-Control':'no-store'});res.end(err?'Not found':bytes)});
}).listen(4181,'127.0.0.1',()=>console.log('http://127.0.0.1:4181/'));
