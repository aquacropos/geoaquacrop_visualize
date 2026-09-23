"""The Dash application object and its HTML index template.

Kept in its own module so the layout and every callback module can import
``app`` without importing each other.
"""

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>GeoAquaCrop Visualizer</title>
        {%favicon%}
        {%css%}
        <style>
            /* ── Accordion base ─────────────────────────────── */
            .accordion-button {
                padding-left: 25px !important;
                font-family: Arial, system-ui, sans-serif !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                background-color: #f8f9fa !important;
                box-shadow: none !important;
                border: none !important;
                color: #000000 !important;
            }
            .accordion-button.collapsed {
                color: #000000 !important;
                background-color: #f8f9fa !important;
            }
            .accordion-button:not(.collapsed) {
                color: #000000 !important;
                font-weight: 700 !important;
                background-color: #eef2f7 !important;
            }
            /* ── Chevron ─────────────────────────────────────── */
            .accordion-button::after {
                background-image: none !important;
                content: '▾' !important;
                font-size: 13px !important;
                line-height: 1 !important;
                width: auto !important;
                height: auto !important;
                transform: none !important;
                transition: none !important;
                color: #000000 !important;
            }
            .accordion-button.collapsed::after {
                content: '▸' !important;
                transform: none !important;
            }
            /* ── All sidebar text black ──────────────────────── */
            .col-3, .col-3 * {
                color: #000000 !important;
            }
            /* ── Dropdown menu z-index fix ───────────────────── */
            .Select-menu-outer {
                z-index: 9999 !important;
                position: absolute !important;
            }
            /* ── Accordion body ──────────────────────────────── */
            .accordion-body {
                overflow: visible !important;
                padding: 5px 10px 7px !important;
            }
            .accordion-item {
                overflow: visible !important;
            }
            .accordion {
                overflow: visible !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
