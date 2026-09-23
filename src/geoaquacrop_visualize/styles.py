"""Style constants, button/dropdown style factories, and sidebar widgets."""

from dash import html

from .config import MAP_VARIABLES, DAILY_VARIABLES

def btn_style(active, color):
    """
    Generate an inline style dict for a toggle button.

    Parameters
    ----------
    active : bool
        If ``True``, the button is rendered with a filled background using
        the palette's border colour and white text. If ``False``, it uses
        the light background colour with dark text.
    color : str
        Named palette key. One of ``'blue'``, ``'green'``, ``'orange'``,
        ``'purple'``, ``'teal'``, ``'red'``.

    Returns
    -------
    dict
        CSS property dict suitable for use as a Dash component ``style``
        argument.
    """

    palette = {
        'blue':   ('#3d5a8a', '#eef2f7'),
        'green':  ('#4caf50', '#e8f4ea'),
        'orange': ('#e65100', '#fff3e0'),
        'purple': ('#6a1b9a', '#f3e5f5'),
        'teal':   ('#00796b', '#e0f2f1'),
        'red':    ('#c0392b', '#fdecea'),
    }
    border, bg = palette[color]
    base = dict(padding='5px 13px', margin='2px', borderRadius='4px',
                cursor='pointer', fontSize='12px',
                fontFamily='Arial, system-ui, sans-serif',
                border=f'1px solid {border}')
    if active:
        return {**base, 'backgroundColor': border, 'color': 'white'}
    return {**base, 'backgroundColor': bg, 'color': '#333'}

def dd_style(w='80px'):
    """
    Generate an inline style dict for an inline dropdown component.

    Parameters
    ----------
    w : str, optional
        CSS width string for the dropdown. Default is ``'80px'``.

    Returns
    -------
    dict
        CSS property dict for use as a Dash ``dcc.Dropdown`` style argument.
    """

    return {'display': 'inline-block', 'width': w,
            'fontSize': '12px', 'marginLeft': '4px',
            'verticalAlign': 'middle'}

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        STYLE CONSTANTS                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

FONT_STACK  = 'Arial, system-ui, -apple-system, sans-serif'
ACCENT      = "#a6c1eb"
SIDEBAR_BG  = '#f8f9fa'

SIDEBAR_STYLE = {
    'backgroundColor': SIDEBAR_BG,
    'borderRight': '1px solid #dee2e6',
    'padding': '14px 12px 80px',
    'minHeight': '100vh',
    'overflowY': 'auto',
    'overflowX': 'visible',
    'fontFamily': FONT_STACK,
    'position': 'relative',
    'color': "#000000",    
}

RIBBON_STYLE = {
    'display': 'flex',
    'alignItems': 'center',
    'justifyContent': 'space-between',
    'backgroundColor': '#edf2f7',
    'padding': '6px 14px',
    'borderTop': '1px solid #dee2e6',
    'borderBottom': '1px solid #dee2e6',
    'fontFamily': FONT_STACK,
    'fontSize': '12px',
    'color': "#000000",
    'minHeight': '38px',
}

DD_CTRL_STYLE = {'fontFamily': FONT_STACK, 'fontSize': '12px', 'marginBottom': '8px'}

def _sec_hdr(text):
    """
    Create a styled section header ``html.Div`` for the sidebar.

    Renders text in uppercase with increased letter spacing, bold weight,
    and black colour matching the sidebar design system.

    Parameters
    ----------
    text : str
        Header label text, e.g. ``'Map Variable'``.

    Returns
    -------
    dash.html.Div
        Styled div element for use in the sidebar layout.
    """

    return html.Div(text, style={
        'fontFamily': FONT_STACK, 'fontSize': '13px', 'fontWeight': '700',
        'color': "#000000", 'letterSpacing': '1.2px', 'textTransform': 'uppercase',
        'margin': '12px 0 4px',
    })

def _ctrl_label(text):
    """
    Create a styled control label element for the sidebar.

    Parameters
    ----------
    text : str
        Label text, e.g. ``'Crop & Irrigation'``.

    Returns
    -------
    dash.html.Label
        Styled label element displayed as a block above a dropdown control.
    """

    return html.Label(text, style={
        'fontFamily': FONT_STACK, 'fontSize': '11px', 'fontWeight': '600',
        'color': "#000000", 'marginBottom': '2px', 'display': 'block',
    })

# ── Variable group membership ─────────────────────────────────────────────────
_YIELD_VARS = ['Dry yield (tonne/ha)', 'Fresh yield (tonne/ha)',
               'Yield potential (tonne/ha)', 'production_tonnes']
_WATER_VARS = ['Seasonal irrigation (mm)', 'seasonal_precip_mm',
               'seasonal_et_mm', 'seasonal_transpiration_mm', 'total_water_input_mm']
_WP_VARS    = ['wp_et_kg_per_m3', 'rainfall_use_efficiency_kg_per_m3']
_FLUX_VARS  = ['Es', 'EsPot', 'Tr', 'TrPot', 'Infl', 'Runoff', 'DeepPerc']
_SOIL_VARS  = ['Wr']
_CROP_VARS  = ['biomass', 'canopy_cover', 'gdd_cum', 'z_root', 'DryYield']

def _map_dd_opts(keys):
    """
    Build dropdown option dicts for map variable keys.

    Parameters
    ----------
    keys : list of str
        Subset of ``MAP_VARIABLES`` keys to include.

    Returns
    -------
    list of dict
        List of ``{'label': ..., 'value': ...}`` dicts using the variable's
        ``label`` field as the display text.
    """

    return [{'label': MAP_VARIABLES[v]['label'], 'value': v}
            for v in keys if v in MAP_VARIABLES]

def _daily_dd_opts(keys):
    """
    Build dropdown option dicts for daily variable keys.

    Parameters
    ----------
    keys : list of str
        Subset of ``DAILY_VARIABLES`` keys to include.

    Returns
    -------
    list of dict
        List of ``{'label': ..., 'value': ...}`` dicts using the variable's
        ``label`` field as the display text.
    """

    return [{'label': DAILY_VARIABLES[v]['label'], 'value': v}
            for v in keys if v in DAILY_VARIABLES]
