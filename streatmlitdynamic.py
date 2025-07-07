# streamlit run stream.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
import pandas as pd
import json
import os

# === Setup ===
st.set_page_config(layout="wide", page_title="Codebase Metrics Dashboard")
st.title("📊 Codebase Metrics Dashboard")

# === Dynamic File Load from Query Params ===
params = st.query_params
repo_id = params.get("id", "default")  # fallback to 'default_repo_metadata.json'
json_file = f"/Users/amitsingh/Desktop/deek/fastapiselenium/111111gitlabproject/{repo_id}repo_metadata.json"
print(json_file)
if not os.path.exists(json_file):
    st.error(f"❌ File `{json_file}` not found. Please provide a valid repo id in URL, e.g., `?id=1023`.")
    st.stop()

with open(json_file) as f:
    repo_model = json.load(f)
file_data_list = repo_model['files']

# === ANALYSIS ===
library_count = defaultdict(int)
for file in file_data_list:
    for imp in file["imports"]:
        imp = imp.split(".")[-1]
        library_count[imp] += 1
lib_df = pd.DataFrame(library_count.items(), columns=["Library", "Count"]).sort_values(by="Count", ascending=False).head(10)

class_func_count = []
class_var_count = []
for file in file_data_list:
    for clazz in file["classes"]:
        class_func_count.append({"Class": clazz, "Functions": len(file["functions"])})
        class_var_count.append({"Class": clazz, "Variables": len(file["variables"])})

func_df = pd.DataFrame(class_func_count).sort_values(by="Functions", ascending=False).head(10)
var_df = pd.DataFrame(class_var_count).sort_values(by="Variables", ascending=False).head(10)

label_map = {}
source_indices = []
target_indices = []
values = []
labels = []
idx = 0

def get_label_index(label):
    global idx
    if label not in label_map:
        label_map[label] = idx
        labels.append(label)
        idx += 1
    return label_map[label]

for file in file_data_list:
    file_idx = get_label_index(file["file_path"])
    for imp in file["imports"]:
        imp_idx = get_label_index(imp)
        source_indices.append(file_idx)
        target_indices.append(imp_idx)
        values.append(1)

# === Streamlit Tabs ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 Top Libraries", "🔧 Function Stats", "📦 Variable Stats", "🔀 Sankey View", "🍰 Library Pie Chart"
])

with tab1:
    st.subheader("📚 Most Used Libraries")
    fig_libraries = px.bar(lib_df, x="Library", y="Count", color="Count", title="Top Imports")
    fig_libraries.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_libraries, use_container_width=True)

with tab2:
    st.subheader("🔧 Classes with Most Functions")
    fig_func = px.bar(func_df, x="Class", y="Functions", color="Functions", title="Function Count by Class")
    st.plotly_chart(fig_func, use_container_width=True)

with tab3:
    st.subheader("📦 Classes with Most Variables")
    fig_var = px.bar(var_df, x="Class", y="Variables", color="Variables", title="Variable Count by Class")
    st.plotly_chart(fig_var, use_container_width=True)

with tab4:
    st.subheader("🔀 File-to-Import Dependency (Sankey)")

    def shorten(label):
        if label.endswith(".java"):
            label = label.replace(".java", "")
        return label if len(label) <= 25 else f"{label[:10]}...{label[-10:]}"
    
    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

    dependency_counter = defaultdict(int)
    for s, t in zip(source_indices, target_indices):
        dependency_counter[(s, t)] += 1

    top_n = 20
    sorted_links = sorted(dependency_counter.items(), key=lambda x: x[1], reverse=True)[:top_n]

    sankey_source = [src for (src, tgt), _ in sorted_links]
    sankey_target = [tgt for (src, tgt), _ in sorted_links]
    sankey_value = [val for (_, _), val in sorted_links]

    shortened_labels = [shorten(label) for label in labels]

    base_colors = [
        "#003f5c", "#58508d", "#bc5090", "#ffa600", "#2f4b7c",
        "#ff6361", "#4C78A8", "#54A24B", "#E45756", "#72B7B2"
    ]
    node_colors = [base_colors[i % len(base_colors)] for i in range(len(shortened_labels))]
    link_colors = [hex_to_rgba(node_colors[src], alpha=0.4) for src in sankey_source]

    fig_sankey = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color="black", width=1.2),
            label=shortened_labels,
            color=node_colors,
            hovertemplate='%{label}<extra></extra>',
        ),
        link=dict(
            source=sankey_source,
            target=sankey_target,
            value=sankey_value,
            color=link_colors,
            hovertemplate='📂 From %{source.label}<br>📥 To %{target.label}<br>🔁 Usage: %{value}<extra></extra>',
        )
    ))

    fig_sankey.update_layout(
        title=dict(
            text="🔗 Top 20 File-to-Import Dependencies",
            x=0.5,
            xanchor='center',
            font=dict(size=22, color='black')
        ),
        font=dict(size=16, color='black', family="Arial"),
        margin=dict(l=10, r=10, t=90, b=40),
        height=800,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    st.plotly_chart(fig_sankey, use_container_width=True)

with tab5:
    st.subheader("🍰 Top 20 Library Import Distribution")
    all_imports = [imp.split(".")[-1] for file in file_data_list for imp in file["imports"]]
    import_freq = pd.Series(all_imports).value_counts().reset_index()
    import_freq.columns = ["Library", "Count"]
    top_20_imports = import_freq.head(20)

    fig_import_pie = px.pie(
        top_20_imports,
        names="Library",
        values="Count",
        title="🍰 Top 20 Library Imports (Most Used)"
    )

    st.plotly_chart(fig_import_pie, use_container_width=True)
