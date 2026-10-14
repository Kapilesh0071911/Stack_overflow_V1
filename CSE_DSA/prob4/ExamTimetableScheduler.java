import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Exam timetable solver: DSatur greedy plus exact branch-and-bound colouring. */
public class ExamTimetableScheduler {
    static class Result { int[] color; int slots; long nanos; boolean optimal; Result(int[] c,int s,long n,boolean o){color=c;slots=s;nanos=n;optimal=o;} }
    static class Graph { int n,r; boolean[][] edge; int m; Graph(int n,int r){this.n=n;this.r=r;edge=new boolean[n][n];} void add(int a,int b){if(a==b||edge[a][b])return;edge[a][b]=edge[b][a]=true;m++;} }
    static Graph graph; static int best; static int[] bestColor; static long deadline; static boolean timedOut;

    static int chooseVertex(int[] color, int k) {
        int pick=-1, bestSat=-1, bestDeg=-1;
        for(int v=0;v<graph.n;v++) if(color[v]<0){
            boolean[] seen=new boolean[k]; int sat=0;
            for(int u=0;u<graph.n;u++) if(graph.edge[v][u]&&color[u]>=0&&!seen[color[u]]){seen[color[u]]=true;sat++;}
            int deg=0;for(int u=0;u<graph.n;u++)if(graph.edge[v][u])deg++;
            if(sat>bestSat||(sat==bestSat&&deg>bestDeg)){pick=v;bestSat=sat;bestDeg=deg;}
        } return pick;
    }
    static boolean canPlace(int v,int c,int[] colors,int[] sizes){if(sizes[c]>=graph.r)return false;for(int u=0;u<graph.n;u++)if(graph.edge[v][u]&&colors[u]==c)return false;return true;}
    static Result dsatur(){long t=System.nanoTime();int[] c=new int[graph.n],sizes=new int[graph.n];Arrays.fill(c,-1);int used=0;
        for(int i=0;i<graph.n;i++){int v=chooseVertex(c,Math.max(used,1)), chosen=-1;for(int x=0;x<used;x++)if(canPlace(v,x,c,sizes)){chosen=x;break;}if(chosen<0){chosen=used++;}c[v]=chosen;sizes[chosen]++;}
        return new Result(c,used,System.nanoTime()-t,false);
    }
    static void search(int[] c,int[] sizes,int done,int used){
        if(System.nanoTime()>deadline){timedOut=true;return;}
        if(done==graph.n){best=used;bestColor=c.clone();return;}
        if(used>=best)return;
        int v=chooseVertex(c,used);
        // Existing colours first; symmetry is broken by creating only the next new colour.
        for(int x=0;x<=used;x++){
            if(x==used && used+1>=best)continue;
            if(x<used&&!canPlace(v,x,c,sizes))continue;
            if(x==used&&sizes[x]>=graph.r)continue;
            c[v]=x;sizes[x]++;search(c,sizes,done+1,Math.max(used,x+1));sizes[x]--;c[v]=-1;
            if(timedOut)return;
        }
    }
    static Result exact(Result upper,int seconds){long t=System.nanoTime();
        if(graph.n==0)return new Result(new int[0],0,0,true);
        best=upper.slots+1;bestColor=upper.color.clone();deadline=t+seconds*1_000_000_000L;timedOut=false;
        // Search increasing limits; first feasible limit is optimal. Keep DSatur as incumbent.
        for(int limit=1;limit<=upper.slots;limit++){
            best=limit+1;bestColor=null;int[] c=new int[graph.n];Arrays.fill(c,-1);searchLimit(c,new int[graph.n],0,0,limit);
            if(bestColor!=null && best<=limit) return new Result(bestColor,best,System.nanoTime()-t,true);
            if(timedOut)break;
        }
        return new Result(upper.color,upper.slots,System.nanoTime()-t,false);
    }
    static void searchLimit(int[] c,int[] sizes,int done,int used,int limit){
        if(System.nanoTime()>deadline){timedOut=true;return;}
        if(done==graph.n){best=used;bestColor=c.clone();return;}
        // Remaining vertices may still fit in an already-open final slot.
        if(used>limit)return;
        int v=chooseVertex(c,used);
        for(int x=0;x<=used&&x<limit;x++){
            if(x==used&&used+1>limit)continue;
            if(x<used&&!canPlace(v,x,c,sizes))continue;
            if(x==used&&sizes[x]>=graph.r)continue;
            c[v]=x;sizes[x]++;searchLimit(c,sizes,done+1,Math.max(used,x+1),limit);sizes[x]--;c[v]=-1;
            if(best<=limit||timedOut)return;
        }
    }
    static Graph parse(String[] args)throws Exception{
        if(args.length>0&&args[0].equalsIgnoreCase("random")){
            int n=Integer.parseInt(args[1]),r=Integer.parseInt(args[2]);double density=Double.parseDouble(args[3]);long seed=args.length>4?Long.parseLong(args[4]):System.nanoTime();Graph g=new Graph(n,r);Random rand=new Random(seed);for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(rand.nextDouble()<density)g.add(i,j);System.out.println("Generated graph with seed "+seed+", density "+density);return g;
        }
        Scanner sc=(args.length>0)?new Scanner(new File(args[0])):new Scanner(System.in);
        if(!sc.hasNextInt())throw new IllegalArgumentException("Expected N M R then M edge pairs");int n=sc.nextInt(),m=sc.nextInt(),r=sc.nextInt();Graph g=new Graph(n,r);for(int i=0;i<m;i++){int u=sc.nextInt()-1,v=sc.nextInt()-1;if(u<0||u>=n||v<0||v>=n)throw new IllegalArgumentException("Course IDs must be 1..N");g.add(u,v);}return g;
    }
    static void writeCsv(String name,Result r)throws Exception{int[] sz=new int[r.slots];for(int c:r.color)sz[c]++;int max=Arrays.stream(sz).max().orElse(0);try(PrintWriter w=new PrintWriter(name)){w.print("Slot");for(int h=1;h<=max;h++)w.print(",Hall "+h);w.println();for(int s=0;s<r.slots;s++){w.print("Slot "+(s+1));int count=0;for(int v=0;v<graph.n;v++)if(r.color[v]==s){w.print(",Course "+(v+1));count++;}for(;count<max;count++)w.print(",");w.println();}}}
    static String data(Result a,Result b){StringBuilder s=new StringBuilder("{\"n\":"+graph.n+",\"r\":"+graph.r+",\"exactOptimal\":"+b.optimal+",\"edges\":[");boolean first=true;for(int i=0;i<graph.n;i++)for(int j=i+1;j<graph.n;j++)if(graph.edge[i][j]){if(!first)s.append(',');first=false;s.append('[').append(i).append(',').append(j).append(']');}s.append("],\"colors\":[");for(int i=0;i<graph.n;i++){if(i>0)s.append(',');s.append(a.color[i]);}s.append("],\"slots\":"+a.slots+",\"exactColors\":[");for(int i=0;i<graph.n;i++){if(i>0)s.append(',');s.append(b.color[i]);}s.append("],\"exactSlots\":"+b.slots+"}");return s.toString();}
    static void writeHtml(String filename,Result greedy,Result exact)throws Exception{String d=data(greedy,exact);String html="""
<!doctype html><html><head><meta charset="utf-8"><title>Exam timetable visualization</title><style>
body{font:16px system-ui;margin:24px;background:#f5f7fb;color:#172033}h1{margin:0 0 8px}.row{display:flex;gap:18px;flex-wrap:wrap}.card{background:white;padding:16px;border-radius:12px;box-shadow:0 2px 12px #14213d18;margin:12px 0}canvas{max-width:100%;border:1px solid #dce2ec;border-radius:8px}.grid{display:grid;gap:6px}.cell{padding:8px 12px;border-radius:6px;color:#132033;text-align:center}.muted{color:#617086}button,select{padding:8px}
</style></head><body><h1>Exam Timetable Scheduling</h1><div id="summary" class="card"></div><div class="card"><label>Graph view: <select id="which"><option value="colors">DSatur greedy</option><option value="exactColors">Exact result</option></select></label><h2 id="viewTitle"></h2><canvas id="graph" width="850" height="480"></canvas></div><div class="card"><h2>Timetable</h2><div id="timetable"></div></div><div class="card"><h2>Algorithm comparison</h2><canvas id="chart" width="850" height="320"></canvas><p class="muted">Times are measured for this input. Run multiple input sizes to build a broader benchmark.</p></div>
<script>const D=DATA, colors=['#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc949','#af7aa1','#ff9da7','#9c755f','#bab0ab'];
function draw(){let mode=document.querySelector('#which').value, cs=D[mode], K=mode==='colors'?D.slots:D.exactSlots;let cv=document.querySelector('#graph'),ctx=cv.getContext('2d'),n=D.n;document.querySelector('#viewTitle').textContent=mode==='colors'?'DSatur greedy assignment ('+K+' slots)':'Exact search assignment ('+K+' slots)'+(D.exactOptimal?' — proven optimal':' — best known');ctx.clearRect(0,0,cv.width,cv.height);let pos=[];for(let i=0;i<n;i++){let a=2*Math.PI*i/Math.max(n,1)-Math.PI/2;pos.push([425+Math.min(190,28*n)*Math.cos(a),240+Math.min(190,28*n)*Math.sin(a)])}ctx.strokeStyle='#aab3c2';ctx.lineWidth=1;for(let [u,v] of D.edges){ctx.beginPath();ctx.moveTo(...pos[u]);ctx.lineTo(...pos[v]);ctx.stroke()}for(let i=0;i<n;i++){ctx.beginPath();ctx.arc(...pos[i],17,0,Math.PI*2);ctx.fillStyle=colors[cs[i]%colors.length];ctx.fill();ctx.strokeStyle='white';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='white';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='bold 12px sans-serif';ctx.fillText(i+1,...pos[i])}
let t=document.querySelector('#timetable');t.innerHTML='';let groups=Array.from({length:K},()=>[]);cs.forEach((c,i)=>groups[c].push(i+1));let g=document.createElement('div');g.className='grid';g.style.gridTemplateColumns='repeat('+Math.max(K,1)+', minmax(120px,1fr))';groups.forEach((xs,i)=>{let col=document.createElement('div');col.className='cell';col.style.background=colors[i%colors.length];col.innerHTML='<b>Slot '+(i+1)+'</b><br>'+xs.map(x=>'Course '+x).join('<br>');g.appendChild(col)});t.appendChild(g)}
document.querySelector('#which').onchange=draw;document.querySelector('#summary').innerHTML='<b>Courses:</b> '+D.n+' &nbsp; <b>Conflicts:</b> '+D.edges.length+' &nbsp; <b>Hall limit:</b> '+D.r+'<br><b>DSatur:</b> '+D.slots+' slots &nbsp; <b>Exact:</b> '+D.exactSlots+' slots';draw();let c=document.querySelector('#chart').getContext('2d');c.font='16px sans-serif';c.fillText('Slots used',100,40);c.fillText('Elapsed time (ms)',490,40);let vals=[D.slots,D.exactSlots],labs=['DSatur','Exact'];vals.forEach((v,i)=>{c.fillStyle=colors[i];c.fillRect(130,75+i*65,Math.max(8,v*48),32);c.fillStyle='#172033';c.fillText(labs[i]+': '+v,140+v*48,98+i*65)});c.fillStyle=colors[0];c.fillRect(500,75,Math.max(8,GREEDY_MS/2),32);c.fillStyle='#172033';c.fillText(GREEDY_MS+' ms DSatur',510+GREEDY_MS/2,98);c.fillStyle=colors[1];c.fillRect(500,140,Math.max(8,EXACT_MS/2),32);c.fillStyle='#172033';c.fillText(EXACT_MS+' ms exact',510+EXACT_MS/2,163);</script></body></html>
""".replace("DATA",d).replace("GREEDY_MS",Long.toString(greedy.nanos/1_000_000)).replace("EXACT_MS",Long.toString(exact.nanos/1_000_000));Files.writeString(Path.of(filename),html);}
    public static void main(String[] args)throws Exception{graph=parse(args);if(graph.r<1&&graph.n>0)throw new IllegalArgumentException("R must be at least 1");Result g=dsatur(),e=exact(g,args.length>5?Integer.parseInt(args[5]):20);System.out.println("DSatur: "+g.slots+" slots (heuristic; not proven optimal), "+(g.nanos/1e6)+" ms");System.out.println("Exact: "+e.slots+" slots ("+(e.optimal?"proven optimal":"best found before timeout")+"), "+(e.nanos/1e6)+" ms");for(int s=0;s<e.slots;s++){System.out.print("Slot "+(s+1)+":");for(int v=0;v<graph.n;v++)if(e.color[v]==s)System.out.print(" "+(v+1));System.out.println();}writeCsv("timetable.csv",e);writeHtml("visualization.html",g,e);System.out.println("Wrote timetable.csv and visualization.html");}
}
