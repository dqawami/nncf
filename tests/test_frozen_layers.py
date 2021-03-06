import pytest

from nncf.utils import get_all_modules_by_type
from tests.helpers import create_compressed_model_and_algo_for_test, TwoConvTestModel, get_empty_config

FIRST_NNCF_CONV_SCOPE = 'TwoConvTestModel/Sequential[features]/Sequential[0]/NNCFConv2d[0]'
FIRST_CONV_SCOPE = 'TwoConvTestModel/Sequential[features]/Sequential[0]/Conv2d[0]'


class AlgoBuilder:
    def __init__(self):
        self._config = {}

    def name(self, algo_name):
        self._config['algorithm'] = algo_name
        return self

    def int4(self):
        self._config.update({'weights': {'bits': 4}, 'activations': {'bits': 4}})
        return self

    def mixed_precision(self):
        self._config.update({'initializer': {'precision': {'type': 'manual'}}})
        return self

    def pruning(self):
        self._config.update({'algorithm': 'filter_pruning',
                             'params': {
                                 'prune_first_conv': True,
                                 'prune_last_conv': True
                             }})
        return self

    def ignore_first_conv(self, is_nncf=False):
        self._config['ignored_scopes'] = FIRST_NNCF_CONV_SCOPE if is_nncf else FIRST_CONV_SCOPE
        return self

    def target_first_conv(self, is_nncf=False):
        self._config['target_scopes'] = FIRST_NNCF_CONV_SCOPE if is_nncf else FIRST_CONV_SCOPE
        return self

    def get_config(self):
        return self._config


class FrozenLayersTestStruct:
    def __init__(self, name='No_name'):
        self.name = name
        self.config_update = {'target_device': 'VPU', 'compression': []}
        self.raising_error = False
        self.printing_warning = False
        self._freeze_all = False

    def freeze_all(self):
        self._freeze_all = True
        return self

    def create_config(self):
        config = get_empty_config()
        config.update(self.config_update)
        return config

    def create_frozen_model(self):
        """ Freeze first conv by default and freeze all convs if _freeze_all is True"""
        model = TwoConvTestModel()
        num_convs_to_freeze = -1 if self._freeze_all else 1
        for i, module in enumerate(get_all_modules_by_type(model, 'Conv2d').values()):
            if i < num_convs_to_freeze or num_convs_to_freeze == -1:
                module.weight.requires_grad = False
        return model

    def add_algo(self, algo_builder: AlgoBuilder):
        self.config_update['compression'].append(algo_builder.get_config())
        return self

    def ignore_first_conv(self, is_nncf=False):
        self.config_update['ignored_scopes'] = FIRST_NNCF_CONV_SCOPE if is_nncf else FIRST_CONV_SCOPE
        return self

    def target_first_conv(self, is_nncf=False):
        self.config_update['target_scopes'] = FIRST_NNCF_CONV_SCOPE if is_nncf else FIRST_CONV_SCOPE
        return self

    def expects_error(self):
        self.raising_error = True
        return self

    def expects_warning(self):
        self.printing_warning = True
        return self


TEST_PARAMS = [
    FrozenLayersTestStruct(name='8_bits_quantization')
        .add_algo(AlgoBuilder().name('quantization'))
        .expects_warning(),
    FrozenLayersTestStruct(name='8_bits_quantization_all_frozen')
        .add_algo(AlgoBuilder().name('quantization'))
        .freeze_all()
        .expects_warning(),
    FrozenLayersTestStruct(name='8_bits_quantization_with_frozen_not_wrapped')
        .add_algo(AlgoBuilder().name('quantization'))
        .ignore_first_conv(),
    FrozenLayersTestStruct(name='8_bits_quantization_with_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('quantization').ignore_first_conv()),
    FrozenLayersTestStruct(name='8_bits_quantization_with_frozen_in_ignored_nncf_scope')
        .add_algo(AlgoBuilder().name('quantization').ignore_first_conv(is_nncf=True)),
    FrozenLayersTestStruct(name='8_bits_quantization_with_not_all_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('quantization').ignore_first_conv(is_nncf=True))
        .freeze_all()
        .expects_warning(),
    FrozenLayersTestStruct(name='mixed_precision_quantization')
        .add_algo(AlgoBuilder().name('quantization').mixed_precision())
        .expects_error(),
    FrozenLayersTestStruct(name='mixed_precision_quantization_with_frozen_not_wrapped')
        .add_algo(AlgoBuilder().name('quantization').mixed_precision())
        .ignore_first_conv(),
    FrozenLayersTestStruct(name='mixed_precision_quantization_with_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('quantization').mixed_precision().ignore_first_conv(is_nncf=True)),
    FrozenLayersTestStruct(name='mixed_precision_quantization_with_not_all_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('quantization').mixed_precision())
        .ignore_first_conv()
        .freeze_all()
        .expects_error(),
    FrozenLayersTestStruct(name='mixed_precision_quantization_with_frozen_in_target_scope')
        .add_algo(AlgoBuilder().name('quantization').mixed_precision())
        .target_first_conv()
        .expects_error(),
    FrozenLayersTestStruct(name='4_bits_quantization')
        .add_algo(AlgoBuilder().name('quantization').int4())
        .expects_error(),
    FrozenLayersTestStruct(name='4_bits_quantization_with_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('quantization').int4().ignore_first_conv()),
    FrozenLayersTestStruct(name='4_bits_quantization_with_not_all_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('quantization').int4().ignore_first_conv())
        .freeze_all()
        .expects_error(),
    FrozenLayersTestStruct(name='magnitude_sparsity')
        .add_algo(AlgoBuilder().name('magnitude_sparsity'))
        .expects_error(),
    FrozenLayersTestStruct(name='rb_sparsity')
        .add_algo(AlgoBuilder().name('rb_sparsity'))
        .expects_error(),
    FrozenLayersTestStruct(name='rb_sparsity_8_bits_quantization_with_frozen')
        .add_algo(AlgoBuilder().name('rb_sparsity'))
        .add_algo(AlgoBuilder().name('quantization'))
        .expects_error(),
    FrozenLayersTestStruct(name='rb_sparsity_8_bits_quantization_with_frozen_sparsity_in_ignored_scope')
        .add_algo(AlgoBuilder().name('rb_sparsity').ignore_first_conv())
        .add_algo(AlgoBuilder().name('quantization'))
        .expects_warning(),
    FrozenLayersTestStruct(name='const_sparsity')
        .add_algo(AlgoBuilder().name('const_sparsity'))
        .expects_warning(),
    FrozenLayersTestStruct(name='const_sparsity_8_bits_quantization')
        .add_algo(AlgoBuilder().name('const_sparsity'))
        .add_algo(AlgoBuilder().name('quantization'))
        .expects_warning(),
    FrozenLayersTestStruct(name='const_sparsity_4_bits_quantization')
        .add_algo(AlgoBuilder().name('const_sparsity'))
        .add_algo(AlgoBuilder().name('quantization').int4())
        .expects_error().expects_warning(),
    FrozenLayersTestStruct(name='const_sparsity_4_bits_quantization_with_frozen_int4_in_ignored_scope')
        .add_algo(AlgoBuilder().name('const_sparsity'))
        .add_algo(AlgoBuilder().name('quantization').int4().ignore_first_conv())
        .expects_warning(),
    FrozenLayersTestStruct(name='rb_sparsity_4_bits_quantization')
        .add_algo(AlgoBuilder().name('rb_sparsity'))
        .add_algo(AlgoBuilder().name('quantization').int4())
        .expects_error(),
    FrozenLayersTestStruct(name='rb_sparsity_4_bits_quantization_with_int4_ignored')
        .add_algo(AlgoBuilder().name('rb_sparsity'))
        .add_algo(AlgoBuilder().name('quantization').int4().ignore_first_conv())
        .expects_error(),
    FrozenLayersTestStruct(name='rb_sparsity_4_bits_quantization_with_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('rb_sparsity'))
        .add_algo(AlgoBuilder().name('quantization').int4())
        .ignore_first_conv(),
    FrozenLayersTestStruct(name='filter_pruning_with_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('filter_pruning').ignore_first_conv()),
    FrozenLayersTestStruct(name='filter_pruning_with_frozen_in_ignored_scope')
        .add_algo(AlgoBuilder().name('filter_pruning'))
        .expects_error(),
    FrozenLayersTestStruct(name='binarization')
        .add_algo(AlgoBuilder().name('binarization'))
        .expects_error()
]


@pytest.mark.parametrize('params', TEST_PARAMS, ids=[p.name for p in TEST_PARAMS])
def test_frozen_layers(_nncf_caplog, params):
    model = params.create_frozen_model()
    config = params.create_config()

    if params.raising_error:
        with pytest.raises(RuntimeError):
            __, _ = create_compressed_model_and_algo_for_test(model, config)
    else:
        __, _ = create_compressed_model_and_algo_for_test(model, config)
    if params.printing_warning:
        assert 'Frozen layers' in _nncf_caplog.text
