# services/captioning.py
from transformers import BlipProcessor, BlipForConditionalGeneration
import config

def load_blip():
    """
    Loads the BLIP captioning model and processor.
    """
    processor = BlipProcessor.from_pretrained(config.BLIP_MODEL_NAME)
    model = BlipForConditionalGeneration.from_pretrained(config.BLIP_MODEL_NAME)
    return processor, model

def generate_caption(processor, model, image):
    """
    Generates a caption and a list of key tags from the image.

    Returns:
        caption: Generated caption string.
        top_tags: List of up to 10 unique, lowercase tags derived from the caption.
    """
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    tags = caption.lower().replace(".", "").split()
    top_tags = list(dict.fromkeys(tags))[:10]
    return caption, top_tags
