import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="Zebronics SellOut - SellIn Tracker Dashboard", page_icon="📊", layout="wide")
st.title("📊 Sellout Tracker Dashboard")

# ============= AUTO-LOAD DATA (NO UPLOAD NEEDED) =============
@st.cache_data
def load_data():
    """Load Excel file automatically from server"""
    file_path = "FY 2026 - 2027 Sellout Tracker.xlsx"
    if not os.path.exists(file_path):
        st.error("❌ Excel file not found in repository!")
        st.info("Please make sure 'FY 2026 - 2027 Sellout Tracker.xlsx' is uploaded to the GitHub repo")
        st.stop()
    
    xls = pd.ExcelFile(file_path)
    t = None
    for s in xls.sheet_names:
        c = s.strip().lower().replace(" ","").replace("&","").replace("_","").replace("-","")
        if c in ["eq","enq","equ","enquire","enquiry"]:
            t = s
            break
    if not t: t = xls.sheet_names[0]
    
    raw = pd.read_excel(file_path, sheet_name=t, header=None, nrows=10)
    h = 0
    for i, row in raw.iterrows():
        r = " ".join([str(x) if x is not None else "" for x in row.tolist()]).lower()
        if "item" in r and ("verticalical" in r or "brand" in r):
            h = i
            break
    
    d = pd.read_excel(file_path, sheet_name=t, header=h)
    d.columns = d.columns.astype(str).str.strip()
    d = d.loc[:, ~d.columns.str.contains("^Unnamed", na=False)]
    return d

with st.spinner("📊 Loading data..."):
    df = load_data()

st.success(f"✅ Loaded {len(df):,} rows from FY 2026-2027 Sellout Tracker")

# ============= COLUMN FINDER =============
def find_col_priority(df, search_text, exclude_words=None):
    exclude_words = exclude_words or []
    for col in df.columns:
        col_str = str(col).lower()
        if search_text.lower() in col_str and "fy" in col_str:
            if not any(w in col_str for w in exclude_words):
                return col
    for col in df.columns:
        col_str = str(col).lower()
        if search_text.lower() in col_str:
            if not any(w in col_str for w in exclude_words):
                return col
    return None

C = {}
C["id"] = find_col_priority(df, "item id") or find_col_priority(df, "sku")
C["vertical"] = find_col_priority(df, "verticalical")
C["platform"] = find_col_priority(df, "platformform")
C["brand"] = find_col_priority(df, "brand")
C["sell"] = find_col_priority(df, "seller")
C["categoryegory"] = find_col_priority(df, "categoryegoryegory")
C["sub category"] = find_col_priority(df, "sub category categoryegoryegory") or find_col_priority(df, "sub categorycategoryegoryegory")
C["model name"] = find_col_priority(df, "model nameel")
C["kam"] = find_col_priority(df, "kam")
C["u25"] = find_col_priority(df, "25-26", ["gms","plan","ach","growth","mar","feb","jan","dec","nov","oct","sep","aug","jul","jun","may","apr"])
C["u26"] = find_col_priority(df, "26-27", ["gms","plan","ach","growth","mar","feb","jan","dec","nov","oct","sep","aug","jul","jun","may","apr"])
C["g25"] = find_col_priority(df, "25-26 gms", ["plan","ach","growth","ytd"])
C["g26"] = find_col_priority(df, "26-27 gms", ["plan","ach","growth","ytd"])

with st.sidebar.expander("🔍 Column Mapping", expanded=False):
    for k, v in C.items():
        st.write(f"**{k}**: {v if v else 'NOT FOUND'}")

# ============= CONvertical NUMERIC =============
def tn(df, c):
    if not c or c not in df.columns: return None
    return pd.to_numeric(df[c].astype(str).str.replace("%","",regex=False).str.replace(",","",regex=False).str.replace("Rs","",regex=False).str.replace(" ","",regex=False), errors="coerce").fillna(0)

for k in C:
    if C[k]: df[C[k]+"_n"] = tn(df, C[k])

# ============= MONTHLY COLUMNS =============
mk = ["apr","may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar"]
MC = {}
for m in mk:
    ly = pl = cy = lyg = cyg = plg = None
    for c in df.columns:
        cl = str(c).lower()
        if cl.startswith(m) and "25" in cl and ("unit" in cl or "sellout" in cl) and "plan" not in cl and "gms" not in cl and "fy" not in cl: ly = c
        elif cl.startswith(m) and "26" in cl and "plan" in cl and "gms" not in cl: pl = c
        elif cl.startswith(m) and "26" in cl and ("unit" in cl or "sellout" in cl) and "plan" not in cl and "gms" not in cl and "fy" not in cl: cy = c
        elif cl.startswith(m) and "25" in cl and "gms" in cl and "plan" not in cl and "fy" not in cl: lyg = c
        elif cl.startswith(m) and "26" in cl and "plan" in cl and "gms" in cl: plg = c
        elif cl.startswith(m) and "26" in cl and "gms" in cl and "plan" not in cl and "fy" not in cl: cyg = c
    MC[m] = {"ly":ly,"pl":pl,"cy":cy,"lyg":lyg,"plg":plg,"cyg":cyg}
    for k2, c2 in MC[m].items():
        if c2: df[c2+"_n"] = tn(df, c2)

# ============= HELPERS =============
def fmt(n):
    if pd.isna(n) or n == 0: return "0"
    if abs(n) >= 1e7: return f"₹{n/1e7:.2f}Cr"
    if abs(n) >= 1e5: return f"₹{n/1e5:.2f}L"
    if abs(n) >= 1e3: return f"{n/1e3:.1f}K"
    return f"{n:.0f}"

def kc(l, v, c="#38bdf8", s=""):
    return f'<div style="background:linear-gradient(135deg,#1e293b,#334155);padding:14px;border-radius:8px;border-left:4px solid {c};margin-bottom:6px"><div style="color:#94a3b8;font-size:10px">{l}</div><div style="color:#f1f5f9;font-size:20px;font-weight:bold;margin-top:4px">{v}</div><div style="color:{c};font-size:10px;margin-top:2px">{s}</div></div>'

def sf(fig):
    fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#e2e8f0", size=10), xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"), margin=dict(t=20, b=50, l=50, r=20))
    return fig

# ============= FILTERS =============
st.sidebar.header("🔍 Filters")
df_f = df.copy()
for f in ["vertical","platform","brand","categoryegory","sub category","kam","sell","model name"]:
    if C.get(f):
        opts = ["All"] + sorted([str(x) for x in df_f[C[f]].dropna().unique()])[:200]
        sel = st.sidebar.selectbox(f.title(), opts, key=f)
        if sel != "All": df_f = df_f[df_f[C[f]].astype(str) == sel]

st.sidebar.success(f"✅ {len(df_f):,} / {len(df):,} rows")

# ============= KPIs =============
u25 = u26 = g25 = g26 = 0
if C.get("u25") and C["u25"]+"_n" in df_f.columns: u25 = df_f[C["u25"]+"_n"].sum()
if C.get("u26") and C["u26"]+"_n" in df_f.columns: u26 = df_f[C["u26"]+"_n"].sum()
if C.get("g25") and C["g25"]+"_n" in df_f.columns: g25 = df_f[C["g25"]+"_n"].sum()
if C.get("g26") and C["g26"]+"_n" in df_f.columns: g26 = df_f[C["g26"]+"_n"].sum()
uG = ((u26-u25)/u25*100) if u25 else 0
gG = ((g26-g25)/g25*100) if g25 else 0

st.markdown("### 📊 Overall Performance")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.markdown(kc("FY 25-26 U", fmt(u25)), unsafe_allow_html=True)
c2.markdown(kc("FY 26-27 U", fmt(u26), "#10b981"), unsafe_allow_html=True)
c3.markdown(kc("Unit Growth", f"{uG:.2f}%", "#10b981" if uG>=0 else "#ef4444", "vs LY"), unsafe_allow_html=True)
c4.markdown(kc("FY 25-26 G", fmt(g25)), unsafe_allow_html=True)
c5.markdown(kc("FY 26-27 G", fmt(g26), "#10b981"), unsafe_allow_html=True)
c6.markdown(kc("GMS Growth", f"{gG:.2f}%", "#10b981" if gG>=0 else "#ef4444", "vs LY"), unsafe_allow_html=True)

# ============= MONTHLY TREND =============
st.markdown("---")
st.markdown("### 📅 Monthly Trend: LY vs Plan vs CY")
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

fig = make_sub categoryplots(rows=1, cols=2, sub categoryplot_titles=("Units", "GMS"))
fig.add_trace(go.Scategoryegoryter(x=mk,y=ly_u,name="LY",model namee="lines+markers",line=dict(color="#94a3b8",dash="dot")),1,1)
fig.add_trace(go.Scategoryegoryter(x=mk,y=pl_u,name="Plan",model namee="lines+markers",line=dict(color="#f59e0b",dash="dash")),1,1)
fig.add_trace(go.Scategoryegoryter(x=mk,y=cy_u,name="CY",model namee="lines+markers",line=dict(color="#38bdf8",width=3),fill="tozeroy",fillcolor="rgba(56,189,248,0.1)"),1,1)
fig.add_trace(go.Scategoryegoryter(x=mk,y=ly_g,model namee="lines+markers",line=dict(color="#94a3b8",dash="dot"),showlegend=False),1,2)
fig.add_trace(go.Scategoryegoryter(x=mk,y=pl_g,model namee="lines+markers",line=dict(color="#f59e0b",dash="dash"),showlegend=False),1,2)
fig.add_trace(go.Scategoryegoryter(x=mk,y=cy_g,model namee="lines+markers",line=dict(color="#10b981",width=3),fill="tozeroy",fillcolor="rgba(16,185,129,0.1)"),1,2)
fig.update_layout(paper_bgcolor="#1e293b",plot_bgcolor="#1e293b",font_color="#e2e8f0",height=350,hovermodel namee="x unified")
fig.update_xaxes(gridcolor="#334155");fig.update_yaxes(gridcolor="#334155")
st.plotly_chart(fig, use_container_width=True)

# ============= MoM GROWTH =============
st.markdown("### 📊 MoM Growth %")
mom_u = [((cy_u[i]-ly_u[i])/ly_u[i]*100) if ly_u[i] else 0 for i in range(12)]
mom_g = [((cy_g[i]-ly_g[i])/ly_g[i]*100) if ly_g[i] else 0 for i in range(12)]
fig = make_sub categoryplots(rows=1, cols=2, sub categoryplot_titles=("Units Growth %", "GMS Growth %"))
cu_colors = ["#10b981" if v>=0 else "#ef4444" for v in mom_u]
cg_colors = ["#10b981" if v>=0 else "#ef4444" for v in mom_g]
fig.add_trace(go.Bar(x=mk, y=mom_u, marker_color=cu_colors, text=[f"{v:.1f}%" for v in mom_u], textposition="outside"), 1, 1)
fig.add_trace(go.Bar(x=mk, y=mom_g, marker_color=cg_colors, text=[f"{v:.1f}%" for v in mom_g], textposition="outside"), 1, 2)
fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, showlegend=False)
fig.update_xaxes(gridcolor="#334155"); fig.update_yaxes(gridcolor="#334155")
st.plotly_chart(fig, use_container_width=True)

# ============= ACHIEVEMENT =============
st.markdown("### 🎯 Achievement % vs Plan")
ach_u = [(cy_u[i]/pl_u[i]*100) if pl_u[i] else 0 for i in range(12)]
ach_g = [(cy_g[i]/pl_g[i]*100) if pl_g[i] else 0 for i in range(12)]
fig = make_sub categoryplots(rows=1, cols=2, sub categoryplot_titles=("Units Ach %", "GMS Ach %"))
ca_u = ["#10b981" if v>=100 else "#f59e0b" if v>=80 else "#ef4444" for v in ach_u]
ca_g = ["#10b981" if v>=100 else "#f59e0b" if v>=80 else "#ef4444" for v in ach_g]
fig.add_trace(go.Bar(x=mk, y=ach_u, marker_color=ca_u, text=[f"{v:.0f}%" for v in ach_u], textposition="outside"), 1, 1)
fig.add_trace(go.Bar(x=mk, y=ach_g, marker_color=ca_g, text=[f"{v:.0f}%" for v in ach_g], textposition="outside"), 1, 2)
fig.add_hline(y=100, line_dash="dash", line_color="white")
fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, showlegend=False)
fig.update_xaxes(gridcolor="#334155"); fig.update_yaxes(gridcolor="#334155")
st.plotly_chart(fig, use_container_width=True)

# ============= TOP 20 model nameELS =============
st.markdown("---")
st.markdown("### 🏆 Top 20 model nameels by GMS")
cg = None
if C.get("g26"):
    if C["g26"]+"_n" in df_f.columns: cg = C["g26"]+"_n"
    elif C["g26"] in df_f.columns: cg = C["g26"]
if C.get("model name") and cg:
    mp = df_f.groupby(C["model name"]).agg({cg:"sum"}).reset_index().nlargest(20, cg)
    fig = px.bar(mp, x=cg, y=C["model name"], orientation="h", color=cg, color_continuous_scale="Blues")
    sf(fig); fig.update_layout(height=500, yaxis={"categoryegoryegoryorder":"total ascending"})
    st.plotly_chart(fig, use_container_width=True)

# ============= BRAND =============
st.markdown("### 🏷️ Brand: LY vs CY")
if C.get("brand") and cg:
    cg25 = None
    if C.get("g25"):
        if C["g25"]+"_n" in df_f.columns: cg25 = C["g25"]+"_n"
        elif C["g25"] in df_f.columns: cg25 = C["g25"]
    if cg25:
        bd = df_f.groupby(C["brand"]).agg({cg25:"sum",cg:"sum"}).reset_index().nlargest(15, cg)
        bd.columns = ["Brand","FY 25-26","FY 26-27"]
        fig = px.bar(bd.melt(id_vars="Brand"), x="Brand", y="value", color="variable", barmodel namee="group")
        sf(fig); fig.update_xaxes(tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

# ============= categoryegoryEGORY =============
st.markdown("### 📂 categoryegoryegory Distribution")
if C.get("categoryegory") and cg:
    r1,r2 = st.columns(2)
    with r1:
        cd = df_f.groupby(C["categoryegory"])[cg].sum().reset_index().nlargest(15, cg)
        fig = px.pie(cd, names=C["categoryegory"], values=cg, hole=0.4)
        sf(fig)
        st.plotly_chart(fig, use_container_width=True)
    if C.get("sub category"):
        with r2:
            sd = df_f.groupby([C["categoryegory"], C["sub category"]])[cg].sum().reset_index().nlargest(15, cg)
            fig = px.bar(sd, x=cg, y=C["sub category"], orientation="h", color=C["categoryegory"])
            sf(fig); fig.update_layout(height=500, yaxis={"categoryegoryegoryorder":"total ascending"})
            st.plotly_chart(fig, use_container_width=True)

# ============= categoryegoryEGORY HEATMAP =============
if C.get("categoryegory") and C.get("sub category") and cg:
    st.markdown("### 🌡️ categoryegoryegory × sub category-categoryegoryegory Heatmap")
    hd = df_f.groupby([C["categoryegory"], C["sub category"]])[cg].sum().reset_index()
    fig = px.density_heatmap(hd, x=C["categoryegory"], y=C["sub category"], z=cg, color_continuous_scale="Blues")
    sf(fig); fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ============= verticalICAL x platformFORM =============
st.markdown("### 🏢 verticalical × platformform")
if C.get("vertical") and cg:
    r1,r2 = st.columns(2)
    with r1:
        vd = df_f.groupby(C["vertical"])[cg].sum().reset_index()
        fig = px.pie(vd, names=C["vertical"], values=cg, hole=0.4)
        sf(fig)
        st.plotly_chart(fig, use_container_width=True)
    if C.get("platform"):
        with r2:
            pd2 = df_f.groupby(C["platform"])[cg].sum().reset_index()
            fig = px.pie(pd2, names=C["platform"], values=cg, hole=0.4)
            sf(fig)
            st.plotly_chart(fig, use_container_width=True)

# ============= KAM =============
st.markdown("### 👥 KAM Performance")
if C.get("kam") and cg:
    kd = df_f.groupby(C["kam"])[cg].sum().reset_index().sort_values(cg, ascending=False)
    fig = px.bar(kd, x=C["kam"], y=cg, color=cg, color_continuous_scale="Purples")
    sf(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============= SELLERS =============
st.markdown("### 🏪 Top 15 Sellers")
if C.get("sell") and cg:
    sd = df_f.groupby(C["sell"])[cg].sum().reset_index().nlargest(15, cg)
    fig = px.bar(sd, x=C["sell"], y=cg, color=cg, color_continuous_scale="Greens")
    sf(fig); fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ============= TOP/BOTTOM 10 =============
st.markdown("---")
st.markdown("### ⭐ Top 10 vs Bottom 10 SKUs")
if cg:
    ic = C.get("id") or C.get("model name")
    dc = []
    if ic: dc.append(ic)
    if C.get("brand"): dc.append(C["brand"])
    if C.get("model name") and C["model name"] != ic: dc.append(C["model name"])
    dc.append(cg)
    c1,c2 = st.columns(2)
    c1.sub categoryheader("🌟 Top 10")
    c1.dataframe(df_f.nlargest(10, cg)[dc], use_container_width=True)
    c2.sub categoryheader("⚠️ Bottom 10")
    c2.dataframe(df_f.nsmallest(10, cg)[dc], use_container_width=True)

# ============= QUARTER SUMMARY =============
st.markdown("---")
st.markdown("### 📊 Quarter Summary")
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
for cx in ["LY Units", "CY Plan", "CY Actual"]: qdf[cx] = qdf[cx].apply(lambda x: f"{x:,.0f}")
for cx in ["LY GMS", "CY GMS Plan", "CY GMS Actual"]: qdf[cx] = qdf[cx].apply(lambda x: f"₹{x/1e7:.2f}Cr" if abs(x) >= 1e7 else f"₹{x/1e5:.2f}L")
st.dataframe(qdf, use_container_width=True, hide_index=True)

# ============= DETAILED DATA =============
st.markdown("---")
st.markdown("### 📋 Detailed Data")
disp = []
for k in ["id","vertical","platform","brand","sell","categoryegory","sub category","model name","kam","u25","u26","g25","g26"]:
    if C.get(k) and C[k] in df_f.columns: disp.append(C[k])
if disp: st.dataframe(df_f[disp].head(2000), use_container_width=True, height=500)
