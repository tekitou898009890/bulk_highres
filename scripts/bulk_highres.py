# This file is always executed
import gradio as gr
import modules.scripts as scripts
import modules.ui

from modules import images
from modules.processing import process_images,Processed
from modules.processing import StableDiffusionProcessingImg2Img
from modules.shared import opts, cmd_opts, state
from modules.images import read_info_from_image

import copy
import math
import os
import sys
import traceback

from PIL import Image, ImageOps

from modules import devices, sd_models, images,extra_networks,sd_samplers
from modules import script_callbacks,processing

from scripts import generation_parameters_copypaste

class Script(scripts.Script):
    def __init__(self):
        self.is_i2i = False
    def title(self):
        return "bulk_highres"
    
    def ui(self, is_img2img):
        
        with gr.Row():
            i2i_mode = gr.Checkbox(value = False, interactive =True, label="i2i_mode", elem_id=f"i2i_mode")
        
        with gr.Row():
            i2i_denoising_strength = gr.Slider(minimum=0.0, maximum=1.0, step=0.01,interactive =True, label="i2i_denoising_strength", elem_id=f"i2i_denoising_strength", value=0.7)

        with gr.Row():
            i2i_upscaler = gr.Slider(minimum=1.0, maximum=4.0, step=0.1,interactive =True, label="i2i_upscale", elem_id=f"i2i_upscale", value=2.0)

        with gr.Row():
            img_dir = gr.Textbox(label="List of images inputs", lines=1, elem_id=self.elem_id("img_dir"))
        
            
        self.is_i2i = is_img2img

        if is_img2img:
            i2i_mode.visible = False
            i2i_denoising_strength.visible = False
            i2i_upscaler.visible = False
            img_dir.visible = False
        
        # We start at one line. When the text changes, we jump to seven lines, or two lines if no \n.
        # We don't shrink back to 1, because that causes the control to ignore [enter], and it may
        # be unclear to the user that shift-enter is needed.
        
        # return [img_dir,i2i_upscaler,i2i_mode]
        return [img_dir,i2i_upscaler, i2i_denoising_strength, i2i_mode]

    def run(self, p, img_dir, i2i_upscaler, i2i_denoising_strength, i2i_mode):
        # print("tes1")
        
        p.do_not_save_grid = True

        images = []
        all_prompts = []
        infotexts = []
        for filename in os.listdir(img_dir):
            if filename.endswith(".png"):
                file_path = os.path.join(img_dir, filename)
                with Image.open(file_path) as im:
                    metadata,items = read_info_from_image(im)
                    if metadata is None:
                      print(f"Skip {filename} as it has no metadata.")
                      continue
                    # print(f"{metadata}")
                metadata = generation_parameters_copypaste.parse_generation_parameters(metadata)
                
                copy_p = copy.copy(p)
                if i2i_mode:
                    img = Image.open(file_path)
                    img = img.convert("RGB")
                    copy_p = StableDiffusionProcessingImg2Img(
                        init_images=[img],
                        outpath_samples=opts.outdir_samples or opts.outdir_img2img_samples,
                        denoising_strength=i2i_denoising_strength
                    )
                    for k, v in metadata.items():
                        if k == 'width' or k == 'height':
                            setattr(copy_p, k, v * i2i_upscaler)
                        else:
                            setattr(copy_p, k, v)
                    
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
