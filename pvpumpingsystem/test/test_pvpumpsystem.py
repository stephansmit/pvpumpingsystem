# -*- coding: utf-8 -*-
"""
@author: Tanguy Lunel
"""

import pytest
import numpy as np
import os
import inspect

import pvpumpingsystem.pump as pp
import pvpumpingsystem.mppt as mppt
import pvpumpingsystem.pipenetwork as pn
import pvpumpingsystem.reservoir as rv
import pvpumpingsystem.consumption as cs
import pvpumpingsystem.pvpumpsystem as pvps
import pvpumpingsystem.pvgeneration as pvgen

test_dir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))


@pytest.fixture
def pvps_set_up():

    pvgen1 = pvgen.PVGeneration(
            # Weather data
            weather_data_and_metadata=(
                    os.path.join(test_dir,
                                 '../data/weather_files/CAN_PQ_Montreal'
                                 '.Intl.AP.716270_CWEC_truncated.epw')),

            # PV array parameters
            pv_module_name='kyocera solar KU270 6MCA',
            price_per_watt=1,  # in US dollars
            surface_tilt=45,  # 0 = horizontal, 90 = vertical
            surface_azimuth=180,  # 180 = South, 90 = East
            albedo=0,  # between 0 and 1
            modules_per_string=2,
            strings_in_parallel=2,
            # PV module glazing parameters (not always given in specs)
            glass_params={'K': 4,  # extinction coefficient [1/m]
                          'L': 0.002,  # thickness [m]
                          'n': 1.526},  # refractive index
            racking_model='open_rack',  # or'close_mount' or 'insulated_back'

            # Models used (check pvlib.modelchain for all available models)
            orientation_strategy=None,  # or 'flat' or 'south_at_latitude_tilt'
            clearsky_model='ineichen',
            transposition_model='haydavies',
            solar_position_method='nrel_numpy',
            airmass_model='kastenyoung1989',
            dc_model='desoto',  # 'desoto' or 'cec' only
            ac_model='pvwatts',
            aoi_model='physical',
            spectral_model='no_loss',
            temperature_model='sapm',
            losses_model='pvwatts'
            )
    pvgen1.run_model()

    mppt1 = mppt.MPPT(efficiency=1,
                      price=200)

    pump_testfile = os.path.join(test_dir,
                                 '../data/pump_files/SCB_10_150_120_BL.txt')
    pump1 = pp.Pump(path=pump_testfile,
                    modeling_method='arab')

    pipes1 = pn.PipeNetwork(h_stat=10, l_tot=100, diam=0.08,
                            material='plastic', optimism=True)

    reserv1 = rv.Reservoir()

    consum1 = cs.Consumption(constant_flow=1)

    pvps1 = pvps.PVPumpSystem(pvgen1,
                              pump1,
                              coupling='mppt',
                              mppt=mppt1,
                              pipes=pipes1,
                              consumption=consum1,
                              reservoir=reserv1)
    return pvps1


def test_calc_flow_mppt_with_friction(pvps_set_up):
    """Test the computing of flows in the case coupled with mppt.
    """
    pvps_set_up.coupling = 'mppt'
    pvps_set_up.calc_flow(friction=True, atol=0.1, stop=24)
    Q = pvps_set_up.flow.Qlpm.values
    Q_expected = np.array([0., 0., 0., 0., 0., 0., 0., 0.,
                           34.02, 52.98, 59.32, 61.18,
                           44.91, 42.06, 34.50, 17.52,
                           0., 0., 0., 0., 0., 0., 0., 0.])
    np.testing.assert_allclose(Q, Q_expected, rtol=0.1)


def test_calc_flow_mppt(pvps_set_up):
    """Test the computing of flows in the case coupled with mppt, but
    without consideration of the friction head.
    """
    pvps_set_up.coupling = 'mppt'
    pvps_set_up.calc_flow(friction=False, stop=24)
    Q = pvps_set_up.flow.Qlpm.values
    Q_expected = np.array([0., 0., 0., 0., 0., 0., 0., 0.,
                           34.06, 53.02, 59.37, 61.22,
                           44.95, 42.10, 34.53, 17.53,
                           0., 0., 0., 0., 0., 0., 0., 0.])
    np.testing.assert_allclose(Q, Q_expected, rtol=0.1)


def test_calc_flow_direct(pvps_set_up):
    """Test the computing of flows when pump and pv are directly coupled.
    """
    import warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    pvps_set_up.coupling = 'direct'
    pvps_set_up.calc_flow(friction=True, atol=0.1, stop=24)
    Q = pvps_set_up.flow.Qlpm.values
    Q_expected = np.array([0., 0., 0., 0., 0., 0., 0., 0.,
                           26.7413, 28.6602, 29.1504, 29.5732,
                           28.6143, 28.3941, 27.3603, np.nan,
                           0, 0., 0., 0., 0., 0., 0., 0.])
    np.testing.assert_allclose(Q, Q_expected, rtol=1)


def test_operating_point(pvps_set_up):
    """Test the ability of code to find the operating point between
    pump and pv array when directly-coupled.
    """
    df_iv = pvps_set_up.operating_point()
    arr_iv = np.array(df_iv[11:19], dtype=float)
    arr_iv_expected = np.array([[3.1552, 75.1672],
                                [3.0930, 74.2068],
                                [3.0753, 73.9332],
                                [2.9869, 72.5665],
                                [np.nan, np.nan],
                                [0., 0.],
                                [0., 0.],
                                [0., 0.]])
    np.testing.assert_allclose(arr_iv, arr_iv_expected, rtol=1)


def test_financial_analysis(pvps_set_up):
    """Test the computation of financial outputs.
    """
    pvps_set_up.run_model(labour_price_coefficient=0.5,
                          discount_rate=0.02, opex=500,
                          lifespan_pv=30, lifespan_mppt=14, lifespan_pump=12)
    invest_and_npv = (pvps_set_up.initial_investment, pvps_set_up.npv)
    invest_and_npv_expected = (3565.56, 17756.26)
    np.testing.assert_allclose(invest_and_npv, invest_and_npv_expected,
                               rtol=0.01)


if __name__ == '__main__':
    # runs all the tests in this module
    pytest.main(['-s', 'test_pvpumpsystem.py'])
