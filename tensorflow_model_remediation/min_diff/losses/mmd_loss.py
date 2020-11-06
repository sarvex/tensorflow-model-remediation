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
"""Implementation of MMD Loss."""

from typing import Optional, Text

from tensorflow_model_remediation.common import types
from tensorflow_model_remediation.min_diff.losses import base_kernel
from tensorflow_model_remediation.min_diff.losses import base_loss
import tensorflow as tf


class MMDLoss(base_loss.MinDiffLoss):
  # pylint: disable=g-classes-have-attributes
  # pyformat: disable
  """Maximum Mean Discrepency between predictions on two groups of examples.

  Arguments:
    kernel: `losses.MinDiffKernel` instance to be applied on the predictions.
      Defaults to `'gauss'` and it is generally recommended that this be either
      `'gauss'`
      (`min_diff.losses.GaussKernel`) or `'laplace'`
      (`min_diff.losses.LaplaceKernel`).
    predictions_transform: Optional transform function to be applied to the
      predictions. This can be used to smooth out the distributions or limit the
      range of predictions.
    name: Name used for logging and tracking. Defaults to `'mmd_loss'`.

  The Maximum Mean Discrepancy (MMD) is a measure of the distance between the
  distributions of prediction scores on two groups of examples. The metric
  guarantees that the result is 0 if and only if the two distributions it is
  comparing are exactly the same.

  The `membership` input indicates with a numerical value whether
  each example is part of the sensitive group with a numerical value. This
  currently only supports hard membership of `0.0` or `1.0`.

  For more details, see the
  [paper](http://papers.nips.cc/paper/3110-a-kernel-method-for-the-two-sample-problem.pdf).
  """
  # pyformat: enable

  def __init__(
      self,
      kernel: base_kernel.MinDiffKernel = 'gauss',
      predictions_transform: Optional[types.TensorTransformType] = None,
      name: Optional[Text] = None):
    """Initialize an instance of MMDLoss."""
    super(MMDLoss, self).__init__(
        predictions_transform=predictions_transform,
        predictions_kernel=kernel,
        name=name or 'mmd_loss')

  def call(
      self,
      membership: types.TensorType,
      predictions: types.TensorType,
      sample_weight: Optional[types.TensorType] = None) -> types.TensorType:
    """Computes MMD the loss value."""

    membership, predictions, normed_weights = self._preprocess_inputs(
        membership, predictions, sample_weight)
    _, predictions_kernel = self._apply_kernels(membership, predictions)

    weights_ij = tf.matmul(normed_weights, tf.transpose(normed_weights))

    pos_mask = tf.cast(tf.equal(membership, 1.0), tf.float32)
    neg_mask = tf.cast(tf.equal(membership, 0.0), tf.float32)

    pos_mean_mask = tf.matmul(pos_mask, tf.transpose(pos_mask))
    pos_mean_weights = weights_ij * pos_mean_mask
    neg_mean_mask = tf.matmul(neg_mask, tf.transpose(neg_mask))
    neg_mean_weights = weights_ij * neg_mean_mask
    pos_neg_mean_mask = tf.matmul(pos_mask, tf.transpose(neg_mask))
    pos_neg_mean_weights = weights_ij * pos_neg_mean_mask

    pos_mean = tf.math.divide_no_nan(
        tf.reduce_sum(pos_mean_weights * predictions_kernel),
        tf.reduce_sum(pos_mean_weights))
    neg_mean = tf.math.divide_no_nan(
        tf.reduce_sum(neg_mean_weights * predictions_kernel),
        tf.reduce_sum(neg_mean_weights))
    pos_neg_mean = tf.math.divide_no_nan(
        tf.reduce_sum(pos_neg_mean_weights * predictions_kernel),
        tf.reduce_sum(pos_neg_mean_weights))

    # MMD is actually the square root of the following quatity. However, the
    # derivative of sqrt is easy to blow up when the value is close to 0. So we
    # do not use that.
    loss = pos_mean - 2 * pos_neg_mean + neg_mean
    return loss
