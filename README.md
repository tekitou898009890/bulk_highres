# bulk_highres

stable-diffusion-webuiで生成された画像のメタデータを読み取って再度生成を行うスクリプトになります。

生成した画像を別の拡張(ControlNetやtwo-shotなど)と組み合わせてみたり、ガチャで回した画像の一部を一括でhighres.fix・i2iで処理したりできます。

## 使用方法

scriptタブの「bulk_highres」からhighresで回したい画像をディレクトリにまとめて、そのディレクトリを入力。

そのままGenerateボタンを押すと生成されていきます。

i2i_modeはディレクトリの画像を「i2i_upscale」で指定した倍率でi2iしていきます。

### 注意

PNGのメタデータから読み取って回してるだけなので、他の拡張(ControlNetやtwo-shot)で生成した画像は分けて生成した方がいいと思います。

papespaceだと「copy path」でコピーされるパスが「stable-diffusion-webui/outputs」と、「/notebooks/」が抜けているので入力する際は「/notebooks/stable-diffusion-webui/outputs」といった感じで入力してください。

img2imgタブのscriptからはとりあえず使用できないようになってます。
