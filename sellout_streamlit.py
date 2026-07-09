import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Sellout Dashboard Pro", page_icon="📊", layout="wide")
st.title("📊 Sellout Tracker Dashboard Pro")

col_u1, col_u2 = st.columns(2)
with col_u1: f_curr = st.file_uploader("FY 2026-27", type=["xlsx","csv"], key="c")
with col_u2: f_prev = st.file_uploader("FY 2025-26 (Optional)", type=["xlsx","csv"], key="p")

if f_curr is None:
    st.info("Upload Current Year file")
    st.stop()

@st.cache_data
def load_file(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    xls = pd.ExcelFile(file)
    target = None
    for s in xls.sheet_names:
        c = s.strip().lower().replace(' ','').replace('&','').replace('_','').replace('-','')
        if c in ['eq','enq','equ','enquire','enquiry']:
            target = s
            break
    if not target:
        target = xls.sheet_names[0]
    raw = pd.read_excel(file, sheet_name=target, header=None, nrows=10)
    hdr = 0
    for i, row in raw.iterrows():
        r = ' '.join([str(x) if x is not None else '' for x in row.tolist()]).lower()
        if 'item' in r and ('vertical' in r or 'brand' in r):
            hdr = i
            break
    df = pd.read_excel(file, sheet_name=target, header=hdr)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
    return df

df = load_file(f_curr)
df_prev = load_file(f_prev) if f_prev else None

def find_col(df, *pats):
    for col in df.columns:
        cs = str(col).lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
        for p in pats:
            ps = p.lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
            if ps in cs:
                return col
    return None

def get_col(df, pat, must=None, notin=None):
    """Get column with optional must-have and must-not-have keywords"""
    for col in df.columns:
        cs = str(col).lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
        p = pat.lower().replace("'","").replace(" ","").replace("-","").replace("_","").replace("&","").replace(".","").replace("(","").replace(")","")
        if p in cs:
            if must:
                if not all(m.lower() in cs for m in must):
                    continue
            if notin:
                if any(n.lower() in cs for n in notin):
                    continue
            return col
    return None

# Column detection with smart fallback
COLS = {}
COLS['item_id'] = find_col(df, 'itemid', 'item id', 'sku')
COLS['vertical'] = find_col(df, 'vertical')
COLS['platform'] = find_col(df, 'platform')
COLS['brand'] = find_col(df, 'brand')
COLS['seller'] = find_col(df, 'seller')
COLS['category'] = find_col(df, 'category')
COLS['subcategory'] = find_col(df, 'subcategory', 'sub category')
COLS['model'] = find_col(df, 'modelname', 'model name', 'model')
COLS['kam'] = find_col(df, 'kam')
COLS['bau_sp'] = find_col(df, 'bausp', 'bau sp')

# FY Units - look for any FY 25-26 / 26-27 units column
COLS['fy25_u'] = get_col(df, '25-26', must=['unit'], notin=['plan', 'gms', 'ach', 'growth']) or get_col(df, '2526', must=['unit'], notin=['plan', 'gms'])
COLS['fy26_u'] = get_col(df, '26-27', must=['unit'], notin=['plan', 'gms', 'ach', 'growth']) or get_col(df, '2627', must=['unit'], notin=['plan', 'gms'])

# FY GMS
COLS['fy25_g'] = get_col(df, '25-26', must=['gms'], notin=['plan', 'ach', 'growth']) or get_col(df, '2526', must=['gms'], notin=['plan'])
COLS['fy26_g'] = get_col(df, '26-27', must=['gms'], notin=['plan', 'ach', 'growth']) or get_col(df, '2627', must=['gms'], notin=['plan'])

# YTD
COLS['ytd25_u'] = get_col(df, 'ytd25-26', must=['unit'], notin=['gms']) or get_col(df, 'ytd25', must=['unit'])
COLS['ytd26_u'] = get_col(df, 'ytd26-27', must=['unit'], notin=['gms']) or get_col(df, 'ytd26', must=['unit'])
COLS['ytd25_g'] = get_col(df, 'ytd25-26', must=['gms']) or get_col(df, 'ytd25', must=['gms'])
COLS['ytd26_g'] = get_col(df, 'ytd26-27', must=['gms']) or get_col(df, 'ytd26', must=['gms'])

# Convert numeric
def to_num(df, c):
    if not c or c not in df.columns:
        return None
    return pd.to_numeric(df[c].astype(str).str.replace('%','',regex=False).str.replace(',','',regex=False).str.replace('Rs','',regex=False).str.replace(' ','',regex=False), errors='coerce').fillna(0)

for k in COLS:
    if COLS[k]:
        df[COLS[k]+'_n'] = to_num(df, COLS[k])

# Monthly columns
month_kw = ['apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar']
MCOLS = {}
for m in month_kw:
    ly = plan = cy = ly_g = cy_g = plan_g = None
    for c in df.columns:
        cl = c.lower().replace("'","").replace(" ","").replace(".","").replace("(","").replace(")","").replace("-","").replace("_","")
        if cl.startswith(m) and '25' in cl and ('unit' in cl or 'sellout' in cl) and 'plan' not in cl and 'gms' not in cl:
            ly = c
        elif cl.startswith(m) and '26' in cl and 'plan' in cl and 'gms' not in cl:
            plan = c
        elif cl.startswith(m) and '26' in cl and ('unit' in cl or 'sellout' in cl) and 'plan' not in cl and 'gms' not in cl:
            cy = c
        elif cl.startswith(m) and '25' in cl and 'gms' in cl and 'plan' not in cl:
            ly_g = c
        elif cl.startswith(m) and '26' in cl and 'plan' in cl and 'gms' in cl:
            plan_g = c
        elif cl.startswith(m) and '26' in cl and 'gms' in cl and 'plan' not in cl:
            cy_g = c
    MCOLS[m] = {'ly': ly, 'plan': plan, 'cy': cy, 'ly_g': ly_g, 'plan_g': plan_g, 'cy_g': cy_g}
    for k2, c2 in MCOLS[m].items():
        if c2:
            df[c2+'_n'] = to_num(df, c2)

def fmt(n):
    if pd.isna(n) or n == 0: return "0"
    if abs(n) >= 1e7: return f"Rs{n/1e7:.2f}Cr"
    if abs(n) >= 1e5: return f"Rs{n/1e5:.2f}L"
    if abs(n) >= 1e3: return f"{n/1e3:.1f}K"
    return f"{n:.0f}"

def gv(key):
    c = COLS.get(key)
    if not c:
        return 0
    nc = c + '_n'
    if nc in df_f.columns:
        return df_f[nc].sum()
    return 0

def kpi(l, v, c="#38bdf8", s=""):
    return f'<div style="background:linear-gradient(135deg,#1e293b,#334155);padding:16px;border-radius:10px;border-left:4px solid {c};margin-bottom:8px"><div style="color:#94a3b8;font-size:11px">{l}</div><div style="color:#f1f5f9;font-size:22px;font-weight:bold;margin-top:5px">{v}</div><div style="color:{c};font-size:11px;margin-top:3px">{s}</div></div>'

def sf(fig):
    fig.update_layout(paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', font=dict(color='#e2e8f0', size=11), xaxis=dict(gridcolor='#334155'), yaxis=dict(gridcolor='#334155'), margin=dict(t=30, b=60, l=60, r=20))
    return fig

def get_col_name(key, prefer_n=True):
    c = COLS.get(key)
    if not c:
        return None
    nc = c + '_n'
    if prefer_n and nc in df_f.columns:
        return nc
    if c in df_f.columns:
        return c
    return None

# Filters
st.sidebar.header("Filters")
df_f = df.copy()
for f in ['vertical','platform','brand','category','subcategory','kam','seller','model']:
    if COLS.get(f):
        opts = ['All'] + sorted([str(x) for x in df_f[COLS[f]].dropna().unique()])[:200]
        sel = st.sidebar.selectbox(f.title(), opts, key=f)
        if sel != 'All':
            df_f = df_f[df_f[COLS[f]].astype(str) == sel]

st.sidebar.success(f"{len(df_f):,} / {len(df):,} rows")
with st.sidebar.expander("Column Mapping", expanded=True):
    for k, v in COLS.items():
        st.write(f"**{k}**: {v if v else 'NOT FOUND'}")

# KPIs
u25 = gv('fy25_u'); u26 = gv('fy26_u')
g25 = gv('fy25_g'); g26 = gv('fy26_g')
yu25 = gv('ytd25_u'); yu26 = gv('ytd26_u')
yg25 = gv('ytd25_g'); yg26 = gv('ytd26_g')
uG = ((u26-u25)/u25*100) if u25 else 0
gG = ((g26-g25)/g25*100) if g25 else 0

st.markdown("### Overall Performance")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.markdown(kpi("FY 25-26 Units", fmt(u25)), unsafe_allow_html=True)
c2.markdown(kpi("FY 26-27 Units", fmt(u26), "#10b981"), unsafe_allow_html=True)
c3.markdown(kpi("Unit Growth", f"{uG:.2f}%", "#10b981" if uG>=0 else "#ef4444", "vs LY"), unsafe_allow_html=True)
c4.markdown(kpi("FY 25-26 GMS", fmt(g25)), unsafe_allow_html=True)
c5.markdown(kpi("FY 26-27 GMS", fmt(g26), "#10b981"), unsafe_allow_html=True)
c6.markdown(kpi("GMS Growth", f"{gG:.2f}%", "#10b981" if gG>=0 else "#ef4444", "vs LY"), unsafe_allow_html=True)

c7,c8,c9,c10,c11,c12 = st.columns(6)
c7.markdown(kpi("YTD 25-26 U", fmt(yu25)), unsafe_allow_html=True)
c8.markdown(kpi("YTD 26-27 U", fmt(yu26), "#10b981"), unsafe_allow_html=True)
c9.markdown(kpi("YTD GMS 25-26", fmt(yg25)), unsafe_allow_html=True)
c10.markdown(kpi("YTD GMS 26-27", fmt(yg26), "#10b981"), unsafe_allow_html=True)
c11.markdown(kpi("Total SKUs", f"{len(df_f):,}"), unsafe_allow_html=True)
c12.markdown(kpi("Avg GMS/SKU", fmt(g26/len(df_f)) if len(df_f) else "0"), unsafe_allow_html=True)

# Monthly trend
st.markdown("---")
st.markdown("### Monthly Trend: LY vs Plan vs CY")
months = month_kw
ly_u = []; plan_u = []; cy_u = []
ly_g = []; plan_g = []; cy_g = []
for m in months:
    cols = MCOLS.get(m, {})
    ly = cols.get('ly')
    pl = cols.get('plan')
    cy = cols.get('cy')
    ly_g_c = cols.get('ly_g')
    pl_g_c = cols.get('plan_g')
    cy_g_c = cols.get('cy_g')
    
    ly_u.append(df_f[ly+'_n'].sum() if ly and (ly+'_n') in df_f.columns else 0)
    plan_u.append(df_f[pl+'_n'].sum() if pl and (pl+'_n') in df_f.columns else 0)
    cy_u.append(df_f[cy+'_n'].sum() if cy and (cy+'_n') in df_f.columns else 0)
    ly_g.append(df_f[ly_g_c+'_n'].sum() if ly_g_c and (ly_g_c+'_n') in df_f.columns else 0)
    plan_g.append(df_f[pl_g_c+'_n'].sum() if pl_g_c and (pl_g_c+'_n') in df_f.columns else 0)
    cy_g.append(df_f[cy_g_c+'_n'].sum() if cy_g_c and (cy_g_c+'_n') in df_f.columns else 0)

fig = make_subplots(rows=1, cols=2, subplot_titles=('Units (LY/Plan/CY)', 'GMS (LY/Plan/CY)'))
fig.add_trace(go.Scatter(x=months, y=ly_u, name='LY', mode='lines+markers', line=dict(color='#94a3b8', dash='dot')), 1, 1)
fig.add_trace(go.Scatter(x=months, y=plan_u, name='Plan', mode='lines+markers', line=dict(color='#f59e0b', dash='dash')), 1, 1)
fig.add_trace(go.Scatter(x=months, y=cy_u, name='CY', mode='lines+markers', line=dict(color='#38bdf8', width=3), fill='tozeroy', fillcolor='rgba(56,189,248,0.1)'), 1, 1)
fig.add_trace(go.Scatter(x=months, y=ly_g, name='LY G', mode='lines+markers', line=dict(color='#94a3b8', dash='dot'), showlegend=False), 1, 2)
fig.add_trace(go.Scatter(x=months, y=plan_g, name='Plan G', mode='lines+markers', line=dict(color='#f59e0b', dash='dash'), showlegend=False), 1, 2)
fig.add_trace(go.Scatter(x=months, y=cy_g, name='CY G', mode='lines+markers', line=dict(color='#10b981', width=3), fill='tozeroy', fillcolor='rgba(16,185,129,0.1)'), 1, 2)
fig.update_layout(paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', font_color='#e2e8f0', height=400, hovermode='x unified')
fig.update_xaxes(gridcolor='#334155'); fig.update_yaxes(gridcolor='#334155')
st.plotly_chart(fig, use_container_width=True)

# MoM Growth
st.markdown("### MoM Growth %")
mom_u = [((cy_u[i]-ly_u[i])/ly_u[i]*100) if ly_u[i] else 0 for i in range(12)]
mom_g = [((cy_g[i]-ly_g[i])/ly_g[i]*100) if ly_g[i] else 0 for i in range(12)]
fig = make_subplots(rows=1, cols=2, subplot_titles=('Units Growth %', 'GMS Growth %'))
cu_colors = ['#10b981' if v>=0 else '#ef4444' for v in mom_u]
cg_colors = ['#10b981' if v>=0 else '#ef4444' for v in mom_g]
fig.add_trace(go.Bar(x=months, y=mom_u, marker_color=cu_colors, text=[f"{v:.1f}%" for v in mom_u], textposition='outside'), 1, 1)
fig.add_trace(go.Bar(x=months, y=mom_g, marker_color=cg_colors, text=[f"{v:.1f}%" for v in mom_g], textposition='outside'), 1, 2)
fig.update_layout(paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', font_color='#e2e8f0', height=400, showlegend=False)
fig.update_xaxes(gridcolor='#334155'); fig.update_yaxes(gridcolor='#334155')
st.plotly_chart(fig, use_container_width=True)

# Achievement
st.markdown("### Achievement % vs Plan")
ach_u = [(cy_u[i]/plan_u[i]*100) if plan_u[i] else 0 for i in range(12)]
ach_g = [(cy_g[i]/plan_g[i]*100) if plan_g[i] else 0 for i in range(12)]
fig = make_subplots(rows=1, cols=2, subplot_titles=('Units Ach %', 'GMS Ach %'))
ca_u = ['#10b981' if v>=100 else '#f59e0b' if v>=80 else '#ef4444' for v in ach_u]
ca_g = ['#10b981' if v>=100 else '#f59e0b' if v>=80 else '#ef4444' for v in ach_g]
fig.add_trace(go.Bar(x=months, y=ach_u, marker_color=ca_u, text=[f"{v:.0f}%" for v in ach_u], textposition='outside'), 1, 1)
fig.add_trace(go.Bar(x=months, y=ach_g, marker_color=ca_g, text=[f"{v:.0f}%" for v in ach_g], textposition='outside'), 1, 2)
fig.add_hline(y=100, line_dash="dash", line_color="white")
fig.update_layout(paper_bgcolor='#1e293b', plot_bgcolor='#1e293b', font_color='#e2e8f0', height=400, showlegend=False)
fig.update_xaxes(gridcolor='#334155'); fig.update_yaxes(gridcolor='#334155')
st.plotly_chart(fig, use_container_width=True)

# Models
st.markdown("---")
st.markdown("### Top 20 Models by GMS")
col_g = get_col_name('fy26_g')
if COLS.get('model') and col_g:
    col_u = get_col_name('fy26_u')
    agg_dict = {col_g: 'sum'}
    if col_u and col_u != col_g:
        agg_dict[col_u] = 'sum'
    mp = df_f.groupby(COLS['model']).agg(agg_dict).reset_index().nlargest(20, col_g)
    fig = px.bar(mp, x=col_g, y=COLS['model'], orientation='h', color=col_g, color_continuous_scale='Blues')
    sf(fig); fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("View Table"):
        st.dataframe(mp, use_container_width=True)

# Brand
st.markdown("### Brand Deep Dive")
r1,r2 = st.columns(2)
col_g = get_col_name('fy26_g')
col_25g = get_col_name('fy25_g')
if COLS.get('brand') and col_g:
    with r1:
        st.subheader("LY vs CY GMS")
        if col_25g:
            bd = df_f.groupby(COLS['brand']).agg({col_25g: 'sum', col_g: 'sum'}).reset_index().nlargest(15, col_g)
            bd.columns = ['Brand', 'FY 25-26', 'FY 26-27']
            fig = px.bar(bd.melt(id_vars='Brand'), x='Brand', y='value', color='variable', barmode='group')
            sf(fig); fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
    with r2:
        st.subheader("Growth %")
        if col_25g:
            b25 = df_f.groupby(COLS['brand'])[col_25g].sum()
            b26 = df_f.groupby(COLS['brand'])[col_g].sum()
            gr = ((b26-b25)/b25.replace(0,1)*100).fillna(0).reset_index()
            gr.columns = ['Brand', 'Growth %']
            gr = gr.sort_values('Growth %', ascending=False).head(15)
            fig = px.bar(gr, x='Brand', y='Growth %', color='Growth %', color_continuous_scale='RdYlGn')
            sf(fig); fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

# Category
st.markdown("### Category Analysis")
col_g = get_col_name('fy26_g')
if COLS.get('category') and col_g:
    r1,r2 = st.columns(2)
    with r1:
        st.subheader("Category Distribution")
        cd = df_f.groupby(COLS['category'])[col_g].sum().reset_index().nlargest(15, col_g)
        fig = px.pie(cd, names=COLS['category'], values=col_g, hole=0.4)
        sf(fig)
        st.plotly_chart(fig, use_container_width=True)
    if COLS.get('subcategory'):
        with r2:
            st.subheader("Top 15 Sub-Categories")
            sd = df_f.groupby([COLS['category'], COLS['subcategory']])[col_g].sum().reset_index().nlargest(15, col_g)
            fig = px.bar(sd, x=col_g, y=COLS['subcategory'], orientation='h', color=COLS['category'])
            sf(fig); fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("Category x Sub-Category Heatmap")
        hd = df_f.groupby([COLS['category'], COLS['subcategory']])[col_g].sum().reset_index()
        fig = px.density_heatmap(hd, x=COLS['category'], y=COLS['subcategory'], z=col_g, color_continuous_scale='Blues')
        sf(fig); fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# Vertical
st.markdown("### Vertical x Platform")
col_g = get_col_name('fy26_g')
col_25g = get_col_name('fy25_g')
if COLS.get('vertical') and col_g:
    r1,r2 = st.columns(2)
    with r1:
        st.subheader("Vertical: LY vs CY")
        if col_25g:
            vd = df_f.groupby(COLS['vertical']).agg({col_25g: 'sum', col_g: 'sum'}).reset_index()
            vd.columns = ['Vertical', 'FY 25-26', 'FY 26-27']
            fig = px.bar(vd.melt(id_vars='Vertical'), x='Vertical', y='value', color='variable', barmode='group')
            sf(fig)
            st.plotly_chart(fig, use_container_width=True)
    if COLS.get('platform'):
        with r2:
            st.subheader("Platform")
            pd2 = df_f.groupby(COLS['platform'])[col_g].sum().reset_index()
            fig = px.pie(pd2, names=COLS['platform'], values=col_g, hole=0.4)
            sf(fig)
            st.plotly_chart(fig, use_container_width=True)

# KAM/Seller
st.markdown("### KAM x Seller")
col_g = get_col_name('fy26_g')
if COLS.get('kam') and col_g:
    r1,r2 = st.columns(2)
    with r1:
        st.subheader("KAM")
        kd = df_f.groupby(COLS['kam'])[col_g].sum().reset_index().sort_values(col_g, ascending=False)
        fig = px.bar(kd, x=COLS['kam'], y=col_g, color=col_g, color_continuous_scale='Purples')
        sf(fig)
        st.plotly_chart(fig, use_container_width=True)
    if COLS.get('seller'):
        with r2:
            st.subheader("Top 15 Sellers")
            sd = df_f.groupby(COLS['seller'])[col_g].sum().reset_index().nlargest(15, col_g)
            fig = px.bar(sd, x=COLS['seller'], y=col_g, color=col_g, color_continuous_scale='Greens')
            sf(fig); fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

# Top/Bottom 10
st.markdown("---")
st.markdown("### Top 10 vs Bottom 10 SKUs")
col_g = get_col_name('fy26_g')
if col_g:
    r1,r2 = st.columns(2)
    ic = COLS.get('item_id') or COLS.get('model')
    dc = []
    if ic: dc.append(ic)
    if COLS.get('brand'): dc.append(COLS['brand'])
    if COLS.get('model') and COLS['model'] != ic: dc.append(COLS['model'])
    dc.append(col_g)
    with r1:
        st.subheader("Top 10")
        st.dataframe(df_f.nlargest(10, col_g)[dc], use_container_width=True)
    with r2:
        st.subheader("Bottom 10")
        st.dataframe(df_f.nsmallest(10, col_g)[dc], use_container_width=True)

# Quarter
st.markdown("---")
st.markdown("### Quarter Summary")
qd = {
    'Quarter': ['Q1 (Apr-Jun)', 'Q2 (Jul-Sep)', 'Q3 (Oct-Dec)', 'Q4 (Jan-Mar)'],
    'LY Units': [sum(ly_u[0:3]), sum(ly_u[3:6]), sum(ly_u[6:9]), sum(ly_u[9:12])],
    'CY Plan': [sum(plan_u[0:3]), sum(plan_u[3:6]), sum(plan_u[6:9]), sum(plan_u[9:12])],
    'CY Actual': [sum(cy_u[0:3]), sum(cy_u[3:6]), sum(cy_u[6:9]), sum(cy_u[9:12])],
    'LY GMS': [sum(ly_g[0:3]), sum(ly_g[3:6]), sum(ly_g[6:9]), sum(ly_g[9:12])],
    'CY GMS Plan': [sum(plan_g[0:3]), sum(plan_g[3:6]), sum(plan_g[6:9]), sum(plan_g[9:12])],
    'CY GMS Actual': [sum(cy_g[0:3]), sum(cy_g[3:6]), sum(cy_g[6:9]), sum(cy_g[9:12])]
}
qdf = pd.DataFrame(qd)
qdf['Units Ach %'] = (qdf['CY Actual']/qdf['CY Plan'].replace(0,1)*100).fillna(0).round(1)
qdf['GMS Ach %'] = (qdf['CY GMS Actual']/qdf['CY GMS Plan'].replace(0,1)*100).fillna(0).round(1)
qdf['Units Growth %'] = ((qdf['CY Actual']-qdf['LY Units'])/qdf['LY Units'].replace(0,1)*100).fillna(0).round(1)
for c2 in ['LY Units', 'CY Plan', 'CY Actual']:
    qdf[c2] = qdf[c2].apply(lambda x: f"{x:,.0f}")
for c2 in ['LY GMS', 'CY GMS Plan', 'CY GMS Actual']:
    qdf[c2] = qdf[c2].apply(lambda x: f"Rs{x/1e7:.2f}Cr" if abs(x) >= 1e7 else f"Rs{x/1e5:.2f}L")
st.dataframe(qdf, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Detailed Data")
disp = []
for k in ['item_id','vertical','platform','brand','seller','category','subcategory','model','kam','fy25_u','fy26_u','fy25_g','fy26_g']:
    if COLS.get(k) and COLS[k] in df_f.columns:
        disp.append(COLS[k])
if disp:
    st.dataframe(df_f[disp].head(2000), use_container_width=True, height=500)
