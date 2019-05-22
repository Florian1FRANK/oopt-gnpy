from gnpy.core.utils import load_json


def load_sim_params(path_sim_params):
    sim_params = load_json(path_sim_params)
    return SimParams(**sim_params)

class RamanParameters():
    def __init__(self, params=None):
        self.flag_raman = params['flag_raman']
        self.space_resolution = params['space_resolution']
        self.tolerance = params['tolerance']
        self.verbose = params['verbose']

class NLIParameters():
    def __init__(self, params=None):
        self.nli_method_name = params['nli_method_name']
        self.wdm_grid_size = params['wdm_grid_size']
        self.dispersion_tolerance = params['dispersion_tolerance']
        self.phase_shift_tollerance = params['phase_shift_tollerance']
        self.verbose = params['verbose']

class SimParams():
    def __init__(self, params=None):
        self.list_of_channels_under_test = params['list_of_channels_under_test']
        self.raman_params = RamanParameters(params=params['raman_parametes'])
        self.nli_params = NLIParameters(params=params['nli_parametes'])