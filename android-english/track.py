import cv2,numpy as np,json,sys
FR=sys.argv[1]
def g(n): return cv2.cvtColor(cv2.imread(FR+'/%04d.png'%n),cv2.COLOR_BGR2GRAY)
W={'ios':(170,(245,65,610,180),range(135,200)),
   'color':(285,(250,45,705,190),range(240,315)),
   'mi':(445,(200,500,740,700),range(425,460))}
out={}
for k,(ref,(x0,y0,x1,y1),rng) in W.items():
    T=g(ref)[y0:y1,x0:x1]; res={}
    prev=None
    for n in rng:
        im=g(n); best=(-1,)
        for s in np.arange(0.6,1.5,0.04):
            t=cv2.resize(T,None,fx=s,fy=s)
            if t.shape[0]>=im.shape[0] or t.shape[1]>=im.shape[1]: continue
            r=cv2.matchTemplate(im,t,cv2.TM_CCOEFF_NORMED); _,mv,_,ml=cv2.minMaxLoc(r)
            if mv>best[0]: best=(mv,ml[0],ml[1],float(s))
        res[n]=[float(best[0]),best[1],best[2],best[3]]
        print(k,n,'%.2f'%best[0],best[1:],flush=True)
    out[k]=res
json.dump(out,open(sys.argv[2],'w'))
