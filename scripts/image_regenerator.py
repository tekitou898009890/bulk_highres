# This file is always executed
import gradio as gr
import modules.scripts as scripts
import modules.shared as shared
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

from modules import generation_parameters_copypaste

def matching_metadata_and_sdprocessparam(p,k,v):
    if k == "Prompt":
        setattr(p,"prompt",v)
    elif k == "Negative prompt":
        setattr(p,"negative_prompt",v)
    elif k == "Size-1":
        setattr(p,"width",int(v))
    elif k == "Size-2":
        setattr(p,"height",int(v))
    if k == "Seed":
        setattr(p,"seed",int(v))
    elif k == "Cfg scale":
        setattr(p,"cfg_scale",int(v))
    elif k == "Sampler":
        setattr(p,"sampler_name",v)
    elif k == "Steps":
        setattr(p,"steps",int(v))
    elif k == "Model":
        setattr(p,"model_name",v)
    elif k == "Denoising strength":
        setattr(p,"denoising_strength",float(v))
    elif k == "Hires resize-1":
        setattr(p,"hr_resize_x",int(v))
    elif k == "Hires resize-2":
        setattr(p,"hr_resize_y",int(v))
    else:
        setattr(p,k,v)



class Script(scripts.Script):
    def __init__(self):
        self.is_i2i = False
    def title(self):
        return "image_regenerator"
    
#     def show(self, is_img2img):
#         return scripts.AlwaysVisible
    
    def ui(self, is_img2img):
        
#         with gr.Group():
#             with gr.Accordion("image_regenerator", open=False):
                
#                 enabled = gr.Checkbox(value=False, label="Enabled")
        
        with gr.Row():
            load_model = gr.Checkbox(value = False, interactive =True, label="load_model_in_metadata", elem_id=f"load_model", visible = not is_img2img)

        with gr.Row():
            i2i_mode = gr.Checkbox(value = False, interactive =True, label="i2i_mode", elem_id=f"i2i_mode", visible = not is_img2img)

        with gr.Row():
            i2i_denoising_strength = gr.Slider(minimum=0.0, maximum=1.0, step=0.01,interactive =True, label="i2i_denoising_strength", elem_id=f"i2i_denoising_strength", value=0.7, visible = not is_img2img)

        with gr.Row():
            i2i_upscaler = gr.Slider(minimum=1.0, maximum=4.0, step=0.1,interactive =True, label="i2i_upscale", elem_id=f"i2i_upscale", value=2.0, visible = not is_img2img)

        with gr.Row():
            img_dir = gr.Textbox(label="List of images inputs", nteractive =True, lines=1, elem_id=self.elem_id("img_dir"), visible = not is_img2img)

        with gr.Row():
            ow_ckpt = gr.Checkbox(value = False, interactive =True, label="Hold ckpt used now", elem_id=f"ow_ckpt", visible = not is_img2img)

        with gr.Row():
            ow_seed_mode = gr.Checkbox(value = False, interactive =True, label="Overwrite seed", elem_id=f"ow_seed_mode", visible = not is_img2img)
            ow_seed = gr.Number(value=-1, interactive =True, label="Overwrite seed number", elem_id=f"ow_seed", visible = not is_img2img)


        with gr.Row():
            ow_step_mode = gr.Checkbox(value = False, interactive =True, label="Overwrite steps", elem_id=f"ow_step_mode", visible = not is_img2img)
            ow_step = gr.Slider(minimum=1, maximum=150, step=1,interactive =True, label="Overwrite steps number", elem_id=f"ow_step", value = 50, visible = not is_img2img)

        with gr.Row():
            add_prompt = gr.Textbox(label="Additional prompt", nteractive =True,lines=2, elem_id=self.elem_id("add_prompt"), visible = not is_img2img)

        with gr.Row():
            pos_pormpt = gr.Radio(label="Prompt insert position", nteractive =True, choices=["begin","end"],value="begin", elem_id=self.elem_id("pos_prompt"), visible = not is_img2img)

        with gr.Row():
            add_neg_prompt = gr.Textbox(label="Additional negative prompt", nteractive =True, lines=2, elem_id=self.elem_id("add_prompt"), visible = not is_img2img)

        with gr.Row():
            pos_neg_pormpt = gr.Radio(label="Negative prompt insert position", nteractive =True, choices=["begin","end"],value="end", elem_id=self.elem_id("pos_neg_prompt"), visible = not is_img2img)



        self.is_i2i = is_img2img
        
        # We start at one line. When the text changes, we jump to seven lines, or two lines if no \n.
        # We don't shrink back to 1, because that causes the control to ignore [enter], and it may
        # be unclear to the user that shift-enter is needed.
        
        # return [img_dir,i2i_upscaler,i2i_mode]
        return [img_dir,i2i_upscaler, i2i_denoising_strength, load_model, i2i_mode, add_prompt, pos_pormpt, add_neg_prompt, pos_neg_pormpt, ow_step_mode, ow_step, ow_seed_mode, ow_seed]
        # return [img_dir,i2i_upscaler, i2i_denoising_strength, load_model, i2i_mode, add_prompt, pos_pormpt, add_neg_prompt, pos_neg_pormpt, ow_step_mode, ow_step, ow_seed_mode, ow_seed]

    
    def run(self, p, img_dir,i2i_upscaler, i2i_denoising_strength, load_model, i2i_mode, add_prompt, pos_pormpt, add_neg_prompt, pos_neg_pormpt, ow_step_mode, ow_step, ow_seed_mode, ow_seed):
        # print("tes1")
        
#         self.enabled = enabled

#         if not self.enabled:
#             return
        
        p.do_not_save_grid = True

        images = []
        all_prompts = []
        infotexts = []

        list_meta = []

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
                if pos_pormpt == "begin":
                    metadata['Prompt'] = add_prompt + metadata['Prompt'] 
                elif pos_pormpt == "end":
                    metadata['Prompt'] = metadata['Prompt'] + add_prompt
                
                if pos_neg_pormpt == "begin":
                    metadata['Negative prompt'] = add_neg_prompt + metadata['Negative prompt'] 
                elif pos_neg_pormpt == "end":
                    metadata['Negative prompt'] = metadata['Negative prompt'] + add_neg_prompt
                
                if "Model hash" not in metadata:
                    # if none -> add 0
                    metadata['Model hash'] = "00000000"
                    
                # print(f"{metadata}")
                list_meta.append(metadata)
        
        list_meta.sort(key=lambda x: x['Model hash'])

        for metadata in list_meta:

            if ow_ckpt:
                # change checkpoints
                sdmodels_list = [{"title": x.title, "model_name": x.model_name, "hash": x.shorthash, "sha256": x.sha256, "filename": x.filename} for x in sd_models.checkpoints_list.values()]
    
                # print(f"{sdmodels_list}")
                
                model_name = ""
                if load_model:
                    for model in sdmodels_list:
                            if 'Model hash' in metadata:
                                if model['hash'] == metadata['Model hash']:
                                            model_name = model['model_name']
                                            break
    
                            if 'Model' in metadata:
                                if model['model_name'] == metadata['Model']:
                                    model_name = model['model_name']
                                    break
                    if model_name is None or model_name == "":
                        print("The checkpoint was not found. So it will continue to use the checkpoint currently in use.")
    
                    else:
                        info = sd_models.get_closet_checkpoint_match(model_name)
    
                        if info.name == "nullModelzeros" or info.shorthash == "17d6549029" or info is None:
                            raise RuntimeError(f"nullModelzeros or Unknown checkpoint in '{filename}' ")
    
                        sd_models.reload_model_weights(shared.sd_model, info)        

            # run process
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
                    if k == 'Size-1' or k == 'Size-2':
                        setattr(copy_p, k, v * i2i_upscaler)
                    else:
                        matching_metadata_and_sdprocessparam(copy_p, k, v)
                
            else:
                for k, v in metadata.items():
                    matching_metadata_and_sdprocessparam(copy_p, k, v)
                
                if copy_p.hr_resize_x == 0 and copy_p.hr_scale == 0:
                    setattr(p,"hr_resize_x",int(copy_p.hr_resize_y))
                if copy_p.hr_resize_y == 0 and copy_p.hr_scale == 0:
                    setattr(p,"hr_resize_y",int(copy_p.hr_resize_x))
            
            if ow_step_mode:
                setattr(copy_p,"steps",int(ow_step))
            if ow_seed_mode:
                setattr(copy_p,"seed",int(ow_seed))
                
            # for k, v in copy_p.__dict__.items():
            #    print(f"k:{k},v:{v}")
            try:
                proc = process_images(copy_p)
            except RuntimeError as e:
                if 'out of memory' in str(e):
                    print('CUDA out of memory')
                    continue
                else:
                    raise e #他のエラーはそのままスルー
            
            
            images += proc.images
            all_prompts += proc.all_prompts
            infotexts += proc.infotexts         

        return Processed(p, images, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)
