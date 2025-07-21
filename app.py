import dash
from dash import dcc, html, Input, Output, State
import dash_cytoscape as cyto
import requests

cyto.load_extra_layouts()

app = dash.Dash(__name__)
server = app.server

STRING_API_BASE = "https://string-db.org/api"
MAX_GENES = 10

def string_get_protein_id(gene_symbol, species=9606):
    url = f"{STRING_API_BASE}/json/get_string_ids"
    params = {"identifiers": gene_symbol, "species": species}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data:
        return data[0]["stringId"]
    return None

def string_get_interactors(string_id, species=9606, required_score=700):
    url = f"{STRING_API_BASE}/json/network"
    params = {"identifiers": string_id, "species": species, "required_score": required_score}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    interactors = set()
    for edge in data:
        interactors.add(edge["preferredName_A"])
        interactors.add(edge["preferredName_B"])
    return interactors

def get_pathways_for_gene(gene_symbol):
    try:
        gene_symbol = gene_symbol.upper()
        find_url = f"https://rest.kegg.jp/find/genes/{gene_symbol}"
        find_resp = requests.get(find_url, timeout=10)
        find_resp.raise_for_status()

        kegg_gene_id = None
        for line in find_resp.text.strip().split("\n"):
            if line.startswith("hsa:"):
                kegg_gene_id = line.split("\t")[0]
                break

        if not kegg_gene_id:
            return []

        link_url = f"https://rest.kegg.jp/link/pathway/{kegg_gene_id}"
        link_resp = requests.get(link_url, timeout=10)
        link_resp.raise_for_status()
        pathway_ids = [line.split("\t")[1] for line in link_resp.text.strip().splitlines()]

        pathways = []
        for pid in pathway_ids:
            get_url = f"https://rest.kegg.jp/get/{pid}"
            r = requests.get(get_url, timeout=10)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if line.startswith("NAME"):
                        pathway_name = line.replace("NAME", "").strip()
                        pathways.append(pathway_name)
                        break
        return pathways

    except Exception as e:
        print(f"KEGG error for {gene_symbol}: {e}")
        return []

def build_network(gene_list, keyword=""):
    elements = []
    seen_nodes = set()
    seen_edges = set()
    gene_to_interactors = {}

    for gene in gene_list:
        gene = gene.upper().strip()
        if not gene:
            continue

        if gene not in seen_nodes:
            elements.append({'data': {'id': gene, 'label': f"{gene} (gene)", 'type': 'gene', 'subtype': 'input_gene'}})
            seen_nodes.add(gene)

        string_id = string_get_protein_id(gene)
        if not string_id:
            continue

        interactors = string_get_interactors(string_id)
        gene_to_interactors[gene] = interactors

        for interactor in interactors:
            interactor = interactor.upper()
            if interactor not in seen_nodes:
                elements.append({'data': {'id': interactor, 'label': f"{interactor} (protein)", 'type': 'protein'}})
                seen_nodes.add(interactor)

            edge_key = (gene, interactor)
            if edge_key not in seen_edges:
                elements.append({'data': {'source': gene, 'target': interactor}})
                seen_edges.add(edge_key)

        for symbol in [gene] + list(interactors):
            symbol = symbol.upper().strip()
            if not symbol:
                continue

            pathways = get_pathways_for_gene(symbol)
            for p in pathways:
                if keyword and keyword.lower() not in p.lower():
                    continue
                if p not in seen_nodes:
                    elements.append({'data': {'id': p, 'label': f"{p} (pathway)", 'type': 'pathway'}})
                    seen_nodes.add(p)
                edge_key = (symbol, p)
                if edge_key not in seen_edges:
                    elements.append({'data': {'source': symbol, 'target': p}})
                    seen_edges.add(edge_key)

    for i, gene1 in enumerate(gene_list):
        for gene2 in gene_list[i + 1:]:
            inter1 = gene_to_interactors.get(gene1.upper(), set())
            inter2 = gene_to_interactors.get(gene2.upper(), set())
            if inter1 & inter2:
                edge_key = (gene1, gene2)
                if edge_key not in seen_edges:
                    elements.append({'data': {'source': gene1, 'target': gene2}})
                    seen_edges.add(edge_key)

    return elements

# === App Layout ===
app.layout = html.Div([
    html.H2("🔬 PathLinker: Gene → Protein → Pathway Explorer"),

    dcc.Input(id="gene-input", type="text", placeholder="e.g. TP53, BRCA1", style={"width": "60%"}),
    dcc.Input(id="keyword-input", type="text", placeholder="Optional pathway keyword", style={"width": "35%"}),
    html.Button("Submit", id="submit-btn", style={"margin": "10px"}),

    html.Div([
        html.Label("Graph Layout:"),
        dcc.Dropdown(
            id='layout-dropdown',
            options=[
                {"label": "Cose (force-directed)", "value": "cose"},
                {"label": "Circle", "value": "circle"},
                {"label": "Grid", "value": "grid"},
                {"label": "Breadthfirst", "value": "breadthfirst"},
                {"label": "Concentric", "value": "concentric"},
            ],
            value="cose",
            clearable=False,
            style={"width": "300px", "marginBottom": "15px"}
        ),
    ]),

    html.Div([
        html.Label("Node Types to Show:"),
        dcc.Checklist(
            id='node-type-filter',
            options=[
                {'label': 'Input Genes', 'value': 'gene'},
                {'label': 'Proteins', 'value': 'protein'},
                {'label': 'Pathways', 'value': 'pathway'}
            ],
            value=['gene', 'protein', 'pathway'],
            labelStyle={'display': 'inline-block', 'marginRight': '15px'}
        )
    ], style={"marginBottom": "15px"}),

    html.Div(id="error-message", style={"color": "red"}),

    cyto.Cytoscape(
        id="cytoscape-network",
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '750px'},
        elements=[],
        stylesheet=[
            {'selector': 'node[type="gene"][subtype="input_gene"]',
             'style': {'background-color': '#1f77b4', 'label': 'data(label)', 'shape': 'ellipse', 'border-width': 3, 'border-color': '#000'}},
            {'selector': 'node[type="protein"]',
             'style': {'background-color': '#2ca02c', 'label': 'data(label)', 'shape': 'roundrectangle'}},
            {'selector': 'node[type="pathway"]',
             'style': {'background-color': '#d62728', 'label': 'data(label)', 'shape': 'hexagon'}},
            {'selector': 'edge',
             'style': {'line-color': '#aaa'}}
        ]
    ),

    html.Div([
        html.H4("Legend"),
        html.Div([
            html.Span(style={'backgroundColor': '#1f77b4', 'display': 'inline-block', 'width': '15px', 'height': '15px', 'marginRight': '5px'}),
            "Input Gene",
        ]),
        html.Div([
            html.Span(style={'backgroundColor': '#2ca02c', 'display': 'inline-block', 'width': '15px', 'height': '15px', 'marginRight': '5px'}),
            "Protein Interactor",
        ]),
        html.Div([
            html.Span(style={'backgroundColor': '#d62728', 'display': 'inline-block', 'width': '15px', 'height': '15px', 'marginRight': '5px'}),
            "Pathway",
        ]),
    ], style={"marginTop": "20px"})
])

# === Callback ===
@app.callback(
    Output("cytoscape-network", "elements"),
    Output("cytoscape-network", "layout"),
    Output("error-message", "children"),
    Input("submit-btn", "n_clicks"),
    State("gene-input", "value"),
    State("keyword-input", "value"),
    State("layout-dropdown", "value"),
    State("node-type-filter", "value")
)
def update_network(n_clicks, gene_input, keyword, selected_layout, node_types):
    if not gene_input:
        return [], {'name': selected_layout}, "⚠️ Please enter at least one gene symbol."

    gene_list = [g.strip().upper() for g in gene_input.split(",") if g.strip()]
    if len(gene_list) > MAX_GENES:
        return [], {'name': selected_layout}, f"⚠️ Limit to {MAX_GENES} genes."

    try:
        elements = build_network(gene_list, keyword.strip().lower() if keyword else "")

        # Filter node types
        filtered_elements = []
        for el in elements:
            if 'source' in el['data']:  # edge
                filtered_elements.append(el)
            else:
                node_type = el['data'].get('type')
                if node_type in node_types:
                    filtered_elements.append(el)

        if len(filtered_elements) <= 1:
            return [], {'name': selected_layout}, "❌ No matching nodes after filtering."

        return filtered_elements, {'name': selected_layout}, ""

    except Exception as e:
        return [], {'name': selected_layout}, f"❌ Error: {str(e)}"

# === Run App ===
if __name__ == "__main__":
    app.run(debug=True)
