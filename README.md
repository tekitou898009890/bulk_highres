# image_regenerator

stable-diffusion-webuiで生成された画像のメタデータを読み取って再度生成を行うスクリプトです。

ガチャで回した画像を特定のフォルダに用意してスクリプトからパスを指定することでフォルダ内の画像を一枚ごとにメタデータを読み取ってhighres.fix・i2iで処理したり、生成した画像を別の拡張(ControlNetやtwo-shotなど)と組み合わせて生成したりできます。

## 使用方法

scriptタブの「bulk_highres」からhighresで回したい画像をディレクトリにまとめて、そのディレクトリを入力。

そのままGenerateボタンを押すと生成されていきます。

i2i_mode:ディレクトリの画像を「i2i_upscale」、「i2i_denoising_strength」で指定した値でi2i処理します。

i2i_upscale:生成する際の拡大倍率。元入力画像のサイズが512x512で、倍率が2であれば1024x1024サイズで出力されます。

i2i_denoising_strength:デノイズ強度。

Additional prompt:追加したいワードをここに記入しておくことで、生成する際に追加プロンプトが自動で挿入されて生成されていきます。

prompt insert position:プロンプトの挿入位置を決定できます。「begin」であれば文頭、「end」であれば文末に挿入されます。

Additional negative prompt:追加したいワードをここに記入しておくことで、生成する際に追加ネガティブプロンプトが自動で挿入されて生成されていきます。

Negative prompt insert position:ネガティブプロンプトの挿入位置を決定できます。「begin」であれば文頭、「end」であれば文末に挿入されます。

### 注意

PNGのメタデータから読み取って回してるだけなので、他の拡張(ControlNetやtwo-shot)で生成した画像は分けて生成した方がいいと思います。

papespaceだと「copy path」でコピーされるパスが「stable-diffusion-webui/outputs」と、「/notebooks/」が抜けているので入力する際は「/notebooks/stable-diffusion-webui/outputs」といった感じで入力してください。

またpaperspaceでは一定の文字数以上のファイル名はアップロード時に「~」で省略されて生成されないことがありますので、その時はリネームしてからアップロードをお願いします。

img2imgタブのscriptからはとりあえず使用できないようになってます。

colabや初めて入れた環境だとhash値が計算されてない故に、上手くマッチングしないことがあるので、その時は再起動してみるといいかもしれません。
