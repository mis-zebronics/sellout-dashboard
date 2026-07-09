import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Sellout Pro", page_icon="📊", layout="wide")
st.title("📊 Sellout Tracker Dashboard Pro")

c1, c2 = st.columns(2)
with c1: f1 = st.file_uploader("FY 2026-27", type=["xlsx","csv"])
with c2: f2 = st.file_uploader("FY 2025-26", type=["xlsx","csv"])

if f1 is None:
    st.info("Upload file")
    st.stop()

@st.cache_data
def load(f):
    if f.name.endswith(".csv"):
        return pd.read_csv(f)
    xls = pd.ExcelFile(f)
    t = None
    for s in xls.sheet_names:
        c = s.strip().lower().replace(" ","").replace("&","").replace("_","").replace("-","")
        if c in ["eq","enq","equ"]:
            t = s
            break
    if not t:
        t = xls.sheet_names[0]
    raw = pd.read_excel(f, sheet_name=t, header=None, nrows=10)
    h = 0
    for i, row in raw.iterrows():
        r = " ".join([str(x) if x else "" for x in row.tolist()]).lower()
        if "item" in r and ("vertical" in r or "brand" in r):
            h = i
            break
    d = pd.read_excel(f, sheet_name=t, header=h)
    d.columns = d.columns.astype(str).str.strip()
    d = d.loc[:, ~d.columns.str.contains("^Unnamed", na=False)]
    return d

df = load(f1)
df2 = load(f2) if f2 else None

def fc(df, *pats):
    for col in df.columns:
        cs = str(col).lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
        for p in pats:
            ps = p.lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
            if ps in cs:
                return col
    return None

def gc(df, pat, must=None, no=None):
    for col in df.columns:
        cs = str(col).lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
        p = pat.lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
        if p in cs:
            if must and not all(m in cs for m in must):
                continue
            if no and any(n in cs for n in no):
                continue
            return col
    return None

C = {}
C["id"] = fc(df, "itemid", "item", "sku")
C["vert"] = fc(df, "vertical")
C["plat"] = fc(df, "platform")
C["brand"] = fc(df, "brand")
C["sell"] = fc(df, "seller")
C["cat"] = fc(df, "category")
C["sub"] = fc(df, "subcategory", "sub category")
C["mod"] = fc(df, "modelname", "model")
C["kam"] = fc(df, "kam")
C["u25"] = gc(df, "25-26", must=["unit"], no=["plan","gms"]) or gc(df, "2526", must=["unit"], no=["plan","gms"])
C["u26"] = gc(df, "26-27", must=["unit"], no=["plan","gms"]) or gc(df, "2627", must=["unit"], no=["plan","gms"])
C["g25"] = gc(df, "25-26", must=["gms"], no=["plan"]) or gc(df, "2526", must=["gms"], no=["plan"])
C["g26"] = gc(df, "26-27", must=["gms"], no=["plan"]) or gc(df, "2627", must=["gms"], no=["plan"])

def tn(df, c):
    if not c or c not in df.columns:
        return None
    return pd.to_numeric(df[c].astype(str).str.replace("%","",regex=False).str.replace(",","",regex=False).str.replace("Rs","",regex=False).str.replace(" ","",regex=False), errors="coerce").fillna(0)

for k in C:
    if C[k]:
        df[C[k]+"_n"] = tn(df, C[k])

mk = ["apr","may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar"]
MC = {}
for m in mk:
    ly = pl = cy = lyg = cyg = plg = None
    for c in df.columns:
        cl = c.lower().replace("'","").replace(" ","").replace(".","").replace("(","").replace(")","").replace("-","").replace("_","")
        if cl.startswith(m) and "25" in cl and ("unit" in cl or "sellout" in cl) and "plan" not in cl and "gms" not in cl:
            ly = c
        elif cl.startswith(m) and "26" in cl and "plan" in cl and "gms" not in cl:
            pl = c
        elif cl.startswith(m) and "26" in cl and ("unit" in cl or "sellout" in cl) and "plan" not in cl and "gms" not in cl:
            cy = c
        elif cl.startswith(m) and "25" in cl and "gms" in cl and "plan" not in cl:
            lyg = c
        elif cl.startswith(m) and "26" in cl and "plan" in cl and "gms" in cl:
            plg = c
        elif cl.startswith(m) and "26" in cl and "gms" in cl and "plan" not in cl:
            cyg = c
    MC[m] = {"ly":ly,"pl":pl,"cy":cy,"lyg":lyg,"plg":plg,"cyg":cyg}
    for k2, c2 in MC[m].items():
        if c2:
            df[c2+"_n"] = tn(df, c2)

def fmt(n):
    if pd.isna(n) or n == 0: return "0"
    if abs(n) >= 1e7: return "Rs"+str(round(n/1e7,2))+"Cr"
    if abs(n) >= 1e5: return "Rs"+str(round(n/1e5,2))+"L"
    if abs(n) >= 1e3: return str(round(n/1e3,1))+"K"
    return str(round(n,0))

def kc(l, v, c="#38bdf8", s=""):
    return "<div style='background:linear-gradient(135deg,#1e293b,#334155);padding:14px;border-radius:8px;border-left:4px solid "+c+";margin-bottom:6px'><div style='color:#94a3b8;font-size:10px'>"+l+"</div><div style='color:#f1f5f9;font-size:20px;font-weight:bold;margin-top:4px'>"+v+"</div><div style='color:"+c+";font-size:10px;margin-top:2px'>"+s+"</div></div>"

def sf(fig):
    fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#e2e8f0", size=10), xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"), margin=dict(t=20, b=50, l=50, r=20))
    return fig

st.sidebar.header("Filters")
df_f = df.copy()
for f in ["vert","plat","brand","cat","sub","kam","sell","mod"]:
    if C.get(f):
        opts = ["All"] + sorted([str(x) for x in df_f[C[f]].dropna().unique()])[:200]
        sel = st.sidebar.selectbox(f.title(), opts, key=f)
        if sel != "All":
            df_f = df_f[df_f[C[f]].astype(str) == sel]

st.sidebar.success(str(len(df_f)) + " / " + str(len(df)) + " rows")
with st.sidebar.expander("Column Mapping"):
    for k, v in C.items():
        st.write("**"+k+"**: " + (v if v else "NOT FOUND"))

u25 = u26 = g25 = g26 = 0
if C.get("u25") and C["u25"]+"_n" in df_f.columns: u25 = df_f[C["u25"]+"_n"].sum()
if C.get("u26") and C["u26"]+"_n" in df_f.columns: u26 = df_f[C["u26"]+"_n"].sum()
if C.get("g25") and C["g25"]+"_n" in df_f.columns: g25 = df_f[C["g25"]+"_n"].sum()
if C.get("g26") and C["g26"]+"_n" in df_f.columns: g26 = df_f[C["g26"]+"_n"].sum()
uG = ((u26-u25)/u25*100) if u25 else 0
gG = ((g26-g25)/g25*100) if g25 else 0

st.markdown("### Overall Performance")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.markdown(kc("FY 25-26 U", fmt(u25)), unsafe_allow_html=True)
c2.markdown(kc("FY 26-27 U", fmt(u26), "#10b981"), unsafe_allow_html=True)
c3.markdown(kc("Unit Growth", str(round(uG,2))+"%", "#10b981" if uG>=0 else "#ef4444"), unsafe_allow_html=True)
c4.markdown(kc("FY 25-26 G", fmt(g25)), unsafe_allow_html=True)
c5.markdown(kc("FY 26-27 G", fmt(g26), "#10b981"), unsafe_allow_html=True)
c6.markdown(kc("GMS Growth", str(round(gG,2))+"%", "#10b981" if gG>=0 else "#ef4444"), unsafe_allow_html=True)

st.markdown("---")
st.markdown("### Monthly Trend: LY vs Plan vs CY")
ly_u=[];pl_u=[];cy_u=[];ly_g=[];pl_g=[];cy_g=[]
for m in mk:
    cols = MC.get(m,{})
    ly=cols.get("ly");p=cols.get("pl");cy=cols.get("cy")
    ly2=cols.get("lyg");p2=cols.get("plg");cy2=cols.get("cyg")
    ly_u.append(df_f[ly+"_n"].sum() if ly and (ly+"_n") in df_f.columns else 0)
    pl_u.append(df_f[p+"_n"].sum() if p and (p+"_n") in df_f.columns else 0)
    cy_u.append(df_f[cy+"_n"].sum() if cy and (cy+"_n") in df_f.columns else 0)
    ly_g.append(df_f[ly2+"_n"].sum() if ly2 and (ly2+"_n") in df_f.columns else 0)
    pl_g.append(df_f[p2+"_n"].sum() if p2 and (p2+"_n") in df_f.columns else 0)
    cy_g.append(df_f[cy2+"_n"].sum() if cy2 and (cy2+"_n") in df_f.columns else 0)

fig = make_subplots(rows=1, cols=2, subplot_titles=("Units", "GMS"))
fig.add_trace(go.Scatter(x=mk,y=ly_u,name="LY",mode="lines+markers",line=dict(color="#94a3b8",dash="dot")),1,1)
fig.add_trace(go.Scatter(x=mk,y=pl_u,name="Plan",mode="lines+markers",line=dict(color="#f59e0b",dash="dash")),1,1)
fig.add_trace(go.Scatter(x=mk,y=cy_u,name="CY",mode="lines+markers",line=dict(color="#38bdf8",width=3),fill="tozeroy",fillcolor="rgba(56,189,248,0.1)"),1,1)
fig.add_trace(go.Scatter(x=mk,y=ly_g,mode="lines+markers",line=dict(color="#94a3b8",dash="dot"),showlegend=False),1,2)
fig.add_trace(go.Scatter(x=mk,y=pl_g,mode="lines+markers",line=dict(color="#f59e0b",dash="dash"),showlegend=False),1,2)
fig.add_trace(go.Scatter(x=mk,y=cy_g,mode="lines+markers",line=dict(color="#10b981",width=3),fill="tozeroy",fillcolor="rgba(16,185,129,0.1)"),1,2)
fig.update_layout(paper_bgcolor="#1e293b",plot_bgcolor="#1e293b",font_color="#e2e8f0",height=350,hovermode="x unified")
fig.update_xaxes(gridcolor="#334155");fig.update_yaxes(gridcolor="#334155")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### MoM Growth %")
mom_u = [((cy_u[i]-ly_u[i])/ly_u[i]*100) if ly_u[i] else 0 for i in range(12)]
mom_g = [((cy_g[i]-ly_g[i])/ly_g[i]*100) if ly_g[i] else 0 for i in range(12)]
fig = make_subplots(rows=1, cols=2, subplot_titles=("Units Growth %", "GMS Growth %"))
cu_colors = ["#10b981" if v>=0 else "#ef4444" for v in mom_u]
cg_colors = ["#10b981" if v>=0 else "#ef4444" for v in mom_g]
fig.add_trace(go.Bar(x=mk, y=mom_u, marker_color=cu_colors, text=[str(round(v,1))+"%" for v in mom_u], textposition="outside"), 1, 1)
fig.add_trace(go.Bar(x=mk, y=mom_g, marker_color=cg_colors, text=[str(round(v,1))+"%" for v in mom_g], textposition="outside"), 1, 2)
fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, showlegend=False)
fig.update_xaxes(gridcolor="#334155"); fig.update_yaxes(gridcolor="#334155")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Achievement % vs Plan")
ach_u = [(cy_u[i]/pl_u[i]*100) if pl_u[i] else 0 for i in range(12)]
ach_g = [(cy_g[i]/pl_g[i]*100) if pl_g[i] else 0 for i in range(12)]
fig = make_subplots(rows=1, cols=2, subplot_titles=("Units Ach %", "GMS Ach %"))
ca_u = ["#10b981" if v>=100 else "#f59e0b" if v>=80 else "#ef4444" for v in ach_u]
ca_g = ["#10b981" if v>=100 else "#f59e0b" if v>=80 else "#ef4444" for v in ach_g]
fig.add_trace(go.Bar(x=mk, y=ach_u, marker_color=ca_u, text=[str(round(v,0))+"%" for v in ach_u], textposition="outside"), 1, 1)
fig.add_trace(go.Bar(x=mk, y=ach_g, marker_color=ca_g, text=[str(round(v,0))+"%" for v in ach_g], textposition="outside"), 1, 2)
fig.add_hline(y=100, line_dash="dash", line_color="white")
fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, showlegend=False)
fig.update_xaxes(gridcolor="#334155"); fig.update_yaxes(gridcolor="#334155")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### Top 20 Models")
cg = None
if C.get("g26"):
    if C["g26"]+"_n" in df_f.columns: cg = C["g26"]+"_n"
    elif C["g26"] in df_f.columns: cg = C["g26"]
if C.get("mod") and cg:
    mp = df_f.groupby(C["mod"]).agg({cg:"sum"}).reset_index().nlargest(20, cg)
    fig = px.bar(mp, x=cg, y=C["mod"], orientation="h", color=cg, color_continuous_scale="Blues")
    sf(fig); fig.update_layout(height=500, yaxis={"categoryorder":"total ascending"})
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Brand: LY vs CY")
if C.get("brand") and cg:
    cg25 = None
    if C.get("g25"):
        if C["g25"]+"_n" in df_f.columns: cg25 = C["g25"]+"_n"
        elif C["g25"] in df_f.columns: cg25 = C["g25"]
    if cg25:
        bd = df_f.groupby(C["brand"]).agg({cg25:"sum",cg:"sum"}).reset_index().nlargest(15, cg)
        bd.columns = ["Brand","FY 25-26","FY 26-27"]
        fig = px.bar(bd.melt(id_vars="Brand"), x="Brand", y="value", color="variable", barmode="group")
        sf(fig); fig.update_xaxes(tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("### Category Distribution")
if C.get("cat") and cg:
    cd = df_f.groupby(C["cat"])[cg].sum().reset_index().nlargest(15, cg)
    fig = px.pie(cd, names=C["cat"], values=cg, hole=0.4)
    sf(fig)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Category x Sub-Category")
if C.get("cat") and C.get("sub") and cg:
    hd = df_f.groupby([C["cat"], C["sub"]])[cg].sum().reset_index()
    fig = px.density_heatmap(hd, x=C["cat"], y=C["sub"], z=cg, color_continuous_scale="Blues")
    sf(fig); fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Vertical x Platform")
if C.get("vert") and cg:
    c1,c2 = st.columns(2)
    with c1:
        vd = df_f.groupby(C["vert"])[cg].sum().reset_index()
        fig = px.pie(vd, names=C["vert"], values=cg, hole=0.4)
        sf(fig)
        st.plotly_chart(fig, use_container_width=True)
    if C.get("plat"):
        with c2:
            pd2 = df_f.groupby(C["plat"])[cg].sum().reset_index()
            fig = px.pie(pd2, names=C["plat"], values=cg, hole=0.4)
            sf(fig)
            st.plotly_chart(fig, use_container_width=True)

st.markdown("### KAM Performance")
if C.get("kam") and cg:
    kd = df_f.groupby(C["kam"])[cg].sum().reset_index().sort_values(cg, ascending=False)
    fig = px.bar(kd, x=C["kam"], y=cg, color=cg, color_continuous_scale="Purples")
    sf(fig)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Top 15 Sellers")
if C.get("sell") and cg:
    sd = df_f.groupby(C["sell"])[cg].sum().reset_index().nlargest(15, cg)
    fig = px.bar(sd, x=C["sell"], y=cg, color=cg, color_continuous_scale="Greens")
    sf(fig); fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### Top 10 vs Bottom 10 SKUs")
if cg:
    ic = C.get("id") or C.get("mod")
    dc = []
    if ic: dc.append(ic)
    if C.get("brand"): dc.append(C["brand"])
    if C.get("mod") and C["mod"] != ic: dc.append(C["mod"])
    dc.append(cg)
    c1,c2 = st.columns(2)
    c1.subheader("Top 10")
    c1.dataframe(df_f.nlargest(10, cg)[dc], use_container_width=True)
    c2.subheader("Bottom 10")
    c2.dataframe(df_f.nsmallest(10, cg)[dc], use_container_width=True)

st.markdown("---")
st.markdown("### Quarter Summary")
qd = {
    "Quarter": ["Q1 (Apr-Jun)", "Q2 (Jul-Sep)", "Q3 (Oct-Dec)", "Q4 (Jan-Mar)"],
    "LY Units": [sum(ly_u[0:3]), sum(ly_u[3:6]), sum(ly_u[6:9]), sum(ly_u[9:12])],
    "CY Plan": [sum(pl_u[0:3]), sum(pl_u[3:6]), sum(pl_u[6:9]), sum(pl_u[9:12])],
    "CY Actual": [sum(cy_u[0:3]), sum(cy_u[3:6]), sum(cy_u[6:9]), sum(cy_u[9:12])],
    "LY GMS": [sum(ly_g[0:3]), sum(ly_g[3:6]), sum(ly_g[6:9]), sum(ly_g[9:12])],
    "CY GMS Plan": [sum(pl_g[0:3]), sum(pl_g[3:6]), sum(pl_g[6:9]), sum(pl_g[9:12])],
    "CY GMS Actual": [sum(cy_g[0:3]), sum(cy_g[3:6]), sum(cy_g[6:9]), sum(cy_g[9:12])]
}
qdf = pd.DataFrame(qd)
qdf["Units Ach %"] = (qdf["CY Actual"]/qdf["CY Plan"].replace(0,1)*100).fillna(0).round(1)
qdf["GMS Ach %"] = (qdf["CY GMS Actual"]/qdf["CY GMS Plan"].replace(0,1)*100).fillna(0).round(1)
qdf["Units Growth %"] = ((qdf["CY Actual"]-qdf["LY Units"])/qdf["LY Units"].replace(0,1)*100).fillna(0).round(1)
for cx in ["LY Units", "CY Plan", "CY Actual"]:
    qdf[cx] = qdf[cx].apply(lambda x: f"{x:,.0f}")
for cx in ["LY GMS", "CY GMS Plan", "CY GMS Actual"]:
    qdf[cx] = qdf[cx].apply(lambda x: "Rs"+str(round(x/1e7,2))+"Cr" if abs(x) >= 1e7 else "Rs"+str(round(x/1e5,2))+"L")
st.dataframe(qdf, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Detailed Data")
disp = []
for k in ["id","vert","plat","brand","sell","cat","sub","mod","kam","u25","u26","g25","g26"]:
    if C.get(k) and C[k] in df_f.columns:
        disp.append(C[k])
if disp:
    st.dataframe(df_f[disp].head(2000), use_container_width=True, height=500)
