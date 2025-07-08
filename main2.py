from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
import pandas as pd
import json
import os
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

BASE_PATH = "/Users/amitsingh/Desktop/deek/fastapiselenium/111111gitlabproject"

def load_repo_data(repo_id: str):
    json_file = os.path.join('/Users/amitsingh/Desktop/deek/fastapiselenium/111111gitlabproject/fastapicharts/data/1repo_metadata.json')
    if not os.path.exists(json_file):
        raise HTTPException(status_code=404, detail=f"File `{json_file}` not found")
    with open(json_file) as f:
        repo_model = json.load(f)
    return repo_model['files']

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, id: str = "default"):
    # Render main page template, pass repo_id
    return templates.TemplateResponse("dashboard.html", {"request": request, "repo_id": id})

@app.get("/data/lib-count")
async def lib_count(id: str = "default"):
    file_data_list = load_repo_data(1)

    library_count = defaultdict(int)
    for file in file_data_list:
        for imp in file["imports"]:
            imp = imp.split(".")[-1]
            library_count[imp] += 1

    lib_df = pd.DataFrame(library_count.items(), columns=["Library", "Count"]).sort_values(by="Count", ascending=False).head(10)
    fig = px.bar(lib_df, x="Library", y="Count", color="Count", title="Top Imports")
    fig.update_layout(xaxis_tickangle=-45)
    return JSONResponse(content=fig.to_json())

@app.get("/data/func-stats")
async def func_stats(id: str = "default"):
    file_data_list = load_repo_data(id)
    class_func_count = []
    for file in file_data_list:
        for clazz in file["classes"]:
            class_func_count.append({"Class": clazz, "Functions": len(file["functions"])})
    func_df = pd.DataFrame(class_func_count).sort_values(by="Functions", ascending=False).head(10)
    fig = px.bar(func_df, x="Class", y="Functions", color="Functions", title="Function Count by Class")
    return JSONResponse(content=fig.to_json())

@app.get("/data/var-stats")
async def var_stats(id: str = "default"):
    file_data_list = load_repo_data(id)
    class_var_count = []
    for file in file_data_list:
        for clazz in file["classes"]:
            class_var_count.append({"Class": clazz, "Variables": len(file["variables"])})
    var_df = pd.DataFrame(class_var_count).sort_values(by="Variables", ascending=False).head(10)
    fig = px.bar(var_df, x="Class", y="Variables", color="Variables", title="Variable Count by Class")
    return JSONResponse(content=fig.to_json())

@app.get("/data/sankey")
async def sankey(id: str = "default"):
    file_data_list = load_repo_data(id)

    label_map = {}
    source_indices = []
    target_indices = []
    values = []
    labels = []
    idx = 0

    def get_label_index(label):
        nonlocal idx
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

    dependency_counter = defaultdict(int)
    for s, t in zip(source_indices, target_indices):
        dependency_counter[(s, t)] += 1

    top_n = 20
    sorted_links = sorted(dependency_counter.items(), key=lambda x: x[1], reverse=True)[:top_n]

    sankey_source = [src for (src, tgt), _ in sorted_links]
    sankey_target = [tgt for (src, tgt), _ in sorted_links]
    sankey_value = [val for (_, _), val in sorted_links]

    def shorten(label):
        if label.endswith(".java"):
            label = label.replace(".java", "")
        return label if len(label) <= 25 else f"{label[:10]}...{label[-10:]}"
    
    shortened_labels = [shorten(label) for label in labels]

    def hex_to_rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{alpha})'

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
    return JSONResponse(content=fig_sankey.to_json())

@app.get("/data/pie")
async def pie(id: str = "default"):
    file_data_list = load_repo_data(id)
    all_imports = [imp.split(".")[-1] for file in file_data_list for imp in file["imports"]]
    import_freq = pd.Series(all_imports).value_counts().reset_index()
    import_freq.columns = ["Library", "Count"]
    top_20_imports = import_freq.head(20)

    fig_pie = px.pie(
        top_20_imports,
        names="Library",
        values="Count",
        title="🍰 Top 20 Library Imports (Most Used)"
    )
    return JSONResponse(content=fig_pie.to_json())

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)
