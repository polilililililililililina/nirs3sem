import numpy as np
import tensorflow as tf
from PIL import Image


def _find_last_conv_layer(model: tf.keras.Model):
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer
    raise ValueError("Conv2D layer not found in model")


def _apply_colormap(heatmap: np.ndarray) -> np.ndarray:
    normalized = np.clip(heatmap, 0, 1)
    rgb = np.zeros((*normalized.shape, 3), dtype=np.uint8)
    rgb[..., 0] = (normalized * 255).astype(np.uint8)
    rgb[..., 2] = ((1 - normalized) * 80).astype(np.uint8)
    return rgb


def generate_gradcam_overlay(
    model: tf.keras.Model,
    input_tensor: np.ndarray,
    input_path: str,
    overlay_path: str,
    raw_path: str,
) -> dict:
    last_conv_layer = _find_last_conv_layer(model)

    grad_model = tf.keras.models.Model(
        inputs=model.inputs,
        outputs=[last_conv_layer.output, model.output],
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(input_tensor, training=False)
        loss = tf.reduce_max(predictions)

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
    heatmap = tf.maximum(heatmap, 0)

    max_value = tf.reduce_max(heatmap)
    if max_value > 0:
        heatmap = heatmap / max_value

    heatmap_np = heatmap.numpy()
    colored = Image.fromarray(_apply_colormap(heatmap_np)).resize((256, 256))
    colored.save(raw_path)

    original = Image.open(input_path).convert("RGB").resize((256, 256))
    overlay = Image.blend(original, colored, alpha=0.45)
    overlay.save(overlay_path)

    return {
        "heatmap_path": overlay_path,
        "heatmap_raw_path": raw_path,
    }
