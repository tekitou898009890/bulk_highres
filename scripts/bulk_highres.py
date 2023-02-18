# This file is always executed
import gradio as gr
import modules.scripts as scripts
import modules.ui

from modules import images
from modules.processing import Processed, process_images
from modules.shared import opts, cmd_opts, state

import copy
import math
import os
import random
import sys
import traceback
import shlex

from PIL import Image

from modules import devices, sd_models, images,extra_networks,sd_samplers
from modules import generation_parameters_copypaste,script_callbacks




def tpl_button_click2(tpl_textbox):
    for filename in os.listdir(tpl_textbox):
        if filename.endswith(".png"):
            file_path = os.path.join(tpl_textbox, filename)
            with Image.open(file_path) as im:
                metadata = im.info
            print(f"{filename}: {metadata}")
            parse_generation_parameters(metadata)

def tpl_button_click3(tpl_textbox):
    print(f"Hello {tpl_textbox}")

class Script(scripts.Script):
    def title(self):
        return "bulk_highres"
    def show(self, is_img2img):
        return modules.scripts.AlwaysVisible
    def ui(self, is_img2img):       
        with gr.Accordion("Bulk Highres Generate",open = False):
        
            prompt_txt = gr.Textbox(label="List of prompt inputs", lines=1, elem_id=self.elem_id("prompt_txt"))
            tpl_button = gr.Button(value='Push me')

            tpl_button.click(
                fn=tpl_button_click3,
                inputs=[prompt_txt],
                outputs=[]
            )
        # We start at one line. When the text changes, we jump to seven lines, or two lines if no \n.
        # We don't shrink back to 1, because that causes the control to ignore [enter], and it may
        # be unclear to the user that shift-enter is needed.

        return [prompt_txt]

    def run(self, p, prompt_txt):
        print("test",file=sys.stderr)
        p.do_not_save_grid = True

        images = []
        all_prompts = []
        infotexts = []
        for filename in os.listdir(prompt_txt):
            if filename.endswith(".png"):
                file_path = os.path.join(prompt_txt, filename)
                with Image.open(file_path) as im:
                    metadata = im.info
                print(f"{filename}: {metadata}")
                res = parse_generation_parameters(metadata)

                copy_p = copy.copy(p)
                for k, v in res.items():
                    setattr(copy_p, k, v)

                proc = process_images(copy_p)
                images += proc.images
                all_prompts += proc.all_prompts
                infotexts += proc.infotexts

        return Processed(p, images, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)
