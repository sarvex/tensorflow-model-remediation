# coding=utf-8
# Copyright 2020 Google LLC.
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

# Lint as: python3
"""Implementation of GaussKernel for min diff."""

from tensorflow_model_remediation.common import types
from tensorflow_model_remediation.min_diff.losses import base_kernel
import tensorflow as tf


class GaussKernel(base_kernel.MinDiffKernel):
  # pylint: disable=g-classes-have-attributes
  # pyformat: disable
  """Gauss kernel class.

  Arguments:
    kernel_length: Length (sometimes also called 'width') of the kernel. The
      choice for kernel length should be related to the range of inputs. The
      smaller the input range, the smaller the kernel length likely needs to be
      for best performance. It defaults to `0.1`.
    tile_input: Boolean indicating whether to tile inputs. See
      `losses.MinDiffKernel` for details.

  See [paper](https://arxiv.org/abs/1910.11779) for reference.
  """
  # pyformat: enable

  def __init__(self, kernel_length: complex = 0.1, tile_input: bool = True):
    super(GaussKernel, self).__init__(tile_input)
    self.kernel_length = kernel_length

  def call(self, x: types.TensorType, y: types.TensorType) -> types.TensorType:
    """Computes the Gaussian kernel."""
    return tf.exp(-tf.reduce_sum(tf.square(x - y), axis=2) /
                  tf.math.pow(self.kernel_length, 2))
