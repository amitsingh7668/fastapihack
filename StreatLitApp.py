# streamlit run stream.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
import pandas as pd

# === Replace with your full metadata ===
import json
with open("repo_metadata.json") as f:
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

# === Streamlit Dashboard ===
st.set_page_config(layout="wide", page_title="Codebase Metrics Dashboard")
st.title("📊 Codebase Metrics Dashboard")

tab1, tab2, tab3, tab4 , tab5= st.tabs(["📚 Top Libraries", "🔧 Function Stats", "📦 Variable Stats", "🔀 Sankey View","🍰 Library Pie Chart"])

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
        """Shortens the label if it exceeds 25 characters and removes the .java extension."""
        if label.endswith(".java"):
            label = label.replace(".java", "")
        return label if len(label) <= 25 else f"{label[:10]}...{label[-10:]}"

    # Top N connections
    top_n = 20
    dependency_counter = defaultdict(int)

    # Count frequency of each source-target pair
    for s, t in zip(source_indices, target_indices):
        dependency_counter[(s, t)] += 1

    # Sort and select top N connections
    sorted_links = sorted(dependency_counter.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Extract sources, targets, and values for the Sankey diagram
    sankey_source = [src for (src, tgt), _ in sorted_links]
    sankey_target = [tgt for (src, tgt), _ in sorted_links]
    sankey_value = [val for (_, _), val in sorted_links]

    # Prepare sharp, clean labels
    shortened_labels = [shorten(label) for label in labels]

    # Create Sankey diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        arrangement='snap',
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color="black", width=1.2),
            label=shortened_labels,
            color="rgba(0, 102, 204, 0.85)",  # Richer blue with better contrast
            hovertemplate='%{label}<extra></extra>',
        ),
        link=dict(
            source=sankey_source,
            target=sankey_target,
            value=sankey_value,
            color="rgba(0, 204, 102, 0.5)",  # Green with better visibility
            hovertemplate='📂 From %{source.label}<br>📥 To %{target.label}<br>🔁 Usage: %{value}<extra></extra>',
        )
    )])

    # Update layout of the figure
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

    # Display the chart
    st.plotly_chart(fig_sankey, use_container_width=True)





with tab5:
    st.subheader("🍰 Top 20 Library Import Distribution")

    # Build import frequency from the same file_data_list
    all_imports = [imp.split(".")[-1] for file in file_data_list for imp in file["imports"]]
    import_freq = pd.Series(all_imports).value_counts().reset_index()
    import_freq.columns = ["Library", "Count"]

    # Take only top 20
    top_20_imports = import_freq.head(20)

    # Create pie chart
    fig_import_pie = px.pie(
        top_20_imports,
        names="Library",
        values="Count",
        title="🍰 Top 20 Library Imports (Most Used)"
    )

    # Display chart
    st.plotly_chart(fig_import_pie, use_container_width=True)

