const cp=require('child_process'), path=require('path');
const {performance}=require('perf_hooks');
const root=path.resolve(__dirname,'../../..');
const {PNG}=require(path.join(root,'mobile/node_modules/pngjs'));
const adb=path.join(process.env.LOCALAPPDATA,'Android/Sdk/platform-tools/adb.exe');
const refs=new Map();let next=0;
require('readline').createInterface({input:process.stdin}).on('line',line=>{
  const command=JSON.parse(line),start=performance.now();
  const data=cp.execFileSync(adb,['-s','emulator-5554','exec-out','screencap','-p'],{maxBuffer:8*1024*1024});
  const image=PNG.sync.read(data);
  if(command.action==='reference') {
    const [x1,y1,x2,y2]=command.bounds,points=[];
    for(let y=y1;y<y2;y+=3)for(let x=x1;x<x2;x+=3){
      const index=(y*image.width+x)*4, color=[...image.data.subarray(index,index+3)];
      if(color.reduce((a,b)=>a+b,0)<500)points.push([x,y,color]);
    }
    if(points.length<20)throw Error('Public marker unavailable');
    const key=++next;refs.set(key,points);
    process.stdout.write(JSON.stringify({key})+'\n');
  } else {
    const points=refs.get(command.key);let total=0;
    for(const [x,y,color]of points){const index=(y*image.width+x)*4;for(let i=0;i<3;i++)total+=Math.abs(image.data[index+i]-color[i]);}
    process.stdout.write(JSON.stringify({difference:total/(points.length*3),capture_ms:performance.now()-start})+'\n');
  }
});
