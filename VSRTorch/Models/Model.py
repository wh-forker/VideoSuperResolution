#  Copyright (c): Wenyi Tang 2017-2019.
#  Author: Wenyi Tang
#  Email: wenyi.tang@intel.com
#  Update Date: 2019 - 3 - 13

import torch
import logging

from ..Framework.Trainer import SRTrainer


class BasicModel:
  """Trainable model wrapper for PyTorch nn.Module objects

  There are 2 built-in attributes:
    - modules: contains a K-V pair of `str: nn.Module`. It will be automatically
      appended if a derived object assign any attribute with `nn.Module` object.
    - opts: contains a K-V pair of `str: optim.Optimizer`. Will be automatically
      appended if a derived object assign any attribute with `optim.Optimizer`.
  """

  def __init__(self, **kwargs):
    self.modules = {}
    self.opts = {}
    self.name = ''
    self._trainer = None

  def __setattr__(self, key, value):
    if key in ('modules', 'opts',):
      if hasattr(self, key):
        raise ValueError(f"Can't overwrite built-in '{key}' of BasicModel")
    if isinstance(value, torch.nn.Module):
      if key in self.modules:
        if self.modules[key] is value:
          return
        else:
          # TODO: why assign twice??
          raise NotImplementedError
      else:
        self.modules[key] = value
        self.name += f'[{key}]'
    if isinstance(value, torch.optim.Optimizer):
      if key in self.opts:
        if self.opts[key] is value:
          return
        else:
          raise NotImplementedError
      else:
        self.opts[key] = value

    return super(BasicModel, self).__setattr__(key, value)

  def trainable_variables(self, name=None):
    _m = self.modules.get(name) if name else self.modules.values()
    _var = []
    for i in _m:
      _var += filter(lambda p: p.requires_grad, i.parameters())
    return _var

  def to_train(self):
    for _m in self.modules.values():
      _m.train()

  def train(self, *args, **kwargs):
    raise NotImplementedError

  def to_eval(self):
    for _m in self.modules.values():
      _m.eval()

  def eval(self, *args, **kwargs):
    raise NotImplementedError

  def display(self):
    num_params = 0
    for m in self.modules.values():
      for p in m.parameters():
        num_params += p.nelement()
    logging.getLogger('VSR').info(f"Total params: {num_params}")

  def cuda(self):
    for i in self.modules:
      if torch.cuda.is_available():
        self.modules[i] = self.modules[i].cuda()

  def export(self, export_dir):
    """export ONNX model.

    Args:
      export_dir: path to save onnx files.
    """

    raise NotImplementedError("Should implement in specific model!")

  @property
  def trainer(self):
    return self._trainer


class SuperResolution(BasicModel):

  def __init__(self, scale, channel, **kwargs):
    super(SuperResolution, self).__init__(**kwargs)
    self.scale = scale
    self.channel = channel
    self._trainer = SRTrainer