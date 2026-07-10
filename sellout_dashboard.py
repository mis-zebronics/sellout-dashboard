import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Sellin-Sellout Dashboard", page_icon="📊", layout="wide")

# ============= SIDEBAR NAVIGATION =============
with st.sidebar:
    st.title("📊 Dashboard Selector")
    st.markdown("---")
    page = st.radio(
        "Choose Dashboard:",
        ["📤 Sellout Tracker", "📥 Sellin Tracker"],
        index=0
    )
    st.markdown("---")
    st.info("💡 Select a dashboard to view analytics")

# ============= SELLOUT DASHBOARD =============
if page == "📤 Sellout Tracker":
    st.title("📊 Sellout Tracker Dashboard")

    @st.cache_data
    def load_sellout():
        file_path = "FY 2026 - 2027 Sellout Tracker.xlsx"
        if not os.path.exists(file_path):
            st.error("❌ Sellout file not found!")
            st.stop()
        xls = pd.ExcelFile(file_path)
        t = None
        for s in xls.sheet_names:
            c = s.strip().lower().replace(" ","").replace("&","").replace("_","").replace("-","")
            if c in ["eq","enq","equ","enquire","enquiry"]:
                t = s
                break
        if not t: 
            t = xls.sheet_names[0]
        raw = pd.read_excel(file_path, sheet_name=t, header=None, nrows=10)
        h = 0
        for i, row in raw.iterrows():
            r = " ".join([str(x) if x is not None else "" for x in row.tolist()]).lower()
            if "item" in r and ("vertical" in r or "brand" in r):
                h = i
                break
        d = pd.read_excel(file_path, sheet_name=t, header=h)
        d.columns = d.columns.astype(str).str.strip()
        d = d.loc[:, ~d.columns.str.contains("^Unnamed", na=False)]
        return d

    with st.spinner("📊 Loading Sellout data..."):
        df = load_sellout()

    st.success(f"✅ Loaded {len(df):,} rows from Sellout Tracker")

    def find_col(df, search_text, exclude_words=None):
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
    C["id"] = find_col(df, "item id") or find_col(df, "sku")
    C["vert"] = find_col(df, "vertical")
    C["plat"] = find_col(df, "platform")
    C["brand"] = find_col(df, "brand")
    C["sell"] = find_col(df, "seller")
    C["cat"] = find_col(df, "category")
    C["sub"] = find_col(df, "sub category") or find_col(df, "subcategory")
    C["mod"] = find_col(df, "model")
    C["kam"] = find_col(df, "kam")
    C["u25"] = find_col(df, "25-26", ["gms","plan","ach","growth","mar","feb","jan","dec","nov","oct","sep","aug","jul","jun","may","apr"])
    C["u26"] = find_col(df, "26-27", ["gms","plan","ach","growth","mar","feb","jan","dec","nov","oct","sep","aug","jul","jun","may","apr"])
    C["g25"] = find_col(df, "25-26 gms", ["plan","ach","growth","ytd"])
    C["g26"] = find_col(df, "26-27 gms", ["plan","ach","growth","ytd"])

    with st.sidebar.expander("🔍 Column Mapping", expanded=False):
        for k, v in C.items():
            st.write(f"**{k}**: {v if v else 'NOT FOUND'}")

    def tn(df, c):
        if not c or c not in df.columns: return None
        return pd.to_numeric(df[c].astype(str).str.replace("%","",regex=False).str.replace(",","",regex=False).str.replace("Rs","",regex=False).str.replace(" ","",regex=False), errors="coerce").fillna(0)

    for k in C:
        if C[k]: df[C[k]+"_n"] = tn(df, C[k])

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

    def fmt_units(n):
        if pd.isna(n) or n == 0:
            return "0"
        if abs(n) >= 1e7:
            return f"{n/1e7:.2f}Cr"
        if abs(n) >= 1e5:
            return f"{n/1e5:.2f}L"
        if abs(n) >= 1e3:
            return f"{n/1e3:.1f}K"
        return f"{n:.0f}"

    def kc(title, value, color="#38bdf8", subtitle=""):
        return f"""
        <div style="
        background:linear-gradient(135deg,#1e293b,#334155);
        padding:15px;
        border-radius:10px;
        border-left:4px solid {color};
        margin-bottom:8px;">
        <div style="color:#94a3b8;font-size:11px;">
        {title}
        </div>
        <div style="color:white;font-size:28px;font-weight:bold;margin-top:6px;">
        {value}
        </div>
        <div style="color:#cbd5e1;font-size:12px;margin-top:8px;">
        {subtitle}
        </div>
        </div>
        """

    def sf(fig):
        fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#e2e8f0", size=10), xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"), margin=dict(t=20, b=50, l=50, r=20))
        return fig

    st.sidebar.header("🔍 Filters")
    df_f = df.copy()
    for f in ["vert","plat","brand","cat","sub","kam","sell","mod"]:
        if C.get(f):
            opts = ["All"] + sorted([str(x) for x in df_f[C[f]].dropna().unique()])[:200]
            sel = st.sidebar.selectbox(f.title(), opts, key="so_"+f)
            if sel != "All": df_f = df_f[df_f[C[f]].astype(str) == sel]

    st.sidebar.success(f"✅ {len(df_f):,} / {len(df):,} rows")

    u25 = u26 = g25 = g26 = 0
    if C.get("u25") and C["u25"]+"_n" in df_f.columns: u25 = df_f[C["u25"]+"_n"].sum()
    if C.get("u26") and C["u26"]+"_n" in df_f.columns: u26 = df_f[C["u26"]+"_n"].sum()
    if C.get("g25") and C["g25"]+"_n" in df_f.columns: g25 = df_f[C["g25"]+"_n"].sum()
    if C.get("g26") and C["g26"]+"_n" in df_f.columns: g26 = df_f[C["g26"]+"_n"].sum()
    uG = ((u26-u25)/u25*100) if u25 else 0
    gG = ((g26-g25)/g25*100) if g25 else 0

    st.markdown("### 📊 Overall Performance")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(kc("FY 25-26 U", fmt_units(u25)), unsafe_allow_html=True)
    c2.markdown(kc("FY 26-27 U", fmt_units(u26), "#10b981"), unsafe_allow_html=True)
    c3.markdown(kc("Unit Growth", f"{uG:.2f}%", "#10b981" if uG>=0 else "#ef4444"), unsafe_allow_html=True)
    c4.markdown(kc("FY 25-26 G", fmt_units(g25)), unsafe_allow_html=True)
    c5.markdown(kc("FY 26-27 G", fmt_units(g26), "#10b981"), unsafe_allow_html=True)
    c6.markdown(kc("GMS Growth", f"{gG:.2f}%", "#10b981" if gG>=0 else "#ef4444"), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📅 Monthly Trend")
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

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=mk, y=ly_u, name="LY", mode="lines+markers", line=dict(color="#94a3b8", dash="dot")))
    fig1.add_trace(go.Scatter(x=mk, y=pl_u, name="Plan", mode="lines+markers", line=dict(color="#f59e0b", dash="dash")))
    fig1.add_trace(go.Scatter(x=mk, y=cy_u, name="CY", mode="lines+markers", line=dict(color="#38bdf8", width=3), fill="tozeroy", fillcolor="rgba(56,189,248,0.1)"))
    fig1.update_layout(title="Units: LY vs Plan vs CY", paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, hovermode="x unified")
    fig1.update_xaxes(gridcolor="#334155"); fig1.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=mk, y=ly_g, name="LY GMS", mode="lines+markers", line=dict(color="#94a3b8", dash="dot")))
    fig2.add_trace(go.Scatter(x=mk, y=pl_g, name="Plan GMS", mode="lines+markers", line=dict(color="#f59e0b", dash="dash")))
    fig2.add_trace(go.Scatter(x=mk, y=cy_g, name="CY GMS", mode="lines+markers", line=dict(color="#10b981", width=3), fill="tozeroy", fillcolor="rgba(16,185,129,0.1)"))
    fig2.update_layout(title="GMS: LY vs Plan vs CY", paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, hovermode="x unified")
    fig2.update_xaxes(gridcolor="#334155"); fig2.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig2, use_container_width=True)

    if C.get("brand") and C.get("g26"):
        cg = C["g26"]+"_n" if C["g26"]+"_n" in df_f.columns else C["g26"]
        st.markdown("### 🏆 Top 20 Brands")
        bd = df_f.groupby(C["brand"])[cg].sum().reset_index().nlargest(20, cg)
        fig = px.bar(bd, x=cg, y=C["brand"], orientation="h", color=cg, color_continuous_scale="Blues")
        sf(fig); fig.update_layout(height=500, yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    if C.get("cat") and C.get("g26"):
        cg = C["g26"]+"_n" if C["g26"]+"_n" in df_f.columns else C["g26"]
        st.markdown("### 📂 Category × Sub-Category Heatmap")
        hd = df_f.groupby([C["cat"], C["sub"]])[cg].sum().reset_index()
        fig = px.density_heatmap(hd, x=C["cat"], y=C["sub"], z=cg, color_continuous_scale="Blues")
        sf(fig); fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# ============= SELLIN DASHBOARD =============
elif page == "📥 Sellin Tracker":
    st.title("📥 Sellin Tracker Dashboard Pro")

    @st.cache_data
    def load_sellin():
        file_path = "FY 2025 - 2026 Sellout Tracker.xlsx"
        if not os.path.exists(file_path):
            st.warning("⚠️ Sellin file not found. Please upload 'FY 2025 - 2026 Sellout Tracker.xlsx' to the GitHub repo.")
            st.info("Showing Sellout data as fallback")
            return None
        xls = pd.ExcelFile(file_path)
        t = None
        for s in xls.sheet_names:
            c = s.strip().lower().replace(" ","").replace("&","").replace("_","").replace("-","")
            if c in ["eq","enq","equ","enquire","enquiry"]:
                t = s
                break
        if not t: 
            t = xls.sheet_names[0]
        raw = pd.read_excel(file_path, sheet_name=t, header=None, nrows=10)
        h = 0
        for i, row in raw.iterrows():
            r = " ".join([str(x) if x is not None else "" for x in row.tolist()]).lower()
            if "item" in r and ("vertical" in r or "brand" in r):
                h = i
                break
        d = pd.read_excel(file_path, sheet_name=t, header=h)
        d.columns = d.columns.astype(str).str.strip()
        d = d.loc[:, ~d.columns.str.contains("^Unnamed", na=False)]
        return d

    with st.spinner("📊 Loading Sellin data..."):
        df_sellin = load_sellin()

    if df_sellin is None:
        st.error("📥 Please upload your Sellin tracker file to GitHub repository")
        st.info("File should be named: FY 2025 - 2026 Sellout Tracker.xlsx")
        st.stop()

    st.success(f"✅ Loaded {len(df_sellin):,} rows from Sellin Tracker")

    def find_col_si(df, search_text, exclude_words=None):
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

    CS = {}
    CS["id"] = find_col_si(df_sellin, "item id") or find_col_si(df_sellin, "sku")
    CS["vert"] = find_col_si(df_sellin, "vertical")
    CS["plat"] = find_col_si(df_sellin, "platform")
    CS["brand"] = find_col_si(df_sellin, "brand")
    CS["sell"] = find_col_si(df_sellin, "seller")
    CS["cat"] = find_col_si(df_sellin, "category")
    CS["sub"] = find_col_si(df_sellin, "sub category") or find_col_si(df_sellin, "subcategory")
    CS["mod"] = find_col_si(df_sellin, "model")
    CS["kam"] = find_col_si(df_sellin, "kam")
    CS["u24"] = find_col_si(df_sellin, "24-25", ["gms","plan","ach","growth"])
    CS["u25"] = find_col_si(df_sellin, "25-26", ["gms","plan","ach","growth"])
    CS["g24"] = find_col_si(df_sellin, "24-25 gms", ["plan","ach","growth","ytd"])
    CS["g25"] = find_col_si(df_sellin, "25-26 gms", ["plan","ach","growth","ytd"])

    with st.sidebar.expander("🔍 Column Mapping (Sellin)", expanded=False):
        for k, v in CS.items():
            st.write(f"**{k}**: {v if v else 'NOT FOUND'}")

    def tn_si(df, c):
        if not c or c not in df.columns: return None
        return pd.to_numeric(df[c].astype(str).str.replace("%","",regex=False).str.replace(",","",regex=False).str.replace("Rs","",regex=False).str.replace(" ","",regex=False), errors="coerce").fillna(0)

    for k in CS:
        if CS[k]: df_sellin[CS[k]+"_n"] = tn_si(df_sellin, CS[k])

    st.sidebar.header("🔍 Filters")
    df_si_f = df_sellin.copy()
    for f in ["vert","plat","brand","cat","sub","kam","sell","mod"]:
        if CS.get(f):
            opts = ["All"] + sorted([str(x) for x in df_si_f[CS[f]].dropna().unique()])[:200]
            sel = st.sidebar.selectbox(f.title(), opts, key="si_"+f)
            if sel != "All": df_si_f = df_si_f[df_si_f[CS[f]].astype(str) == sel]

    st.sidebar.success(f"✅ {len(df_si_f):,} / {len(df_sellin):,} rows")

    def fmt_si(n):
        if pd.isna(n) or n == 0: return "0"
        if abs(n) >= 1e7: return f"₹{n/1e7:.2f}Cr"
        if abs(n) >= 1e5: return f"₹{n/1e5:.2f}L"
        if abs(n) >= 1e3: return f"{n/1e3:.1f}K"
        return f"{n:.0f}"

    def kc_si(l, v, c="#38bdf8", s=""):
        return f'<div style="background:linear-gradient(135deg,#1e293b,#334155);padding:14px;border-radius:8px;border-left:4px solid {c};margin-bottom:6px"><div style="color:#94a3b8;font-size:10px">{l}</div><div style="color:#f1f5f9;font-size:20px;font-weight:bold;margin-top:4px">{v}</div><div style="color:{c};font-size:10px;margin-top:2px">{s}</div></div>'

    def sf_si(fig):
        fig.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#e2e8f0", size=10), xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"), margin=dict(t=20, b=50, l=50, r=20))
        return fig

    u24 = u25 = g24 = g25 = 0
    if CS.get("u24") and CS["u24"]+"_n" in df_si_f.columns: u24 = df_si_f[CS["u24"]+"_n"].sum()
    if CS.get("u25") and CS["u25"]+"_n" in df_si_f.columns: u25 = df_si_f[CS["u25"]+"_n"].sum()
    if CS.get("g24") and CS["g24"]+"_n" in df_si_f.columns: g24 = df_si_f[CS["g24"]+"_n"].sum()
    if CS.get("g25") and CS["g25"]+"_n" in df_si_f.columns: g25 = df_si_f[CS["g25"]+"_n"].sum()
    uG = ((u25-u24)/u24*100) if u24 else 0
    gG = ((g25-g24)/g24*100) if g24 else 0

    st.markdown("### 📊 Overall Performance")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(kc_si("FY 24-25 Units", fmt_si(u24)), unsafe_allow_html=True)
    c2.markdown(kc_si("FY 25-26 Units", fmt_si(u25), "#10b981"), unsafe_allow_html=True)
    c3.markdown(kc_si("Unit Growth %", f"{uG:.2f}%", "#10b981" if uG>=0 else "#ef4444"), unsafe_allow_html=True)
    c4.markdown(kc_si("FY 24-25 GMS", fmt_si(g24)), unsafe_allow_html=True)
    c5.markdown(kc_si("FY 25-26 GMS", fmt_si(g25), "#10b981"), unsafe_allow_html=True)
    c6.markdown(kc_si("GMS Growth %", f"{gG:.2f}%", "#10b981" if gG>=0 else "#ef4444"), unsafe_allow_html=True)

    mk_si = ["apr","may","jun","jul","aug","sep","oct","nov","dec","jan","feb","mar"]
    MC_si = {}
    for m in mk_si:
        ly = pl = cy = lyg = cyg = plg = None
        for c in df_sellin.columns:
            cl = str(c).lower()
            if cl.startswith(m) and "24" in cl and ("unit" in cl or "sellout" in cl) and "plan" not in cl and "gms" not in cl and "fy" not in cl: ly = c
            elif cl.startswith(m) and "25" in cl and "plan" in cl and "gms" not in cl: pl = c
            elif cl.startswith(m) and "25" in cl and ("unit" in cl or "sellout" in cl) and "plan" not in cl and "gms" not in cl and "fy" not in cl: cy = c
            elif cl.startswith(m) and "24" in cl and "gms" in cl and "plan" not in cl and "fy" not in cl: lyg = c
            elif cl.startswith(m) and "25" in cl and "plan" in cl and "gms" in cl: plg = c
            elif cl.startswith(m) and "25" in cl and "gms" in cl and "plan" not in cl and "fy" not in cl: cyg = c
        MC_si[m] = {"ly":ly,"pl":pl,"cy":cy,"lyg":lyg,"plg":plg,"cyg":cyg}
        for k2, c2 in MC_si[m].items():
            if c2: df_sellin[c2+"_n"] = tn_si(df_sellin, c2)

    st.markdown("---")
    st.markdown("### 📅 Monthly Trend")
    ly_u=[];pl_u=[];cy_u=[];ly_g=[];pl_g=[];cy_g=[]
    for m in mk_si:
        cols = MC_si.get(m,{})
        ly=cols.get("ly");p=cols.get("pl");cy=cols.get("cy")
        ly2=cols.get("lyg");p2=cols.get("plg");cy2=cols.get("cyg")
        ly_u.append(df_si_f[ly+"_n"].sum() if ly and (ly+"_n") in df_si_f.columns else 0)
        pl_u.append(df_si_f[p+"_n"].sum() if p and (p+"_n") in df_si_f.columns else 0)
        cy_u.append(df_si_f[cy+"_n"].sum() if cy and (cy+"_n") in df_si_f.columns else 0)
        ly_g.append(df_si_f[ly2+"_n"].sum() if ly2 and (ly2+"_n") in df_si_f.columns else 0)
        pl_g.append(df_si_f[p2+"_n"].sum() if p2 and (p2+"_n") in df_si_f.columns else 0)
        cy_g.append(df_si_f[cy2+"_n"].sum() if cy2 and (cy2+"_n") in df_si_f.columns else 0)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=mk_si, y=ly_u, name="LY", mode="lines+markers", line=dict(color="#94a3b8", dash="dot")))
    fig1.add_trace(go.Scatter(x=mk_si, y=pl_u, name="Plan", mode="lines+markers", line=dict(color="#f59e0b", dash="dash")))
    fig1.add_trace(go.Scatter(x=mk_si, y=cy_u, name="CY", mode="lines+markers", line=dict(color="#38bdf8", width=3), fill="tozeroy", fillcolor="rgba(56,189,248,0.1)"))
    fig1.update_layout(title="Units: LY vs Plan vs CY", paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, hovermode="x unified")
    fig1.update_xaxes(gridcolor="#334155"); fig1.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=mk_si, y=ly_g, name="LY GMS", mode="lines+markers", line=dict(color="#94a3b8", dash="dot")))
    fig2.add_trace(go.Scatter(x=mk_si, y=pl_g, name="Plan GMS", mode="lines+markers", line=dict(color="#f59e0b", dash="dash")))
    fig2.add_trace(go.Scatter(x=mk_si, y=cy_g, name="CY GMS", mode="lines+markers", line=dict(color="#10b981", width=3), fill="tozeroy", fillcolor="rgba(16,185,129,0.1)"))
    fig2.update_layout(title="GMS: LY vs Plan vs CY", paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font_color="#e2e8f0", height=350, hovermode="x unified")
    fig2.update_xaxes(gridcolor="#334155"); fig2.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig2, use_container_width=True)

    if CS.get("brand") and CS.get("g25"):
        cg = CS["g25"]+"_n" if CS["g25"]+"_n" in df_si_f.columns else CS["g25"]
        st.markdown("### 🏆 Top 20 Brands")
        bd = df_si_f.groupby(CS["brand"])[cg].sum().reset_index().nlargest(20, cg)
        fig = px.bar(bd, x=cg, y=CS["brand"], orientation="h", color=cg, color_continuous_scale="Greens")
        sf_si(fig); fig.update_layout(height=500, yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    if CS.get("cat") and CS.get("sub") and CS.get("g25"):
        cg = CS["g25"]+"_n" if CS["g25"]+"_n" in df_si_f.columns else CS["g25"]
        st.markdown("### 📂 Category × Sub-Category Heatmap")
        hd = df_si_f.groupby([CS["cat"], CS["sub"]])[cg].sum().reset_index()
        fig = px.density_heatmap(hd, x=CS["cat"], y=CS["sub"], z=cg, color_continuous_scale="Greens")
        sf_si(fig); fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
