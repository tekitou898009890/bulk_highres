# This file is always executed
import gradio as gr
import modules.scripts as scripts
import modules.ui

from modules import images
from modules.processing import process_images,Processed
from modules.processing import Processed
from modules.shared import opts, cmd_opts, state

import copy
import math
import os
import sys
import traceback


from PIL import Image

from modules import devices, sd_models, images,extra_networks,sd_samplers
from modules import script_callbacks,processing

from scripts import generation_parameters_copypaste

class Script(scripts.Script):
    
    def __init__(self):
        self.upscale = 1.0
        
    def title(self):
        return "bulk_highres"

    def ui(self, is_img2img):
        with gr.Row():
            if is_img2img:
                self.upscale = gr.Slider(minimum=1.0, maximum=4.0, step=0.1, label="upscale", elem_id=f"upscale", value=2.0)
            prompt_txt = gr.Textbox(label="List of prompt inputs", lines=1, elem_id=self.elem_id("prompt_txt"))
        
        # We start at one line. When the text changes, we jump to seven lines, or two lines if no \n.
        # We don't shrink back to 1, because that causes the control to ignore [enter], and it may
        # be unclear to the user that shift-enter is needed.

        return [prompt_txt,upscale]

    def run(self, p, prompt_txt,upscale):
        # print("tes1")
        
        p.do_not_save_grid = True

        images = []
        all_prompts = []
        infotexts = []
        for filename in os.listdir(prompt_txt):
                if filename.endswith(".png"):
                    file_path = os.path.join(prompt_txt, filename)
                    with Image.open(file_path) as im:
                        metadata = im.info
                    metadata = generation_parameters_copypaste.parse_generation_parameters(metadata['parameters'])
                    
                    copy_p = copy.copy(p)
                    if self.upscale > 1.0:
                        for k, v in metadata.items():
                            if k == 'width' or k == 'height':
                                setattr(copy_p, k, v * self.upscale)
                    else:
                        for k, v in metadata.items():
                            setattr(copy_p, k, v)
                    # for k, v in copy_p.__dict__.items():
                    #     print(f"k:{k},v:{v}")

                    proc = process_images(copy_p)
                    images += proc.images
                    all_prompts += proc.all_prompts
                    infotexts += proc.infotexts
                    
                    

        return Processed(p, images, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)
