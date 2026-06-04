"""Кастомные Keras-слои для сериализации без Lambda."""

import tensorflow as tf


@tf.keras.saving.register_keras_serializable(package="mri_analyzer")
class ResizeToReference(tf.keras.layers.Layer):
    """Масштабирует первый тензор до пространственного размера второго."""

    def call(self, inputs):
        tensor, reference = inputs
        h = tf.shape(reference)[1]
        w = tf.shape(reference)[2]
        return tf.image.resize(tensor, [h, w])
