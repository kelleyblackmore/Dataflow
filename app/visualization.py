"""
Visualization module for creating data flow diagrams.
"""

import plotly.graph_objects as go
from typing import List
import html

from app.models import TransferStatus

# Maximum number of recent transfers to display
MAX_RECENT_TRANSFERS = 10


def create_flow_diagram(transfers: List[TransferStatus]) -> str:
    """
    Create an interactive flow diagram showing data transfers.

    Args:
        transfers: List of transfer status objects

    Returns:
        HTML string with embedded Plotly diagram
    """
    if not transfers:
        return _create_empty_diagram()

    # Collect unique databases and tables
    nodes = {}
    edges = []

    node_id = 0

    # Process each transfer
    for transfer in transfers:
        # Create source node if not exists
        source_key = f"source_{transfer.source_table}"
        if source_key not in nodes:
            nodes[source_key] = {
                "id": node_id,
                "label": f"Source\n{transfer.source_table}",
                "type": "source",
            }
            node_id += 1

        # Create destination node if not exists
        dest_key = f"dest_{transfer.destination_table}"
        if dest_key not in nodes:
            nodes[dest_key] = {
                "id": node_id,
                "label": f"Destination\n{transfer.destination_table}",
                "type": "destination",
            }
            node_id += 1

        # Add edge
        edges.append(
            {
                "source": nodes[source_key]["id"],
                "target": nodes[dest_key]["id"],
                "label": f"{transfer.records_transferred} records",
                "status": transfer.status,
            }
        )

    # Create Plotly figure
    fig = _create_plotly_diagram(nodes, edges)

    # Convert to HTML
    html = fig.to_html(include_plotlyjs="cdn", div_id="flow-diagram")

    # Wrap in styled HTML
    return _wrap_diagram_html(html, transfers)


def _create_plotly_diagram(nodes: dict, edges: list) -> go.Figure:
    """
    Create a Plotly Sankey diagram.

    Args:
        nodes: Dictionary of nodes
        edges: List of edges

    Returns:
        Plotly Figure object
    """
    # Prepare data for Sankey diagram
    node_labels = []
    node_colors = []

    for key, node in nodes.items():
        node_labels.append(node["label"])
        if node["type"] == "source":
            node_colors.append("lightblue")
        else:
            node_colors.append("lightgreen")

    # Prepare edges
    sources = []
    targets = []
    values = []
    edge_colors = []

    for edge in edges:
        sources.append(edge["source"])
        targets.append(edge["target"])
        # Extract number from label
        label = edge["label"]
        try:
            value = int(label.split()[0])
        except (ValueError, IndexError):
            value = 1
        values.append(value)

        # Color based on status
        if edge["status"] == "completed":
            edge_colors.append("rgba(0, 255, 0, 0.3)")
        elif edge["status"] == "failed":
            edge_colors.append("rgba(255, 0, 0, 0.3)")
        else:
            edge_colors.append("rgba(128, 128, 128, 0.3)")

    # Create Sankey diagram
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=node_labels,
                    color=node_colors,
                ),
                link=dict(
                    source=sources, target=targets, value=values, color=edge_colors
                ),
            )
        ]
    )

    fig.update_layout(title_text="Data Flow Diagram", font_size=12, height=600)

    return fig


def _create_empty_diagram() -> str:
    """Create an empty diagram message."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Flow Diagram</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
                text-align: center;
            }
            .message {
                background-color: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="message">
            <h1>📊 No Data Flows Yet</h1>
            <p>No data transfers have been performed yet. Start a transfer to see the flow diagram.</p>
            <p>Use the <code>/transfer</code> endpoint to transfer data between databases.</p>
        </div>
    </body>
    </html>
    """
    return html


def _wrap_diagram_html(plotly_html: str, transfers: List[TransferStatus]) -> str:
    """
    Wrap the Plotly diagram in a styled HTML page.

    Args:
        plotly_html: HTML from Plotly
        transfers: List of transfers for summary

    Returns:
        Complete HTML page
    """
    # Create summary table with HTML escaping to prevent XSS
    summary_rows = ""
    for transfer in transfers[-MAX_RECENT_TRANSFERS:]:
        status_color = (
            "green"
            if transfer.status == "completed"
            else "red" if transfer.status == "failed" else "orange"
        )
        # Escape all user-provided data to prevent XSS attacks
        summary_rows += f"""
        <tr>
            <td>{html.escape(transfer.transfer_id)}</td>
            <td>{html.escape(transfer.source_table)}</td>
            <td>{html.escape(transfer.destination_table)}</td>
            <td>{transfer.records_transferred}</td>
            <td style="color: {status_color}; font-weight: bold;">{html.escape(transfer.status)}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Flow Diagram</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                text-align: center;
            }}
            .summary {{
                margin: 20px 0;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .diagram {{
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 Data Flow Visualization</h1>

            <div class="summary">
                <h2>Recent Transfers</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Transfer ID</th>
                            <th>Source</th>
                            <th>Destination</th>
                            <th>Records</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {summary_rows}
                    </tbody>
                </table>
            </div>

            <div class="diagram">
                {plotly_html}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
