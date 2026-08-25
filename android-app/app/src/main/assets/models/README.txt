PUT YOUR LIVE2D MODELS HERE.

One folder per model. Each folder must contain a complete, exported model:

  assets/models/
    hiyori/
      hiyori.model3.json      <- the entry point
      hiyori.moc3
      hiyori.physics3.json    (optional)
      hiyori.pose3.json       (optional)
      textures/
        texture_00.png
      expressions/
        exp_f01.exp3.json     (optional, but this is what drives emotions)
      motions/
        hiyori_m01.motion3.json
        hiyori_idle_01.motion3.json

Where to get a free model
-------------------------
Live2D's official free sample models (Hiyori, Haru, Mark, Rice, Wanko) are
distributed with the Cubism SDK and in the Live2D "Free Material" collection.
Download the SDK from https://www.live2d.com/en/sdk/download/java/ -- you need
it anyway for Live2DCubismCore.aar.

Licensing matters
-----------------
Each model has its own licence. The official samples are free for development
and testing under the Live2D Free Material Licence Agreement. Check the licence
file shipped with any model before you ship an app containing it.

Expression and motion names
---------------------------
Emotion.kt maps emotional states to expression names. The official sample models
use names like "Smile", "Angry", "Sad", "Relaxed", "Surprised". If your model
uses different names, either rename the .exp3.json entries in model3.json or edit
the mapping in companion/Emotion.kt.

Loading from external storage instead
-------------------------------------
CubismBootstrap.readAsset() also accepts absolute paths, so you can ship models
to /sdcard/Android/data/<pkg>/files/models/ and switch to them without rebuilding.
Set the shared-preference key "model_path" to the absolute path of the
.model3.json.
