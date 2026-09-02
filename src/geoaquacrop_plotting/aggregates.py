"""Startup pre-computation of every (crop, variable, aggregation) combination.

Doing this once at import keeps the map callbacks to a dictionary lookup
instead of a groupby on every user interaction.
"""

from .data import summary, crop_irr_list, map_var_keys

crop_var_range = {}
for ci in crop_irr_list:
    crop_var_range[ci] = {}
    for var in map_var_keys:
        sub = summary[summary['crop_irr'] == ci][var]
        if var == 'Seasonal irrigation (mm)':
            vmax = sub.max() if sub.max() > 0 else 1
            crop_var_range[ci][var] = (0, vmax)
        else:
            crop_var_range[ci][var] = (sub.min(), sub.max())


# ── Pre-compute all aggregations at startup ───────────────────────────────────
crop_var_range_all  = {}  # (ci, var, agg) → (vmin, vmax)
precomputed_agg     = {}  # (ci, var, agg) → DataFrame with cell_id + var columns

for ci in crop_irr_list:
    crop_var_range_all[ci] = {}
    sub_ci = summary[summary['crop_irr'] == ci]

    for var in map_var_keys:
        if var not in sub_ci.columns:
            continue
        grouped = sub_ci.groupby('cell_id')[var]

        for agg in ['mean', 'sum']:
            agg_vals = grouped.sum() if agg == 'sum' else grouped.mean()

            # Store colorbar range
            if var == 'Seasonal irrigation (mm)':
                vmax = agg_vals.max() if agg_vals.max() > 0 else 1
                crop_var_range_all[ci][f'{var}_{agg}'] = (0, vmax)
            else:
                crop_var_range_all[ci][f'{var}_{agg}'] = (agg_vals.min(), agg_vals.max())

            # Store aggregated values per cell as a DataFrame
            agg_df = agg_vals.reset_index()
            agg_df.columns = ['cell_id', var]
            agg_df = agg_df.merge(
                summary[['cell_id', 'x', 'y', 'crop', 'irrigation']].drop_duplicates('cell_id'),
                on='cell_id'
            )
            precomputed_agg[(ci, var, agg)] = agg_df
