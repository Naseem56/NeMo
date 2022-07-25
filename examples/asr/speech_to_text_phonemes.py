# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO: run examples comment

import pytorch_lightning as pl
from omegaconf import OmegaConf

from nemo.collections.asr.models.ctc_phoneme_models import EncDecCTCModel, EncDecCTCModelPhoneme
from nemo.core.config import hydra_runner
from nemo.utils import logging
from nemo.utils.exp_manager import exp_manager


@hydra_runner(config_path="conf/quartznet", config_name="phoneme_quartznet_15x5")
def main(cfg):
    logging.info(f'Hydra config: {OmegaConf.to_yaml(cfg)}')

    trainer = pl.Trainer(**cfg.trainer)
    exp_manager(trainer, cfg.get("exp_manager", None))

    asr_model = EncDecCTCModelPhoneme(cfg=cfg.model, trainer=trainer)

    # Initialize the weights of the model from another model, if provided via config
    non_phoneme_ckpt_path = cfg.get('init_from_non_phoneme_model', None)
    ckpt_path = cfg.get('init_from_nemo_model', None)

    if non_phoneme_ckpt_path:
        ckpt_model = EncDecCTCModel.restore_from(non_phoneme_ckpt_path)
        ckpt_model.change_vocabulary(list(asr_model.tokenizer.vocab.keys()))
        asr_model.load_state_dict(ckpt_model.state_dict(), strict=False)
        del ckpt_model
    elif ckpt_path:
        ckpt_model = EncDecCTCModelPhoneme.restore_from(ckpt_path)
        ckpt_model.change_vocabulary(cfg.model['phonemes_file'])
        asr_model.load_state_dict(ckpt_model.state_dict(), strict=False)
        del ckpt_model

    trainer.fit(asr_model)

    if hasattr(cfg.model, 'test_ds') and cfg.model.test_ds.manifest_filepath is not None:
        gpu = 1 if cfg.trainer.gpus != 0 else 0
        test_trainer = pl.Trainer(
            gpus=gpu,
            precision=trainer.precision,
            amp_level=trainer.accelerator_connector.amp_level,
            amp_backend=cfg.trainer.get("amp_backend", "native"),
        )
        if asr_model.prepare_test(test_trainer):
            test_trainer.test(asr_model)

    # asr_model.save_to('/home/jocelynh/Desktop/checkpoints/phoneme_asr//finetune_qn_base_50ep_2021-07-02/checkpoints/finetune_asr_phonemes.nemo')


if __name__ == '__main__':
    main()