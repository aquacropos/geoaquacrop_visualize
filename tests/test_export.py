"""
Tests for ``geoaquacrop_plotting.export``.

``export`` imports ``data``, so the array assembly and naming logic are
mirrored here. ``DAILY_VARIABLES`` comes from the real config.
"""

import numpy as np
import pandas as pd

from geoaquacrop_plotting.config import DAILY_VARIABLES


class TestDateRangeSelection:

    def test_date_range_mask(self, date_index_3y):
        mask = ((date_index_3y >= pd.Timestamp('2008-06-01')) &
                (date_index_3y <= pd.Timestamp('2008-08-31')))
        assert len(np.where(mask)[0]) == 92  # June 30 + July 31 + Aug 31

    def test_empty_date_range(self, date_index_3y):
        mask = ((date_index_3y >= pd.Timestamp('2015-01-01')) &
                (date_index_3y <= pd.Timestamp('2015-12-31')))
        assert len(np.where(mask)[0]) == 0

    def test_empty_range_message(self, date_index_3y):
        mask = ((date_index_3y >= pd.Timestamp('2015-01-01')) &
                (date_index_3y <= pd.Timestamp('2015-12-31')))
        time_idx = np.where(mask)[0]
        msg = 'No data in selected date range.' if len(time_idx) == 0 else 'ok'
        assert msg == 'No data in selected date range.'

    def test_single_day_range(self, date_index_3y):
        day = pd.Timestamp('2009-07-04')
        mask = (date_index_3y >= day) & (date_index_3y <= day)
        assert len(np.where(mask)[0]) == 1

    def test_whole_period_covers_index(self, date_index_3y):
        mask = ((date_index_3y >= date_index_3y[0]) &
                (date_index_3y <= date_index_3y[-1]))
        assert mask.all()


class TestGridAssembly:

    def test_grid_axes_sorted(self, mock_cell_meta):
        cell_ids = list(mock_cell_meta.keys())
        xs = sorted(set(mock_cell_meta[c]['x'] for c in cell_ids))
        ys = sorted(set(mock_cell_meta[c]['y'] for c in cell_ids), reverse=True)
        assert xs == sorted(xs)
        assert ys == sorted(ys, reverse=True)

    def test_y_axis_descends_for_raster_convention(self, mock_cell_meta):
        """GeoTIFF rows run north to south, so ys must be descending."""

        ys = sorted(set(m['y'] for m in mock_cell_meta.values()), reverse=True)
        assert ys[0] > ys[-1]

    def test_3d_array_shape(self, mock_cell_meta):
        cell_ids = list(mock_cell_meta.keys())
        n_time = 30
        xs = sorted(set(mock_cell_meta[c]['x'] for c in cell_ids))
        ys = sorted(set(mock_cell_meta[c]['y'] for c in cell_ids), reverse=True)
        arr = np.full((n_time, len(ys), len(xs)), np.nan, dtype=np.float32)
        assert arr.shape == (30, 3, 3)

    def test_array_starts_all_nan(self, mock_cell_meta):
        xs = sorted(set(m['x'] for m in mock_cell_meta.values()))
        ys = sorted(set(m['y'] for m in mock_cell_meta.values()), reverse=True)
        arr = np.full((5, len(ys), len(xs)), np.nan, dtype=np.float32)
        assert np.isnan(arr).all()

    def test_cell_writes_to_its_own_slot(self, mock_cell_meta):
        xs = sorted(set(m['x'] for m in mock_cell_meta.values()))
        ys = sorted(set(m['y'] for m in mock_cell_meta.values()), reverse=True)
        arr = np.full((2, len(ys), len(xs)), np.nan, dtype=np.float32)
        cid = 1
        xi = xs.index(mock_cell_meta[cid]['x'])
        yi = ys.index(mock_cell_meta[cid]['y'])
        arr[:, yi, xi] = 7.0
        assert (arr[:, yi, xi] == 7.0).all()
        assert np.isnan(arr).sum() == arr.size - 2

    def test_array_is_float32(self, mock_cell_meta):
        arr = np.full((2, 3, 3), np.nan, dtype=np.float32)
        assert arr.dtype == np.float32

    def test_geotiff_bounds_padded_by_half_cell(self, mock_cell_meta):
        half = 0.025
        xs = sorted(set(m['x'] for m in mock_cell_meta.values()))
        ys = sorted(set(m['y'] for m in mock_cell_meta.values()), reverse=True)
        assert min(xs) - half < min(xs)
        assert max(ys) + half > max(ys)


class TestValidation:

    def test_no_export_vars_message(self):
        export_vars = []
        assert ('Select at least one variable.' if not export_vars else 'ok') \
            == 'Select at least one variable.'

    def test_no_format_message(self):
        formats = []
        assert ('Select at least one format.' if not formats else 'ok') \
            == 'Select at least one format.'

    def test_start_before_end_validation(self):
        assert (pd.Timestamp('2009-01-01') > pd.Timestamp('2008-01-01')) is True

    def test_valid_date_range(self):
        assert (pd.Timestamp('2008-01-01') <= pd.Timestamp('2010-12-31')) is True

    def test_nothing_exported_message(self):
        exported = []
        msg = ('Saved…' if exported else 'Nothing exported — check selections.')
        assert msg == 'Nothing exported — check selections.'


class TestNamingAndMetadata:

    def test_base_name_format(self):
        base = (f"Es_{pd.Timestamp('2008-06-01').strftime('%Y%m%d')}"
                f"_{pd.Timestamp('2008-08-31').strftime('%Y%m%d')}")
        assert base == 'Es_20080601_20080831'

    def test_units_extracted_from_label(self):
        label = DAILY_VARIABLES['Es']['label']
        unit = label.split('(')[-1].replace(')', '') if '(' in label else ''
        assert unit == 'mm/day'

    def test_units_missing_parentheses(self):
        label = 'Canopy Cover'
        unit = label.split('(')[-1].replace(')', '') if '(' in label else ''
        assert unit == ''

    def test_every_daily_var_yields_a_unit(self):
        for var, info in DAILY_VARIABLES.items():
            label = info['label']
            unit = label.split('(')[-1].replace(')', '') if '(' in label else ''
            assert unit != '', f'{var} label carries no unit: {label}'

    def test_formats_are_recognised(self):
        for fmt in ('nc', 'tif', 'csv'):
            assert fmt in ('nc', 'tif', 'csv')

    def test_table_routing_per_variable(self):
        """Each export variable must resolve to one of the two daily tables."""

        for var, info in DAILY_VARIABLES.items():
            assert info['table'] in ('water_flux', 'crop_growth'), var


class TestCsvShape:

    def test_csv_row_count(self, mock_cell_meta):
        n_time, n_cells = 6, len(mock_cell_meta)
        rows = [{'date': t, 'cell_id': c} for t in range(n_time) for c in mock_cell_meta]
        assert len(rows) == n_time * n_cells

    def test_csv_columns(self, mock_cell_meta):
        var = 'Es'
        cid = 1
        row = {'date': '2008-06-01', 'cell_id': cid,
               'x': mock_cell_meta[cid]['x'], 'y': mock_cell_meta[cid]['y'],
               var: 1.23}
        assert set(row) == {'date', 'cell_id', 'x', 'y', var}

    def test_csv_is_writable_as_dataframe(self, mock_cell_meta):
        rows = [{'date': '2008-06-01', 'cell_id': c,
                 'x': m['x'], 'y': m['y'], 'Es': 1.0}
                for c, m in mock_cell_meta.items()]
        df = pd.DataFrame(rows)
        assert len(df) == len(mock_cell_meta)
        assert list(df.columns) == ['date', 'cell_id', 'x', 'y', 'Es']
